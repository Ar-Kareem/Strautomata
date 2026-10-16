
import time
from collections import deque

SIZE = 11
N = SIZE * SIZE
INF = 10 ** 6
WIN_SCORE = 10 ** 7

DIRECTIONS = (
    (-1, 0), (-1, 1),
    (0, -1), (0, 1),
    (1, -1), (1, 0),
)

NEIGHBORS = [[] for _ in range(N)]
for r in range(SIZE):
    for c in range(SIZE):
        u = r * SIZE + c
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                NEIGHBORS[u].append(nr * SIZE + nc)

NEIGHBOR_SETS = [set(x) for x in NEIGHBORS]

# A bridge consists of two nonadjacent cells having exactly two common
# neighboring cells.
BRIDGES = []
for a in range(N):
    for b in range(a + 1, N):
        if b in NEIGHBOR_SETS[a]:
            continue
        common = NEIGHBOR_SETS[a].intersection(NEIGHBOR_SETS[b])
        if len(common) == 2:
            x, y = sorted(common)
            BRIDGES.append((a, b, x, y))

BRIDGE_BY_CONNECTOR = [[] for _ in range(N)]
for bridge in BRIDGES:
    a, b, x, y = bridge
    BRIDGE_BY_CONNECTOR[x].append(bridge)
    BRIDGE_BY_CONNECTOR[y].append(bridge)


