
import numpy as np

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    # Generate all valid moves
    valid_moves = [(r, c) for r in range(15) for c in range(15) if valid_mask[r][c]]
    
    # Check for immediate winning moves
    for move in valid_moves:
        if is_winning_move(me + [move], opp, move):
            return move
    
    # Check for opponent's winning threats
    for move in valid_moves:
        if is_winning_move(opp + [move], me, move):
            return move
    
    # Evaluate board control (center dominance)
    center_scores = np.zeros((15, 15))
    center_scores[7][7] = 3
    center_scores[7][8] = 2
    center_scores[8][7] = 2
    center_scores[8][8] = 1
    
    # Calculate move scores based on board control
    move_scores = np.zeros((15, 15))
    for r, c in valid_moves:
        move_scores[r][c] = center_scores[r][c]
    
    # Return move with highest board control score
    best_move = np.unravel_index(move_scores.argmax(), move_scores.shape)
    return best_move
