
from heapq import heappush, heappop
from collections import deque

N = 11
NN = N * N
MID = 5
INF = 10 ** 9

# Hex neighbors for the coordinate system described in the prompt.
_DIRS = ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, -1), (1, 0))

NEIGHBORS = [[] for _ in range(NN)]
ROW = [0] * NN
COL = [0] * NN
CORNER = [False] * NN

for r in range(N):
    for c in range(N):
        i = r * N + c
        ROW[i] = r
        COL[i] = c
        CORNER[i] = (r in (0, N - 1) and c in (0, N - 1))
        for dr, dc in _DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                NEIGHBORS[i].append(rr * N + cc)


def _idx(move):
    return move[0] * N + move[1]


def _rc(i):
    return (ROW[i], COL[i])


def _fallback_move(me, opp):
    occupied = set(me) | set(opp)
    cells = [(r, c) for r in range(N) for c in range(N)]
    cells.sort(key=lambda x: (abs(x[0] - MID) + abs(x[1] - MID), abs(x[0] - MID), abs(x[1] - MID)))
    for m in cells:
        if m not in occupied:
            return m
    return (0, 0)


def _has_won(board, color, code):
    q = deque()
    seen = [False] * NN

    if color == "b":
        for c in range(N):
            i = c
            if board[i] == code:
                seen[i] = True
                q.append(i)

        while q:
            i = q.popleft()
            if ROW[i] == N - 1:
                return True
            for nb in NEIGHBORS[i]:
                if not seen[nb] and board[nb] == code:
                    seen[nb] = True
                    q.append(nb)

    else:
        for r in range(N):
            i = r * N
            if board[i] == code:
                seen[i] = True
                q.append(i)

        while q:
            i = q.popleft()
            if COL[i] == N - 1:
                return True
            for nb in NEIGHBORS[i]:
                if not seen[nb] and board[nb] == code:
                    seen[nb] = True
                    q.append(nb)

    return False


def _winning_moves(board, color, code, empties):
    wins = []
    for i in empties:
        board[i] = code
        if _has_won(board, color, code):
            wins.append(i)
        board[i] = 0
    return wins


def _cell_costs(board, color, code):
    costs = [INF] * NN
    other = 2 if code == 1 else 1

    for i in range(NN):
        v = board[i]
        if v == code:
            costs[i] = 0
        elif v == other:
            costs[i] = INF
        else:
            own_adj = 0
            for nb in NEIGHBORS[i]:
                if board[nb] == code:
                    own_adj += 1

            # Empty base cost.  The minimum is kept high enough that
            # one empty cell is always better than any two empty cells.
            cost = 100 - 12 * min(own_adj, 3)

            # A cell touching multiple friendly stones is often a bridge/gap completion.
            if own_adj >= 2:
                cost -= 8

            # Prefer the useful central lane for the player's connection direction.
            if color == "b":
                cost += abs(COL[i] - MID)
                if ROW[i] == 0 or ROW[i] == N - 1:
                    cost -= 4
            else:
                cost += abs(ROW[i] - MID)
                if COL[i] == 0 or COL[i] == N - 1:
                    cost -= 4

            # Hex corners are usually less flexible.
            if CORNER[i]:
                cost += 10

            if cost < 70:
                cost = 70

            costs[i] = cost

    return costs


def _shortest_distance(board, color, code):
    costs = _cell_costs(board, color, code)
    dist = [INF] * NN
    heap = []

    if color == "b":
        starts = range(N)
    else:
        starts = range(0, NN, N)

    for i in starts:
        c = costs[i]
        if c < INF:
            dist[i] = c
            heappush(heap, (c, i))

    while heap:
        d, i = heappop(heap)
        if d != dist[i]:
            continue

        if color == "b":
            if ROW[i] == N - 1:
                return d
        else:
            if COL[i] == N - 1:
                return d

        for nb in NEIGHBORS[i]:
            step = costs[nb]
            if step >= INF:
                continue
            nd = d + step
            if nd < dist[nb]:
                dist[nb] = nd
                heappush(heap, (nd, nb))

    return INF


def _evaluate(board, my_color, opp_color):
    my_d = _shortest_distance(board, my_color, 1)
    opp_d = _shortest_distance(board, opp_color, 2)

    if my_d == 0:
        return 10_000_000
    if opp_d == 0:
        return -10_000_000

    if my_d >= INF:
        my_d = 1_000_000
    if opp_d >= INF:
        opp_d = 1_000_000

    return opp_d - my_d


