
from collections import deque

N = 11
SIZE = N * N
MID = N // 2
CENTER = MID * N + MID
INF = 10**9

WIN_VALUE = 100000.0
THREAT_VALUE = 50000.0
FORCED_BLOCK_PENALTY = 30.0

# Hex neighbors in the coordinate system from the prompt:
# (r, c) touches (r, c-1), (r, c+1), (r-1, c), (r-1, c+1), (r+1, c-1), (r+1, c)
DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]

RC = [(r, c) for r in range(N) for c in range(N)]

NEI = [[] for _ in range(SIZE)]
for i, (r, c) in enumerate(RC):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            NEI[i].append(nr * N + nc)

TOP = [c for c in range(N)]
BOTTOM = [(N - 1) * N + c for c in range(N)]
LEFT = [r * N for r in range(N)]
RIGHT = [r * N + (N - 1) for r in range(N)]

PATH_SIDES = {
    1: (TOP, BOTTOM),   # black: top -> bottom
    2: (LEFT, RIGHT),   # white: left -> right
}

EDGE_CELLS = {
    1: TOP + BOTTOM,
    2: LEFT + RIGHT,
}

TOUCH_A = {
    1: [1 if r == 0 else 0 for r, c in RC],
    2: [1 if c == 0 else 0 for r, c in RC],
}
TOUCH_B = {
    1: [1 if r == N - 1 else 0 for r, c in RC],
    2: [1 if c == N - 1 else 0 for r, c in RC],
}

OWN_EDGE = {
    1: [1 if (r == 0 or r == N - 1) else 0 for r, c in RC],
    2: [1 if (c == 0 or c == N - 1) else 0 for r, c in RC],
}

CENTER_BIAS = [10 - (abs(r - MID) + abs(c - MID)) for r, c in RC]
AXIS_BIAS = {
    1: [5 - abs(c - MID) for r, c in RC],  # black likes central columns
    2: [5 - abs(r - MID) for r, c in RC],  # white likes central rows
}

EDGES = []
for i in range(SIZE):
    for j in NEI[i]:
        if j > i:
            EDGES.append((i, j))

# Bridge patterns in this coordinate system.
# Each entry is:
# partner offset, support1 offset, support2 offset
BRIDGE_SPECS = [
    ((-1, 2), (-1, 1), (0, 1)),
    ((-2, 1), (-1, 0), (-1, 1)),
    ((-1, -1), (-1, 0), (0, -1)),
    ((1, -2), (0, -1), (1, -1)),
    ((2, -1), (1, -1), (1, 0)),
    ((1, 1), (0, 1), (1, 0)),
]

BRIDGE_REL = [[] for _ in range(SIZE)]   # per cell: (partner, s1, s2)
SUPPORT_REL = [[] for _ in range(SIZE)]  # per support cell: (end1, end2, other_support)
BRIDGE_TRIPLES = []                      # unique global bridge triples

for i, (r, c) in enumerate(RC):
    for (pr, pc), (s1r, s1c), (s2r, s2c) in BRIDGE_SPECS:
        rr, cc = r + pr, c + pc
        a1, b1 = r + s1r, c + s1c
        a2, b2 = r + s2r, c + s2c
        if (
            0 <= rr < N and 0 <= cc < N and
            0 <= a1 < N and 0 <= b1 < N and
            0 <= a2 < N and 0 <= b2 < N
        ):
            p = rr * N + cc
            s1 = a1 * N + b1
            s2 = a2 * N + b2
            BRIDGE_REL[i].append((p, s1, s2))
            if p > i:
                BRIDGE_TRIPLES.append((i, p, s1, s2))
                SUPPORT_REL[s1].append((i, p, s2))
                SUPPORT_REL[s2].append((i, p, s1))


def move_wins(board, color, idx):
    """Assumes board[idx] == color. Checks whether the component through idx connects both goal sides."""
    touch_a = TOUCH_A[color]
    touch_b = TOUCH_B[color]
    seen = bytearray(SIZE)
    stack = [idx]
    seen[idx] = 1
    a = bool(touch_a[idx])
    b = bool(touch_b[idx])
    if a and b:
        return True

    while stack:
        u = stack.pop()
        for v in NEI[u]:
            if not seen[v] and board[v] == color:
                seen[v] = 1
                if touch_a[v]:
                    a = True
                if touch_b[v]:
                    b = True
                if a and b:
                    return True
                stack.append(v)
    return False


def find_immediate_win(board, color):
    """Return one immediate winning move index, or None."""
    for i, v in enumerate(board):
        if v == 0:
            board[i] = color
            won = move_wins(board, color, i)
            board[i] = 0
            if won:
                return i
    return None


def list_immediate_wins(board, color, limit=None):
    """Return up to limit immediate winning move indices."""
    wins = []
    for i, v in enumerate(board):
        if v == 0:
            board[i] = color
            won = move_wins(board, color, i)
            board[i] = 0
            if won:
                wins.append(i)
                if limit is not None and len(wins) >= limit:
                    break
    return wins


