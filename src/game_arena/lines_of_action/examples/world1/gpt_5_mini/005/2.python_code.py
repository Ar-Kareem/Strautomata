
import time
import random
from collections import deque
import math

# Lines of Action policy
# Exposes: policy(board) -> "r1,c1:r2,c2"

# Parameters (tune for speed/strength)
TIME_LIMIT = 0.90  # seconds per move (keep below 1s)
MAX_DEPTH = 3      # search depth (plies)
BEAM_WIDTH_ROOT = 60
BEAM_WIDTH = 25

# Directions for LOA movement (8 directions)
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)]

def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def generate_moves_for(board, player):
    """
    Generate all legal moves for player (1 or -1).
    Returns list of tuples (r1,c1,r2,c2, capture_flag)
    """
    moves = []
    # Precompute occupied map for quick access
    for r in range(8):
        for c in range(8):
            if board[r][c] != player:
                continue
            # For each direction
            for dr, dc in DIRS:
                # Count pieces along the line (both directions)
                count = 0
                # go positive direction
                rr, cc = r, c
                while in_bounds(rr, cc):
                    if board[rr][cc] != 0:
                        count += 1
                    rr += dr
                    cc += dc
                # go negative direction
                rr, cc = r - dr, c - dc
                while in_bounds(rr, cc):
                    if board[rr][cc] != 0:
                        count += 1
                    rr -= dr
                    cc -= dc
                # The piece itself counted twice? No: above counts include the start once in positive or both? Let's verify:
                # Positive loop started at r,c includes it once. Negative started at r-dr,c-dc excludes the start.
                # So count is correct.

                # Destination
                tr = r + dr * count
                tc = c + dc * count
                if not in_bounds(tr, tc):
                    continue
                # landing square must not have friendly piece
                if board[tr][tc] == player:
                    continue
                # cannot jump over enemy pieces: check intermediate squares
                blocked = False
                for k in range(1, count):
                    ir = r + dr * k
                    ic = c + dc * k
                    if board[ir][ic] == -player:
                        blocked = True
                        break
                if blocked:
                    continue
                capture = (board[tr][tc] == -player)
                moves.append((r, c, tr, tc, capture))
    return moves

def apply_move(board, move, player):
    r1, c1, r2, c2, _ = move
    newb = [list(row) for row in board]
    newb[r1][c1] = 0
    newb[r2][c2] = player
    return newb

def board_to_key(board):
    return tuple(tuple(row) for row in board)

def count_components(board, player):
    """
    Count connected components of 'player' pieces using 8-neighbor adjacency.
    """
    visited = [[False]*8 for _ in range(8)]
    comps = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] != player or visited[r][c]:
                continue
            comps += 1
            # BFS
            dq = deque()
            dq.append((r,c))
            visited[r][c] = True
            while dq:
                y,x = dq.popleft()
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        if dy==0 and dx==0:
                            continue
                        ny, nx = y+dy, x+dx
                        if 0 <= ny < 8 and 0 <= nx < 8 and not visited[ny][nx] and board[ny][nx]==player:
                            visited[ny][nx] = True
                            dq.append((ny,nx))
    return comps

def mst_chebyshev_length(positions):
    """
    Approximate minimal total connection length (spanning tree) using Prim's algorithm
    with Chebyshev distance (because 8-neighbor connectivity).
    """
    n = len(positions)
    if n <= 1:
        return 0
    used = [False]*n
    dist = [10**9]*n
    dist[0] = 0
    total = 0
    for _ in range(n):
        # find unused with min dist
        v = -1
        dv = 10**9
        for i in range(n):
            if not used[i] and dist[i] < dv:
                dv = dist[i]
                v = i
        if v == -1:
            break
        used[v] = True
        total += dist[v]
        yv, xv = positions[v]
        for u in range(n):
            if not used[u]:
                yu, xu = positions[u]
                # Chebyshev distance
                d = max(abs(yv-yu), abs(xv-xu))
                if d < dist[u]:
                    dist[u] = d
    return total

def collect_positions(board, player):
    pos = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                pos.append((r,c))
    return pos

def center_distance_metric(positions):
    # Sum of Chebyshev distances to center (3.5,3.5)
    total = 0.0
    for r,c in positions:
        total += max(abs(r-3.5), abs(c-3.5))
    return total

