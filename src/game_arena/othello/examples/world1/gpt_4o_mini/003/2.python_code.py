
import numpy as np

def is_valid_move(board, r, c, player):
    # Directions for checking flips
    directions = [(-1, 0), (-1, -1), (-1, 1), (0, -1), (0, 1), (1, 0), (1, -1), (1, 1)]
    opponent = 1 - player
    
    if board[r][c] != 0:  # Must be an empty cell
        return False
    
    for dr, dc in directions:
        cr, cc = r + dr, c + dc
        has_opponent = False
        
        # Check in this direction
        while 0 <= cr < 8 and 0 <= cc < 8:
            if board[cr][cc] == opponent:
                has_opponent = True  # There is at least one opponent's disc in the direction
            elif board[cr][cc] == player:
                if has_opponent:
                    return True  # Valid move found
                else:
                    break  # If no opponent's discs are found, break
            else:
                break  # Hit an empty space, break
        
            # Move in the direction
            cr += dr
            cc += dc
            
    return False

def get_flips(board, r, c, player):
    directions = [(-1, 0), (-1, -1), (-1, 1), (0, -1), (0, 1), (1, 0), (1, -1), (1, 1)]
    opponent = 1 - player
    flips = []
    
    for dr, dc in directions:
        cr, cc = r + dr, c + dc
        temp_flips = []
        
        while 0 <= cr < 8 and 0 <= cc < 8:
            if board[cr][cc] == opponent:
                temp_flips.append((cr, cc))  # Collect opponent discs to flip
            elif board[cr][cc] == player:
                flips.extend(temp_flips)  # Valid move, add all flips
                break
            else:
                break
            
            # Move in the direction
            cr += dr
            cc += dc
            
    return flips

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    board = you + opponent  # Combined board
    legal_moves = []
    
    # Find legal moves
    for r in range(8):
        for c in range(8):
            if is_valid_move(board, r, c, 1):  # Check for player (you)
                flips = get_flips(board, r, c, 1)
                legal_moves.append((r, c, len(flips)))  # Append row, column, number of flips
    
    if not legal_moves:
        return "pass"
    
    # Sort moves by number of flips (descending)
    legal_moves.sort(key=lambda x: x[2], reverse=True)
    
    # Select the best move (first in sorted list)
    best_move = legal_moves[0]
    r, c, _ = best_move
    
    # Convert to algebraic notation
    return f"{chr(c + ord('a'))}{r + 1}"

