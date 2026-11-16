
import math
import sys
from collections import deque

# Constants
INF = 10**9
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
WIN_EVAL = 100000000  # Big constant to prefer immediate wins

def connectivity_stats(board, player):
    """Return (largest_component_size, total_pieces, num_components) for player."""
    seen = [[False]*8 for _ in range(8)]
    best = 0
    total = 0
    comps = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player and not seen[r][c]:
                comps += 1
                q = deque()
                q.append((r,c))
                seen[r][c] = True
                cnt = 0
                while q:
                    cr, cc = q.popleft()
                    cnt += 1
                    for dr, dc in DIRECTIONS:
                        nr, nc = cr+dr, cc+dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and not seen[nr][nc] and board[nr][nc] == player:
                            seen[nr][nc] = True
                            q.append((nr, nc))
                if cnt > best:
                    best = cnt
                total += cnt
    return best, total, comps

def count_pieces(board):
    cnt = 0
    for r in range(8):
        for c in range(8):
            v = board[r][c]
            if v != 0:
                cnt += 1
    return cnt

def is_line_clear(board, r0, c0, dr, dc, steps, target_r, target_c, player):
    """Check path from (r0,c0) stepping (dr,dc) for 'steps' does not cross opponent pieces.
    It allows landing on opponent piece at target and forbids landing on own piece.
    """
    # Step by step, excluding the final destination for crossing check
    cr, cc = r0, c0
    for s in range(steps):
        cr += dr
        cc += dc
        if (cr, cc) == (target_r, target_c):
            # This is the destination cell; it can be empty or opponent (capture)
            continue
        if not (0 <= cr < 8 and 0 <= cc < 8):
            return False
        if board[cr][cc] == -player:
            # Cannot jump over opponent piece
            return False
        if board[cr][cc] == player:
            # Cannot move through own piece (would imply landing on it which is illegal)
            return False
    return True

def generate_legal_moves(board, player):
    """Generate all legal moves for player under LOA rules.
    Returns list of tuples: (r0, c0, r1, c1, capture_flag)
    """
    total_pieces = count_pieces(board)
    moves = []
    for r0 in range(8):
        for c0 in range(8):
            if board[r0][c0] != player:
                continue
            for dr, dc in DIRECTIONS:
                # Count pieces along the line in direction (dr, dc)
                cr, cc = r0 + dr, c0 + dc
                line_cnt = 0
                while 0 <= cr < 8 and 0 <= cc < 8:
                    if board[cr][cc] != 0:
                        line_cnt += 1
                    cr += dr
                    cc += dc
                if line_cnt == 0:
                    continue
                if line_cnt != total_pieces:
                    continue
                steps = total_pieces
                tr = r0 + dr * steps
                tc = c0 + dc * steps
                if not (0 <= tr < 8 and 0 <= tc < 8):
                    continue
                if board[tr][tc] == player:
                    continue  # cannot land on own piece
                # Path must be clear of opponent pieces
                if not is_line_clear(board, r0, c0, dr, dc, steps, tr, tc, player):
                    continue
                capture_flag = 1 if board[tr][tc] == -player else 0
                moves.append((r0, c0, tr, tc, capture_flag))
    return moves

def make_move(board, move, player):
    r0, c0, r1, c1, capture = move
    new_board = [row[:] for row in board]
    new_board[r0][c0] = 0
    new_board[r1][c1] = player
    return new_board

def evaluate_board(board, perspective):
    """Heuristic evaluation from perspective (1 or -1). Higher is better for perspective.
    Combines connectivity, mobility, and material/center weighting.
    """
    # Connectivity: favor larger connected groups for perspective and fewer components
    my_best, my_total, my_comps = connectivity_stats(board, perspective)
    op_best, op_total, op_comps = connectivity_stats(board, -perspective)
    # If either side has all pieces connected => terminal; handle outside evaluation, but still reward
    if my_total > 0 and my_comps == 1:
        score = WIN_EVAL  # winning terminal
        return score
    if op_total > 0 and op_comps == 1:
        score = -WIN_EVAL  # losing terminal
        return score

    # Connectivity signal
    # Normalize by total pieces to reduce early-game variance
    denom = max(1, my_total + op_total)
    conn = (my_best - op_best) / denom

    # Mobility signal (number of legal moves)
    my_moves = len(generate_legal_moves(board, perspective))
    op_moves = len(generate_legal_moves(board, -perspective))
    mobility = (my_moves - op_moves) / 64.0  # scale down

    # Material signal (encourage presence; small weight)
    material = (my_total - op_total) / 12.0

    # Center control (average distance to center)
    def center_score(player):
        total = 0
        cnt = 0
        for r in range(8):
            for c in range(8):
                if board[r][c] == player:
                    total += abs(r - 3.5) + abs(c - 3.5)
                    cnt += 1
        return total / max(1, cnt)
    my_center = center_score(perspective)
    op_center = center_score(-perspective)
    center = (op_center - my_center) / 7.0  # inverted: lower distance is better

    # Weighted sum
    # Connectivity is the primary signal in LOA, followed by mobility and material
    eval_score = 120.0 * conn + 3.0 * mobility + 2.0 * material + 1.0 * center
    return eval_score