def evaluate(board):
    """
    Higher is better for the policy player (player 1).
    """
    # Basic features
    my_positions = collect_positions(board, 1)
    opp_positions = collect_positions(board, -1)
    my_count = len(my_positions)
    opp_count = len(opp_positions)

    # Components
    my_comps = count_components(board, 1)
    opp_comps = count_components(board, -1)

    # MST lengths (lower better)
    my_mst = mst_chebyshev_length(my_positions) if my_count>0 else 0
    opp_mst = mst_chebyshev_length(opp_positions) if opp_count>0 else 0

    # Mobility
    my_moves = generate_moves_for(board, 1)
    opp_moves = generate_moves_for(board, -1)
    my_mob = len(my_moves)
    opp_mob = len(opp_moves)

    # Center control
    my_center = center_distance_metric(my_positions)
    opp_center = center_distance_metric(opp_positions)

    # Compose score with tuned weights
    score = 0.0
    score += -1200.0 * (my_comps - 1)   # fewer components very good
    score +=  1000.0 * (opp_comps - 1)  # opponent having many components is good
    score += -6.0 * my_mst              # shorter own MST is better
    score +=  4.0 * opp_mst             # longer opponent MST is better
    score += 1.8 * (my_mob - opp_mob)   # mobility
    score += 6.0 * (my_count - opp_count)  # having more pieces slightly good
    score += -0.9 * (my_center - opp_center) # centralization
    # small random to break ties
    score += random.uniform(-0.001, 0.001)
    return score

def move_to_str(move):
    r1,c1,r2,c2,_ = move
    return f"{r1},{c1}:{r2},{c2}"

def static_move_score(board, move, player):
    # Quick heuristic to rank moves for beam
    r1,c1,r2,c2,capture = move
    score = 0
    if capture:
        score += 200
    # favor reducing own components
    # Apply move minimally and evaluate delta of components
    newb = apply_move(board, move, player)
    before = count_components(board, player)
    after = count_components(newb, player)
    score += 300*(before - after)
    # prefer moving towards center
    center_before = max(abs(r1-3.5), abs(c1-3.5))
    center_after = max(abs(r2-3.5), abs(c2-3.5))
    score += 3*(center_before - center_after)
    # prefer reducing MST
    pos_before = collect_positions(board, player)
    pos_after = collect_positions(newb, player)
    mst_before = mst_chebyshev_length(pos_before) if len(pos_before)>0 else 0
    mst_after = mst_chebyshev_length(pos_after) if len(pos_after)>0 else 0
    score += 5*(mst_before - mst_after)
    return score

def minimax(board, depth, maximizing, alpha, beta, start_time, time_limit, beam_width):
    """
    Minimax with alpha-beta pruning.
    maximizing: True if it's policy player's turn (player 1), False otherwise (opponent -1)
    Returns (best_score, best_move)
    """
    # Time check
    if time.time() - start_time > time_limit:
        raise TimeoutError()

    # Terminal or depth 0
    if depth == 0:
        return evaluate(board), None

    player = 1 if maximizing else -1
    moves = generate_moves_for(board, player)
    if not moves:
        # No moves: evaluate board
        return evaluate(board), None

    # Move ordering: score and keep top beam_width
    scored = []
    for m in moves:
        sc = static_move_score(board, m, player)
        scored.append((sc, m))
    scored.sort(key=lambda x: -x[0])
    if beam_width is not None and len(scored) > beam_width:
        scored = scored[:beam_width]
    moves_ordered = [m for (_, m) in scored]

    best_move = None
    if maximizing:
        value = -1e18
        for m in moves_ordered:
            newb = apply_move(board, m, player)
            try:
                child_val, _ = minimax(newb, depth-1, False, alpha, beta, start_time, time_limit, BEAM_WIDTH)
            except TimeoutError:
                raise
            if child_val > value:
                value = child_val
                best_move = m
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        # minimizing for opponent: they try to reduce our evaluation
        value = 1e18
        for m in moves_ordered:
            newb = apply_move(board, m, player)
            try:
                child_val, _ = minimax(newb, depth-1, True, alpha, beta, start_time, time_limit, BEAM_WIDTH)
            except TimeoutError:
                raise
            if child_val < value:
                value = child_val
                best_move = m
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_move

