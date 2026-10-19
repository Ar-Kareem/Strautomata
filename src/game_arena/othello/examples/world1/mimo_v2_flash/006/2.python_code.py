
import numpy as np
import sys

# Precomputed board weights for positional advantage
# 100 for corners, -20 for adjacent to corners, -40 for X-squares, etc.
# Indices are [row][col] -> 0-7
BOARD_WEIGHTS = np.array([
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10, -2, 5, 1, 1, 5, -2, 10],
    [5, -2, 1, 0, 0, 1, -2, 5],
    [5, -2, 1, 0, 0, 1, -2, 5],
    [10, -2, 5, 1, 1, 5, -2, 10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10, 5, 5, 10, -20, 100]
])

# Directions: (dr, dc)
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Minimax with Alpha-Beta pruning for Othello.
    Prioritizes corners and mobility.
    """
    # Determine game phase for depth adjustment
    # Early game: fewer pieces on board -> deeper search
    # Late game: more pieces -> shallower search (but actually need endgame solvers, 
    # here we clamp depth to 4-6 for performance).
    total_discs = np.sum(you) + np.sum(opponent)
    
    # Adjust depth based on game progression
    if total_discs < 10:
        max_depth = 5
    elif total_discs < 50:
        max_depth = 4
    else:
        max_depth = 4 # Keep consistent or reduce for speed in endgame
        
    # Get all legal moves
    legal_moves = get_legal_moves(you, opponent)
    
    if not legal_moves:
        return "pass"
    
    # Move ordering: sort moves by heuristic value to improve alpha-beta pruning
    # We use a simple positional score (corner capture potential) for sorting
    def move_key(move):
        r, c = move
        # Prefer corners heavily
        if (r == 0 or r == 7) and (c == 0 or c == 7):
            return 1000
        # Avoid squares adjacent to corners (dangerous early on)
        if (r == 0 or r == 7) and (c == 1 or c == 6) or (c == 0 or c == 7) and (r == 1 or r == 6):
            return -1000
        return BOARD_WEIGHTS[r][c]

    legal_moves.sort(key=move_key, reverse=True)
    
    best_move = legal_moves[0]
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    for move in legal_moves:
        # Apply move
        y_new, o_new = apply_move(you, opponent, move)
        
        # Minimax call
        score = minimax(y_new, o_new, max_depth - 1, alpha, beta, False)
        
        if score > best_score:
            best_score = score
            best_move = move
        
        alpha = max(alpha, best_score)
        
    return format_move(best_move)

def get_legal_moves(you: np.ndarray, opponent: np.ndarray):
    moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:
                if is_valid_move(you, opponent, r, c):
                    moves.append((r, c))
    return moves

def is_valid_move(you: np.ndarray, opponent: np.ndarray, r, c):
    if you[r][c] == 1 or opponent[r][c] == 1:
        return False
    
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc] == 1:
            # Walk the line
            k = 1
            while True:
                nnr, nnc = nr + k * dr, nc + k * dc
                if 0 <= nnr < 8 and 0 <= nnc < 8:
                    if you[nnr][nnc] == 1:
                        return True
                    if opponent[nnr][nnc] == 0:
                        break
                else:
                    break
                k += 1
    return False

def apply_move(you: np.ndarray, opponent: np.ndarray, move):
    r, c = move
    y_new = you.copy()
    o_new = opponent.copy()
    y_new[r][c] = 1
    
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        flips = []
        if 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc] == 1:
            flips.append((nr, nc))
            k = 1
            while True:
                nnr, nnc = nr + k * dr, nc + k * dc
                if 0 <= nnr < 8 and 0 <= nnc < 8:
                    if y_new[nnr][nnc] == 1:
                        for fr, fc in flips:
                            y_new[fr][fc] = 1
                            o_new[fr][fc] = 0
                        break
                    if o_new[nnr][nnc] == 1:
                        flips.append((nnr, nnc))
                    else:
                        break
                else:
                    break
                k += 1
    return y_new, o_new

def evaluate(you: np.ndarray, opponent: np.ndarray):
    # Positional Score
    pos_score = np.sum(you * BOARD_WEIGHTS) - np.sum(opponent * BOARD_WEIGHTS)
    
    # Mobility Score (Difference in legal moves)
    my_moves = len(get_legal_moves(you, opponent))
    
    # Swap roles to check opponent mobility
    # Note: apply_move creates new arrays, but for evaluation we just need counts.
    # We must calculate opponent's legal moves given the current board state.
    opp_moves = len(get_legal_moves(opponent, you)) 
    
    # Weight mobility heavily in mid-game, less in endgame
    mobility_score = (my_moves - opp_moves) * 2 
    
    return pos_score + mobility_score

def minimax(you: np.ndarray, opponent: np.ndarray, depth, alpha, beta, is_maximizing):
    if depth == 0:
        return evaluate(you, opponent)
    
    legal_moves = get_legal_moves(you, opponent) if is_maximizing else get_legal_moves(opponent, you)
    
    # If no legal moves, pass or game over
    if not legal_moves:
        # Check if opponent also has no moves (Game Over)
        if not get_legal_moves(opponent, you) if is_maximizing else not get_legal_moves(you, opponent):
            # End game scoring: pure disc count
            score = np.sum(you) - np.sum(opponent)
            # Add positional weight to break ties or endgame nuances
            score += np.sum(you * BOARD_WEIGHTS) - np.sum(opponent * BOARD_WEIGHTS)
            return score * 100 # Magnify endgame result
        else:
            # Pass turn
            return minimax(you, opponent, depth - 1, alpha, beta, not is_maximizing)

    # Move ordering heuristic for minimizer as well
    def move_key(move):
        r, c = move
        return BOARD_WEIGHTS[r][c]

    legal_moves.sort(key=move_key, reverse=True)

    if is_maximizing:
        max_eval = -float('inf')
        for move in legal_moves:
            y_new, o_new = apply_move(you, opponent, move)
            eval_score = minimax(y_new, o_new, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            # Opponent's move: swap roles in arguments
            o_new, y_new = apply_move(opponent, you, move)
            eval_score = minimax(y_new, o_new, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def format_move(move):
    r, c = move
    col_char = chr(ord('a') + c)
    row_str = str(r + 1)
    return col_char + row_str