def _move_feature(board, i, code, target_color):
    other = 2 if code == 1 else 1
    own_adj = 0
    opp_adj = 0

    for nb in NEIGHBORS[i]:
        if board[nb] == code:
            own_adj += 1
        elif board[nb] == other:
            opp_adj += 1

    r, c = ROW[i], COL[i]

    feature = 18 * own_adj + 10 * opp_adj

    if own_adj >= 2:
        feature += 25

    if target_color == "b":
        feature += 3 * (MID - abs(c - MID))
    else:
        feature += 3 * (MID - abs(r - MID))

    feature += 10 - (abs(r - MID) + abs(c - MID))

    if CORNER[i]:
        feature -= 25

    return feature


def _ordered_moves(board, my_color, opp_color, code, limit):
    target_color = my_color if code == 1 else opp_color
    empties = [i for i in range(NN) if board[i] == 0]

    scored = []
    for i in empties:
        board[i] = code
        val = _evaluate(board, my_color, opp_color)
        feat = _move_feature(board, i, code, target_color)
        board[i] = 0

        if code == 1:
            key = val + feat
        else:
            # Opponent wants to minimize our evaluation.
            key = -val + feat

        scored.append((key, i))

    scored.sort(reverse=True)
    return [i for _, i in scored[:limit]]


def _opening_move(board, color, occupied_count):
    if occupied_count == 0:
        return _idx((5, 5))

    if occupied_count == 1:
        if color == "b":
            preferred = [
                (5, 5), (4, 5), (6, 5), (5, 4), (5, 6),
                (4, 6), (6, 4), (4, 4), (6, 6)
            ]
        else:
            preferred = [
                (5, 5), (5, 4), (5, 6), (4, 5), (6, 5),
                (4, 6), (6, 4), (4, 4), (6, 6)
            ]

        for m in preferred:
            i = _idx(m)
            if board[i] == 0:
                return i

    return None


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    try:
        my_color = color
        opp_color = "w" if color == "b" else "b"

        board = [0] * NN
        for r, c in me:
            if 0 <= r < N and 0 <= c < N:
                board[r * N + c] = 1
        for r, c in opp:
            if 0 <= r < N and 0 <= c < N:
                board[r * N + c] = 2

        empties = [i for i in range(NN) if board[i] == 0]
        if not empties:
            return _fallback_move(me, opp)

        occupied_count = len(me) + len(opp)

        op = _opening_move(board, my_color, occupied_count)
        if op is not None and board[op] == 0:
            return _rc(op)

        # 1. Win immediately if possible.
        my_wins = _winning_moves(board, my_color, 1, empties)
        if my_wins:
            my_wins.sort(key=lambda i: _move_feature(board, i, 1, my_color), reverse=True)
            return _rc(my_wins[0])

        # 2. Block opponent's immediate win if necessary.
        opp_wins = _winning_moves(board, opp_color, 2, empties)
        if opp_wins:
            best_i = opp_wins[0]
            best_val = -INF
            for i in opp_wins:
                board[i] = 1
                val = _evaluate(board, my_color, opp_color) + _move_feature(board, i, 1, my_color)
                board[i] = 0
                if val > best_val:
                    best_val = val
                    best_i = i
            return _rc(best_i)

        # Candidate/search size tuned for a 1 second budget.
        if occupied_count < 12:
            my_limit = 18
            opp_limit = 10
        elif occupied_count < 55:
            my_limit = 24
            opp_limit = 12
        else:
            my_limit = 32
            opp_limit = 16

        candidates = _ordered_moves(board, my_color, opp_color, 1, my_limit)

        best_move = candidates[0] if candidates else empties[0]
        best_score = -INF

        for move in candidates:
            if board[move] != 0:
                continue

            board[move] = 1

            if _has_won(board, my_color, 1):
                board[move] = 0
                return _rc(move)

            base_val = _evaluate(board, my_color, opp_color)

            responses = _ordered_moves(board, my_color, opp_color, 2, opp_limit)

            if not responses:
                score = base_val
            else:
                worst = INF

                for resp in responses:
                    if board[resp] != 0:
                        continue

                    board[resp] = 2
                    val = _evaluate(board, my_color, opp_color)
                    board[resp] = 0

                    if val < worst:
                        worst = val

                    # Light alpha-style cutoff.
                    if worst < best_score - 500:
                        break

                score = worst + 0.03 * base_val + 0.15 * _move_feature(board, move, 1, my_color)

            board[move] = 0

            if score > best_score:
                best_score = score
                best_move = move

        if 0 <= best_move < NN and board[best_move] == 0:
            return _rc(best_move)

        return _fallback_move(me, opp)

    except Exception:
        return _fallback_move(me, opp)
