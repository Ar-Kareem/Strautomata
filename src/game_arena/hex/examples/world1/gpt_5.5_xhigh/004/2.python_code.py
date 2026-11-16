
from __future__ import annotations

import heapq
import time

N = 11
NN = N * N
INF = 10 ** 9
WIN_SCORE = 1_000_000.0
VIRTUAL_COST = 0.28

# Hex neighbors for the coordinate system in the prompt:
# all 8 grid neighbors except NW and SE.
DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]

ROWS = [i // N for i in range(NN)]
COLS = [i % N for i in range(NN)]

NEIGHBORS = []
for r in range(N):
    for c in range(N):
        ns = []
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                ns.append(rr * N + cc)
        NEIGHBORS.append(tuple(ns))

SIDE_CELLS = {
    "b": (
        tuple(range(N)),                       # top
        tuple(range((N - 1) * N, NN)),          # bottom
    ),
    "w": (
        tuple(r * N for r in range(N)),         # left
        tuple(r * N + (N - 1) for r in range(N)) # right
    ),
}

CENTER_ID = (N // 2) * N + (N // 2)
MAX_CENTER_D2 = 2 * (N // 2) * (N // 2)
CENTER_WEIGHT = []
for i in range(NN):
    dr = ROWS[i] - N // 2
    dc = COLS[i] - N // 2
    w = 1.0 - (dr * dr + dc * dc) / float(MAX_CENTER_D2)
    CENTER_WEIGHT.append(max(0.0, w))

HASH_TIE = [((i * 37 + 17) % 101) * 0.0001 for i in range(NN)]
PREFERRED_CELLS = sorted(
    range(NN),
    key=lambda i: (-CENTER_WEIGHT[i], abs(ROWS[i] - N // 2) + abs(COLS[i] - N // 2), ROWS[i], COLS[i]),
)

# Precompute bridge relationships.
# A Hex bridge is a non-adjacent pair of cells with exactly two common neighbors.
NEIGHBOR_SETS = [set(ns) for ns in NEIGHBORS]
VBRIDGES = [[] for _ in range(NN)]            # stone -> [(other_stone, connector1, connector2), ...]
CONNECTOR_BRIDGES = [[] for _ in range(NN)]   # connector -> [(stone1, stone2, other_connector), ...]

for a in range(NN):
    na = NEIGHBOR_SETS[a]
    for b in range(a + 1, NN):
        if b in na:
            continue
        common = [x for x in NEIGHBORS[a] if x in NEIGHBOR_SETS[b]]
        if len(common) == 2:
            x, y = common
            VBRIDGES[a].append((b, x, y))
            VBRIDGES[b].append((a, x, y))
            CONNECTOR_BRIDGES[x].append((a, b, y))
            CONNECTOR_BRIDGES[y].append((a, b, x))

# Side bridges: a stone one step off its target edge often has two edge connectors.
SIDE_VIRTUAL = {"b": [[], []], "w": [[], []]}
SIDE_BRIDGES = {"b": [[] for _ in range(NN)], "w": [[] for _ in range(NN)]}

for pc in ("b", "w"):
    for side in (0, 1):
        side_set = set(SIDE_CELLS[pc][side])
        for stone in range(NN):
            if stone in side_set:
                continue
            conns = [nb for nb in NEIGHBORS[stone] if nb in side_set]
            if len(conns) >= 2:
                c1, c2 = conns[0], conns[1]
                SIDE_VIRTUAL[pc][side].append((stone, c1, c2))
                SIDE_BRIDGES[pc][c1].append((stone, c2))
                SIDE_BRIDGES[pc][c2].append((stone, c1))


def _other_color(color: str) -> str:
    return "w" if color == "b" else "b"


def _make_board(me, opp):
    board = [0] * NN
    for p in me:
        try:
            r, c = p
        except Exception:
            continue
        if 0 <= r < N and 0 <= c < N:
            board[r * N + c] = 1
    for p in opp:
        try:
            r, c = p
        except Exception:
            continue
        if 0 <= r < N and 0 <= c < N:
            idx = r * N + c
            if board[idx] == 0:
                board[idx] = -1
    return board


def _fallback_id(board):
    for i in PREFERRED_CELLS:
        if board[i] == 0:
            return i
    return 0


def _fallback_move(me, opp):
    occ = set()
    try:
        for r, c in me:
            if 0 <= r < N and 0 <= c < N:
                occ.add((r, c))
        for r, c in opp:
            if 0 <= r < N and 0 <= c < N:
                occ.add((r, c))
    except Exception:
        pass

    for i in PREFERRED_CELLS:
        rc = (ROWS[i], COLS[i])
        if rc not in occ:
            return rc
    return (0, 0)


def _compute_costs(board, val: int, pl_color: str, weighted: bool):
    enemy = -val
    costs = [0.0] * NN

    for i in range(NN):
        b = board[i]
        if b == val:
            costs[i] = 0.0
        elif b == enemy:
            costs[i] = INF
        else:
            if not weighted:
                costs[i] = 1.0
            else:
                own_adj = 0
                enemy_adj = 0
                for nb in NEIGHBORS[i]:
                    x = board[nb]
                    if x == val:
                        own_adj += 1
                    elif x == enemy:
                        enemy_adj += 1

                w = 1.0
                if own_adj:
                    w -= 0.045 * own_adj + 0.025 * max(0, own_adj - 1)
                if enemy_adj:
                    w += 0.018 * enemy_adj

                r, c = ROWS[i], COLS[i]
                if pl_color == "b":
                    if r == 0 or r == N - 1:
                        w -= 0.020
                    if c == 0 or c == N - 1:
                        w += 0.035
                else:
                    if c == 0 or c == N - 1:
                        w -= 0.020
                    if r == 0 or r == N - 1:
                        w += 0.035

                w -= 0.015 * CENTER_WEIGHT[i]
                if w < 0.68:
                    w = 0.68
                elif w > 1.20:
                    w = 1.20
                costs[i] = w

    return costs


def _dijkstra(board, val: int, pl_color: str, side: int, costs, virtual: bool):
    enemy = -val
    dist = [INF] * NN
    heap = []
    push = heapq.heappush
    pop = heapq.heappop

    for idx in SIDE_CELLS[pl_color][side]:
        c = costs[idx]
        if c < INF and c < dist[idx]:
            dist[idx] = c
            push(heap, (c, idx))

    if virtual:
        for stone, c1, c2 in SIDE_VIRTUAL[pl_color][side]:
            if board[stone] == val and board[c1] != enemy and board[c2] != enemy:
                if VIRTUAL_COST < dist[stone]:
                    dist[stone] = VIRTUAL_COST
                    push(heap, (VIRTUAL_COST, stone))

    while heap:
        d, i = pop(heap)
        if d > dist[i] + 1e-12:
            continue

        for nb in NEIGHBORS[i]:
            c = costs[nb]
            if c >= INF:
                continue
            nd = d + c
            if nd + 1e-12 < dist[nb]:
                dist[nb] = nd
                push(heap, (nd, nb))

        if virtual and board[i] == val:
            for nb, c1, c2 in VBRIDGES[i]:
                if board[nb] == val and board[c1] != enemy and board[c2] != enemy:
                    nd = d + VIRTUAL_COST
                    if nd + 1e-12 < dist[nb]:
                        dist[nb] = nd
                        push(heap, (nd, nb))

    return dist


def _connection_info(board, val: int, pl_color: str, weighted: bool = True, virtual: bool = True):
    costs = _compute_costs(board, val, pl_color, weighted)
    ds = _dijkstra(board, val, pl_color, 0, costs, virtual)
    dt = _dijkstra(board, val, pl_color, 1, costs, virtual)
    total = min(ds[i] for i in SIDE_CELLS[pl_color][1])
    return total, ds, dt, costs


def _shortest_distance(board, val: int, pl_color: str, weighted: bool = False, virtual: bool = False):
    costs = _compute_costs(board, val, pl_color, weighted)
    ds = _dijkstra(board, val, pl_color, 0, costs, virtual)
    return min(ds[i] for i in SIDE_CELLS[pl_color][1])


def _has_won(board, val: int, pl_color: str) -> bool:
    seen = [False] * NN
    stack = []

    if pl_color == "b":
        for idx in SIDE_CELLS["b"][0]:
            if board[idx] == val:
                seen[idx] = True
                stack.append(idx)

        while stack:
            i = stack.pop()
            if ROWS[i] == N - 1:
                return True
            for nb in NEIGHBORS[i]:
                if not seen[nb] and board[nb] == val:
                    seen[nb] = True
                    stack.append(nb)
    else:
        for idx in SIDE_CELLS["w"][0]:
            if board[idx] == val:
                seen[idx] = True
                stack.append(idx)

        while stack:
            i = stack.pop()
            if COLS[i] == N - 1:
                return True
            for nb in NEIGHBORS[i]:
                if not seen[nb] and board[nb] == val:
                    seen[nb] = True
                    stack.append(nb)

    return False


def _winning_moves(board, val: int, pl_color: str, empties=None, limit=None):
    if empties is None:
        empties = [i for i, b in enumerate(board) if b == 0]

    wins = []
    for i in empties:
        if board[i] != 0:
            continue
        board[i] = val
        won = _has_won(board, val, pl_color)
        board[i] = 0

        if won:
            wins.append(i)
            if limit is not None and len(wins) >= limit:
                break

    return wins


def _on_target_edge(idx: int, pl_color: str) -> bool:
    r, c = ROWS[idx], COLS[idx]
    if pl_color == "b":
        return r == 0 or r == N - 1
    return c == 0 or c == N - 1


def _bridge_score(board, idx: int, val: int, pl_color: str) -> float:
    enemy = -val
    s = 0.0

    # Interior bridge completions/cuts.
    for a, b, other in CONNECTOR_BRIDGES[idx]:
        va = board[a]
        vb = board[b]
        o = board[other]

        if va == val and vb == val:
            if o == 0:
                s += 18.0
            elif o == enemy:
                s += 30.0
        elif va == enemy and vb == enemy:
            if o == val:
                s += 18.0
            elif o == 0:
                s += 5.0

    # Friendly side bridges.
    for stone, other in SIDE_BRIDGES[pl_color][idx]:
        if board[stone] == val:
            o = board[other]
            if o == 0:
                s += 12.0
            elif o == enemy:
                s += 23.0

    # Attacking opponent side bridges.
    opp_color = _other_color(pl_color)
    for stone, other in SIDE_BRIDGES[opp_color][idx]:
        if board[stone] == enemy:
            o = board[other]
            if o == val:
                s += 16.0
            elif o == 0:
                s += 4.5

    return s


def _local_score(board, idx: int, val: int, pl_color: str) -> float:
    enemy = -val
    own_adj = 0
    enemy_adj = 0

    for nb in NEIGHBORS[idx]:
        x = board[nb]
        if x == val:
            own_adj += 1
        elif x == enemy:
            enemy_adj += 1

    s = 16.0 * own_adj + 10.0 * enemy_adj
    if own_adj >= 2:
        s += 11.0 * (own_adj - 1)
    if enemy_adj >= 2:
        s += 7.0 * (enemy_adj - 1)
    if own_adj == 0 and enemy_adj == 0:
        s -= 4.0

    s += 12.0 * CENTER_WEIGHT[idx]

    if _on_target_edge(idx, pl_color):
        s += 7.0
    if _on_target_edge(idx, _other_color(pl_color)):
        s += 4.0

    r, c = ROWS[idx], COLS[idx]
    if (r == 0 or r == N - 1) and (c == 0 or c == N - 1):
        s -= 8.0

    s += _bridge_score(board, idx, val, pl_color)
    return s


def _move_scores(board, val: int, pl_color: str, candidates=None):
    if candidates is None:
        candidates = [i for i, b in enumerate(board) if b == 0]
    else:
        candidates = [i for i in candidates if 0 <= i < NN and board[i] == 0]

    if not candidates:
        return []

    enemy = -val
    opp_color = _other_color(pl_color)

    my_exact = _shortest_distance(board, val, pl_color, weighted=False, virtual=False)
    op_exact = _shortest_distance(board, enemy, opp_color, weighted=False, virtual=False)

    my_total, ms, mt, mcosts = _connection_info(board, val, pl_color, weighted=True, virtual=True)
    op_total, os, ot, ocosts = _connection_info(board, enemy, opp_color, weighted=True, virtual=True)

    my_e = min(my_exact, 50.0)
    op_e = min(op_exact, 50.0)

    attack_weight = 330.0 + 300.0 / (my_e + 1.0)
    defense_weight = 360.0 + 340.0 / (op_e + 1.0)

    if my_e <= 2.0:
        attack_weight += 180.0
    if op_e <= 2.0:
        defense_weight += 240.0

    scored = []
    for idx in candidates:
        s = 0.0

        cm = mcosts[idx]
        if cm < INF / 2 and ms[idx] < INF / 2 and mt[idx] < INF / 2:
            through = ms[idx] + mt[idx] - cm
            s += attack_weight / (through + 0.60)
            if through <= my_total + 0.05:
                s += 55.0 / (my_e + 1.0)

        co = ocosts[idx]
        if co < INF / 2 and os[idx] < INF / 2 and ot[idx] < INF / 2:
            through_o = os[idx] + ot[idx] - co
            s += defense_weight / (through_o + 0.60)
            if through_o <= op_total + 0.05:
                s += 70.0 / (op_e + 1.0)

        s += _local_score(board, idx, val, pl_color)
        s += HASH_TIE[idx]
        scored.append((s, idx))

    scored.sort(reverse=True)
    return scored


def _select_from_set(board, moves, val: int, pl_color: str) -> int:
    if not moves:
        return _fallback_id(board)
    if len(moves) == 1:
        return moves[0]
    scored = _move_scores(board, val, pl_color, moves)
    if scored:
        return scored[0][1]
    return moves[0]


def _static_eval(board, root_color: str, to_move: int = 1) -> float:
    opp_color = _other_color(root_color)

    md = _shortest_distance(board, 1, root_color, weighted=False, virtual=False)
    od = _shortest_distance(board, -1, opp_color, weighted=False, virtual=False)

    if md <= 1e-9:
        return WIN_SCORE
    if od <= 1e-9:
        return -WIN_SCORE

    mw = _shortest_distance(board, 1, root_color, weighted=True, virtual=True)
    ow = _shortest_distance(board, -1, opp_color, weighted=True, virtual=True)

    md_c = min(md, 50.0)
    od_c = min(od, 50.0)
    mw_c = min(mw, 50.0)
    ow_c = min(ow, 50.0)

    score = 850.0 * (od_c - md_c) + 170.0 * (ow_c - mw_c)
    score += 520.0 / (md_c + 0.35) - 540.0 / (od_c + 0.35)

    if to_move == 1:
        score += 70.0
        if md <= 1.000001:
            score += 18000.0
        elif od <= 1.000001:
            score -= 3500.0
        if md <= 2.000001:
            score += 900.0
        if od <= 2.000001:
            score -= 700.0
    else:
        score -= 70.0
        if od <= 1.000001:
            score -= 18000.0
        elif md <= 1.000001:
            score += 3500.0
        if od <= 2.000001:
            score -= 900.0
        if md <= 2.000001:
            score += 700.0

    return score


def _reply_eval(board, root_color: str, deadline: float) -> float:
    base = _static_eval(board, root_color, to_move=1)

    if time.perf_counter() > deadline or abs(base) > WIN_SCORE * 0.5:
        return base

    empties = [i for i, b in enumerate(board) if b == 0]
    if not empties or len(empties) > 24:
        return base

    scored = _move_scores(board, 1, root_color, empties)
    limit = min(6, len(scored))
    best = -INF

    for _, m in scored[:limit]:
        if time.perf_counter() > deadline:
            break
        board[m] = 1
        if _has_won(board, 1, root_color):
            val = WIN_SCORE * 0.8
        else:
            val = _static_eval(board, root_color, to_move=-1)
        board[m] = 0

        if val > best:
            best = val

    if best <= -INF / 2:
        return base
    return best


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    board = None
    try:
        color = (color or "b").lower()
        if color not in ("b", "w"):
            color = "b"
        opp_color = _other_color(color)

        board = _make_board(me, opp)
        empties = [i for i, b in enumerate(board) if b == 0]

        if not empties:
            return (0, 0)

        total_stones = NN - len(empties)

        # Strong, safe opening: take the center if available very early.
        if total_stones <= 1 and board[CENTER_ID] == 0:
            return (ROWS[CENTER_ID], COLS[CENTER_ID])

        # Exact tactics: win now, or block an opponent win now.
        my_wins = _winning_moves(board, 1, color, empties)
        if my_wins:
            m = _select_from_set(board, my_wins, 1, color)
            return (ROWS[m], COLS[m])

        opp_wins = _winning_moves(board, -1, opp_color, empties)
        if opp_wins:
            m = _select_from_set(board, opp_wins, 1, color)
            return (ROWS[m], COLS[m])

        deadline = time.perf_counter() + 0.86

        e = len(empties)
        if e > 95:
            root_limit, reply_limit = 16, 7
        elif e > 70:
            root_limit, reply_limit = 18, 8
        elif e > 40:
            root_limit, reply_limit = 24, 10
        elif e > 18:
            root_limit, reply_limit = min(30, e), 12
        else:
            root_limit, reply_limit = e, min(max(e - 1, 1), 16)

        root_scored = _move_scores(board, 1, color, empties)
        if not root_scored:
            m = _fallback_id(board)
            return (ROWS[m], COLS[m])

        root_scored = root_scored[:root_limit]
        quick = {i: s for s, i in root_scored}

        best_id = root_scored[0][1]
        best_val = -INF

        for _, m in root_scored:
            if time.perf_counter() > deadline:
                break
            if board[m] != 0:
                continue

            remaining = [x for x in empties if x != m]
            board[m] = 1

            if _has_won(board, 1, color):
                val = WIN_SCORE
            else:
                # If opponent can win immediately after this move, it is usually fatal.
                opp_now = _winning_moves(board, -1, opp_color, remaining, limit=1)
                if opp_now:
                    val = -WIN_SCORE * 0.45 + 0.02 * quick.get(m, 0.0)
                else:
                    # Count our next-turn immediate threats. Multiple threats are decisive.
                    my_threats = _winning_moves(board, 1, color, remaining, limit=3)
                    if len(my_threats) >= 2:
                        threat_bonus = 45000.0 + 2000.0 * len(my_threats)
                    elif len(my_threats) == 1:
                        threat_bonus = 900.0
                    else:
                        threat_bonus = 0.0

                    opp_scored = _move_scores(board, -1, opp_color, remaining)
                    opp_responses = [i for _, i in opp_scored[:reply_limit]]

                    # Ensure opponent is allowed to block our immediate threats in search.
                    present = set(opp_responses)
                    for t in my_threats:
                        if board[t] == 0 and t not in present:
                            opp_responses.insert(0, t)
                            present.add(t)

                    max_responses = reply_limit + len(my_threats)
                    if len(opp_responses) > max_responses:
                        opp_responses = opp_responses[:max_responses]

                    worst = INF
                    for om in opp_responses:
                        if time.perf_counter() > deadline:
                            break
                        if board[om] != 0:
                            continue

                        board[om] = -1
                        if _has_won(board, -1, opp_color):
                            leaf = -WIN_SCORE
                        else:
                            if e <= 28:
                                leaf = _reply_eval(board, color, deadline)
                            else:
                                leaf = _static_eval(board, color, to_move=1)
                        board[om] = 0

                        if leaf < worst:
                            worst = leaf

                        if worst + threat_bonus + 0.02 * quick.get(m, 0.0) < best_val - 5000.0:
                            break

                    if worst >= INF / 2:
                        worst = _static_eval(board, color, to_move=-1)

                    val = worst + threat_bonus + 0.02 * quick.get(m, 0.0)

            board[m] = 0

            if val > best_val:
                best_val = val
                best_id = m

        if 0 <= best_id < NN and board[best_id] == 0:
            return (ROWS[best_id], COLS[best_id])

        m = _fallback_id(board)
        return (ROWS[m], COLS[m])

    except Exception:
        return _fallback_move(me, opp)
