import gc
import time

ROWS = 5
COLS = 6
CELLS = ROWS * COLS
FULL_MASK = (1 << CELLS) - 1
MATE = 1_000_000

# Cells from which horizontal shifts cannot wrap around a row.
NOT_LEFT = 0
NOT_RIGHT = 0
for _r in range(ROWS):
    for _c in range(COLS):
        _bit = 1 << (_r * COLS + _c)
        if _c > 0:
            NOT_LEFT |= _bit
        if _c < COLS - 1:
            NOT_RIGHT |= _bit

# Orthogonal-neighbor masks.
ADJ = [0] * CELLS
for _r in range(ROWS):
    for _c in range(COLS):
        _i = _r * COLS + _c
        _mask = 0
        if _r > 0:
            _mask |= 1 << (_i - COLS)
        if _c < COLS - 1:
            _mask |= 1 << (_i + 1)
        if _r < ROWS - 1:
            _mask |= 1 << (_i + COLS)
        if _c > 0:
            _mask |= 1 << (_i - 1)
        ADJ[_i] = _mask

# Transposition entries are:
# key -> (searched_depth, score, flag, best_move)
# flag: 0 exact, 1 lower bound, 2 upper bound.
_TT = {}
_HISTORY = [0] * (CELLS * CELLS)

_DEADLINE = 0.0
_NODES = 0
_KILLERS = [[-1, -1] for _ in range(CELLS + 4)]


class _SearchTimeout(Exception):
    pass


def _to_bits(board) -> int:
    """Accept nested lists, NumPy-style arrays, or a flat length-30 list."""
    bits = 0

    try:
        board[0][0]

        def get_value(r, c):
            return board[r][c]
    except (TypeError, IndexError, KeyError):
        try:
            board[0, 0]

            def get_value(r, c):
                return board[r, c]
        except (TypeError, IndexError, KeyError):

            def get_value(r, c):
                return board[r * COLS + c]

    for r in range(ROWS):
        for c in range(COLS):
            if get_value(r, c):
                bits |= 1 << (r * COLS + c)
    return bits


def _moves(own: int, enemy: int) -> list[int]:
    """Moves are encoded as source * 30 + destination."""
    result = []

    # Up
    targets = (own >> COLS) & enemy
    while targets:
        bit = targets & -targets
        d = bit.bit_length() - 1
        result.append((d + COLS) * CELLS + d)
        targets ^= bit

    # Right
    targets = ((own & NOT_RIGHT) << 1) & enemy
    while targets:
        bit = targets & -targets
        d = bit.bit_length() - 1
        result.append((d - 1) * CELLS + d)
        targets ^= bit

    # Down
    targets = ((own << COLS) & FULL_MASK) & enemy
    while targets:
        bit = targets & -targets
        d = bit.bit_length() - 1
        result.append((d - COLS) * CELLS + d)
        targets ^= bit

    # Left
    targets = ((own & NOT_LEFT) >> 1) & enemy
    while targets:
        bit = targets & -targets
        d = bit.bit_length() - 1
        result.append((d + 1) * CELLS + d)
        targets ^= bit

    return result


def _play(own: int, enemy: int, move: int) -> tuple[int, int]:
    """Apply a move and return the state from the next player's perspective."""
    source = move // CELLS
    destination = move - source * CELLS
    source_bit = 1 << source
    destination_bit = 1 << destination

    moved_side = (own ^ source_bit) | destination_bit
    captured_side = enemy ^ destination_bit

    # The opponent is now the side to move.
    return captured_side, moved_side


def _evaluate(own: int, enemy: int, moves: list[int]) -> int:
    """
    Structural leaf evaluation.

    Besides movable-piece concentration, it measures how many contact edges
    each side could eliminate with its best immediate capture. A move that
    removes every contact edge is an actual immediate win.
    """
    edge_count = len(moves)
    own_degree = [0] * CELLS
    enemy_degree = [0] * CELLS
    own_sources = 0
    enemy_sources = 0

    for move in moves:
        source = move // CELLS
        destination = move - source * CELLS
        own_degree[source] += 1
        enemy_degree[destination] += 1
        own_sources |= 1 << source
        enemy_sources |= 1 << destination

    own_square_sum = 0
    enemy_square_sum = 0
    x = own_sources
    while x:
        bit = x & -x
        i = bit.bit_length() - 1
        degree = own_degree[i]
        own_square_sum += degree * degree
        x ^= bit

    x = enemy_sources
    while x:
        bit = x & -x
        i = bit.bit_length() - 1
        degree = enemy_degree[i]
        enemy_square_sum += degree * degree
        x ^= bit

    best_own_edges = edge_count + 8
    best_enemy_edges = edge_count + 8

    for move in moves:
        source = move // CELLS
        destination = move - source * CELLS

        common_removed = (
            own_degree[source] + enemy_degree[destination] - 1
        )

        # Contact edges after own source -> destination.
        resulting_own = (
            edge_count
            - common_removed
            + (ADJ[destination] & enemy).bit_count()
        )
        if resulting_own == 0:
            return MATE
        if resulting_own < best_own_edges:
            best_own_edges = resulting_own

        # Contact edges if the enemy instead made the reverse-oriented move.
        resulting_enemy = (
            edge_count
            - common_removed
            + (ADJ[source] & own).bit_count()
        )
        if resulting_enemy < best_enemy_edges:
            best_enemy_edges = resulting_enemy

    movable_own = own_sources.bit_count()
    movable_enemy = enemy_sources.bit_count()

    score = 0
    score += 44 * (best_enemy_edges - best_own_edges)
    score += 7 * (own_square_sum - enemy_square_sum)
    score += 9 * (movable_enemy - movable_own)
    score += 2 * (own.bit_count() - enemy.bit_count())

    # Small first-move/initiative bonus.
    score += 4
    return score


