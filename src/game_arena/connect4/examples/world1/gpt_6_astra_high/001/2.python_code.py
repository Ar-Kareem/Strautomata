
from time import perf_counter

# Seven bits per column: six playable cells and one sentinel.
_BOTTOM = sum(1 << (7 * c) for c in range(7))
_BOARD = sum(63 << (7 * c) for c in range(7))
_COLUMNS = tuple(63 << (7 * c) for c in range(7))

_ORDER = (3, 2, 4, 1, 5, 0, 6)
_COLUMN_BONUS = (0, 4, 8, 12, 7, 3, -1)

_CENTER = _COLUMNS[3]
_ADJACENT = _COLUMNS[2] | _COLUMNS[4]
_FLANKS = _COLUMNS[1] | _COLUMNS[5]
_ODD_ROWS = sum(0x15 << (7 * c) for c in range(7))
_EVEN_ROWS = _BOARD ^ _ODD_ROWS

# Direction, twice direction, three times direction, valid window starts.
_WINDOWS = (
    (1, 2, 3, sum(7 << (7 * c) for c in range(7))),
    (7, 14, 21, sum(63 << (7 * c) for c in range(4))),
    (6, 12, 18, sum(0x38 << (7 * c) for c in range(4))),
    (8, 16, 24, sum(7 << (7 * c) for c in range(4))),
)

_MATE = 30000
_INF = 1000000

# Entries: (searched depth, score, bound type, best move bit).
# Bound types: 0 exact, 1 lower bound, 2 upper bound.
_TT = {}


class _SearchTimeout(Exception):
    pass


def _winning_cells(p, occupied):
    """Empty cells that complete four for p, whether supported or not."""
    result = (p << 1) & (p << 2) & (p << 3)

    left = p << 7
    right = p >> 7
    result |= (
        (left & (p << 14) & ((p << 21) | right))
        | (right & (p >> 14) & ((p >> 21) | left))
    )

    left = p << 6
    right = p >> 6
    result |= (
        (left & (p << 12) & ((p << 18) | right))
        | (right & (p >> 12) & ((p >> 18) | left))
    )

    left = p << 8
    right = p >> 8
    result |= (
        (left & (p << 16) & ((p << 24) | right))
        | (right & (p >> 16) & ((p >> 24) | left))
    )

    return result & (_BOARD ^ occupied)


def _evaluate(p, occupied, remaining, pw, ow, possible):
    opponent = occupied ^ p

    score = 4 * (
        (p & _CENTER).bit_count()
        - (opponent & _CENTER).bit_count()
    )
    score += 2 * (
        (p & _ADJACENT).bit_count()
        - (opponent & _ADJACENT).bit_count()
    )
    score += (
        (p & _FLANKS).bit_count()
        - (opponent & _FLANKS).bit_count()
    )

    score += 24 * (pw.bit_count() - ow.bit_count())

    # The first player generally benefits from odd-height threats;
    # the second player generally benefits from even-height threats.
    if remaining & 1:
        preferred, other_preferred = _EVEN_ROWS, _ODD_ROWS
    else:
        preferred, other_preferred = _ODD_ROWS, _EVEN_ROWS

    score += 8 * (
        (pw & preferred).bit_count()
        - (ow & other_preferred).bit_count()
    )

    # Vertically stacked threats and threats just above a playable cell.
    score += 18 * (
        (pw & (pw >> 1)).bit_count()
        - (ow & (ow >> 1)).bit_count()
    )
    supported_next = possible << 1
    score += 8 * (
        (pw & supported_next).bit_count()
        - (ow & supported_next).bit_count()
    )

    # Count unblocked four-cell windows containing at least two discs.
    for shift, shift2, shift3, starts in _WINDOWS:
        a = p >> shift
        b = p >> shift2
        c = p >> shift3
        x = opponent >> shift
        y = opponent >> shift2
        z = opponent >> shift3

        pairs_p = (p & a) | (b & c) | ((p | a) & (b | c))
        pairs_o = (
            (opponent & x) | (y & z)
            | ((opponent | x) & (y | z))
        )

        open_p = pairs_p & ~(opponent | x | y | z) & starts
        open_o = pairs_o & ~(p | a | b | c) & starts
        score += 3 * (open_p.bit_count() - open_o.bit_count())

    return score


