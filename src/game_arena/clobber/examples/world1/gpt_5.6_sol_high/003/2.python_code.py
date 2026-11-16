
"""Clobber policy for a 5x6 board."""

from time import perf_counter


ROWS = 5
COLS = 6
CELLS = ROWS * COLS
FULL_MASK = (1 << CELLS) - 1

DIR_CHARS = ("U", "R", "D", "L")

COL0_MASK = sum(1 << (r * COLS) for r in range(ROWS))
COL5_MASK = sum(1 << (r * COLS + COLS - 1) for r in range(ROWS))
NOT_COL0 = FULL_MASK ^ COL0_MASK
NOT_COL5 = FULL_MASK ^ COL5_MASK

# Move code is source_cell * 4 + direction.
SOURCE_BITS = [0] * (CELLS * 4)
DEST_BITS = [0] * (CELLS * 4)
MOVE_STRINGS = [""] * (CELLS * 4)

for row in range(ROWS):
    for col in range(COLS):
        source = row * COLS + col
        for direction, char in enumerate(DIR_CHARS):
            nr, nc = row, col
            if char == "U":
                nr -= 1
            elif char == "R":
                nc += 1
            elif char == "D":
                nr += 1
            else:
                nc -= 1

            code = source * 4 + direction
            MOVE_STRINGS[code] = f"{row},{col},{char}"
            SOURCE_BITS[code] = 1 << source

            if 0 <= nr < ROWS and 0 <= nc < COLS:
                DEST_BITS[code] = 1 << (nr * COLS + nc)


MATE = 30000
INF = 32000

EXACT = 0
LOWER = 1
UPPER = 2

_TT = {}
_HISTORY = [0] * (CELLS * 4)
_KILLERS = [[-1, -1] for _ in range(32)]
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _to_bits(board) -> int:
    """Convert a nested list, flat list, or numpy-like array to a bitboard."""
    result = 0
    for row in range(ROWS):
        for col in range(COLS):
            try:
                value = board[row][col]
            except (TypeError, IndexError):
                value = board[row * COLS + col]
            if value:
                result |= 1 << (row * COLS + col)
    return result


def _moves(player: int, enemy: int) -> list[int]:
    """Generate all directed captures from player onto enemy."""
    result = []

    # Up: destination bit is source shifted down by six bit positions.
    bits = (player >> COLS) & enemy
    while bits:
        bit = bits & -bits
        dest = bit.bit_length() - 1
        result.append((dest + COLS) * 4)
        bits ^= bit

    # Right.
    bits = ((player & NOT_COL5) << 1) & enemy
    while bits:
        bit = bits & -bits
        dest = bit.bit_length() - 1
        result.append((dest - 1) * 4 + 1)
        bits ^= bit

    # Down.
    bits = ((player << COLS) & FULL_MASK) & enemy
    while bits:
        bit = bits & -bits
        dest = bit.bit_length() - 1
        result.append((dest - COLS) * 4 + 2)
        bits ^= bit

    # Left.
    bits = ((player & NOT_COL0) >> 1) & enemy
    while bits:
        bit = bits & -bits
        dest = bit.bit_length() - 1
        result.append((dest + 1) * 4 + 3)
        bits ^= bit

    return result


def _mobility(player: int, enemy: int) -> int:
    """Count legal captures without allocating a move list."""
    return (
        ((player >> COLS) & enemy).bit_count()
        + (((player & NOT_COL5) << 1) & enemy).bit_count()
        + (((player << COLS) & FULL_MASK) & enemy).bit_count()
        + (((player & NOT_COL0) >> 1) & enemy).bit_count()
    )


def _apply(player: int, enemy: int, move: int) -> tuple[int, int]:
    """Apply a move, returning mover pieces and remaining enemy pieces."""
    source = SOURCE_BITS[move]
    destination = DEST_BITS[move]
    new_player = (player ^ source) | destination
    new_enemy = enemy ^ destination
    return new_player, new_enemy


def _annotate(player: int, enemy: int, moves: list[int]):
    """Attach resulting opponent mobility to each move."""
    result = []
    winning_move = -1

    for move in moves:
        new_player, new_enemy = _apply(player, enemy, move)
        child_mobility = _mobility(new_enemy, new_player)
        result.append((move, child_mobility))
        if child_mobility == 0 and winning_move == -1:
            winning_move = move

    return result, winning_move


def _active_sources(items) -> int:
    mask = 0
    for move, _ in items:
        mask |= SOURCE_BITS[move]
    return mask.bit_count()


def _evaluate(player: int, enemy: int, current_items) -> int:
    """
    Evaluate how effectively each side can reduce the next player's
    mobility. Lower resulting mobility is strategically desirable.
    """
    current_values = [mobility for _, mobility in current_items]

    enemy_moves = _moves(enemy, player)
    enemy_items, _ = _annotate(enemy, player, enemy_moves)
    enemy_values = [mobility for _, mobility in enemy_items]

    current_values.sort()
    enemy_values.sort()

    current_best = current_values[0]
    enemy_best = enemy_values[0]

    sample_count = min(4, len(current_values))
    current_sample = sum(current_values[:sample_count])
    enemy_sample = sum(enemy_values[:sample_count])

    current_active = _active_sources(current_items)
    enemy_active = _active_sources(enemy_items)

    score = 32 * (enemy_best - current_best)
    score += 5 * (enemy_sample - current_sample)
    score += 6 * (current_active - enemy_active)

    # Keep all heuristic values far below proven win/loss values.
    if score > 5000:
        return 5000
    if score < -5000:
        return -5000
    return score


