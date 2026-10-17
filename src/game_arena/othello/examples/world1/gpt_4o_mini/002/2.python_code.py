
import numpy as np

def is_valid_move(you: np.ndarray, opponent: np.ndarray, row: int, col: int) -> bool:
    if you[row][col] != 0:
        return False  # Move must be to an empty cell

    directions = [(-1, -1), (-1, 0), (-1, 1), 
                  (0, -1),          (0, 1), 
                  (1, -1), (1, 0), (1, 1)]

    valid = False
    for dr, dc in directions:
        r, c = row + dr, col + dc
        found_opponent = False
        
        while 0 <= r < 8 and 0 <= c < 8:
            if opponent[r][c] == 1:
                found_opponent = True
            elif you[r][c] == 1:
                if found_opponent:
                    valid = True
                break
            else:
                break
            r += dr
            c += dc
            
    return valid

def get_flips(you: np.ndarray, opponent: np.ndarray, row: int, col: int) -> int:
    flips = 0
    directions = [(-1, -1), (-1, 0), (-1, 1), 
                  (0, -1),          (0, 1), 
                  (1, -1), (1, 0), (1, 1)]

    for dr, dc in directions:
        r, c = row + dr, col + dc
        found_opponent = False
        
        while 0 <= r < 8 and 0 <= c < 8:
            if opponent[r][c] == 1:
                found_opponent = True
            elif you[r][c] == 1:
                if found_opponent:
                    # Count the opponent discs that will be flipped
                    flips += 1
                break
            else:
                break
            r += dr
            c += dc
            
    return flips

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    best_move = None
    best_flips = 0

    for row in range(8):
        for col in range(8):
            if is_valid_move(you, opponent, row, col):
                flips = get_flips(you, opponent, row, col)
                if flips > best_flips:
                    best_flips = flips
                    best_move = (row, col)

    if best_move:
        file = chr(ord('a') + best_move[1])  # Column to letter
        rank = str(best_move[0] + 1)          # Row to number (1-indexed)
        return file + rank
    
    return "pass"
