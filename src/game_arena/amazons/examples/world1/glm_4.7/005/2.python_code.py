
import numpy as np
import random

# Directions for Queen movement: (row_change, col_change)
DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
]

def get_legal_moves(board, player):
    """
    Generates all legal moves for a given player.
    Returns a list of tuples: (from_r, from_c, to_r, to_c, arrow_r, arrow_c)
    """
    moves = []
    # Find all amazons belonging to the player
    rows, cols = np.where(board == player)
    
    for r, c in zip(rows, cols):
        # Explore all moving directions
        for dr, dc in DIRECTIONS:
            for step in range(1, 6):
                nr, nc = r + dr * step, c + dc * step
                
                # Check boundaries and blockage
                if not (0 <= nr < 6 and 0 <= nc < 6):
                    break
                if board[nr, nc] != 0:
                    break
                
                # Amazon has moved to (nr, nc). Now consider arrow shots.
                # The 'from' square (r, c) is effectively empty now for the arrow path.
                for adr, adc in DIRECTIONS:
                    for astep in range(1, 6):
                        ar, ac = nr + adr * astep, nc + adc * astep
                        
                        if not (0 <= ar < 6 and 0 <= ac < 6):
                            break
                        
                        # Check if landing spot is valid for arrow
                        # It can be the original 'from' spot (now empty) or any other empty spot.
                        if ar == r and ac == c:
                            moves.append((r, c, nr, nc, ar, ac))
                            continue
                        
                        if board[ar, ac] != 0:
                            break
                            
                        moves.append((r, c, nr, nc, ar, ac))
    return moves

def count_reachable_squares(board, player):
    """
    Counts the number of unique squares an amazon can reach in one move.
    Used as a lightweight mobility metric.
    """
    count = 0
    rows, cols = np.where(board == player)
    
    # Using a set might be slower than just counting paths, 
    # but simple iteration is fine for 6x6.
    # We count destinations, not distinct squares, as it's a good proxy for options.
    
    for r, c in zip(rows, cols):
        for dr, dc in DIRECTIONS:
            for step in range(1, 6):
                nr, nc = r + dr * step, c + dc * step
                if not (0 <= nr < 6 and 0 <= nc < 6):
                    break
                if board[nr, nc] != 0:
                    break
                count += 1
    return count

def evaluate(board):
    """
    Heuristic evaluation of the board state.
    Positive is good for Player 1, Negative for Player 2.
    """
    # Mobility: difference in reachable squares
    mobility_1 = count_reachable_squares(board, 1)
    mobility_2 = count_reachable_squares(board, 2)
    score = (mobility_1 - mobility_2) * 10
    
    # Centrality: Sum of squared distances from center (2.5, 2.5)
    # We want to minimize this distance (maximize negative distance)
    
    def sum_sq_dist(player_val):
        rows, cols = np.where(board == player_val)
        dist = 0
        for r, c in zip(rows, cols):
            dist += (r - 2.5)**2 + (c - 2.5)**2
        return dist

    score -= (sum_sq_dist(1) - sum_sq_dist(2))
    
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0:
        return evaluate(board)
    
    if maximizing_player:
        max_eval = -float('inf')
        moves = get_legal_moves(board, 1)
        if not moves:
            return -10000 # Loss for me
        
        # Move ordering: Sort by immediate evaluation to help pruning
        # Note: Sorting takes time, skipping for performance in python for inner nodes
        # is often better unless the branching factor is huge. Here it is small.
        
        for m in moves:
            fr_r, fr_c, to_r, to_c, ar_r, ar_c = m
            
            # Apply move
            # Copy board to avoid mutating state
            new_board = board.copy()
            new_board[fr_r, fr_c] = 0
            new_board[to_r, to_c] = 1
            new_board[ar_r, ar_c] = -1
            
            eval_score = minimax(new_board, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        moves = get_legal_moves(board, 2)
        if not moves:
            return 10000 # Win for me (Opponent has no moves)
            
        for m in moves:
            fr_r, fr_c, to_r, to_c, ar_r, ar_c = m
            
            new_board = board.copy()
            new_board[fr_r, fr_c] = 0
            new_board[to_r, to_c] = 2
            new_board[ar_r, ar_c] = -1
            
            eval_score = minimax(new_board, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    """
    Main policy function called by the environment.
    """
    # Get all legal moves for Player 1
    moves = get_legal_moves(board, 1)
    
    if not moves:
        # No legal moves, return a default to avoid DQ, though game should be over
        return "0,0:0,0:0,0"
        
    best_score = -float('inf')
    best_move = None
    alpha = -float('inf')
    beta = float('inf')
    
    # Sort moves by a quick 1-ply heuristic to improve alpha-beta pruning at root
    # We evaluate the state resulting from the move immediately
    scored_moves = []
    for m in moves:
        fr_r, fr_c, to_r, to_c, ar_r, ar_c = m
        # Simulate
        b_temp = board.copy()
        b_temp[fr_r, fr_c] = 0
        b_temp[to_r, to_c] = 1
        b_temp[ar_r, ar_c] = -1
        scored_moves.append((m, evaluate(b_temp)))
    
    # Sort in descending order of score (best first)
    scored_moves.sort(key=lambda x: x[1], reverse=True)
    
    # Search Depth 2: Lookahead (Me -> Opponent -> Static Eval)
    DEPTH = 2
    
    for m, initial_score in scored_moves:
        fr_r, fr_c, to_r, to_c, ar_r, ar_c = m
        
        # Create new board state
        new_board = board.copy()
        new_board[fr_r, fr_c] = 0
        new_board[to_r, to_c] = 1
        new_board[ar_r, ar_c] = -1
        
        # Run minimax
        score = minimax(new_board, DEPTH - 1, alpha, beta, False)
        
        if score > best_score:
            best_score = score
            best_move = m
            
        alpha = max(alpha, score)
        
        # Optional: break if we found a certain win? Not necessary.
        
    # Format: "from_row,from_col:to_row,to_col:arrow_row,arrow_col"
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}:{best_move[4]},{best_move[5]}"