def _pick_column(bits, legal):
    for col in legal:
        if bits & _COLUMNS[col]:
            return col
    return legal[0]


def policy(board: list[list[int]]) -> int:
    deadline = perf_counter() + 0.88

    legal = [
        c for c in _ORDER
        if any(board[r][c] == 0 for r in range(6))
    ]
    if not legal:
        # A full board has no legal action; normally policy is not
        # called after the game has ended.
        return 0

    fallback = legal[0]
    p = 0
    occupied = 0

    for col in range(7):
        for height in range(6):
            cell = board[5 - height][col]
            if cell:
                bit = 1 << (7 * col + height)
                occupied |= bit
                if cell == 1:
                    p |= bit

    remaining = 42 - occupied.bit_count()
    if remaining >= 41:
        return 3 if 3 in legal else fallback

    possible = (occupied + _BOTTOM) & _BOARD
    opponent = occupied ^ p
    pw = _winning_cells(p, occupied)
    ow = _winning_cells(opponent, occupied)

    immediate = possible & pw
    if immediate:
        return _pick_column(immediate, legal)

    forced = possible & ow
    if forced and (forced & (forced - 1)):
        # Two immediate enemy wins cannot both be blocked.
        return _pick_column(forced, legal)

    safe = forced if forced else possible
    # Never supply the support for an enemy winning cell.
    safe &= ~(ow >> 1)

    if not safe:
        return _pick_column(forced or possible, legal)

    if not (safe & (safe - 1)):
        return _pick_column(safe, legal)

    if len(_TT) > 180000:
        _TT.clear()
    table = _TT
    root_key = p + occupied

    # Establish a good legal fallback before beginning timed search.
    best_move = safe & -safe
    fallback_score = -_INF

    for col in legal:
        move = safe & _COLUMNS[col]
        if not move:
            continue

        new_occupied = occupied | move
        new_wins = _winning_cells(p | move, new_occupied)
        next_possible = (new_occupied + _BOTTOM) & _BOARD
        threats = new_wins & next_possible

        if threats and (threats & (threats - 1)):
            return col

        value = -_evaluate(
            opponent,
            new_occupied,
            remaining - 1,
            ow & ~move,
            new_wins,
            next_possible,
        )
        if value > fallback_score:
            fallback_score = value
            best_move = move

    cached = table.get(root_key)
    if cached and cached[3] & safe:
        best_move = cached[3]
        if cached[2] == 0 and (
            abs(cached[1]) >= _MATE or cached[0] >= remaining
        ):
            return _pick_column(best_move, legal)

    killers = [0] * 43
    history = [[0] * 7 for _ in range(2)]
    nodes = 0

    win_cells = _winning_cells
    evaluate = _evaluate
    clock = perf_counter
    bottom = _BOTTOM
    board_mask = _BOARD

    def search(position, mask, my_wins, enemy_wins,
               depth, alpha, beta, left):
        nonlocal nodes

        nodes += 1
        if (nodes & 255) == 0 and clock() >= deadline:
            raise _SearchTimeout

        if left == 0:
            return 0

        # This sum uniquely identifies a legal gravity-based position,
        # including which discs belong to the player to move.
        key = position + mask
        entry = table.get(key)
        tt_move = 0

        if entry is not None:
            old_depth, old_value, bound, tt_move = entry
            if old_depth >= depth:
                if bound == 0:
                    return old_value
                if bound == 1 and old_value >= beta:
                    return old_value
                if bound == 2 and old_value <= alpha:
                    return old_value

        available = (mask + bottom) & board_mask
        winning = available & my_wins

        if winning:
            value = _MATE + left
            table[key] = (64, value, 0, winning & -winning)
            return value

        forced_moves = available & enemy_wins
        if forced_moves and (forced_moves & (forced_moves - 1)):
            value = -_MATE - left + 1
            table[key] = (
                64, value, 0, forced_moves & -forced_moves
            )
            return value

        moves = forced_moves if forced_moves else available
        moves &= ~(enemy_wins >> 1)

        if not moves:
            value = -_MATE - left + 1
            table[key] = (64, value, 0, available & -available)
            return value

        if left <= 2:
            table[key] = (64, 0, 0, moves & -moves)
            return 0

        single_move = not (moves & (moves - 1))

        # Forced moves do not consume search depth.
        if depth <= 0 and not single_move:
            value = evaluate(
                position, mask, left, my_wins, enemy_wins, available
            )
            if entry is None or entry[0] <= 0:
                table[key] = (0, value, 0, 0)
            return value

        next_depth = depth if single_move else depth - 1
        original_alpha = alpha
        null_window = beta == alpha + 1
        enemy = mask ^ position
        hist = history[left & 1]

        best_value = -_INF
        node_best_move = 0
        searched = 0

        # Try the transposition-table move before spending time
        # sorting the remaining moves.
        if tt_move and (tt_move & moves):
            stages = (tt_move, moves ^ tt_move)
        else:
            stages = (moves,)

        for subset in stages:
            if not subset:
                continue

            ordered = []
            while subset:
                move = subset & -subset
                subset ^= move

                new_mask = mask | move
                new_enemy_wins = win_cells(position | move, new_mask)
                next_available = (new_mask + bottom) & board_mask
                threats = new_enemy_wins & next_available

                if threats and (threats & (threats - 1)):
                    # This safe move creates two playable threats.
                    # With no immediate win available, winning in
                    # three plies is the best possible result.
                    value = _MATE + left - 2
                    table[key] = (64, value, 0, move)
                    return value

                col = (move.bit_length() - 1) // 7
                priority = (
                    64 * new_enemy_wins.bit_count()
                    + 512 * bool(threats)
                    + _COLUMN_BONUS[col]
                    + (48 if move == killers[left] else 0)
                    + (min(hist[col], 1024) >> 4)
                )
                ordered.append(
                    (priority, move, new_enemy_wins, bool(threats))
                )

            if len(ordered) > 1:
                ordered.sort(reverse=True)

            for _, move, new_enemy_wins, forcing in ordered:
                new_mask = mask | move
                new_my_wins = enemy_wins & ~move

                if searched == 0 or depth <= 2:
                    value = -search(
                        enemy, new_mask, new_my_wins, new_enemy_wins,
                        next_depth, -beta, -alpha, left - 1
                    )
                else:
                    reduced_depth = next_depth

                    # Conservative late-move reduction: only quiet,
                    # late moves at null-window nodes, and never when
                    # the search is close to reaching the full board.
                    if (
                        null_window
                        and depth >= 5
                        and depth < left - 2
                        and searched >= 3
                        and not forcing
                        and not (new_enemy_wins & ~my_wins)
                    ):
                        reduced_depth -= 1

                    value = -search(
                        enemy, new_mask, new_my_wins, new_enemy_wins,
                        reduced_depth, -alpha - 1, -alpha, left - 1
                    )

                    if reduced_depth != next_depth and value > alpha:
                        value = -search(
                            enemy, new_mask, new_my_wins, new_enemy_wins,
                            next_depth, -alpha - 1, -alpha, left - 1
                        )

                    if alpha < value < beta:
                        value = -search(
                            enemy, new_mask, new_my_wins, new_enemy_wins,
                            next_depth, -beta, -alpha, left - 1
                        )

                searched += 1

                if value > best_value:
                    best_value = value
                    node_best_move = move

                if value > alpha:
                    alpha = value

                if alpha >= beta:
                    if not forcing:
                        killers[left] = move
                        col = (move.bit_length() - 1) // 7
                        hist[col] = min(
                            2048, hist[col] + max(1, depth * depth)
                        )
                    if entry is None or depth >= entry[0]:
                        table[key] = (depth, best_value, 1, node_best_move)
                    return best_value

        flag = 2 if best_value <= original_alpha else 0
        if entry is None or depth >= entry[0] or flag == 0:
            table[key] = (depth, best_value, flag, node_best_move)

        return best_value

    last_score = 0

    try:
        for depth in range(1, remaining + 1):
            if clock() >= deadline:
                break

            if depth >= 4:
                alpha = last_score - 64
                beta = last_score + 64
            else:
                alpha, beta = -_INF, _INF

            score = search(
                p, occupied, pw, ow, depth,
                alpha, beta, remaining
            )

            if score <= alpha or score >= beta:
                if clock() >= deadline:
                    break
                score = search(
                    p, occupied, pw, ow, depth,
                    -_INF, _INF, remaining
                )

            completed = table.get(root_key)
            if completed and completed[3] & safe:
                best_move = completed[3]

            last_score = score
            if abs(score) >= _MATE:
                break

    except _SearchTimeout:
        pass

    return int(_pick_column(best_move, legal))
