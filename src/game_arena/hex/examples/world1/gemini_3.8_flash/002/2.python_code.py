
import time
import collections
import random

# Precompute board constants
BOARD_SIZE = 11
NUM_CELLS = 121

# Precompute neighbor offsets
NEIGHBORS = [[] for _ in range(NUM_CELLS)]
for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        idx = r * BOARD_SIZE + c
        for dr, dc in ((-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                NEIGHBORS[idx].append(nr * BOARD_SIZE + nc)

# Precompute 2-bridge patterns
# Each pattern: (target_dr, target_dc, carrier1_dr, carrier1_dc, carrier2_dr, carrier2_dc)
BRIDGE_OFFSETS = [
    (-1, 2, -1, 1, 0, 1),
    (1, 1, 0, 1, 1, 0),
    (2, -1, 1, 0, 1, -1),
    (1, -2, 1, -1, 0, -1),
    (-1, -1, 0, -1, -1, 0),
    (-2, 1, -1, 0, -1, 1),
]

BRIDGES = [[] for _ in range(NUM_CELLS)]
for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        idx = r * BOARD_SIZE + c
        for dr, dc, c1r, c1c, c2r, c2c in BRIDGE_OFFSETS:
            tr, tc = r + dr, c + dc
            cr1, cc1 = r + c1r, c + c1c
            cr2, cc2 = r + c2r, c + c2c
            if 0 <= tr < BOARD_SIZE and 0 <= tc < BOARD_SIZE and \
               0 <= cr1 < BOARD_SIZE and 0 <= cc1 < BOARD_SIZE and \
               0 <= cr2 < BOARD_SIZE and 0 <= cc2 < BOARD_SIZE:
                t_idx = tr * BOARD_SIZE + tc
                c1_idx = cr1 * BOARD_SIZE + cc1
                c2_idx = cr2 * BOARD_SIZE + cc2
                BRIDGES[idx].append((t_idx, c1_idx, c2_idx))

# Precompute center proximity values for tie-breaking
CENTER_VAL = [0] * NUM_CELLS
for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        idx = r * BOARD_SIZE + c
        dist_to_center = abs(r - 5) + abs(c - 5)
        CENTER_VAL[idx] = 12 - dist_to_center

# Boundary definitions
BLACK_STARTS = [c for c in range(BOARD_SIZE)]
BLACK_TARGETS = [10 * BOARD_SIZE + c for c in range(BOARD_SIZE)]
BLACK_TARGETS_SET = set(BLACK_TARGETS)

WHITE_STARTS = [r * BOARD_SIZE for r in range(BOARD_SIZE)]
WHITE_TARGETS = [r * BOARD_SIZE + 10 for r in range(BOARD_SIZE)]
WHITE_TARGETS_SET = set(WHITE_TARGETS)

# Zobrist keys for transposition table
_rng = random.Random(1337)
ZOBRIST = [[_rng.getrandbits(64) for _ in range(NUM_CELLS)] for _ in range(3)]

INF = 999


def _get_dist(board, player, starts, targets_set):
    """0-1 BFS returning minimum distance to reach targets_set."""
    other = 3 - player
    dist = [INF] * NUM_CELLS
    dq = collections.deque()

    for idx in starts:
        cell = board[idx]
        if cell != other:
            w = 0 if cell == player else 1
            dist[idx] = w
            if w == 0:
                dq.appendleft(idx)
            else:
                dq.append(idx)

    while dq:
        u = dq.popleft()
        d = dist[u]
        if u in targets_set:
            return d
        for v in NEIGHBORS[u]:
            cell_v = board[v]
            if cell_v != other:
                w = 0 if cell_v == player else 1
                if d + w < dist[v]:
                    dist[v] = d + w
                    if w == 0:
                        dq.appendleft(v)
                    else:
                        dq.append(v)
    return INF


def _get_full_dist(board, player, starts):
    """Full 0-1 BFS returning distances to all nodes."""
    other = 3 - player
    dist = [INF] * NUM_CELLS
    dq = collections.deque()

    for idx in starts:
        cell = board[idx]
        if cell != other:
            w = 0 if cell == player else 1
            dist[idx] = w
            if w == 0:
                dq.appendleft(idx)
            else:
                dq.append(idx)

    while dq:
        u = dq.popleft()
        d = dist[u]
        for v in NEIGHBORS[u]:
            cell_v = board[v]
            if cell_v != other:
                w = 0 if cell_v == player else 1
                if d + w < dist[v]:
                    dist[v] = d + w
                    if w == 0:
                        dq.appendleft(v)
                    else:
                        dq.append(v)
    return dist


class SearchTimeout(Exception):
    pass


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    start_time = time.time()
    deadline = start_time + 0.75

    # First move opening
    if not me and not opp:
        return (5, 5)

    # Initialize board array: 0 = empty, 1 = me, 2 = opp
    board = [0] * NUM_CELLS
    current_hash = 0
    for r, c in me:
        idx = r * BOARD_SIZE + c
        board[idx] = 1
        current_hash ^= ZOBRIST[1][idx]
    for r, c in opp:
        idx = r * BOARD_SIZE + c
        board[idx] = 2
        current_hash ^= ZOBRIST[2][idx]

    # Setup boundaries based on color
    if color == 'b':
        my_starts = BLACK_STARTS
        my_targets = BLACK_TARGETS
        my_targets_set = BLACK_TARGETS_SET
        opp_starts = WHITE_STARTS
        opp_targets = WHITE_TARGETS
        opp_targets_set = WHITE_TARGETS_SET
    else:
        my_starts = WHITE_STARTS
        my_targets = WHITE_TARGETS
        my_targets_set = WHITE_TARGETS_SET
        opp_starts = BLACK_STARTS
        opp_targets = BLACK_TARGETS
        opp_targets_set = BLACK_TARGETS_SET

    empty_cells = [idx for idx in range(NUM_CELLS) if board[idx] == 0]
    if not empty_cells:
        return (0, 0)
    if len(empty_cells) == 1:
        return (empty_cells[0] // BOARD_SIZE, empty_cells[0] % BOARD_SIZE)

    # 1. IMMEDIATE WIN DETECTION
    my_dist = _get_dist(board, 1, my_starts, my_targets_set)
    if my_dist == 1:
        for idx in empty_cells:
            board[idx] = 1
            if _get_dist(board, 1, my_starts, my_targets_set) == 0:
                return (idx // BOARD_SIZE, idx % BOARD_SIZE)
            board[idx] = 0

    # 2. IMMEDIATE BLOCK DETECTION
    opp_dist = _get_dist(board, 2, opp_starts, opp_targets_set)
    winning_blocks = []
    if opp_dist == 1:
        for idx in empty_cells:
            board[idx] = 2
            if _get_dist(board, 2, opp_starts, opp_targets_set) == 0:
                winning_blocks.append(idx)
            board[idx] = 0

        if len(winning_blocks) == 1:
            return (winning_blocks[0] // BOARD_SIZE, winning_blocks[0] % BOARD_SIZE)

    # 3. ROOT MOVE CANDIDATE GENERATION & RANKING
    dist_my_start = _get_full_dist(board, 1, my_starts)
    dist_my_target = _get_full_dist(board, 1, my_targets)
    dist_opp_start = _get_full_dist(board, 2, opp_starts)
    dist_opp_target = _get_full_dist(board, 2, opp_targets)

    search_pool = winning_blocks if winning_blocks else empty_cells
    candidate_scores = []
    for idx in search_pool:
        p_my = dist_my_start[idx] + dist_my_target[idx] - 1
        p_opp = dist_opp_start[idx] + dist_opp_target[idx] - 1

        bridge_score = 0
        for t_idx, c1, c2 in BRIDGES[idx]:
            if board[t_idx] == 1 and board[c1] == 0 and board[c2] == 0:
                bridge_score += 4
            elif board[t_idx] == 2 and board[c1] == 0 and board[c2] == 0:
                bridge_score += 3

        score = -p_my * 20 - p_opp * 22 + bridge_score * 3 + CENTER_VAL[idx]
        candidate_scores.append((score, idx))

    candidate_scores.sort(reverse=True)
    root_candidates = [idx for _, idx in candidate_scores[:16]]

    # 4. ITERATIVE DEEPENING ALPHA-BETA SEARCH
    tt = {}
    best_overall_move = root_candidates[0]
    node_count = 0

    def evaluate_leaf():
        m_d = _get_dist(board, 1, my_starts, my_targets_set)
        if m_d == 0:
            return 100000
        o_d = _get_dist(board, 2, opp_starts, opp_targets_set)
        if o_d == 0:
            return -100000
        if m_d >= INF:
            return -90000
        if o_d >= INF:
            return 90000
        return (o_d - m_d) * 1000

    def alphabeta(depth, alpha, beta, is_max, current_hash):
        nonlocal node_count
        node_count += 1
        if (node_count & 63) == 0 and time.time() > deadline:
            raise SearchTimeout()

        entry = tt.get(current_hash)
        if entry is not None:
            tt_depth, tt_val, tt_flag, tt_best = entry
            if tt_depth >= depth:
                if tt_flag == 0:  # EXACT
                    return tt_val, tt_best
                elif tt_flag == 1 and tt_val > alpha:  # LOWERBOUND
                    alpha = tt_val
                elif tt_flag == 2 and tt_val < beta:  # UPPERBOUND
                    beta = tt_val
                if alpha >= beta:
                    return tt_val, tt_best

        if depth == 0:
            val = evaluate_leaf()
            return val, None

        # Filter candidates near active stones
        player = 1 if is_max else 2
        moves = []
        for idx in range(NUM_CELLS):
            if board[idx] == 0:
                has_adj = any(board[v] != 0 for v in NEIGHBORS[idx])
                if has_adj:
                    moves.append(idx)

        if not moves:
            moves = [idx for idx in range(NUM_CELLS) if board[idx] == 0]

        # Prioritize TT move if available
        tt_move = entry[3] if entry is not None else None
        if tt_move in moves:
            moves.remove(tt_move)
            moves.insert(0, tt_move)

        moves = moves[:8]
        best_move = moves[0]

        if is_max:
            max_eval = -999999
            for m in moves:
                board[m] = 1
                next_hash = current_hash ^ ZOBRIST[1][m]
                eval_val, _ = alphabeta(depth - 1, alpha, beta, False, next_hash)
                board[m] = 0

                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = m
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break

            flag = 0
            if max_eval <= alpha:
                flag = 2
            elif max_eval >= beta:
                flag = 1
            tt[current_hash] = (depth, max_eval, flag, best_move)
            return max_eval, best_move
        else:
            min_eval = 999999
            for m in moves:
                board[m] = 2
                next_hash = current_hash ^ ZOBRIST[2][m]
                eval_val, _ = alphabeta(depth - 1, alpha, beta, True, next_hash)
                board[m] = 0

                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = m
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break

            flag = 0
            if min_eval <= alpha:
                flag = 2
            elif min_eval >= beta:
                flag = 1
            tt[current_hash] = (depth, min_eval, flag, best_move)
            return min_eval, best_move

    # Iterative deepening loop
    for current_depth in range(1, 6):
        try:
            best_val = -999999
            best_move_this_depth = root_candidates[0]
            alpha = -999999
            beta = 999999

            for m in root_candidates:
                board[m] = 1
                next_hash = current_hash ^ ZOBRIST[1][m]
                val, _ = alphabeta(current_depth - 1, alpha, beta, False, next_hash)
                board[m] = 0

                # Add intrinsic root score as tie-breaker
                total_val = val * 100 + CENTER_VAL[m]
                if total_val > best_val:
                    best_val = total_val
                    best_move_this_depth = m
                alpha = max(alpha, val)

            best_overall_move = best_move_this_depth
            if time.time() > deadline or best_val >= 9000000:
                break
        except SearchTimeout:
            break

    return (best_overall_move // BOARD_SIZE, best_overall_move % BOARD_SIZE)
