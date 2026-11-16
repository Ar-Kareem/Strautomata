
import time
from collections import deque

BOARD_SIZE = 11
NUM_CELLS = 121

# Neighbor offsets for Hex on 11x11 board
NEIGHBOR_OFFSETS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]

# Precompute neighbor indices for each cell
NEIGHBORS = [[] for _ in range(NUM_CELLS)]
CELL_ROW = [0] * NUM_CELLS
CELL_COL = [0] * NUM_CELLS

for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        idx = r * BOARD_SIZE + c
        CELL_ROW[idx] = r
        CELL_COL[idx] = c
        for dr, dc in NEIGHBOR_OFFSETS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                NEIGHBORS[idx].append(nr * BOARD_SIZE + nc)

# Boundary nodes for Black (top to bottom)
BLACK_TOP = [c for c in range(BOARD_SIZE)]
BLACK_BOTTOM = [10 * BOARD_SIZE + c for c in range(BOARD_SIZE)]

# Boundary nodes for White (left to right)
WHITE_LEFT = [r * BOARD_SIZE for r in range(BOARD_SIZE)]
WHITE_RIGHT = [r * BOARD_SIZE + 10 for r in range(BOARD_SIZE)]

# Bridge patterns: offset to partner and the two common neighbors
# Using only forward offsets to avoid double-counting pairs
BRIDGE_OFFSETS = [
    ((1, 1), (0, 1), (1, 0)),
    ((1, -2), (0, -1), (1, -1)),
    ((2, -1), (1, -1), (1, 0)),
]

BRIDGES_FROM = [[] for _ in range(NUM_CELLS)]
for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        u = r * BOARD_SIZE + c
        for (dr, dc), (cr1, cc1), (cr2, cc2) in BRIDGE_OFFSETS:
            pr, pc = r + dr, c + dc
            n1r, n1c = r + cr1, c + cc1
            n2r, n2c = r + cr2, c + cc2
            if (0 <= pr < BOARD_SIZE and 0 <= pc < BOARD_SIZE and
                0 <= n1r < BOARD_SIZE and 0 <= n1c < BOARD_SIZE and
                0 <= n2r < BOARD_SIZE and 0 <= n2c < BOARD_SIZE):
                v = pr * BOARD_SIZE + pc
                c1 = n1r * BOARD_SIZE + n1c
                c2 = n2r * BOARD_SIZE + n2c
                BRIDGES_FROM[u].append((v, c1, c2))

def bfs_01(is_player, is_opp, sources):
    dist = [999] * NUM_CELLS
    q = deque()
    for s in sources:
        if is_opp[s]:
            continue
        if is_player[s]:
            dist[s] = 0
            q.appendleft(s)
        else:
            dist[s] = 1
            q.append(s)

    while q:
        u = q.popleft()
        d = dist[u]
        for v in NEIGHBORS[u]:
            if is_opp[v]:
                continue
            cost = 0 if is_player[v] else 1
            new_d = d + cost
            if new_d < dist[v]:
                dist[v] = new_d
                if cost == 0:
                    q.appendleft(v)
                else:
                    q.append(v)
    return dist

def get_player_distances(is_player, is_opp, color):
    if color == 'b':
        src_nodes = BLACK_TOP
        tgt_nodes = BLACK_BOTTOM
    else:
        src_nodes = WHITE_LEFT
        tgt_nodes = WHITE_RIGHT

    d_src = bfs_01(is_player, is_opp, src_nodes)
    d_tgt = bfs_01(is_player, is_opp, tgt_nodes)

    min_dist = min((d_src[t] for t in tgt_nodes), default=999)
    path_len = [999] * NUM_CELLS
    for u in range(NUM_CELLS):
        if not is_opp[u]:
            if is_player[u]:
                path_len[u] = d_src[u] + d_tgt[u]
            else:
                path_len[u] = d_src[u] + d_tgt[u] - 1

    return min_dist, path_len

def evaluate(is_me, is_opp, my_color, opp_color):
    d_me, pl_me = get_player_distances(is_me, is_opp, my_color)
    if d_me == 0:
        return 1000000.0
    d_opp, pl_opp = get_player_distances(is_opp, is_me, opp_color)
    if d_opp == 0:
        return -1000000.0

    score = (d_opp - d_me) * 500.0

    # Shortest path multiplicity & connectivity potential
    for u in range(NUM_CELLS):
        if not is_me[u] and not is_opp[u]:
            diff_me = pl_me[u] - d_me
            if diff_me == 0:
                score += 30.0
            elif diff_me == 1:
                score += 10.0
            elif diff_me == 2:
                score += 3.0

            diff_opp = pl_opp[u] - d_opp
            if diff_opp == 0:
                score -= 35.0
            elif diff_opp == 1:
                score -= 12.0
            elif diff_opp == 2:
                score -= 4.0

    # Virtual connections: unbroken bridges
    for u in range(NUM_CELLS):
        if is_me[u]:
            for v, c1, c2 in BRIDGES_FROM[u]:
                if is_me[v] and not is_opp[c1] and not is_me[c1] and not is_opp[c2] and not is_me[c2]:
                    score += 18.0
        elif is_opp[u]:
            for v, c1, c2 in BRIDGES_FROM[u]:
                if is_opp[v] and not is_me[c1] and not is_opp[c1] and not is_me[c2] and not is_opp[c2]:
                    score -= 22.0

    # Center control
    for u in range(NUM_CELLS):
        r, c = CELL_ROW[u], CELL_COL[u]
        center_val = 10 - (abs(r - 5) + abs(c - 5))
        if is_me[u]:
            score += center_val * 1.5
        elif is_opp[u]:
            score -= center_val * 1.5

    return score

