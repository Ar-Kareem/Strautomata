
import numpy as np
from functools import lru_cache

# Positional weight matrix (higher is better)
WEIGHTS = np.array([
    [120, -20,  20,   5,   5,  20, -20, 120],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [120, -20,  20,   5,   5,  20, -20, 120]
])

# Direction vectors for checking lines
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),           (0, 1),
              (1, -1),  (1, 0), (1, 1)]

@lru_cache(maxsize=1)
def get_all_moves(you, opponent):
    """Return all legal moves for the current player"""
    you_arr = np.frombuffer(you, dtype=np.uint8).reshape(8, 8)
    opponent_arr = np.frombuffer(opponent, dtype=np.uint8).reshape(8, 8)
    
    legal_moves = set()
    empty_cells = np.argwhere((you_arr == 0) & (opponent_arr == 0))
    
    for r, c in empty_cells:
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and opponent_arr[nr, nc] == 1:
                nr += dr
                nc += dc
                while 0 <= nr < 8 and 0 <= nc < 8:
                    if you_arr[nr, nc] == 1:
                        legal_moves.add((r, c))
                        break
                    elif opponent_arr[nr, nc] == 0:
                        break
                    nr += dr
                    nc += dc
                    
    return legal_moves

def evaluate_position(you, opponent):
    """Evaluate the board position from your perspective"""
    # Early game: more weight to mobility and position
    # Late game: more weight to disc count
    
    total_pieces = np.sum(you) + np.sum(opponent)
    game_phase = min(total_pieces / 10, 1.0)  # 0-1 scale
    
    # Positional advantage
    positional = np.sum(you * WEIGHTS) - np.sum(opponent * WEIGHTS)
    
    # Mobility advantage
    you_moves = len(get_all_moves(you.tobytes(), opponent.tobytes()))
    opponent_moves = len(get_all_moves(opponent.tobytes(), you.tobytes()))
    mobility = (you_moves - opponent_moves) * 3
    
    # Disc count becomes more important later
    disc_diff = (np.sum(you) - np.sum(opponent)) * (1 + game_phase * 1.5)
    
    corner_control = 0
    corners = [(0,0), (0,7), (7,0), (7,7)]
    for r, c in corners:
        if you[r, c] == 1:
            corner_control += 25
        elif opponent[r, c] == 1:
            corner_control -= 25
            
    return (positional * 0.8 + mobility * 1.2 + disc_diff * 1.5 + corner_control) * (1 + game_phase)

def apply_move(you, opponent, move):
    """Apply a move to the board and return the new board state"""
    new_you = you.copy()
    new_opponent = opponent.copy()
    r, c = move
    
    if move is None:  # pass
        return new_you, new_opponent
    
    new_you[r, c] = 1
    
    for dr, dc in DIRECTIONS:
        to_flip = []
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr, nc] == 1:
            to_flip.append((nr, nc))
            nr += dr
            nc += dc
            if 0 <= nr < 8 and 0 <= nc < 8 and you[nr, nc] == 1:
                for flip_r, flip_c in to_flip:
                    new_you[flip_r, flip_c] = 1
                    new_opponent[flip_r, flip_c] = 0
                break
                
    return new_you, new_opponent

def minimax(you, opponent, depth, alpha, beta, maximizing_player, max_depth=2):
    """Minimax search with alpha-beta pruning"""
    if depth == max_depth:
        return evaluate_position(you, opponent), None
    
    legal_moves = get_all_moves(you.tobytes(), opponent.tobytes())
    
    if not legal_moves:
        # If no moves, check opponent's moves (could be endgame)
        opponent_has_moves = get_all_moves(opponent.tobytes(), you.tobytes())
        if not opponent_has_moves:  # Game over
            score = 1000 * (np.sum(you) - np.sum(opponent))
            return score, None
        else:  # Pass and let opponent move
            _, opponent_new_you = apply_move(opponent, you, None)
            score = -minimax(opponent_new_you, you, depth+1, -beta, -alpha, not maximizing_player, max_depth)[0]
            return score, None
    
    best_move = None
    if maximizing_player:
        max_eval = -float('inf')
        for move in legal_moves:
            new_you, new_opponent = apply_move(you, opponent, move)
            eval = minimax(new_you, new_opponent, depth+1, alpha, beta, False, max_depth)[0]
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in legal_moves:
            new_you, new_opponent = apply_move(you, opponent, move)
            eval = minimax(new_you, new_opponent, depth+1, alpha, beta, True, max_depth)[0]
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Convert to bytes for caching
    you_bytes = you.tobytes()
    opponent_bytes = opponent.tobytes()
    
    legal_moves = get_all_moves(you_bytes, opponent_bytes)
    
    if not legal_moves:
        return "pass"
    
    # Always take corners if available
    corners = {(0,0), (0,7), (7,0), (7,7)}
    available_corners = corners & legal_moves
    if available_corners:
        best_corner = max(available_corners, key=lambda m: WEIGHTS[m[0], m[1]])
        return f"{chr(best_corner[1] + ord('a'))}{best_corner[0] + 1}"
    
    # Use minimax for other moves
    _, best_move = minimax(you, opponent, 0, -float('inf'), float('inf'), True)
    
    if best_move is None:  # Shouldn't happen since we checked legal_moves
        best_move = next(iter(legal_moves))
        
    return f"{chr(best_move[1] + ord('a'))}{best_move[0] + 1}"