def policy(board) -> str:
    start_time = time.time()
    time_limit = TIME_LIMIT
    best_move = None

    # Generate all legal moves for root player (1)
    root_moves = generate_moves_for(board, 1)
    if not root_moves:
        # No moves - select any (shouldn't normally happen)
        # Return a harmless "no-op" like moving a piece 0 squares is illegal; but we must return a legal move.
        # Try to find any move by scanning board for any piece and direction with count > 0
        for r in range(8):
            for c in range(8):
                if board[r][c] != 1:
                    continue
                for dr,dc in DIRS:
                    # count as in generator
                    count = 0
                    rr, cc = r, c
                    while in_bounds(rr, cc):
                        if board[rr][cc] != 0:
                            count += 1
                        rr += dr
                        cc += dc
                    rr, cc = r - dr, c - dc
                    while in_bounds(rr, cc):
                        if board[rr][cc] != 0:
                            count += 1
                        rr -= dr
                        cc -= dc
                    tr = r + dr * count
                    tc = c + dc * count
                    if in_bounds(tr, tc) and board[tr][tc] != 1:
                        blocked = False
                        for k in range(1, count):
                            ir = r + dr * k
                            ic = c + dc * k
                            if board[ir][ic] == -1:
                                blocked = True
                                break
                        if not blocked:
                            return f"{r},{c}:{tr},{tc}"
        # As ultimate fallback (shouldn't happen), return fixed legal coordinates though might be illegal:
        return "0,0:0,1"

    # Root move ordering
    scored = []
    for m in root_moves:
        sc = static_move_score(board, m, 1)
        scored.append((sc, m))
    scored.sort(key=lambda x: -x[0])
    # limit root branching
    if len(scored) > BEAM_WIDTH_ROOT:
        scored = scored[:BEAM_WIDTH_ROOT]
    candidate_moves = [m for (_, m) in scored]

    # Iterative deepening style but limited: try decreasing depths/time-check
    final_best = candidate_moves[0]
    final_best_score = -1e18
    try:
        # Try full depth once (may raise TimeoutError)
        sc, mv = minimax_root_search(board, candidate_moves, MAX_DEPTH, start_time, time_limit)
        if mv is not None:
            final_best = mv
    except TimeoutError:
        # If timeout, pick best available from static ordering
        pass

    return move_to_str(final_best)

def minimax_root_search(board, root_moves, max_depth, start_time, time_limit):
    """
    Evaluate each root move with minimax (depth max_depth-1 for the opponent) and return the best move.
    """
    best_score = -1e18
    best_move = None
    alpha = -1e18
    beta = 1e18
    for m in root_moves:
        if time.time() - start_time > time_limit:
            raise TimeoutError()
        newb = apply_move(board, m, 1)
        # For opponent's turn now (minimizing)
        try:
            val, _ = minimax(newb, max_depth-1, False, alpha, beta, start_time, time_limit, BEAM_WIDTH)
        except TimeoutError:
            raise
        if val > best_score:
            best_score = val
            best_move = m
        alpha = max(alpha, best_score)
    return best_score, best_move

# The required API function
def policy(board) -> str:
    # convert board to nested lists if it's provided as numpy array or similar
    b = []
    for r in range(8):
        row = []
        for c in range(8):
            row.append(int(board[r][c]))
        b.append(row)
    return policy_impl(b)

def policy_impl(board):
    # wrapper to use local policy logic (to avoid name clash)
    start_time = time.time()
    time_limit = TIME_LIMIT
    # Generate root moves
    root_moves = generate_moves_for(board, 1)
    if not root_moves:
        # Try to return any plausible legal move (should not occur)
        for r in range(8):
            for c in range(8):
                if board[r][c] != 1:
                    continue
                for dr,dc in DIRS:
                    count = 0
                    rr, cc = r, c
                    while in_bounds(rr, cc):
                        if board[rr][cc] != 0:
                            count += 1
                        rr += dr
                        cc += dc
                    rr, cc = r - dr, c - dc
                    while in_bounds(rr, cc):
                        if board[rr][cc] != 0:
                            count += 1
                        rr -= dr
                        cc -= dc
                    tr = r + dr * count
                    tc = c + dc * count
                    if in_bounds(tr, tc) and board[tr][tc] != 1:
                        blocked = False
                        for k in range(1, count):
                            ir = r + dr * k
                            ic = c + dc * k
                            if board[ir][ic] == -1:
                                blocked = True
                                break
                        if not blocked:
                            return f"{r},{c}:{tr},{tc}"
        # fallback
        return "0,0:0,1"

    # Score root moves and pick top candidates
    scored = []
    for m in root_moves:
        sc = static_move_score(board, m, 1)
        scored.append((sc, m))
    scored.sort(key=lambda x: -x[0])
    if len(scored) > BEAM_WIDTH_ROOT:
        scored = scored[:BEAM_WIDTH_ROOT]
    candidates = [m for (_, m) in scored]

    # Search each candidate with minimax depth MAX_DEPTH
    best_move = candidates[0]
    best_score = -1e18
    alpha = -1e18
    beta = 1e18

    # Try depths decreasing if time is tight
    try:
        for m in candidates:
            if time.time() - start_time > time_limit:
                break
            newb = apply_move(board, m, 1)
            val, _ = minimax(newb, MAX_DEPTH-1, False, alpha, beta, start_time, time_limit, BEAM_WIDTH)
            if val > best_score:
                best_score = val
                best_move = m
            alpha = max(alpha, best_score)
    except TimeoutError:
        # Time's up: return current best_move
        pass

    return move_to_str(best_move)

# If this module is run directly, provide a tiny random test
if __name__ == "__main__":
    # Example starting board (not necessarily actual LOA start) - random
    test_board = [[0]*8 for _ in range(8)]
    # place a couple pieces
    test_board[0][0] = 1
    test_board[7][7] = -1
    print(policy_impl(test_board))