def get_candidates(is_me, is_opp, my_color, opp_color, limit=14):
    d_me, pl_me = get_player_distances(is_me, is_opp, my_color)
    d_opp, pl_opp = get_player_distances(is_opp, is_me, opp_color)

    scored = []
    for u in range(NUM_CELLS):
        if is_me[u] or is_opp[u]:
            continue

        p_me = pl_me[u]
        p_opp = pl_opp[u]
        r, c = CELL_ROW[u], CELL_COL[u]
        center_bonus = 10 - (abs(r - 5) + abs(c - 5))

        # Check adjacent stones
        adj_me = sum(1 for v in NEIGHBORS[u] if is_me[v])
        adj_opp = sum(1 for v in NEIGHBORS[u] if is_opp[v])

        priority = -12.0 * p_me - 14.0 * p_opp + center_bonus * 2.0 + adj_me * 4.0 + adj_opp * 4.0
        scored.append((priority, u))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [u for _, u in scored[:limit]]

def alpha_beta(depth, alpha, beta, is_me_turn, is_me, is_opp, my_color, opp_color, deadline):
    if time.time() > deadline:
        raise TimeoutError()

    if depth == 0:
        return evaluate(is_me, is_opp, my_color, opp_color)

    d_me, _ = get_player_distances(is_me, is_opp, my_color)
    if d_me == 0:
        return 1000000.0 + depth
    d_opp, _ = get_player_distances(is_opp, is_me, opp_color)
    if d_opp == 0:
        return -1000000.0 - depth

    limit = 8 if depth >= 2 else 5
    candidates = get_candidates(is_me, is_opp, my_color, opp_color, limit=limit)
    if not candidates:
        return evaluate(is_me, is_opp, my_color, opp_color)

    if is_me_turn:
        val = -float('inf')
        for m in candidates:
            is_me[m] = True
            res = alpha_beta(depth - 1, alpha, beta, False, is_me, is_opp, my_color, opp_color, deadline)
            is_me[m] = False
            if res > val:
                val = res
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return val
    else:
        val = float('inf')
        for m in candidates:
            is_opp[m] = True
            res = alpha_beta(depth - 1, alpha, beta, True, is_me, is_opp, my_color, opp_color, deadline)
            is_opp[m] = False
            if res < val:
                val = res
            beta = min(beta, val)
            if beta <= alpha:
                break
        return val

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    start_time = time.time()
    deadline = start_time + 0.85

    my_color = color.lower()
    opp_color = 'w' if my_color == 'b' else 'b'

    is_me = [False] * NUM_CELLS
    is_opp = [False] * NUM_CELLS

    for r, c in me:
        is_me[r * BOARD_SIZE + c] = True
    for r, c in opp:
        is_opp[r * BOARD_SIZE + c] = True

    # Empty board opening
    center_idx = 5 * BOARD_SIZE + 5
    if len(me) == 0 and len(opp) == 0:
        return (5, 5)

    if len(me) == 0 and len(opp) == 1:
        if not is_opp[center_idx]:
            return (5, 5)
        return (4, 5) if my_color == 'b' else (5, 4)

    # 1. Immediate Win Check
    d_me, pl_me = get_player_distances(is_me, is_opp, my_color)
    win_moves = [u for u in range(NUM_CELLS) if not is_me[u] and not is_opp[u] and pl_me[u] == 1]
    if win_moves:
        best_u = win_moves[0]
        return (CELL_ROW[best_u], CELL_COL[best_u])

    # 2. Immediate Loss Block Check
    d_opp, pl_opp = get_player_distances(is_opp, is_me, opp_color)
    threats = [u for u in range(NUM_CELLS) if not is_me[u] and not is_opp[u] and pl_opp[u] == 1]
    if len(threats) == 1:
        block_u = threats[0]
        return (CELL_ROW[block_u], CELL_COL[block_u])
    elif len(threats) > 1:
        # Multiple threats: pick the threat move that maximizes our own connectivity
        best_block = max(threats, key=lambda u: -pl_me[u])
        return (CELL_ROW[best_block], CELL_COL[best_block])

    # 3. Double Threat Check (2-move forced win)
    primary_candidates = get_candidates(is_me, is_opp, my_color, opp_color, limit=16)
    for m in primary_candidates:
        is_me[m] = True
        _, pl_after = get_player_distances(is_me, is_opp, my_color)
        is_me[m] = False
        winning_threats = sum(1 for u in range(NUM_CELLS) if not is_me[u] and not is_opp[u] and u != m and pl_after[u] == 1)
        if winning_threats >= 2:
            return (CELL_ROW[m], CELL_COL[m])

    # 4. Iterative Deepening Alpha-Beta Search
    best_move_idx = primary_candidates[0]
    try:
        for depth in range(1, 6):
            current_best_score = -float('inf')
            current_best_move = None
            alpha = -float('inf')
            beta = float('inf')

            for m in primary_candidates:
                if time.time() > deadline:
                    raise TimeoutError()
                is_me[m] = True
                score = alpha_beta(depth - 1, alpha, beta, False, is_me, is_opp, my_color, opp_color, deadline)
                is_me[m] = False

                if score > current_best_score:
                    current_best_score = score
                    current_best_move = m
                alpha = max(alpha, score)

            if current_best_move is not None:
                best_move_idx = current_best_move

            if current_best_score >= 900000.0:
                break
    except TimeoutError:
        pass

    return (CELL_ROW[best_move_idx], CELL_COL[best_move_idx])