def _store(key, depth: int, value: int, flag: int, best_move: int) -> None:
    old = _TT.get(key)
    if old is not None and old[0] > depth:
        return

    # Avoid uncontrolled growth while still permitting updates to old keys.
    if old is not None or len(_TT) < 250000:
        _TT[key] = (depth, value, flag, best_move)


def _ordered(items, tt_move: int, depth: int):
    killer_index = min(max(depth, 0), len(_KILLERS) - 1)
    killer_a, killer_b = _KILLERS[killer_index]

    decorated = []
    for move, child_mobility in items:
        priority = -96 * child_mobility + min(_HISTORY[move], 4000)

        if move == killer_b:
            priority += 5000
        if move == killer_a:
            priority += 7000
        if move == tt_move:
            priority += 1000000

        decorated.append((priority, move, child_mobility))

    decorated.sort(reverse=True)
    return [(move, mobility) for _, move, mobility in decorated]


def _search(player: int, enemy: int, depth: int, alpha: int, beta: int) -> int:
    global _NODES

    _NODES += 1
    if (_NODES & 255) == 0 and perf_counter() >= _DEADLINE:
        raise _SearchTimeout

    key = (player, enemy)
    entry = _TT.get(key)
    tt_move = -1

    if entry is not None:
        stored_depth, stored_value, stored_flag, tt_move = entry
        if stored_depth >= depth:
            if stored_flag == EXACT:
                return stored_value
            if stored_flag == LOWER:
                if stored_value > alpha:
                    alpha = stored_value
            else:
                if stored_value < beta:
                    beta = stored_value
            if alpha >= beta:
                return stored_value

    alpha_original = alpha
    beta_original = beta

    legal = _moves(player, enemy)
    if not legal:
        _store(key, depth, -MATE, EXACT, -1)
        return -MATE

    items, winning_move = _annotate(player, enemy, legal)

    # This is an exact tactical result: the move leaves the opponent immobile.
    if winning_move != -1:
        _store(key, depth, MATE, EXACT, winning_move)
        return MATE

    # Extend very short forced sequences slightly beyond the nominal horizon.
    forced_extension = depth <= 0 and len(items) == 1 and depth > -2

    if depth <= 0 and not forced_extension:
        value = _evaluate(player, enemy, items)
        best_hint = min(items, key=lambda item: item[1])[0]
        _store(key, depth, value, EXACT, best_hint)
        return value

    ordered = _ordered(items, tt_move, depth)

    best_value = -INF
    best_move = ordered[0][0]
    next_depth = depth - 1

    for index, (move, child_mobility) in enumerate(ordered):
        new_player, new_enemy = _apply(player, enemy, move)

        # Swap roles for the opponent's turn.
        child_player = new_enemy
        child_enemy = new_player

        if index == 0:
            value = -_search(
                child_player, child_enemy, next_depth, -beta, -alpha
            )
        else:
            use_reduction = (
                depth >= 4
                and index >= 6
                and move != tt_move
                and child_mobility > 1
            )

            if use_reduction:
                value = -_search(
                    child_player,
                    child_enemy,
                    next_depth - 1,
                    -alpha - 1,
                    -alpha,
                )
                if value > alpha:
                    value = -_search(
                        child_player,
                        child_enemy,
                        next_depth,
                        -beta,
                        -alpha,
                    )
            else:
                # Principal-variation search with a null window first.
                value = -_search(
                    child_player,
                    child_enemy,
                    next_depth,
                    -alpha - 1,
                    -alpha,
                )
                if alpha < value < beta:
                    value = -_search(
                        child_player,
                        child_enemy,
                        next_depth,
                        -beta,
                        -alpha,
                    )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            if depth > 0:
                bonus = depth * depth
                _HISTORY[move] = min(8000, _HISTORY[move] + bonus)

                killer_index = min(depth, len(_KILLERS) - 1)
                if _KILLERS[killer_index][0] != move:
                    _KILLERS[killer_index][1] = _KILLERS[killer_index][0]
                    _KILLERS[killer_index][0] = move
            break

    if best_value <= alpha_original:
        flag = UPPER
    elif best_value >= beta_original:
        flag = LOWER
    else:
        flag = EXACT

    _store(key, depth, best_value, flag, best_move)
    return best_value


def policy(you: list[int], opponent: list[int]) -> str:
    global _TT, _HISTORY, _KILLERS, _DEADLINE, _NODES

    player = _to_bits(you)
    enemy = _to_bits(opponent)

    root_moves = _moves(player, enemy)

    # Game controllers normally never request a move in a terminal position.
    if not root_moves:
        return "0,0,U"

    # Establish a legal answer before doing any timed search.
    best_move = root_moves[0]
    if len(root_moves) == 1:
        return MOVE_STRINGS[best_move]

    _TT = {}
    _HISTORY = [0] * (CELLS * 4)
    _KILLERS = [[-1, -1] for _ in range(32)]
    _NODES = 0
    _DEADLINE = perf_counter() + 0.93

    maximum_depth = player.bit_count() + enemy.bit_count() - 1

    depth = 1
    while depth <= maximum_depth:
        if perf_counter() >= _DEADLINE:
            break

        try:
            score = _search(player, enemy, depth, -INF, INF)
        except _SearchTimeout:
            break

        entry = _TT.get((player, enemy))
        if entry is not None:
            candidate = entry[3]
            if candidate in root_moves:
                best_move = candidate

        # A mate-valued root result is a proven result, not a heuristic.
        if score == MATE or score == -MATE:
            break

        depth += 1

    # Final validation ensures that stale table data can never cause
    # an illegal response.
    if best_move not in root_moves:
        best_move = root_moves[0]

    return MOVE_STRINGS[best_move]
