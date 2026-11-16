
import numpy as np
from collections import defaultdict

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Determine movement direction based on color
    direction = 1 if color == 'w' else -1
    
    # Create board representation
    board = np.zeros((8, 8), dtype=int)
    for r, c in me:
        board[r][c] = 1  # my pieces
    for r, c in opp:
        board[r][c] = -1  # opponent pieces
    
    # Generate all possible legal moves
    legal_moves = []
    for (r, c) in me:
        # Forward move
        new_r = r + direction
        if 0 <= new_r < 8 and board[new_r][c] == 0:
            legal_moves.append(((r, c), (new_r, c)))
        
        # Diagonal captures/advances
        for new_c in [c-1, c+1]:
            if 0 <= new_r < 8 and 0 <= new_c < 8:
                if board[new_r][new_c] == 0:  # Diagonal advance
                    legal_moves.append(((r, c), (new_r, new_c)))
                elif board[new_r][new_c] == -1:  # Capture
                    legal_moves.append(((r, c), (new_r, new_c)))
    
    # If no legal moves (shouldn't happen as per game rules), return a dummy move
    if not legal_moves:
        return ((0, 0), (0, 0))
    
    # Score each move based on multiple factors
    move_scores = []
    for (from_pos, to_pos) in legal_moves:
        score = 0
        
        # Base score for advancement
        if color == 'w':
            score += to_pos[0]  # higher row is better for white
        else:
            score += (7 - to_pos[0])  # lower row is better for black
        
        # Bonus for reaching promotion row
        if (color == 'w' and to_pos[0] == 7) or (color == 'b' and to_pos[0] == 0):
            score += 100
        
        # Bonus for captures
        if board[to_pos[0]][to_pos[1]] == -1:
            score += 3
        
        # Bonus for center control
        center_dist = abs(to_pos[1] - 3.5)
        score += (3.5 - center_dist) * 0.5
        
        # Penalty for leaving pieces undefended
        defended = False
        for dr, dc in [(direction, -1), (direction, 1)]:
            def_r, def_c = to_pos[0] + dr, to_pos[1] + dc
            if 0 <= def_r < 8 and 0 <= def_c < 8 and board[def_r][def_c] == 1:
                defended = True
                break
        if not defended:
            score -= 1
        
        # Bonus for creating multiple threats
        threat_count = 0
        for dr, dc in [(direction, -1), (direction, 1)]:
            threat_r, threat_c = to_pos[0] + direction, to_pos[1] + dc
            if 0 <= threat_r < 8 and 0 <= threat_c < 8:
                if board[threat_r][threat_c] == -1:
                    threat_count += 1
        score += threat_count * 0.5
        
        move_scores.append(score)
    
    # Select the move with highest score
    best_move_index = np.argmax(move_scores)
    return legal_moves[best_move_index]
