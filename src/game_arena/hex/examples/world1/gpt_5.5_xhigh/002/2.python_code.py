
from __future__ import annotations

from collections import deque
import random
import time

N = 11
NN = N * N
INF = 10**6
WIN_SCORE = 1_000_000

# Hex neighbors for the coordinate system in the prompt.
DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]

ROWS = [i // N for i in range(NN)]
COLS = [i % N for i in range(NN)]


def _idx(r: int, c: int) -> int:
    return r * N + c


def _rc(i: int) -> tuple[int, int]:
    return (i // N, i % N)


NEIGHBORS: list[list[int]] = []
for r in range(N):
    for c in range(N):
        ns = []
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                ns.append(_idx(rr, cc))
        NEIGHBORS.append(ns)

NEIGHBOR_SETS = [set(x) for x in NEIGHBORS]

START_BORDER = {
    "b": [_idx(0, c) for c in range(N)],
    "w": [_idx(r, 0) for r in range(N)],
}
GOAL_MASK = {
    "b": [ROWS[i] == N - 1 for i in range(NN)],
    "w": [COLS[i] == N - 1 for i in range(NN)],
}


def _opp_color(color: str) -> str:
    return "w" if color == "b" else "b"


def _border_set(orient: str, side: int) -> set[int]:
    if orient == "b":
        row = 0 if side == 0 else N - 1
        return {_idx(row, c) for c in range(N)}
    col = 0 if side == 0 else N - 1
    return {_idx(r, col) for r in range(N)}


# Ordinary bridge pairs: two non-adjacent cells with two common carrier cells.
BRIDGES: list[list[tuple[int, int, int]]] = [[] for _ in range(NN)]
CARRIER_BRIDGES: list[list[tuple[int, int, int]]] = [[] for _ in range(NN)]

for u in range(NN):
    for v in range(u + 1, NN):
        if v in NEIGHBOR_SETS[u]:
            continue
        common = sorted(NEIGHBOR_SETS[u] & NEIGHBOR_SETS[v])
        if len(common) == 2:
            a, b = common
            BRIDGES[u].append((v, a, b))
            BRIDGES[v].append((u, a, b))
            CARRIER_BRIDGES[a].append((u, v, b))
            CARRIER_BRIDGES[b].append((u, v, a))

# Side bridges: an interior stone one step away from a side with two side carriers.
SIDE_BRIDGES: dict[tuple[str, int], list[tuple[int, int, int]]] = {}
SIDE_BRIDGE_BY_STONE: dict[tuple[str, int], list[list[tuple[int, int]]]] = {}
CARRIER_SIDE = {"b": [[] for _ in range(NN)], "w": [[] for _ in range(NN)]}

for orient in ("b", "w"):
    for side in (0, 1):
        border = _border_set(orient, side)
        entries: list[tuple[int, int, int]] = []
        by_stone: list[list[tuple[int, int]]] = [[] for _ in range(NN)]
        for u in range(NN):
            if u in border:
                continue
            carriers = [v for v in NEIGHBORS[u] if v in border]
            if len(carriers) == 2:
                a, b = carriers
                entries.append((u, a, b))
                by_stone[u].append((a, b))
                CARRIER_SIDE[orient][a].append((side, u, b))
                CARRIER_SIDE[orient][b].append((side, u, a))
        SIDE_BRIDGES[(orient, side)] = entries
        SIDE_BRIDGE_BY_STONE[(orient, side)] = by_stone

JITTER = [((i * 73) % 19) * 0.001 for i in range(NN)]


def _make_board(me: list[tuple[int, int]], opp: list[tuple[int, int]]) -> list[int]:
    board = [0] * NN
    for r, c in me:
        if 0 <= r < N and 0 <= c < N:
            board[_idx(r, c)] = 1
    for r, c in opp:
        if 0 <= r < N and 0 <= c < N:
            k = _idx(r, c)
            if board[k] == 0:
                board[k] = -1
    return board


def _opening_move(board: list[int], me_count: int, opp_count: int, color: str) -> int | None:
    total = me_count + opp_count
    center = _idx(N // 2, N // 2)

    if total == 0 and board[center] == 0:
        return center

    # First move as second player: take center if possible; otherwise play a central neighbor
    # along our connection direction.
    if total == 1 and me_count == 0:
        if board[center] == 0:
            return center

        opp_cells = [i for i, v in enumerate(board) if v == -1]
        prefs: list[tuple[int, int]] = []
        if opp_cells:
            o = opp_cells[0]
            r, c = ROWS[o], COLS[o]
            if color == "w":
                prefs.extend([(r, c - 1), (r, c + 1), (r - 1, c), (r + 1, c),
                              (r - 1, c + 1), (r + 1, c - 1)])
            else:
                prefs.extend([(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1),
                              (r - 1, c + 1), (r + 1, c - 1)])

        prefs.extend([
            (5, 4), (5, 6), (4, 5), (6, 5), (4, 6), (6, 4),
            (5, 3), (5, 7), (3, 5), (7, 5)
        ])

        for r, c in prefs:
            if 0 <= r < N and 0 <= c < N:
                k = _idx(r, c)
                if board[k] == 0:
                    return k

    return None


def _winning_if_play(board: list[int], move: int, sign: int, orient: str) -> bool:
    if board[move] != 0:
        return False

    seen = [False] * NN
    stack = [move]
    seen[move] = True
    touch_a = False
    touch_b = False

    while stack:
        u = stack.pop()
        r, c = ROWS[u], COLS[u]
        if orient == "b":
            if r == 0:
                touch_a = True
            if r == N - 1:
                touch_b = True
        else:
            if c == 0:
                touch_a = True
            if c == N - 1:
                touch_b = True

        if touch_a and touch_b:
            return True

        for v in NEIGHBORS[u]:
            if not seen[v] and board[v] == sign:
                seen[v] = True
                stack.append(v)

    return False


def _find_winning_moves(board: list[int], sign: int, orient: str, empties: list[int]) -> list[int]:
    return [m for m in empties if _winning_if_play(board, m, sign, orient)]


def _has_win(board: list[int], sign: int, orient: str) -> bool:
    seen = [False] * NN
    q = deque()
    for s in START_BORDER[orient]:
        if board[s] == sign:
            seen[s] = True
            q.append(s)

    goal = GOAL_MASK[orient]
    while q:
        u = q.popleft()
        if goal[u]:
            return True
        for v in NEIGHBORS[u]:
            if not seen[v] and board[v] == sign:
                seen[v] = True
                q.append(v)
    return False


def _connection_distance(board: list[int], sign: int, orient: str, virtual: bool = True) -> int:
    """0-1 BFS shortest connection cost. Own stones cost 0, empties cost 1.
    If virtual=True, intact Hex bridges are treated as zero-cost virtual links.
    """
    opp = -sign
    dist = [INF] * NN
    q = deque()

    for v in START_BORDER[orient]:
        bv = board[v]
        if bv == opp:
            continue
        w = 0 if bv == sign else 1
        if w < dist[v]:
            dist[v] = w
            if w == 0:
                q.appendleft(v)
            else:
                q.append(v)

    if virtual:
        for stone, a, b in SIDE_BRIDGES[(orient, 0)]:
            if board[stone] == sign and board[a] != opp and board[b] != opp:
                if dist[stone] > 0:
                    dist[stone] = 0
                    q.appendleft(stone)

    goal = GOAL_MASK[orient]
    goal_side_bridges = SIDE_BRIDGE_BY_STONE[(orient, 1)]

    while q:
        u = q.popleft()
        d = dist[u]

        if goal[u]:
            return d

        if virtual and board[u] == sign:
            # Virtual connection from this stone to the target side.
            for a, b in goal_side_bridges[u]:
                if board[a] != opp and board[b] != opp:
                    return d

            # Virtual bridges to friendly stones.
            for v, a, b in BRIDGES[u]:
                if board[v] == sign and board[a] != opp and board[b] != opp:
                    if d < dist[v]:
                        dist[v] = d
                        q.appendleft(v)

        for v in NEIGHBORS[u]:
            bv = board[v]
            if bv == opp:
                continue
            nd = d if bv == sign else d + 1
            if nd < dist[v]:
                dist[v] = nd
                if bv == sign:
                    q.appendleft(v)
                else:
                    q.append(v)

    return INF


def _finite(d: int) -> int:
    return 60 if d >= INF else d


def _position_value(board: list[int], sign: int, orient: str, turn_sign: int = 0) -> float:
    opp_orient = _opp_color(orient)

    my_raw = _connection_distance(board, sign, orient, virtual=False)
    op_raw = _connection_distance(board, -sign, opp_orient, virtual=False)

    if my_raw == 0:
        return float(WIN_SCORE)
    if op_raw == 0:
        return float(-WIN_SCORE)

    my_v = _connection_distance(board, sign, orient, virtual=True)
    op_v = _connection_distance(board, -sign, opp_orient, virtual=True)

    mr, oraw = _finite(my_raw), _finite(op_raw)
    mv, ov = _finite(my_v), _finite(op_v)

    value = 700.0 * (ov - mv) + 140.0 * (oraw - mr)

    # Immediate threats matter much more for the player to move.
    if my_raw == 1:
        value += 8500.0 if turn_sign == sign else 1300.0
    if op_raw == 1:
        value -= 8500.0 if turn_sign == -sign else 1300.0

    if my_v == 0:
        value += 900.0
    if op_v == 0:
        value -= 900.0

    return value


def _move_shape_score(board: list[int], move: int, sign: int, orient: str) -> float:
    r, c = ROWS[move], COLS[move]
    center = N // 2
    dr, dc = r - center, c - center
    hex_center_dist = max(abs(dr), abs(dc), abs(dr + dc))

    s = (N - hex_center_dist) * 2.8

    # Prefer the central band perpendicular to our connection direction.
    if orient == "b":
        s -= abs(c - center) * 1.1
        if c == 0 or c == N - 1:
            s -= 3.5
    else:
        s -= abs(r - center) * 1.1
        if r == 0 or r == N - 1:
            s -= 3.5

    opp = -sign
    own_adj = 0
    opp_adj = 0
    for nb in NEIGHBORS[move]:
        if board[nb] == sign:
            own_adj += 1
        elif board[nb] == opp:
            opp_adj += 1

    s += own_adj * 2.5 + opp_adj * 1.5
    if own_adj >= 2:
        s += 3.0
    if opp_adj >= 2:
        s += 2.0
    if own_adj and opp_adj:
        s += 1.5

    # Creating friendly bridges as an endpoint.
    for v, a, b in BRIDGES[move]:
        bv = board[v]
        if bv == sign:
            if board[a] != opp and board[b] != opp:
                s += 6.0
            elif board[a] == sign or board[b] == sign:
                s += 2.0
        elif bv == opp:
            if board[a] != sign and board[b] != sign:
                s += 0.8

    # Playing inside bridge carriers: repair own bridges or damage opponent bridges.
    for u, v, other in CARRIER_BRIDGES[move]:
        bu, bv = board[u], board[v]
        bo = board[other]
        if bu == sign and bv == sign:
            if bo == opp:
                s += 24.0
            elif bo == 0:
                s += 8.0
            else:
                s += 2.0
        elif bu == opp and bv == opp:
            if bo == sign:
                s += 12.0
            elif bo == 0:
                s += 4.5

    # Side bridge carriers for us.
    for _side, stone, other in CARRIER_SIDE[orient][move]:
        if board[stone] == sign:
            bo = board[other]
            if bo == opp:
                s += 18.0
            elif bo == 0:
                s += 5.0
            else:
                s += 1.5

    # Side bridge carriers for opponent.
    opp_orient = _opp_color(orient)
    for _side, stone, other in CARRIER_SIDE[opp_orient][move]:
        if board[stone] == opp:
            bo = board[other]
            if bo == sign:
                s += 10.0
            elif bo == 0:
                s += 3.5

    return s + JITTER[move]


def _score_move_for(board: list[int], move: int, sign: int, orient: str) -> float:
    if board[move] != 0:
        return -1e18
    board[move] = sign
    val = _position_value(board, sign, orient, turn_sign=-sign)
    val += _move_shape_score(board, move, sign, orient)
    board[move] = 0
    return val


def _seed_from_board(board: list[int], color: str) -> int:
    seed = 0xA5A5A5A5 ^ (1 if color == "b" else 2)
    for i, v in enumerate(board):
        if v:
            seed = (seed * 1000003) ^ ((i + 17) * (37 if v == 1 else 91))
            seed &= 0xFFFFFFFF
    return seed


def _rollout_win(base_board: list[int], candidate: int, rest: list[int],
                 color: str, rng: random.Random) -> bool:
    b = base_board[:]
    b[candidate] = 1
    order = rest[:]
    rng.shuffle(order)

    sign = -1
    for cell in order:
        b[cell] = sign
        sign = -sign

    return _has_win(b, 1, color)


def _monte_carlo_adjust(board: list[int], empties: list[int], candidates: list[int],
                        values: dict[int, float], color: str, deadline: float) -> None:
    if len(empties) < 25 or time.perf_counter() > deadline - 0.04:
        return

    viable = [m for m in candidates if values.get(m, -1e18) > -WIN_SCORE / 4]
    viable.sort(key=lambda x: values.get(x, -1e18), reverse=True)
    viable = viable[:5 if len(empties) > 70 else 6]

    if len(viable) < 2:
        return

    rng = random.Random(_seed_from_board(board, color))
    rests = {m: [e for e in empties if e != m] for m in viable}
    wins = {m: 0 for m in viable}
    plays = {m: 0 for m in viable}

    max_playouts = 500 if len(empties) > 85 else (800 if len(empties) > 45 else 1000)
    total = 0

    while total < max_playouts and time.perf_counter() < deadline:
        for m in viable:
            if total >= max_playouts or time.perf_counter() >= deadline:
                break
            if _rollout_win(board, m, rests[m], color, rng):
                wins[m] += 1
            plays[m] += 1
            total += 1

    for m in viable:
        if plays[m] >= 6:
            rate = wins[m] / plays[m]
            values[m] = values.get(m, 0.0) + (rate - 0.5) * 1400.0


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    start_time = time.perf_counter()

    color = "b" if color == "b" else "w"
    opp_color = _opp_color(color)

    board = _make_board(me, opp)
    empties = [i for i, v in enumerate(board) if v == 0]

    if not empties:
        return (0, 0)
    if len(empties) == 1:
        return _rc(empties[0])

    opening = _opening_move(board, len(me), len(opp), color)
    if opening is not None and board[opening] == 0:
        return _rc(opening)

    # Forced tactical moves.
    if len(me) + 1 >= N:
        my_wins = _find_winning_moves(board, 1, color, empties)
        if my_wins:
            return _rc(my_wins[0])

    opp_wins: list[int] = []
    if len(opp) + 1 >= N:
        opp_wins = _find_winning_moves(board, -1, opp_color, empties)
        if len(opp_wins) == 1:
            return _rc(opp_wins[0])

    opp_win_set = set(opp_wins)

    # Static scoring of every legal move.
    root_scores: list[tuple[float, int]] = []
    for m in empties:
        sc = _score_move_for(board, m, 1, color)
        if m in opp_win_set:
            sc += 20000.0
        root_scores.append((sc, m))

    root_scores.sort(key=lambda x: x[0], reverse=True)
    root_score_map = {m: sc for sc, m in root_scores}

    ecount = len(empties)
    if ecount > 85:
        root_k, response_k = 12, 6
    elif ecount > 45:
        root_k, response_k = 16, 8
    else:
        root_k, response_k = 24, 10

    candidates: list[int] = []
    seen: set[int] = set()

    for m in opp_wins:
        if board[m] == 0 and m not in seen:
            candidates.append(m)
            seen.add(m)

    for _sc, m in root_scores[:root_k]:
        if m not in seen:
            candidates.append(m)
            seen.add(m)

    if not candidates:
        return _rc(root_scores[0][1] if root_scores else empties[0])

    best = candidates[0]
    best_val = -1e100
    root_values: dict[int, float] = {}

    search_deadline = start_time + 0.78

    # Shallow minimax over selected moves.
    for ci, m in enumerate(candidates):
        if ci > 0 and time.perf_counter() > search_deadline:
            break
        if board[m] != 0:
            continue

        board[m] = 1

        my_raw = _connection_distance(board, 1, color, virtual=False)
        if my_raw == 0:
            val = float(WIN_SCORE) + 0.001 * root_score_map.get(m, 0.0)
        else:
            op_raw = _connection_distance(board, -1, opp_color, virtual=False)
            if op_raw == 0:
                val = float(-WIN_SCORE)
            elif op_raw == 1:
                # Opponent can win immediately after this move.
                val = -WIN_SCORE / 3.0 + 0.01 * root_score_map.get(m, 0.0)
            else:
                opp_scores: list[tuple[float, int]] = []
                for k, r in enumerate(empties):
                    if r == m or board[r] != 0:
                        continue
                    opp_scores.append((_score_move_for(board, r, -1, opp_color), r))
                    if (k & 15) == 15 and time.perf_counter() > search_deadline:
                        break

                if not opp_scores:
                    val = _position_value(board, 1, color, turn_sign=-1)
                else:
                    opp_scores.sort(key=lambda x: x[0], reverse=True)
                    worst = 1e100

                    for _rank, (_osc, r) in enumerate(opp_scores[:response_k]):
                        board[r] = -1
                        child = _position_value(board, 1, color, turn_sign=1)
                        board[r] = 0

                        if child < worst:
                            worst = child

                        # Alpha-style pruning: already worse than our current best.
                        if worst < best_val - 3000.0:
                            break
                        if time.perf_counter() > search_deadline:
                            break

                    val = worst + 0.06 * root_score_map.get(m, 0.0)

        board[m] = 0
        root_values[m] = val

        if val > best_val:
            best_val = val
            best = m

    # Unevaluated candidates keep their static value.
    for m in candidates:
        if m not in root_values:
            root_values[m] = root_score_map.get(m, -1e18)

    if best_val > WIN_SCORE / 2 and board[best] == 0:
        return _rc(best)

    # Small deterministic Monte Carlo tie-break when safe and time remains.
    mc_deadline = start_time + 0.90
    if not opp_wins and time.perf_counter() < mc_deadline - 0.05:
        _monte_carlo_adjust(board, empties, candidates, root_values, color, mc_deadline)
        best = max(candidates, key=lambda x: root_values.get(x, -1e18))

    if 0 <= best < NN and board[best] == 0:
        return _rc(best)

    # Absolute safety fallback.
    return _rc(empties[0])
