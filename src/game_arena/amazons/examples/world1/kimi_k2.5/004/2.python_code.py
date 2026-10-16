
import numpy as np
import time

# 8 directions (queen moves)
DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
INF = 1000000

def get_amazons(board, player):
    """Return list of (r, c) positions for the given player."""
    return list(zip(*np.where(board == player)))

def count_mobility(board, player):
    """Count total number of valid queen moves for all amazons of a player."""
    count = 0
    for r, c in get_amazons(board, player):
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
                count += 1
                nr += dr
                nc += dc
    return count

def generate_moves(board, player):
    """Generate all legal moves for player. Returns list of (fr, fc, tr, tc, ar, ac)."""
    moves = []
    amazons = get_amazons(board, player)
    for fr, fc in amazons:
        # Amazon movement
        for dr, dc in DIRS:
            for step in range(1, 6):
                tr = fr + dr * step
                tc = fc + dc * step
                if not (0 <= tr < 6 and 0 <= tc < 6):
                    break
                if board[tr, tc] != 0:
                    break
                # Arrow shot from (tr, tc)
                for dr2, dc2 in DIRS:
                    for step2 in range(1, 6):
                        ar = tr + dr2 * step2
                        ac = tc + dc2 * step2
                        if not (0 <= ar < 6 and 0 <= ac < 6):
                            break
                        # Arrow can pass through or land on the vacated (fr, fc)
                        if ar == fr and ac == fc:
                            moves.append((fr, fc, tr, tc, ar, ac))
                            continue
                        if board[ar, ac] != 0:
                            break
                        moves.append((fr, fc, tr, tc, ar, ac))
    return moves

def apply_move(board, move, player):
    """Apply move to board. move = (fr, fc, tr, tc, ar, ac)"""
    fr, fc, tr, tc, ar, ac = move
    board[fr, fc] = 0
    board[tr, tc] = player
    board[ar, ac] = -1

def undo_move(board, move, player):
    """Undo move on board."""
    fr, fc, tr, tc, ar, ac = move
    board[ar, ac] = 0
    board[tr, tc] = 0
    board[fr, fc] = player

def evaluate(board):
    """Evaluate board state. Positive is good for player 1."""
    # Check terminal conditions
    my_moves = generate_moves(board, 1)
    if not my_moves:
        return -INF
    opp_moves = generate_moves(board, 2)
    if not opp_moves:
        return INF
    # Mobility difference
    return count_mobility(board, 1) - count_mobility(board, 2)

def minimax(board, depth, alpha, beta, is_maximizing):
    """Alpha-beta minimax search."""
    if depth == 0:
        return evaluate(board)
    
    player = 1 if is_maximizing else 2
    moves = generate_moves(board, player)
    
    if not moves:
        return -INF if is_maximizing else INF
    
    if is_maximizing:
        max_eval = -INF
        for move in moves:
            apply_move(board, move, player)
            eval = minimax(board, depth - 1, alpha, beta, False)
            undo_move(board, move, player)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = INF
        for move in moves:
            apply_move(board, move, player)
            eval = minimax(board, depth - 1, alpha, beta, True)
            undo_move(board, move, player)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    """Select the best move."""
    board = np.array(board)  # Ensure numpy array
    moves = generate_moves(board, 1)
    
    if not moves:
        # Should not happen per problem statement, but return a dummy to avoid crash
        return "0,0:0,0:0,0"
    
    start_time = time.time()
    best_move = moves[0]
    best_val = -INF
    
    # Adaptive depth: use depth 2 if move count is manageable, else depth 1
    if len(moves) <= 100:
        # Depth 2 search (my move + opponent best response)
        for move in moves:
            if time.time() - start_time > 0.9:
                break
            apply_move(board, move, 1)
            val = minimax(board, 1, -INF, INF, False)  # Opponent minimizes
            undo_move(board, move, 1)
            if val > best_val:
                best_val = val
                best_move = move
    else:
        # Depth 1 (greedy) for high branching factor
        for move in moves:
            if time.time() - start_time > 0.9:
                break
            apply_move(board, move, 1)
            val = evaluate(board)
            undo_move(board, move, 1)
            if val > best_val:
                best_val = val
                best_move = move
    
    fr, fc, tr, tc, ar, ac = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
