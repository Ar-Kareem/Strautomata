
from collections import deque

N = 11
INF = 10 ** 9

# Hex neighbors for the coordinate system described in the prompt.
DIRS = ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1))

ALL_CELLS = [(r, c) for r in range(N) for c in range(N)]
CENTER = (N // 2, N // 2)
CENTER_ORDER = sorted(
    ALL_CELLS,
    key=lambda x: (abs(x[0] - CENTER[0]) + abs(x[1] - CENTER[1]),
                   abs(x[0] - CENTER[0]) ** 2 + abs(x[1] - CENTER[1]) ** 2,
                   x[0], x[1])
)

# Graph-distance-2 offsets, useful for bridge-like virtual connections.
_direct = set(DIRS)
_dist2 = set()
for a in DIRS:
    for b in DIRS:
        off = (a[0] + b[0], a[1] + b[1])
        if off != (0, 0) and off not in _direct:
            _dist2.add(off)
DIST2_DIRS = tuple(sorted(_dist2))


def other_color(color: str) -> str:
    return 'w' if color == 'b' else 'b'


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def neighbors(r: int, c: int):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def build_board(me, opp):
    board = [[0] * N for _ in range(N)]
    for r, c in me:
        if 0 <= r < N and 0 <= c < N:
            board[r][c] = 1
    for r, c in opp:
        if 0 <= r < N and 0 <= c < N:
            board[r][c] = 2
    return board


def empty_cells(board):
    return [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]


def fallback_move(board):
    for r, c in CENTER_ORDER:
        if board[r][c] == 0:
            return (r, c)
    return (0, 0)


def cell_cost(v: int, side: int) -> int:
    if v == side:
        return 0
    if v == 0:
        return 1
    return INF


def shortest_distance(board, side: int, color: str) -> int:
    """
    Minimum number of empty cells side still needs to occupy to connect.
    Own stones cost 0, empty cells cost 1, enemy stones are blocked.
    """
    dist = [[INF] * N for _ in range(N)]
    dq = deque()

    if color == 'b':
        starts = [(0, c) for c in range(N)]
    else:
        starts = [(r, 0) for r in range(N)]

    for r, c in starts:
        cost = cell_cost(board[r][c], side)
        if cost >= INF:
            continue
        if cost < dist[r][c]:
            dist[r][c] = cost
            if cost == 0:
                dq.appendleft((r, c))
            else:
                dq.append((r, c))

    while dq:
        r, c = dq.popleft()
        d = dist[r][c]

        if (color == 'b' and r == N - 1) or (color == 'w' and c == N - 1):
            return d

        for nr, nc in neighbors(r, c):
            cost = cell_cost(board[nr][nc], side)
            if cost >= INF:
                continue
            nd = d + cost
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                if cost == 0:
                    dq.appendleft((nr, nc))
                else:
                    dq.append((nr, nc))

    return INF


def shortest_path_empty_cells(board, side: int, color: str):
    """
    Returns empty cells lying on one current cheapest connection path.
    Used for candidate generation.
    """
    dist = [[INF] * N for _ in range(N)]
    parent = [[None] * N for _ in range(N)]
    dq = deque()

    if color == 'b':
        starts = [(0, c) for c in range(N)]
        targets = [(N - 1, c) for c in range(N)]
    else:
        starts = [(r, 0) for r in range(N)]
        targets = [(r, N - 1) for r in range(N)]

    for r, c in starts:
        cost = cell_cost(board[r][c], side)
        if cost >= INF:
            continue
        dist[r][c] = cost
        if cost == 0:
            dq.appendleft((r, c))
        else:
            dq.append((r, c))

    while dq:
        r, c = dq.popleft()
        d = dist[r][c]
        for nr, nc in neighbors(r, c):
            cost = cell_cost(board[nr][nc], side)
            if cost >= INF:
                continue
            nd = d + cost
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                parent[nr][nc] = (r, c)
                if cost == 0:
                    dq.appendleft((nr, nc))
                else:
                    dq.append((nr, nc))

    best = None
    best_d = INF
    for r, c in targets:
        if dist[r][c] < best_d:
            best_d = dist[r][c]
            best = (r, c)

    if best is None or best_d >= INF:
        return set()

    path = set()
    cur = best
    while cur is not None:
        r, c = cur
        if board[r][c] == 0:
            path.add((r, c))
        cur = parent[r][c]
    return path


def is_winning_after(board, side: int, color: str, move) -> bool:
    r, c = move
    if board[r][c] != 0:
        return False
    board[r][c] = side
    win = shortest_distance(board, side, color) == 0
    board[r][c] = 0
    return win


def winning_moves(board, side: int, color: str):
    wins = []
    for r, c in empty_cells(board):
        board[r][c] = side
        if shortest_distance(board, side, color) == 0:
            wins.append((r, c))
        board[r][c] = 0
    return wins


def span_score(board, side: int, color: str) -> float:
    """
    Rewards large connected components spanning toward the correct edges.
    """
    seen = [[False] * N for _ in range(N)]
    best = 0.0
    total = 0.0

    for sr in range(N):
        for sc in range(N):
            if board[sr][sc] != side or seen[sr][sc]:
                continue

            q = deque([(sr, sc)])
            seen[sr][sc] = True
            cells = []

            while q:
                r, c = q.popleft()
                cells.append((r, c))
                for nr, nc in neighbors(r, c):
                    if not seen[nr][nc] and board[nr][nc] == side:
                        seen[nr][nc] = True
                        q.append((nr, nc))

            if color == 'b':
                vals = [r for r, _ in cells]
            else:
                vals = [c for _, c in cells]

            mn, mx = min(vals), max(vals)
            span = mx - mn + 1
            edge_bonus = 0
            if mn == 0:
                edge_bonus += 3
            if mx == N - 1:
                edge_bonus += 3

            val = span + edge_bonus
            best = max(best, val)
            total += val * val

    return best * 2.5 + total * 0.08


def virtual_bridge_score(board, side: int) -> float:
    """
    Counts bridge-like pairs of stones at graph distance two whose common
    connecting cells have not been occupied by the opponent.
    """
    opp = 3 - side
    score = 0.0

    for r in range(N):
        for c in range(N):
            if board[r][c] != side:
                continue
            for dr, dc in DIST2_DIRS:
                nr, nc = r + dr, c + dc
                if not in_bounds(nr, nc):
                    continue
                if (nr, nc) <= (r, c):
                    continue
                if board[nr][nc] != side:
                    continue

                common = []
                nset = set(neighbors(r, c))
                for x in neighbors(nr, nc):
                    if x in nset:
                        common.append(x)

                if len(common) == 2:
                    blocked = False
                    empties = 0
                    for cr, cc in common:
                        if board[cr][cc] == opp:
                            blocked = True
                            break
                        if board[cr][cc] == 0:
                            empties += 1
                    if not blocked:
                        score += 1.0 + 0.35 * empties

    return score


def evaluate_side(board, side: int, color: str) -> float:
    """
    Static evaluation from side/color perspective.
    """
    opp = 3 - side
    oc = other_color(color)

    my_d = shortest_distance(board, side, color)
    op_d = shortest_distance(board, opp, oc)

    if my_d == 0:
        return 1_000_000.0
    if op_d == 0:
        return -1_000_000.0

    if my_d >= INF:
        my_d = 50
    if op_d >= INF:
        op_d = 50

    # Nonlinear urgency: distance 1 and 2 threats matter a lot in Hex.
    score = 520.0 * (op_d - my_d)
    score += 1900.0 / (my_d + 1.0)
    score -= 1900.0 / (op_d + 1.0)

    score += 13.0 * (span_score(board, side, color) - span_score(board, opp, oc))
    score += 7.0 * (virtual_bridge_score(board, side) - virtual_bridge_score(board, opp))

    return score


def bridge_score_for_move(board, side: int, move) -> float:
    r, c = move
    opp = 3 - side
    score = 0.0

    for dr, dc in DIST2_DIRS:
        nr, nc = r + dr, c + dc
        if not in_bounds(nr, nc):
            continue
        if board[nr][nc] != side:
            continue

        common = []
        nset = set(neighbors(r, c))
        for x in neighbors(nr, nc):
            if x in nset:
                common.append(x)

        if len(common) == 2:
            blocked = False
            for cr, cc in common:
                if board[cr][cc] == opp:
                    blocked = True
                    break
            if not blocked:
                score += 1.0

    return score


def local_move_score(board, side: int, color: str, move) -> float:
    r, c = move
    opp = 3 - side

    adj_own = 0
    adj_opp = 0
    for nr, nc in neighbors(r, c):
        if board[nr][nc] == side:
            adj_own += 1
        elif board[nr][nc] == opp:
            adj_opp += 1

    center_dist = abs(r - CENTER[0]) + abs(c - CENTER[1])
    score = 7.0 * (10 - center_dist)
    score += 18.0 * adj_own
    score += 13.0 * adj_opp
    score += 20.0 * bridge_score_for_move(board, side, move)

    # Slight orientation preference: black wants vertical structure,
    # white wants horizontal structure.
    if color == 'b':
        score -= 1.6 * abs(c - CENTER[1])
    else:
        score -= 1.6 * abs(r - CENTER[0])

    return score


def candidate_set(board, side: int, color: str):
    empties = set(empty_cells(board))
    if not empties:
        return []

    occupied = [(r, c) for r in range(N) for c in range(N) if board[r][c] != 0]
    if len(occupied) <= 1:
        return list(empties)

    cand = set()

    # Moves adjacent to existing stones are usually tactically relevant.
    for r, c in occupied:
        for nr, nc in neighbors(r, c):
            if board[nr][nc] == 0:
                cand.add((nr, nc))

    # Include current shortest-path cells for both players and their vicinity.
    oc = other_color(color)
    for s, col in ((side, color), (3 - side, oc)):
        p = shortest_path_empty_cells(board, s, col)
        for x in p:
            if x in empties:
                cand.add(x)
            for y in neighbors(*x):
                if y in empties:
                    cand.add(y)

    # Always include a central region for opening/shape stability.
    for x in CENTER_ORDER[:31]:
        if x in empties:
            cand.add(x)

    if len(cand) < 18:
        cand |= empties

    return list(cand)


def ordered_moves(board, side: int, color: str, limit: int, all_moves: bool = False):
    if all_moves:
        moves = empty_cells(board)
    else:
        moves = candidate_set(board, side, color)

    scored = []
    for m in moves:
        r, c = m
        if board[r][c] != 0:
            continue

        board[r][c] = side
        if shortest_distance(board, side, color) == 0:
            score = 1_000_000.0
        else:
            score = evaluate_side(board, side, color)
        board[r][c] = 0

        score += local_move_score(board, side, color, m)
        # Tiny deterministic tie-break toward center.
        score -= 0.001 * (abs(r - CENTER[0]) + abs(c - CENTER[1]))
        scored.append((score, m))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [m for _, m in scored[:limit]]


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    board = build_board(me, opp)
    opp_color = other_color(color)

    try:
        # Opening preferences.
        if len(me) == 0:
            if board[CENTER[0]][CENTER[1]] == 0:
                return CENTER

            if color == 'b':
                prefs = [(4, 5), (6, 5), (5, 4), (5, 6), (4, 6), (6, 4)]
            else:
                prefs = [(5, 4), (5, 6), (4, 5), (6, 5), (6, 4), (4, 6)]

            for r, c in prefs:
                if board[r][c] == 0:
                    return (r, c)

        empties = empty_cells(board)
        if not empties:
            return (0, 0)

        # 1. Win immediately if possible.
        my_wins = winning_moves(board, 1, color)
        if my_wins:
            my_wins.sort(key=lambda m: -local_move_score(board, 1, color, m))
            return my_wins[0]

        # 2. Block opponent immediate win.
        opp_wins = winning_moves(board, 2, opp_color)
        if opp_wins:
            best_block = None
            best_score = -INF
            for m in opp_wins:
                r, c = m
                if board[r][c] != 0:
                    continue
                board[r][c] = 1
                sc = evaluate_side(board, 1, color) + local_move_score(board, 1, color, m)
                board[r][c] = 0
                if sc > best_score:
                    best_score = sc
                    best_block = m
            if best_block is not None:
                return best_block

        # Adaptive search width.
        ecount = len(empties)
        if ecount > 90:
            root_limit = 16
            reply_limit = 10
        elif ecount > 55:
            root_limit = 22
            reply_limit = 12
        else:
            root_limit = 28
            reply_limit = 16

        root_moves = ordered_moves(board, 1, color, root_limit, all_moves=True)
        if not root_moves:
            return fallback_move(board)

        best_move = root_moves[0]
        best_value = -10 ** 18

        for m in root_moves:
            r, c = m
            if board[r][c] != 0:
                continue

            board[r][c] = 1

            # If this somehow wins, take it.
            if shortest_distance(board, 1, color) == 0:
                board[r][c] = 0
                return m

            # Avoid moves that allow an immediate opponent win.
            ow = winning_moves(board, 2, opp_color)
            if ow:
                value = -850_000.0 + evaluate_side(board, 1, color) * 0.01
            else:
                replies = ordered_moves(board, 2, opp_color, reply_limit, all_moves=False)

                if not replies:
                    value = evaluate_side(board, 1, color)
                else:
                    worst = 10 ** 18
                    for om in replies:
                        orow, ocol = om
                        if board[orow][ocol] != 0:
                            continue

                        board[orow][ocol] = 2
                        val = evaluate_side(board, 1, color)
                        board[orow][ocol] = 0

                        if val < worst:
                            worst = val

                    value = worst

            # Prefer locally solid moves as a small tie-break.
            value += 0.08 * local_move_score(board, 1, color, m)

            board[r][c] = 0

            if value > best_value:
                best_value = value
                best_move = m

        br, bc = best_move
        if in_bounds(br, bc) and board[br][bc] == 0:
            return best_move

        return fallback_move(board)

    except Exception:
        # Absolute safety: never fail to return a legal move if one exists.
        return fallback_move(board)
