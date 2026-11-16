
import numpy as np

def policy(you, opponent):
    """
    A pentago policy using minimax with heuristic evaluation.
    
    Args:
        you: 6x6 array of your marbles (1 where you have a marble, 0 elsewhere)
        opponent: 6x6 array of opponent's marbles
        
    Returns:
        str: move in format "row,col,quad,dir"
    """
    
    # Convert to numpy arrays for easier manipulation
    you_board = np.array(you)
    opp_board = np.array(opponent)
    
    # Find all empty positions
    empty = (you_board == 0) & (opp_board == 0)
    
    # Evaluate all possible moves and pick the best one
    best_move = None
    best_score = float('-inf')
    
    # Generate all possible moves
    for r in range(6):
        for c in range(6):
            if empty[r, c]:
                # Try placing at this position
                new_you = you_board.copy()
                new_you[r, c] = 1
                
                # Try rotating each quadrant in each direction
                for quad in range(4):
                    for direction in ['L', 'R']:
                        # Apply rotation
                        rotated_you, rotated_opp = rotate_quadrant(new_you.copy(), opp_board.copy(), quad, direction)
                        
                        # Check for immediate win
                        if check_win(rotated_you):
                            # If we can win immediately, take it
                            return f"{r+1},{c+1},{quad},{direction}"
                        
                        # Evaluate position from opponent's perspective after our move
                        score = -evaluate_position(rotated_opp, rotated_you)
                        
                        if score > best_score:
                            best_score = score
                            best_move = f"{r+1},{c+1},{quad},{direction}"
    
    return best_move

def rotate_quadrant(you_board, opp_board, quad, direction):
    """Rotate a quadrant of both player boards."""
    # Define quadrant boundaries
    if quad == 0:
        rows, cols = slice(0, 3), slice(0, 3)
    elif quad == 1:
        rows, cols = slice(0, 3), slice(3, 6)
    elif quad == 2:
        rows, cols = slice(3, 6), slice(0, 3)
    else:  # quad == 3
        rows, cols = slice(3, 6), slice(3, 6)
    
    # Extract quadrants
    you_quad = you_board[rows, cols].copy()
    opp_quad = opp_board[rows, cols].copy()
    
    # Rotate 90 degrees
    if direction == 'R':
        you_rotated = np.rot90(you_quad, k=-1)
        opp_rotated = np.rot90(opp_quad, k=-1)
    else:  # 'L'
        you_rotated = np.rot90(you_quad, k=1)
        opp_rotated = np.rot90(opp_quad, k=1)
    
    # Place back
    you_board[rows, cols] = you_rotated
    opp_board[rows, cols] = opp_rotated
    
    return you_board, opp_board

def check_win(board):
    """Check if the board has a 5-in-a-row."""
    # Check horizontal
    for r in range(6):
        for c in range(2):
            if all(board[r, c+i] == 1 for i in range(5)):
                return True
    
    # Check vertical
    for c in range(6):
        for r in range(2):
            if all(board[r+i, c] == 1 for i in range(5)):
                return True
    
    # Check diagonals
    for r in range(2):
        for c in range(2):
            # Main diagonal
            if all(board[r+i, c+i] == 1 for i in range(5)):
                return True
            # Anti-diagonal
            if all(board[r+i, c+4-i] == 1 for i in range(5)):
                return True
    
    return False

def evaluate_position(board, opp_board):
    """Heuristic evaluation of a board position."""
    score = 0
    
    # Evaluate lines (horizontal, vertical, diagonals) for potential 5-in-a-row
    lines = []
    
    # Horizontal lines
    for r in range(6):
        for c in range(2):
            line = [board[r, c+i] for i in range(5)]
            opp_line = [opp_board[r, c+i] for i in range(5)]
            lines.append((line, opp_line))
    
    # Vertical lines
    for c in range(6):
        for r in range(2):
            line = [board[r+i, c] for i in range(5)]
            opp_line = [opp_board[r+i, c] for i in range(5)]
            lines.append((line, opp_line))
    
    # Diagonals
    for r in range(2):
        for c in range(2):
            # Main diagonal
            line = [board[r+i, c+i] for i in range(5)]
            opp_line = [opp_board[r+i, c+i] for i in range(5)]
            lines.append((line, opp_line))
            # Anti-diagonal
            line = [board[r+i, c+4-i] for i in range(5)]
            opp_line = [opp_board[r+i, c+4-i] for i in range(5)]
            lines.append((line, opp_line))
    
    for line, opp_line in lines:
        my_count = sum(line)
        opp_count = sum(opp_line)
        empty_count = 5 - my_count - opp_count
        
        # If opponent has 4 and we have none, that's bad
        if opp_count == 4 and my_count == 0:
            score -= 100
        # If we have 4 and opponent has none, that's good
        elif my_count == 4 and opp_count == 0:
            score += 100
        # If opponent has 3 and we have none, that's somewhat bad
        elif opp_count == 3 and my_count == 0 and empty_count == 2:
            score -= 10
        # If we have 3 and opponent has none, that's somewhat good
        elif my_count == 3 and opp_count == 0 and empty_count == 2:
            score += 10
    
    # Control center positions
    center_positions = [(2,2), (2,3), (3,2), (3,3)]
    for r, c in center_positions:
        if board[r, c] == 1:
            score += 2
        elif opp_board[r, c] == 1:
            score -= 2
            
    # Mobility - number of possible moves
    empty_count = np.sum((board == 0) & (opp_board == 0))
    score += empty_count * 0.1  # Small bonus for having more moves
    
    return score