def zero_one_dist(board, color, starts):
    """0-1 BFS vertex-weight shortest path distances from one side."""
    opp = 3 - color
    dist = [INF] * SIZE
    dq = deque()
    append = dq.append
    appendleft = dq.appendleft

    for s in starts:
        st = board[s]
        if st == opp:
            continue
        d = 0 if st == color else 1
        if d < dist[s]:
            dist[s] = d
            if d == 0:
                appendleft(s)
            else:
                append(s)

    while dq:
        i = dq.popleft()
        di = dist[i]
        for j in NEI[i]:
            st = board[j]
            if st == opp:
                continue
            nd = di if st == color else di + 1
            if nd < dist[j]:
                dist[j] = nd
                if st == color:
                    appendleft(j)
                else:
                    append(j)

    return dist


def path_len(board, color):
    starts, goals = PATH_SIDES[color]
    d = zero_one_dist(board, color, starts)
    best = INF
    for g in goals:
        if d[g] < best:
            best = d[g]
    return best


def path_info(board, color):
    starts, goals = PATH_SIDES[color]
    d0 = zero_one_dist(board, color, starts)
    d1 = zero_one_dist(board, color, goals)
    best = INF
    for g in goals:
        if d0[g] < best:
            best = d0[g]
    return best, d0, d1


def component_ids(board, color):
    comp = [-1] * SIZE
    cid = 0
    for i in range(SIZE):
        if board[i] == color and comp[i] == -1:
            comp[i] = cid
            stack = [i]
            while stack:
                u = stack.pop()
                for v in NEI[u]:
                    if board[v] == color and comp[v] == -1:
                        comp[v] = cid
                        stack.append(v)
            cid += 1
    return comp


def bridge_move_score(board, idx, color, opp):
    bonus = 0.0

    # As an endpoint of a bridge.
    for partner, s1, s2 in BRIDGE_REL[idx]:
        p = board[partner]
        if p == color:
            if board[s1] != opp and board[s2] != opp:
                bonus += 3.5
                if board[s1] == color or board[s2] == color:
                    bonus += 1.5
        elif p == opp:
            if board[s1] != color and board[s2] != color:
                bonus += 1.2

    # As a support cell of a bridge.
    for a, b, other_support in SUPPORT_REL[idx]:
        sa = board[a]
        sb = board[b]
        if sa == color and sb == color:
            if board[other_support] != opp:
                bonus += 2.0
        elif sa == opp and sb == opp:
            if board[other_support] != color:
                bonus += 0.8

    return bonus


def bridge_count(board, color):
    opp = 3 - color
    total = 0
    for a, b, s1, s2 in BRIDGE_TRIPLES:
        if board[a] == color and board[b] == color and board[s1] != opp and board[s2] != opp:
            total += 1
    return total


def adj_pairs(board, color):
    total = 0
    for a, b in EDGES:
        if board[a] == color and board[b] == color:
            total += 1
    return total


def edge_contacts(board, color):
    total = 0
    for i in EDGE_CELLS[color]:
        if board[i] == color:
            total += 1
    return total


def evaluate(board, root):
    opp = 3 - root
    my_best = path_len(board, root)
    opp_best = path_len(board, opp)

    if my_best == 0:
        return WIN_VALUE
    if opp_best == 0:
        return -WIN_VALUE

    if my_best >= INF // 2 and opp_best >= INF // 2:
        score = 0.0
    elif my_best >= INF // 2:
        return -0.9 * WIN_VALUE
    elif opp_best >= INF // 2:
        return 0.9 * WIN_VALUE
    else:
        score = 42.0 * (opp_best - my_best)

    score += 2.8 * (bridge_count(board, root) - bridge_count(board, opp))
    score += 1.4 * (adj_pairs(board, root) - adj_pairs(board, opp))
    score += 0.8 * (edge_contacts(board, root) - edge_contacts(board, opp))
    return score


def leaf_value(board, root):
    """
    Value for a position where root is to move.
    Adds tactical checks beyond static evaluation.
    """
    opp = 3 - root

    # If root can win immediately, that's a huge score.
    win_now = find_immediate_win(board, root)
    if win_now is not None:
        return THREAT_VALUE

    # If opp has 2 different immediate wins, root cannot stop both.
    opp_threats = list_immediate_wins(board, opp, limit=2)
    if len(opp_threats) >= 2:
        return -THREAT_VALUE

    # If opp has exactly one immediate win, root is forced to block it.
    if len(opp_threats) == 1:
        t = opp_threats[0]
        board[t] = root
        if move_wins(board, root, t):
            val = THREAT_VALUE
        else:
            val = evaluate(board, root) - FORCED_BLOCK_PENALTY
        board[t] = 0
        return val

    return evaluate(board, root)


