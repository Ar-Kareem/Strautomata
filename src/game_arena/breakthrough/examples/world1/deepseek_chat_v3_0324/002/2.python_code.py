
import numpy as np

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Determine movement direction based on color
    direction = 1 if color == 'w' else -1
    
    # Convert to numpy arrays for easier manipulation
    my_pieces = np.array(me)
    opp_pieces = np.array(opp)
    
    # Create board representation (0=empty, 1=my piece, 2=opponent piece)
    board = np.zeros((8, 8), dtype=int)
    for piece in my_pieces:
        board[piece[0], piece[1]] = 1
    for piece in opp_pieces:
        board[piece[0], piece[1]] = 2
    
    best_move = None
    best_score = -float('inf')
    
    # Check all possible moves
    for piece in my_pieces:
        row, col = piece
        
        # Possible moves: forward left, forward right, straight forward (if white)
        # For black, direction is -1 so it's still "forward"
        moves = [
            (row + direction, col - 1),  # diagonal left
            (row + direction, col + 1),  # diagonal right
            (row + direction, col)       # straight
        ]
        
        for move in moves:
            to_row, to_col = move
            
            # Check if move is on the board
            if 0 <= to_row < 8 and 0 <= to_col < 8:
                # Check if it's a capture (diagonal move to opponent piece)
                if board[to_row, to_col] == 2 and abs(to_col - col) == 1:
                    # Calculate score for this capture
                    score = 10  # base score for capture
                    
                    # Bonus for capturing advanced pieces
                    if color == 'w':
                        score += (7 - to_row) * 2  # opponent was close to our home
                    else:
                        score += to_row * 2  # opponent was close to our home
                        
                    # Bonus for moving toward opponent's home
                    if color == 'w':
                        score += to_row * 3
                    else:
                        score += (7 - to_row) * 3
                        
                    # Check if this move reaches the home row
                    if (color == 'w' and to_row == 7) or (color == 'b' and to_row == 0):
                        score += 1000  # instant win
                        
                    if score > best_score:
                        best_score = score
                        best_move = ((row, col), (to_row, to_col))
                
                # Check if it's a regular move to empty square
                elif board[to_row, to_col] == 0:
                    # Calculate score for this move
                    score = 0
                    
                    # Base score for advancement
                    if color == 'w':
                        score += to_row * 2
                    else:
                        score += (7 - to_row) * 2
                    
                    # Bonus for moving toward center (better mobility)
                    score += (3 - abs(to_col - 3.5)) * 0.5
                    
                    # Bonus for protecting other pieces
                    protect_bonus = 0
                    for neighbor in [(to_row - direction, to_col - 1), 
                                    (to_row - direction, to_col + 1)]:
                        if 0 <= neighbor[0] < 8 and 0 <= neighbor[1] < 8:
                            if board[neighbor[0], neighbor[1]] == 1:
                                protect_bonus += 2
                    score += protect_bonus
                    
                    # Bonus for threatening opponent pieces
                    threat_bonus = 0
                    for threat in [(to_row + direction, to_col - 1),
                                  (to_row + direction, to_col + 1)]:
                        if 0 <= threat[0] < 8 and 0 <= threat[1] < 8:
                            if board[threat[0], threat[1]] == 2:
                                threat_bonus += 3
                    score += threat_bonus
                    
                    # Check if this move reaches the home row
                    if (color == 'w' and to_row == 7) or (color == 'b' and to_row == 0):
                        score += 1000  # instant win
                        
                    if score > best_score:
                        best_score = score
                        best_move = ((row, col), (to_row, to_col))
    
    # If no moves found (shouldn't happen in legal game state), return first possible move as fallback
    if best_move is None:
        for piece in my_pieces:
            row, col = piece
            for move in [(row + direction, col - 1), (row + direction, col + 1), (row + direction, col)]:
                to_row, to_col = move
                if 0 <= to_row < 8 and 0 <= to_col < 8:
                    if board[to_row, to_col] == 0 or (board[to_row, to_col] == 2 and abs(to_col - col) == 1):
                        return ((row, col), (to_row, to_col))
    
    return best_move