def game_is_over(board):
    """Return True if the board is a terminal state for either player."""
    my_best, my_total, my_comps = connectivity_stats(board, 1)
    op_best, op_total, op_comps = connectivity_stats(board, -1)
    if my_total > 0 and my_comps == 1:
        return True
    if op_total > 0 and op_comps == 1:
        return True
    return False

def transposition_key(board, player, depth, flag):
    return (tuple(tuple(row) for row in board), player, depth, flag)

def alpha_beta(board, player, depth, alpha, beta, start_time, time_limit, time_budget, tt=None, path=None, last_move=None):
    """Alpha-beta with basic time checking and simple transposition table.
    player: 1 if we are maximizing, -1 if minimizing.
    depth: remaining plies to search.
    flag: 0 for exact, 1 for lowerbound, -1 for upperbound.
    Returns (best_value, best_move) or (score, None) at terminal.
    """
    if path is None:
        path = []
    # Time control
    if time_limit is not None:
        if sys.getsizeof(board) > 0:
            pass  # just to avoid linter
        if time.time() - start_time > time_budget:
            # Out of time; evaluate current node and return
            return evaluate_board(board, 1) if player == 1 else evaluate_board(board, -1), None

    # Check terminal by connectivity
    my_best, my_total, my_comps = connectivity_stats(board, 1)
    op_best, op_total, op_comps = connectivity_stats(board, -1)
    if my_total > 0 and my_comps == 1:
        return WIN_EVAL, None
    if op_total > 0 and op_comps == 1:
        return -WIN_EVAL, None

    if depth == 0:
        ev = evaluate_board(board, 1) if player == 1 else evaluate_board(board, -1)
        return ev, None

    moves = generate_legal_moves(board, player)
    if not moves:
        # No legal moves => losing position
        return -WIN_EVAL + depth, None

    # Move ordering: captures first, then heuristics about connectivity
    def move_score(m):
        r0, c0, r1, c1, cap = m
        sc = 0
        if cap:
            sc += 10000  # prioritize captures heavily
        # Slight bias towards moving towards the center
        sc -= abs(r1 - 3.5) + abs(c1 - 3.5)
        return sc
    moves.sort(key=move_score, reverse=True)

    best_move = None
    if player == 1:  # maximizing for perspective 1
        value = -INF
        for move in moves:
            new_board = make_move(board, move, player)
            child_val, _ = alpha_beta(new_board, -player, depth-1, alpha, beta, start_time, time_limit, time_budget, tt, path+[(move)], move)
            if child_val > value:
                value = child_val
                best_move = move
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
            if time_limit is not None and (time.time() - start_time > time_budget):
                break
        return value, best_move
    else:  # minimizing for perspective -1
        value = INF
        for move in moves:
            new_board = make_move(board, move, player)
            child_val, _ = alpha_beta(new_board, -player, depth-1, alpha, beta, start_time, time_limit, time_budget, tt, path+[(move)], move)
            if child_val < value:
                value = child_val
                best_move = move
            if value < beta:
                beta = value
            if alpha >= beta:
                break
            if time_limit is not None and (time.time() - start_time > time_budget):
                break
        return value, best_move

def policy(board):
    """Main policy entry. Always returns a legal move in 'r0,c0:r1,c1' format.
    Uses iterative deepening with time-aware cutoff.
    """
    player = 1  # We are always the player to move
    # Quick capture check (one-ply)
    moves = generate_legal_moves(board, player)
    # Prefer immediate winning capture if any (rare)
    best_capture = None
    for mv in moves:
        if mv[4] == 1:  # capture
            best_capture = mv
            break
    # Iterative deepening
    start_time = time.time()
    time_limit = 0.98  # seconds
    best_overall = None
    best_value = -INF
    # Adjust depth based on branching factor to keep within time
    n_moves = len(moves)
    max_depth = 4 if n_moves <= 40 else (3 if n_moves <= 80 else 2)

    for depth in range(1, max_depth+1):
        if time.time() - start_time > time_limit:
            break
        val, move = alpha_beta(board, player, depth, -INF, INF, start_time, time_limit, time_limit, None, [], None)
        if move is not None:
            best_overall = move
            best_value = val
        else:
            # No move found at this depth (shouldn't happen), keep previous
            pass

    if best_overall is None:
        # Fallback: pick a legal move deterministically
        if not moves:
            # Should never happen in legal positions; return a no-op to avoid crash
            return "0,0:0,0"
        moves.sort(key=lambda m: (m[4], -(abs(m[2]-3.5) + abs(m[3]-3.5))))
        best_overall = moves[0]

    r0, c0, r1, c1, _ = best_overall
    return f"{r0},{c0}:{r1},{c1}"
