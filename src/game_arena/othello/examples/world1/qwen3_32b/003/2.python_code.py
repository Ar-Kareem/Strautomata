
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    weights = [
        [100, -1, 8, 6, 6, 8, -1, 100],
        [-1, -20, -4, -3, -3, -4, -20, -1],
        [8, -4, 7, 4, 4, 7, -4, 8],
        [6, -3, 4, 2, 2, 4, -3, 6],
        [6, -3, 4, 2, 2, 4, -3, 6],
        [8, -4, 7, 4, 4, 7, -4, 8],
        [-1, -20, -4, -3, -3, -4, -20, -1],
        [100, -1, 8, 6, 6, 8, -1, 100]
    ]
    
    legal_moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1), (1, 0), (1, 1)]
    
    # Check all cells for valid moves
    for r in range(8):
        for c in range(8):
            if you[r][c] == 1 or opponent[r][c] == 1:
                continue  # Skip non-empty cells
                
            valid = False
            for dr, dc in directions:
                current_r, current_c = r + dr, c + dc
                has_opponent = False
                
                while 0 <= current_r < 8 and 0 <= current_c < 8:
                    if opponent[current_r][current_c] == 1 and you[current_r][current_c] == 0:
                        has_opponent = True
                        current_r += dr
                        current_c += dc
                    elif you[current_r][current_c] == 1:
                        if has_opponent:
                            valid = True
                            break
                        else:
                            break
                    else:
                        break
                if valid:
                    break
            if valid:
                legal_moves.append((r, c))
    
    if not legal_moves:
        return "pass"
    
    best_move = None
    best_score = -float('inf')
    
    # Evaluate moves based on flipped discs and position value
    for r, c in legal_moves:
        total_flips = 0
        
        for dr, dc in directions:
            current_r, current_c = r + dr, c + dc
            count = 0
            has_opponent = False
            
            while 0 <= current_r < 8 and 0 <= current_c < 8:
                if opponent[current_r][current_c] == 1 and you[current_r][current_c] == 0:
                    count += 1
                    has_opponent = True
                    current_r += dr
                    current_c += dc
                elif you[current_r][current_c] == 1:
                    if has_opponent:
                        total_flips += count
                    break
                else:
                    break
        
        position_score = weights[r][c]
        score = total_flips + position_score
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    # Convert best move to algebraic notation
    r, c = best_move
    col = chr(ord('a') + c)
    row = r + 1
    return f"{col}{row}"
