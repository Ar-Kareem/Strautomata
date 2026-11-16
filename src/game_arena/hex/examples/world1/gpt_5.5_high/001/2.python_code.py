
from collections import deque
import time

N = 11
SIZE = N * N
MID = N // 2
INF = 10 ** 6
WIN_SCORE = 100_000_000

DIRS = ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, -1), (1, 0))


def _idx(r, c):
    return r * N + c


def _rc(i):
    return divmod(i, N)


ROWS = [i // N for i in range(SIZE)]
COLS = [i % N for i in range(SIZE)]

NEIGHBORS = [[] for _ in range(SIZE)]
for r in range(N):
    for c in range(N):
        i = _idx(r, c)
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                NEIGHBORS[i].append(_idx(rr, cc))

NEI_SETS = [set(x) for x in NEIGHBORS]

TOP = [_idx(0, c) for c in range(N)]
BOTTOM = [_idx(N - 1, c) for c in range(N)]
LEFT = [_idx(r, 0) for r in range(N)]
RIGHT = [_idx(r, N - 1) for r in range(N)]

SIDES = {
    "b": (TOP, BOTTOM),
    "w": (LEFT, RIGHT),
}

START_MASK = {
    "b": [ROWS[i] == 0 for i in range(SIZE)],
    "w": [COLS[i] == 0 for i in range(SIZE)],
}
END_MASK = {
    "b": [ROWS[i] == N - 1 for i in range(SIZE)],
    "w": [COLS[i] == N - 1 for i in range(SIZE)],
}

# Row/column centered positional value. Corners are intentionally not overvalued.
CENTER = []
for i in range(SIZE):
    r, c = _rc(i)
    CENTER.append(max(0, 20 - 2 * (abs(r - MID) + abs(c - MID))))

CORNERS = {_idx(0, 0), _idx(0, N - 1), _idx(N - 1, 0), _idx(N - 1, N - 1)}


def other_color(color):
    return "w" if color == "b" else "b"


# Hex bridge patterns: two non-adjacent cells with exactly two common neighbors.
BRIDGES = []
VBRIDGES = [[] for _ in range(SIZE)]
BRIDGE_BY_EMPTY = [[] for _ in range(SIZE)]
BRIDGE_ENDPOINTS = [[] for _ in range(SIZE)]

for a in range(SIZE):
    for b in range(a + 1, SIZE):
        if b in NEI_SETS[a]:
            continue
        common = list(NEI_SETS[a].intersection(NEI_SETS[b]))
        if len(common) == 2:
            c1, c2 = common[0], common[1]
            BRIDGES.append((a, b, c1, c2))
            VBRIDGES[a].append((b, c1, c2))
            VBRIDGES[b].append((a, c1, c2))
            BRIDGE_BY_EMPTY[c1].append((a, b, c2))
            BRIDGE_BY_EMPTY[c2].append((a, b, c1))
            BRIDGE_ENDPOINTS[a].append((b, c1, c2))
            BRIDGE_ENDPOINTS[b].append((a, c1, c2))


def _add_virtual_side_sources(board, val, orient, side_name, dist, dq):
    """Virtual edge templates: a stone one line from a target side with two empty
    side-adjacent cells is treated as virtually connected to that side."""
    def add(stone, e1, e2):
        if board[stone] == val and board[e1] == 0 and board[e2] == 0 and dist[stone] > 0:
            dist[stone] = 0
            dq.appendleft(stone)

    if orient == "b":
        if side_name == "start":  # top
            for c in range(N - 1):
                add(_idx(1, c), _idx(0, c), _idx(0, c + 1))
        else:  # bottom
            for c in range(1, N):
                add(_idx(N - 2, c), _idx(N - 1, c), _idx(N - 1, c - 1))
    else:
        if side_name == "start":  # left
            for r in range(N - 1):
                add(_idx(r, 1), _idx(r, 0), _idx(r + 1, 0))
        else:  # right
            for r in range(1, N):
                add(_idx(r, N - 2), _idx(r, N - 1), _idx(r - 1, N - 1))


def _zero_one_dist(board, costs, val, orient, side_name, use_virtual):
    starts, ends = SIDES[orient]
    sources = starts if side_name == "start" else ends

    dist = [INF] * SIZE
    dq = deque()

    for s in sources:
        w = costs[s]
        if w < INF and w < dist[s]:
            dist[s] = w
            if w == 0:
                dq.appendleft(s)
            else:
                dq.append(s)

    if use_virtual:
        _add_virtual_side_sources(board, val, orient, side_name, dist, dq)

    while dq:
        v = dq.popleft()
        d = dist[v]

        for nb in NEIGHBORS[v]:
            w = costs[nb]
            if w >= INF:
                continue
            nd = d + w
            if nd < dist[nb]:
                dist[nb] = nd
                if w == 0:
                    dq.appendleft(nb)
                else:
                    dq.append(nb)

        if use_virtual and board[v] == val:
            for j, c1, c2 in VBRIDGES[v]:
                if board[j] == val and board[c1] == 0 and board[c2] == 0 and d < dist[j]:
                    dist[j] = d
                    dq.appendleft(j)

    return dist


def connection_stats(board, val, orient, use_virtual=False):
    enemy = -val
    costs = [0] * SIZE
    for i, x in enumerate(board):
        if x == enemy:
            costs[i] = INF
        elif x == val:
            costs[i] = 0
        else:
            costs[i] = 1

    ds = _zero_one_dist(board, costs, val, orient, "start", use_virtual)
    de = _zero_one_dist(board, costs, val, orient, "end", use_virtual)

    best = INF
    for i in range(SIZE):
        if costs[i] < INF and ds[i] < INF and de[i] < INF:
            v = ds[i] + de[i] - costs[i]
            if v < best:
                best = v

    potential = 0
    shortest_cells = 0
    if best < INF:
        weights = (16, 8, 4, 2)
        for i, x in enumerate(board):
            if x == 0 and ds[i] < INF and de[i] < INF:
                through = ds[i] + de[i] - 1
                gap = through - best
                if 0 <= gap <= 3:
                    potential += weights[gap]
                    if gap == 0:
                        shortest_cells += 1

    return best, potential, shortest_cells, ds, de


def has_connection(board, val, orient):
    starts, _ = SIDES[orient]
    end_mask = END_MASK[orient]
    seen = [False] * SIZE
    q = deque()

    for s in starts:
        if board[s] == val:
            if end_mask[s]:
                return True
            seen[s] = True
            q.append(s)

    while q:
        v = q.popleft()
        for nb in NEIGHBORS[v]:
            if not seen[nb] and board[nb] == val:
                if end_mask[nb]:
                    return True
                seen[nb] = True
                q.append(nb)
    return False


def winning_moves(board, val, orient):
    comp = [-1] * SIZE
    touch_start = []
    touch_end = []
    cid = 0
    smask = START_MASK[orient]
    emask = END_MASK[orient]

    for i in range(SIZE):
        if board[i] == val and comp[i] < 0:
            stack = [i]
            comp[i] = cid
            ts = smask[i]
            te = emask[i]

            while stack:
                v = stack.pop()
                for nb in NEIGHBORS[v]:
                    if board[nb] == val and comp[nb] < 0:
                        comp[nb] = cid
                        ts = ts or smask[nb]
                        te = te or emask[nb]
                        stack.append(nb)

            touch_start.append(ts)
            touch_end.append(te)
            cid += 1

    wins = []
    for e in range(SIZE):
        if board[e] != 0:
            continue

        ts = smask[e]
        te = emask[e]
        roots = []

        for nb in NEIGHBORS[e]:
            if board[nb] == val:
                r = comp[nb]
                if r not in roots:
                    roots.append(r)
                    ts = ts or touch_start[r]
                    te = te or touch_end[r]

        if ts and te:
            wins.append(e)

    return wins


def local_score(board, e, val):
    enemy = -val
    own_adj = 0
    enemy_adj = 0

    for nb in NEIGHBORS[e]:
        if board[nb] == val:
            own_adj += 1
        elif board[nb] == enemy:
            enemy_adj += 1

    score = 22 * own_adj + 14 * enemy_adj + 6 * CENTER[e]

    if e in CORNERS:
        score -= 25

    # Filling or repairing bridge cells.
    for a, b, other in BRIDGE_BY_EMPTY[e]:
        if board[a] == val and board[b] == val:
            if board[other] == 0:
                score += 35
            elif board[other] == enemy:
                score += 120
            else:
                score += 10
        elif board[a] == enemy and board[b] == enemy:
            if board[other] == 0:
                score += 30

    # Creating a bridge to an existing friendly stone.
    for other, c1, c2 in BRIDGE_ENDPOINTS[e]:
        if board[other] == val:
            if board[c1] == 0 and board[c2] == 0:
                score += 24
            elif board[c1] == val or board[c2] == val:
                score += 10
        elif board[other] == enemy and board[c1] == 0 and board[c2] == 0:
            score += 10

    if own_adj == 0 and enemy_adj == 0:
        score -= 18

    return score


def _gap_bonus(gap, base):
    if gap <= 0:
        return base
    if gap == 1:
        return base // 2
    if gap == 2:
        return base // 4
    if gap == 3:
        return base // 8
    return 0


def generate_candidates(board, val, orient, limit):
    empties = [i for i, x in enumerate(board) if x == 0]
    if not empties:
        return []

    enemy_orient = other_color(orient)
    md, _, _, ds, de = connection_stats(board, val, orient, use_virtual=False)
    emd, _, _, eds, ede = connection_stats(board, -val, enemy_orient, use_virtual=False)

    stones = SIZE - len(empties)
    scored = []

    for e in empties:
        q = local_score(board, e, val)

        if md < INF and ds[e] < INF and de[e] < INF:
            through = ds[e] + de[e] - 1
            gap = through - md
            base = 760 if md <= 2 else 560
            q += _gap_bonus(gap, base)

        if emd < INF and eds[e] < INF and ede[e] < INF:
            through = eds[e] + ede[e] - 1
            gap = through - emd
            base = 920 if emd <= 2 else 650
            q += _gap_bonus(gap, base)

        # After the opening, completely isolated moves are rarely urgent.
        if stones > 10:
            adj_any = False
            for nb in NEIGHBORS[e]:
                if board[nb] != 0:
                    adj_any = True
                    break
            if not adj_any:
                q -= 80

        scored.append((q, e))

    scored.sort(reverse=True)
    return [e for _, e in scored[:min(limit, len(scored))]]


def advancement_score(board, val, orient):
    coords = []
    if orient == "b":
        for i, x in enumerate(board):
            if x == val:
                coords.append(ROWS[i])
    else:
        for i, x in enumerate(board):
            if x == val:
                coords.append(COLS[i])

    if not coords:
        return 0

    mn = min(coords)
    mx = max(coords)
    return 20 * (mx - mn) + 60 * (mn == 0) + 60 * (mx == N - 1)


def evaluate(board, my_color):
    opp_color = other_color(my_color)

    if has_connection(board, 1, my_color):
        return WIN_SCORE
    if has_connection(board, -1, opp_color):
        return -WIN_SCORE

    my_wins = winning_moves(board, 1, my_color)
    if my_wins:
        return WIN_SCORE // 3 + 10_000 * len(my_wins)

    opp_wins = winning_moves(board, -1, opp_color)
    if len(opp_wins) >= 2:
        return -WIN_SCORE // 3 - 10_000 * len(opp_wins)

    my_d, my_pot, my_short, _, _ = connection_stats(board, 1, my_color, use_virtual=True)
    op_d, op_pot, op_short, _, _ = connection_stats(board, -1, opp_color, use_virtual=True)

    if my_d >= INF:
        my_d = 40
    if op_d >= INF:
        op_d = 40

    score = 70_000 * (op_d - my_d)
    score += 260 * (my_pot - op_pot)
    score += 90 * (my_short - op_short)

    if len(opp_wins) == 1:
        score -= 85_000

    pos = 0
    for i, x in enumerate(board):
        if x == 1:
            pos += CENTER[i]
        elif x == -1:
            pos -= CENTER[i]
    score += 5 * pos

    score += 35 * (
        advancement_score(board, 1, my_color)
        - advancement_score(board, -1, opp_color)
    )

    return score


def choose_from_moves(board, moves, val):
    best = moves[0]
    best_s = -INF
    for m in moves:
        s = local_score(board, m, val)
        if s > best_s:
            best_s = s
            best = m
    return best


def _limits(empty_count):
    if empty_count > 95:
        return 18, 8
    if empty_count > 65:
        return 22, 10
    if empty_count > 35:
        return 28, 12
    if empty_count > 18:
        return 36, 16
    return empty_count, empty_count


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    color = "b" if color == "b" else "w"
    opp_color = other_color(color)

    board = [0] * SIZE
    for r, c in me:
        if 0 <= r < N and 0 <= c < N:
            board[_idx(r, c)] = 1
    for r, c in opp:
        if 0 <= r < N and 0 <= c < N:
            board[_idx(r, c)] = -1

    empties = [i for i, x in enumerate(board) if x == 0]
    if not empties:
        return (0, 0)

    center = _idx(MID, MID)
    total_stones = SIZE - len(empties)

    # Strong and safe opening.
    if total_stones == 0 and board[center] == 0:
        return (MID, MID)

    # Immediate tactical necessities.
    my_now = winning_moves(board, 1, color)
    if my_now:
        m = choose_from_moves(board, my_now, 1)
        return _rc(m)

    opp_now = winning_moves(board, -1, opp_color)
    if opp_now:
        if len(opp_now) == 1:
            return _rc(opp_now[0])
        m = choose_from_moves(board, opp_now, 1)
        return _rc(m)

    # If opponent opened away from the center, take it.
    if total_stones == 1 and board[center] == 0:
        return (MID, MID)

    start_time = time.perf_counter()
    deadline = start_time + 0.92

    my_limit, opp_limit = _limits(len(empties))
    candidates = generate_candidates(board, 1, color, my_limit)
    if not candidates:
        m = empties[0]
        return _rc(m)

    fallback = candidates[0]
    best_move = fallback
    best_score = -WIN_SCORE * 2

    for ci, m in enumerate(candidates):
        if ci > 0 and time.perf_counter() > deadline:
            break

        board[m] = 1

        if has_connection(board, 1, color):
            score = WIN_SCORE
        else:
            # Never allow an immediate opponent win if avoidable.
            op_w = winning_moves(board, -1, opp_color)
            if op_w:
                score = -WIN_SCORE + local_score(board, m, 1)
            else:
                my_follow = winning_moves(board, 1, color)

                # Two winning threats means the opponent can block at most one.
                if len(my_follow) >= 2:
                    score = WIN_SCORE // 2 + 1_000 * len(my_follow)
                else:
                    opp_cands = generate_candidates(board, -1, opp_color, opp_limit)

                    # If we have one winning threat, opponent's block must be considered.
                    if len(my_follow) == 1 and my_follow[0] not in opp_cands:
                        opp_cands = [my_follow[0]] + opp_cands

                    if not opp_cands:
                        score = evaluate(board, color)
                    else:
                        worst = WIN_SCORE * 2
                        searched = 0

                        for oi, om in enumerate(opp_cands):
                            if oi > 0 and time.perf_counter() > deadline:
                                break

                            if board[om] != 0:
                                continue

                            board[om] = -1
                            searched += 1

                            if has_connection(board, -1, opp_color):
                                val = -WIN_SCORE
                            else:
                                val = evaluate(board, color)

                            board[om] = 0

                            if val < worst:
                                worst = val

                            # Alpha-style cutoff: this move is already worse than our best.
                            if worst < best_score - 250_000:
                                break

                        if searched == 0:
                            worst = evaluate(board, color)
                        score = worst

        board[m] = 0

        # Small deterministic tie breaker for better-shaped moves.
        score += local_score(board, m, 1)

        if score > best_score:
            best_score = score
            best_move = m

    if board[best_move] != 0:
        best_move = fallback if board[fallback] == 0 else empties[0]

    return _rc(best_move)