def _splitmix64(x):
    x = (x + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
    z = x
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
    return (z ^ (z >> 31)) & 0xFFFFFFFFFFFFFFFF


ZOBRIST = [[0] * N for _ in range(2)]
_seed = 0x1234ABCD5678EF90
for p in range(2):
    for i in range(N):
        _seed = _splitmix64(_seed)
        ZOBRIST[p][i] = _seed


_DEADLINE = 0.0
_NODES = 0
_TT = {}


class _SearchTimeout(Exception):
    pass


def _piece_hash_index(side):
    return 0 if side == 1 else 1


def _target_cells(side, target):
    if side == 1:
        row = SIZE - 1 if target else 0
        return [row * SIZE + c for c in range(SIZE)]
    col = SIZE - 1 if target else 0
    return [r * SIZE + col for r in range(SIZE)]


def _edge_virtual_stones(board, side, target):
    """Stones connected to an edge by an intact two-cell edge bridge."""
    result = []
    enemy = -side

    if side == 1:
        if not target:
            # Stone (1,c), connectors (0,c) and (0,c+1).
            for c in range(SIZE - 1):
                stone = SIZE + c
                x = c
                y = c + 1
                if (board[stone] == side and
                        board[x] != enemy and board[y] != enemy):
                    result.append(stone)
        else:
            # Stone (9,c), connectors (10,c) and (10,c-1).
            for c in range(1, SIZE):
                stone = (SIZE - 2) * SIZE + c
                x = (SIZE - 1) * SIZE + c
                y = (SIZE - 1) * SIZE + c - 1
                if (board[stone] == side and
                        board[x] != enemy and board[y] != enemy):
                    result.append(stone)
    else:
        if not target:
            # Stone (r,1), connectors (r,0) and (r+1,0).
            for r in range(SIZE - 1):
                stone = r * SIZE + 1
                x = r * SIZE
                y = (r + 1) * SIZE
                if (board[stone] == side and
                        board[x] != enemy and board[y] != enemy):
                    result.append(stone)
        else:
            # Stone (r,9), connectors (r,10) and (r-1,10).
            for r in range(1, SIZE):
                stone = r * SIZE + SIZE - 2
                x = r * SIZE + SIZE - 1
                y = (r - 1) * SIZE + SIZE - 1
                if (board[stone] == side and
                        board[x] != enemy and board[y] != enemy):
                    result.append(stone)

    return result


def _virtual_links(board, side):
    links = {}
    enemy = -side
    for a, b, x, y in BRIDGES:
        if (board[a] == side and board[b] == side and
                board[x] != enemy and board[y] != enemy):
            links.setdefault(a, []).append(b)
            links.setdefault(b, []).append(a)
    return links


def _path_field(board, side, target=False, virtual=False):
    """0-1 shortest-path distances from one of the player's goal edges."""
    dist = [INF] * N
    queue = deque()
    enemy = -side

    for u in _target_cells(side, target):
        if board[u] != enemy:
            cost = 0 if board[u] == side else 1
            if cost < dist[u]:
                dist[u] = cost
                if cost == 0:
                    queue.appendleft(u)
                else:
                    queue.append(u)

    links = None
    if virtual:
        for u in _edge_virtual_stones(board, side, target):
            if dist[u] > 0:
                dist[u] = 0
                queue.appendleft(u)
        links = _virtual_links(board, side)

    while queue:
        u = queue.popleft()
        du = dist[u]

        for v in NEIGHBORS[u]:
            if board[v] == enemy:
                continue
            weight = 0 if board[v] == side else 1
            nd = du + weight
            if nd < dist[v]:
                dist[v] = nd
                if weight == 0:
                    queue.appendleft(v)
                else:
                    queue.append(v)

        if links is not None:
            for v in links.get(u, ()):
                if du < dist[v]:
                    dist[v] = du
                    queue.appendleft(v)

    return dist


def _connection_distance(board, side, virtual=False):
    dist = _path_field(board, side, False, virtual)
    result = min(dist[u] for u in _target_cells(side, True))

    if virtual:
        for u in _edge_virtual_stones(board, side, True):
            if dist[u] < result:
                result = dist[u]

    return result


def _normal_path_info(board, side):
    start = _path_field(board, side, False, False)
    finish = _path_field(board, side, True, False)
    total = min(start[u] for u in _target_cells(side, True))
    return total, start, finish


def _immediate_cells_from_info(board, total, start, finish):
    if total != 1:
        return []

    result = []
    for i in range(N):
        if board[i] == 0 and start[i] < INF and finish[i] < INF:
            # Both fields count this empty cell, so subtract its cost once.
            if start[i] + finish[i] - 1 == total:
                result.append(i)
    return result


def _immediate_wins(board, side):
    total, start, finish = _normal_path_info(board, side)
    return _immediate_cells_from_info(board, total, start, finish)


def _wins_from(board, move, side):
    seen = {move}
    stack = [move]

    if side == 1:
        first = move // SIZE == 0
        second = move // SIZE == SIZE - 1
    else:
        first = move % SIZE == 0
        second = move % SIZE == SIZE - 1

    while stack:
        u = stack.pop()
        r, c = divmod(u, SIZE)

        if side == 1:
            if r == 0:
                first = True
            elif r == SIZE - 1:
                second = True
        else:
            if c == 0:
                first = True
            elif c == SIZE - 1:
                second = True

        if first and second:
            return True

        for v in NEIGHBORS[u]:
            if v not in seen and board[v] == side:
                seen.add(v)
                stack.append(v)

    return False


def _bridge_strength(board, side):
    enemy = -side
    value = 0

    for a, b, x, y in BRIDGES:
        if board[a] != side or board[b] != side:
            continue

        bx, by = board[x], board[y]
        blocked = (bx == enemy) + (by == enemy)
        empty = (bx == 0) + (by == 0)

        if blocked == 0:
            if empty == 2:
                value += 16
            elif empty == 1:
                value += 7
            else:
                value += 3
        elif blocked == 1 and empty == 1:
            value += 2

    # Intact virtual edge bridges.
    value += 11 * len(_edge_virtual_stones(board, side, False))
    value += 11 * len(_edge_virtual_stones(board, side, True))
    return value


def _positional_strength(board, side):
    value = 0
    for i, stone in enumerate(board):
        if stone != side:
            continue
        r, c = divmod(i, SIZE)
        lateral = c if side == 1 else r
        value += 9 - abs(lateral - 5)
        value += max(0, 5 - (abs(r - 5) + abs(c - 5)) // 2)
    return value


def _side_strength(board, side):
    regular = _connection_distance(board, side, False)
    virtual = _connection_distance(board, side, True)

    regular = min(regular, 30)
    virtual = min(virtual, 30)

    value = -700 * regular - 450 * virtual
    value += _bridge_strength(board, side)
    value += _positional_strength(board, side)
    return value, regular


def _evaluate(board, side):
    mine, my_regular = _side_strength(board, side)
    theirs, opp_regular = _side_strength(board, -side)

    # At a horizon, a move that wins immediately must dominate positional
    # considerations. If both players have such a move, the player to move wins.
    if my_regular == 1:
        return 50000
    if opp_regular == 1:
        return -50000

    return mine - theirs + 4


def _edge_bridge_move_bonus(board, side, move):
    bonus = 0
    enemy = -side
    r, c = divmod(move, SIZE)

    tests = []

    if r == 0:
        if c > 0:
            tests.append(((1, c - 1), (0, c - 1)))
        if c < SIZE - 1:
            tests.append(((1, c), (0, c + 1)))
    if r == SIZE - 1:
        if c > 0:
            tests.append(((SIZE - 2, c), (SIZE - 1, c - 1)))
        if c < SIZE - 1:
            tests.append(((SIZE - 2, c + 1), (SIZE - 1, c + 1)))
    if c == 0:
        if r > 0:
            tests.append(((r - 1, 1), (r - 1, 0)))
        if r < SIZE - 1:
            tests.append(((r, 1), (r + 1, 0)))
    if c == SIZE - 1:
        if r > 0:
            tests.append(((r, SIZE - 2), (r - 1, SIZE - 1)))
        if r < SIZE - 1:
            tests.append(((r + 1, SIZE - 2), (r + 1, SIZE - 1)))

    for stone_rc, other_rc in tests:
        sr, sc = stone_rc
        orow, oc = other_rc
        stone = sr * SIZE + sc
        other = orow * SIZE + oc

        if board[stone] == side and board[other] == enemy:
            bonus += 1500
        elif board[stone] == enemy and board[other] == side:
            bonus += 1500
        elif board[stone] == side and board[other] == 0:
            bonus += 45
        elif board[stone] == enemy and board[other] == 0:
            bonus += 50

    return bonus


def _candidate_score(board, side, move,
                     my_total, my_start, my_finish,
                     opp_total, opp_start, opp_finish):
    r, c = divmod(move, SIZE)
    score = 0

    # General center preference and preference for the center of the
    # player's transverse dimension.
    score += 18 - abs(r - 5) - abs(c - 5)
    lateral = c if side == 1 else r
    score += 12 - 2 * abs(lateral - 5)

    own_neighbors = 0
    enemy_neighbors = 0
    for v in NEIGHBORS[move]:
        if board[v] == side:
            own_neighbors += 1
        elif board[v] == -side:
            enemy_neighbors += 1

    score += min(own_neighbors, 3) * 13
    score += min(enemy_neighbors, 3) * 11

    if my_start[move] < INF and my_finish[move] < INF:
        slack = my_start[move] + my_finish[move] - 1 - my_total
        if slack <= 0:
            score += 105
        elif slack == 1:
            score += 48
        elif slack == 2:
            score += 15

    if opp_start[move] < INF and opp_finish[move] < INF:
        slack = opp_start[move] + opp_finish[move] - 1 - opp_total
        if slack <= 0:
            score += 112
        elif slack == 1:
            score += 52
        elif slack == 2:
            score += 17

    # General and forced bridge responses.
    for a, b, x, y in BRIDGE_BY_CONNECTOR[move]:
        other = y if move == x else x
        if board[a] == side and board[b] == side:
            if board[other] == -side:
                score += 1700
            elif board[other] == 0:
                score += 44
        elif board[a] == -side and board[b] == -side:
            if board[other] == side:
                score += 1650
            elif board[other] == 0:
                score += 50

    score += _edge_bridge_move_bonus(board, side, move)
    return score


def _generate_candidates(board, side, limit, tt_move=-1):
    my_total, my_start, my_finish = _normal_path_info(board, side)
    my_wins = _immediate_cells_from_info(
        board, my_total, my_start, my_finish
    )
    if my_wins:
        if tt_move in my_wins:
            my_wins.remove(tt_move)
            my_wins.insert(0, tt_move)
        return my_wins, True

    opp_total, opp_start, opp_finish = _normal_path_info(board, -side)
    opp_wins = _immediate_cells_from_info(
        board, opp_total, opp_start, opp_finish
    )

    # One enemy winning cell is a forced block. Multiple distinct winning
    # cells constitute an unavoidable loss, so search the possible blocks.
    if opp_wins:
        if tt_move in opp_wins:
            opp_wins.remove(tt_move)
            opp_wins.insert(0, tt_move)
        return opp_wins, False

    scored = []
    for move in range(N):
        if board[move] != 0:
            continue
        score = _candidate_score(
            board, side, move,
            my_total, my_start, my_finish,
            opp_total, opp_start, opp_finish
        )
        if move == tt_move:
            score += 100000
        scored.append((score, move))

    scored.sort(reverse=True)
    if limit < len(scored):
        scored = scored[:limit]
    return [move for _, move in scored], False


def _branch_limit(empty_count):
    if empty_count > 80:
        return 11
    if empty_count > 50:
        return 13
    if empty_count > 28:
        return 16
    return empty_count


def _negamax(board, side, depth, alpha, beta, board_hash, ply, empty_count):
    global _NODES
    _NODES += 1
    if (_NODES & 31) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout

    if depth <= 0:
        return _evaluate(board, side)

    key = (board_hash, side)
    entry = _TT.get(key)
    tt_move = -1
    old_alpha = alpha
    original_beta = beta

    if entry is not None:
        stored_depth, stored_score, flag, tt_move = entry
        if stored_depth >= depth:
            if flag == 0:
                return stored_score
            if flag == 1:
                alpha = max(alpha, stored_score)
            else:
                beta = min(beta, stored_score)
            if alpha >= beta:
                return stored_score

    limit = _branch_limit(empty_count)
    moves, has_immediate_win = _generate_candidates(
        board, side, limit, tt_move
    )

    if has_immediate_win:
        return WIN_SCORE - ply

    if not moves:
        return _evaluate(board, side)

    best_score = -WIN_SCORE * 2
    best_move = moves[0]
    hash_index = _piece_hash_index(side)

    for move in moves:
        if time.perf_counter() >= _DEADLINE:
            raise _SearchTimeout

        board[move] = side
        new_hash = board_hash ^ ZOBRIST[hash_index][move]

        if _wins_from(board, move, side):
            score = WIN_SCORE - ply
        else:
            score = -_negamax(
                board, -side, depth - 1,
                -beta, -alpha, new_hash,
                ply + 1, empty_count - 1
            )

        board[move] = 0

        if score > best_score:
            best_score = score
            best_move = move
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    if best_score <= old_alpha:
        flag = 2  # Upper bound
    elif best_score >= original_beta:
        flag = 1  # Lower bound
    else:
        flag = 0  # Exact

    _TT[key] = (depth, best_score, flag, best_move)
    return best_score


def policy(me: list[tuple[int, int]],
           opp: list[tuple[int, int]],
           color: str) -> tuple[int, int]:
    global _DEADLINE, _NODES, _TT

    start_time = time.perf_counter()
    side = 1 if color == 'b' else -1
    board = [0] * N

    for r, c in me:
        if 0 <= r < SIZE and 0 <= c < SIZE:
            board[r * SIZE + c] = side
    for r, c in opp:
        if 0 <= r < SIZE and 0 <= c < SIZE:
            board[r * SIZE + c] = -side

    legal = [i for i in range(N) if board[i] == 0]

    # A valid nonterminal Hex position always has a legal move.
    if not legal:
        return (0, 0)

    # Establish a guaranteed legal fallback before doing any search.
    fallback = legal[0]

    # Strong and deterministic first move.
    if len(legal) == N:
        return (5, 5)

    # Exact tactical checks.
    wins = _immediate_wins(board, side)
    if wins:
        move = wins[0]
        return divmod(move, SIZE)

    enemy_wins = _immediate_wins(board, -side)
    if len(enemy_wins) == 1:
        move = enemy_wins[0]
        return divmod(move, SIZE)
    if len(enemy_wins) > 1:
        # The position is tactically lost, but this is still a legal move.
        move = enemy_wins[0]
        return divmod(move, SIZE)

    board_hash = 0
    for i, stone in enumerate(board):
        if stone == 1:
            board_hash ^= ZOBRIST[0][i]
        elif stone == -1:
            board_hash ^= ZOBRIST[1][i]

    empty_count = len(legal)
    root_limit = empty_count
    if empty_count > 75:
        root_limit = 28
    elif empty_count > 45:
        root_limit = 32
    elif empty_count > 28:
        root_limit = 36

    root_moves, _ = _generate_candidates(
        board, side, root_limit, -1
    )
    if root_moves:
        fallback = root_moves[0]
    else:
        return divmod(fallback, SIZE)

    _DEADLINE = start_time + 0.92
    _NODES = 0
    _TT = {}

    best_move = fallback
    ordered_moves = root_moves[:]
    hash_index = _piece_hash_index(side)

    # Iterative deepening guarantees that the last fully completed iteration
    # supplies the returned move.
    for depth in range(1, 8):
        iteration_scores = []
        iteration_best = ordered_moves[0]
        iteration_value = -WIN_SCORE * 2
        alpha = -WIN_SCORE * 2
        beta = WIN_SCORE * 2

        try:
            for move in ordered_moves:
                if time.perf_counter() >= _DEADLINE:
                    raise _SearchTimeout

                board[move] = side
                new_hash = board_hash ^ ZOBRIST[hash_index][move]

                if _wins_from(board, move, side):
                    score = WIN_SCORE
                else:
                    score = -_negamax(
                        board, -side, depth - 1,
                        -beta, -alpha, new_hash,
                        1, empty_count - 1
                    )

                board[move] = 0
                iteration_scores.append((score, move))

                if score > iteration_value:
                    iteration_value = score
                    iteration_best = move
                if score > alpha:
                    alpha = score

            # Only commit results from a fully completed iteration.
            best_move = iteration_best
            iteration_scores.sort(reverse=True)
            ordered_moves = [move for _, move in iteration_scores]

            if iteration_value >= WIN_SCORE - 20:
                break

        except _SearchTimeout:
            # Restore defensively in case timeout occurred in recursive search.
            for move in legal:
                if board[move] == side and move not in {
                    r * SIZE + c for r, c in me
                }:
                    board[move] = 0
            break

    # Final legality guard.
    if best_move < 0 or best_move >= N or best_move not in legal:
        best_move = fallback
    if best_move not in legal:
        best_move = legal[0]

    return divmod(best_move, SIZE)