def _ordered_moves(
    moves: list[int],
    own: int,
    enemy: int,
    tt_move: int,
    ply: int,
) -> list[int]:
    if len(moves) <= 1:
        return moves

    edge_count = len(moves)
    killer0, killer1 = _KILLERS[ply]
    ranked = []

    for move in moves:
        source = move // CELLS
        destination = move - source * CELLS

        source_degree = (ADJ[source] & enemy).bit_count()
        destination_degree = (ADJ[destination] & own).bit_count()
        new_contacts = (ADJ[destination] & enemy).bit_count()

        resulting_edges = (
            edge_count
            - source_degree
            - destination_degree
            + 1
            + new_contacts
        )

        rank = _HISTORY[move] - 32 * resulting_edges

        if resulting_edges == 0:
            rank += 100_000
        if move == killer0:
            rank += 40_000
        elif move == killer1:
            rank += 20_000
        if move == tt_move:
            rank += 1_000_000

        ranked.append((rank, move))

    ranked.sort(reverse=True)
    return [move for _, move in ranked]


def _store_tt(key: int, depth: int, score: int, flag: int, best: int) -> None:
    old = _TT.get(key)
    if old is None or depth > old[0] or (
        depth == old[0] and flag == 0 and old[2] != 0
    ):
        _TT[key] = (depth, score, flag, best)


def _search(
    own: int,
    enemy: int,
    depth: int,
    alpha: int,
    beta: int,
    ply: int,
) -> int:
    global _NODES

    _NODES += 1
    if (_NODES & 255) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout

    key = own | (enemy << CELLS)
    entry = _TT.get(key)
    tt_move = -1

    if entry is not None:
        stored_depth, stored_score, stored_flag, tt_move = entry
        if stored_depth >= depth:
            if stored_flag == 0:
                return stored_score
            if stored_flag == 1:
                if stored_score > alpha:
                    alpha = stored_score
            else:
                if stored_score < beta:
                    beta = stored_score
            if alpha >= beta:
                return stored_score

    window_alpha = alpha
    window_beta = beta

    legal = _moves(own, enemy)
    if not legal:
        _store_tt(key, depth, -MATE, 0, -1)
        return -MATE

    if depth <= 0:
        value = _evaluate(own, enemy, legal)
        _store_tt(key, depth, value, 0, -1)
        return value

    legal = _ordered_moves(legal, own, enemy, tt_move, ply)

    best_score = -MATE - 1
    best_move = legal[0]

    for index, move in enumerate(legal):
        next_own, next_enemy = _play(own, enemy, move)

        if index == 0:
            score = -_search(
                next_own,
                next_enemy,
                depth - 1,
                -beta,
                -alpha,
                ply + 1,
            )
        else:
            # Principal-variation search: try a null window first.
            score = -_search(
                next_own,
                next_enemy,
                depth - 1,
                -alpha - 1,
                -alpha,
                ply + 1,
            )
            if alpha < score < beta:
                score = -_search(
                    next_own,
                    next_enemy,
                    depth - 1,
                    -beta,
                    -alpha,
                    ply + 1,
                )

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            killers = _KILLERS[ply]
            if move != killers[0]:
                killers[1] = killers[0]
                killers[0] = move
            _HISTORY[move] = min(
                6000, _HISTORY[move] + depth * depth + 1
            )
            break

    if best_score <= window_alpha:
        flag = 2
    elif best_score >= window_beta:
        flag = 1
    else:
        flag = 0

    _store_tt(key, depth, best_score, flag, best_move)
    return best_score


def _move_string(move: int) -> str:
    source = move // CELLS
    destination = move - source * CELLS
    row, col = divmod(source, COLS)

    if destination == source - COLS:
        direction = "U"
    elif destination == source + 1:
        direction = "R"
    elif destination == source + COLS:
        direction = "D"
    else:
        direction = "L"

    return f"{row},{col},{direction}"


def policy(you: list[int], opponent: list[int]) -> str:
    global _DEADLINE, _NODES, _KILLERS

    own = _to_bits(you)
    enemy = _to_bits(opponent)
    legal = _moves(own, enemy)

    # Terminal states normally are not submitted to a policy. This preserves
    # the required return type if one is supplied anyway.
    if not legal:
        return "0,0,U"

    # Keep a legal answer available even if every search iteration times out.
    best_move = legal[0]
    root_key = own | (enemy << CELLS)

    # Bound persistent cache memory while retaining useful states between turns.
    if len(_TT) > 350_000:
        _TT.clear()

    # Gradually age history values so old games cannot dominate ordering.
    for i, value in enumerate(_HISTORY):
        if value > 3000:
            _HISTORY[i] = value // 2

    _KILLERS = [[-1, -1] for _ in range(CELLS + 4)]
    _NODES = 0
    _DEADLINE = time.perf_counter() + 0.93

    total_pieces = own.bit_count() + enemy.bit_count()
    maximum_depth = max(1, total_pieces - 1)

    gc_was_enabled = gc.isenabled()
    if gc_was_enabled:
        gc.disable()

    try:
        for depth in range(1, maximum_depth + 1):
            try:
                value = _search(
                    own, enemy, depth, -MATE - 1, MATE + 1, 0
                )
            except _SearchTimeout:
                break

            root_entry = _TT.get(root_key)
            if root_entry is not None and root_entry[3] != -1:
                best_move = root_entry[3]

            # A mate score is a genuine terminal proof, including immediate
            # wins recognized by the tactical leaf evaluator.
            if value == MATE or value == -MATE:
                break

            if time.perf_counter() >= _DEADLINE:
                break
    finally:
        if gc_was_enabled:
            gc.enable()

    return _move_string(best_move)