def generate_candidates(board, color, max_cand=12):
    legal = [i for i, v in enumerate(board) if v == 0]
    if not legal:
        return []

    if len(legal) == 1:
        return legal

    opp = 3 - color
    my_best, my_d0, my_d1 = path_info(board, color)
    opp_best, opp_d0, opp_d1 = path_info(board, opp)
    my_comp = component_ids(board, color)
    opp_comp = component_ids(board, opp)

    occupied = SIZE - len(legal)
    if occupied < 8:
        center_w = 1.8
    elif occupied < 20:
        center_w = 1.0
    else:
        center_w = 0.4

    def_w = 1.0
    if opp_best < my_best:
        def_w += 0.5
    if opp_best <= 2:
        def_w += 0.7

    scored = []

    for i in legal:
        score = 0.0
        score += center_w * CENTER_BIAS[i]
        score += 0.6 * AXIS_BIAS[color][i]
        if OWN_EDGE[color][i]:
            score += 1.2

        d0 = my_d0[i]
        d1 = my_d1[i]
        if d0 < INF and d1 < INF and my_best < INF:
            slack = d0 + d1 - 1 - my_best
            if slack < 0:
                slack = 0
            off = 20.0 - 4.0 * slack
            if off > 0:
                score += off

        od0 = opp_d0[i]
        od1 = opp_d1[i]
        if od0 < INF and od1 < INF and opp_best < INF:
            slacko = od0 + od1 - 1 - opp_best
            if slacko < 0:
                slacko = 0
            deff = 18.0 - 3.0 * slacko
            if deff > 0:
                score += def_w * deff

        friendly_adj = 0
        enemy_adj = 0
        my_ids = []
        opp_ids = []

        for n in NEI[i]:
            st = board[n]
            if st == color:
                friendly_adj += 1
                cid = my_comp[n]
                if cid not in my_ids:
                    my_ids.append(cid)
            elif st == opp:
                enemy_adj += 1
                cid = opp_comp[n]
                if cid not in opp_ids:
                    opp_ids.append(cid)

        score += 1.8 * friendly_adj + 0.7 * enemy_adj
        score += 4.0 * len(my_ids) + 3.0 * max(0, len(my_ids) - 1)
        score += 2.2 * len(opp_ids) + 1.8 * max(0, len(opp_ids) - 1)
        score += bridge_move_score(board, i, color, opp)

        scored.append((score, i))

    scored.sort(reverse=True)
    limit = min(max_cand, len(scored))
    return [i for _, i in scored[:limit]]


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    my_color = 1 if color == 'b' else 2
    opp_color = 3 - my_color

    board = [0] * SIZE
    for r, c in me:
        board[r * N + c] = my_color
    for r, c in opp:
        board[r * N + c] = opp_color

    legal = [i for i, v in enumerate(board) if v == 0]
    if not legal:
        return (0, 0)
    if len(legal) == 1:
        return RC[legal[0]]

    occupied = SIZE - len(legal)

    # Exact immediate win.
    win = find_immediate_win(board, my_color)
    if win is not None:
        return RC[win]

    # Exact immediate block. If there are multiple opponent wins, we are lost anyway,
    # but occupying one winning cell is still the best legal damage control.
    block = find_immediate_win(board, opp_color)
    if block is not None:
        return RC[block]

    # Very early opening preference.
    if occupied <= 1 and board[CENTER] == 0:
        return RC[CENTER]

    root_candidates = generate_candidates(board, my_color, max_cand=16)
    if not root_candidates:
        return RC[legal[0]]

    best_move = root_candidates[0]
    best_score = -1e18

    for m in root_candidates:
        board[m] = my_color

        # Should already have been caught by immediate win search, but keep it exact.
        if move_wins(board, my_color, m):
            board[m] = 0
            return RC[m]

        # If opponent can win immediately after this, the move is bad.
        opp_now = find_immediate_win(board, opp_color)
        if opp_now is not None:
            score = -WIN_VALUE
        else:
            # If this move creates at least two immediate winning threats for us,
            # opponent cannot stop both.
            my_threats = list_immediate_wins(board, my_color, limit=2)
            if len(my_threats) >= 2:
                board[m] = 0
                return RC[m]

            # If exactly one immediate threat exists, opponent is forced to occupy it.
            if len(my_threats) == 1:
                forced = my_threats[0]
                board[forced] = opp_color
                score = leaf_value(board, my_color)
                board[forced] = 0
            else:
                opp_candidates = generate_candidates(board, opp_color, max_cand=14)
                if not opp_candidates:
                    score = evaluate(board, my_color)
                else:
                    worst = 1e18
                    for om in opp_candidates:
                        board[om] = opp_color
                        if move_wins(board, opp_color, om):
                            val = -WIN_VALUE
                        else:
                            val = leaf_value(board, my_color)
                        board[om] = 0

                        if val < worst:
                            worst = val
                            if worst <= best_score:
                                break
                    score = worst

        board[m] = 0

        if score > best_score:
            best_score = score
            best_move = m
            if score >= THREAT_VALUE:
                return RC[m]

    # Final safety fallback: always return a legal move.
    if board[best_move] == 0:
        return RC[best_move]
    return RC[legal[0]]
