
import numpy as np

def policy(you, opponent) -> str:
    # Convert to numpy arrays for easier manipulation
    you_arr = np.array(you)
    opponent_arr = np.array(opponent)
    
    # Create full board representation (1 for you, -1 for opponent, 0 for empty)
    board = you_arr - opponent_arr
    
    # Find all empty positions
    empty_positions = []
    for r in range(6):
        for c in range(6):
            if you_arr[r][c] == 0 and opponent_arr[r][c] == 0:
                empty_positions.append((r, c))
    
    # Check for immediate win moves (place to get 5 in a row)
    for r, c in empty_positions:
        # Try placing here and check if it creates a win
        board[r, c] = 1
        if has_five_in_a_row(board, 1):
            # Find a quadrant that contains this position to rotate
            quad = get_quadrant(r, c)
            # Try both rotation directions (both should be legal since we just need any move)
            for dir in ['L', 'R']:
                # Return the first winning move found
                return f"{r+1},{c+1},{quad},{dir}"
        # Revert the board
        board[r, c] = 0
    
    # Check for opponent win blocks
    for r, c in empty_positions:
        # Pretend opponent places here
        board[r, c] = -1
        if has_five_in_a_row(board, -1):
            # Block it by placing here
            board[r, c] = 1
            quad = get_quadrant(r, c)
            for dir in ['L', 'R']:
                return f"{r+1},{c+1},{quad},{dir}"
        # Revert the board
        board[r, c] = 0
    
    # If no immediate win or block, use a heuristic: prioritize center positions
    # and try to create threats
    
    # Score positions based on proximity to center and potential for lines
    best_move = None
    best_score = -float('inf')
    
    for r, c in empty_positions:
        # Score position based on center proximity (center 2x2 area is most valuable)
        center_score = 0
        if r in [2, 3] and c in [2, 3]:
            center_score = 5
        elif r in [1, 4] and c in [1, 4]:
            center_score = 3
        else:
            center_score = 1
        
        # Check how many potential lines this position contributes to
        line_potential = count_potential_lines(board, r, c, 1)
        
        # Consider rotations - try to find a rotation that creates a threat
        quad = get_quadrant(r, c)
        for dir in ['L', 'R']:
            # Simulate rotation on this quadrant and see if it creates a winning threat
            # We'll just use a heuristic score combining position score + rotation effect
            score = center_score + line_potential
            
            # Increase score if rotation could connect with existing pieces in the quadrant
            quad_score = evaluate_quadrant_rotation(board, quad, dir, 1)
            score += quad_score
            
            if score > best_score:
                best_score = score
                best_move = (r, c, quad, dir)
    
    # If we found a good move, return it
    if best_move is not None:
        r, c, quad, dir = best_move
        return f"{r+1},{c+1},{quad},{dir}"
    
    # Fallback: return any legal move
    r, c = empty_positions[0]
    quad = get_quadrant(r, c)
    dir = 'L'  # Default to left rotation
    return f"{r+1},{c+1},{quad},{dir}"

def get_quadrant(row, col):
    """Convert 0-based (row, col) to quadrant 0-3"""
    if row < 3:  # top half
        if col < 3:  # left side
            return 0
        else:  # right side
            return 1
    else:  # bottom half
        if col < 3:  # left side
            return 2
        else:  # right side
            return 3

def has_five_in_a_row(board, player):
    """Check if player has 5 or more in a row in any direction"""
    # Check horizontal
    for r in range(6):
        for c in range(2):  # can start at c=0 to c=2 for 5-in-a-row
            if all(board[r, c+i] == player for i in range(5)):
                return True
    
    # Check vertical
    for c in range(6):
        for r in range(2):  # can start at r=0 to r=2 for 5-in-a-row
            if all(board[r+i, c] == player for i in range(5)):
                return True
    
    # Check diagonal (top-left to bottom-right)
    for r in range(2):
        for c in range(2):
            if all(board[r+i, c+i] == player for i in range(5)):
                return True
    
    # Check diagonal (top-right to bottom-left)
    for r in range(2):
        for c in range(2, 6):  # c from 2 to 5 for 5-in-a-row starting from top-right
            if all(board[r+i, c-i] == player for i in range(5)):
                return True
    
    return False

def count_potential_lines(board, row, col, player):
    """Count potential lines that include this position"""
    count = 0
    
    # Check horizontal
    for start_col in range(max(0, col-4), min(col+1, 2)):
        if all(board[row, start_col + i] in [player, 0] for i in range(5)):
            if sum(1 for i in range(5) if board[row, start_col + i] == player) >= 1:
                count += 1
    
    # Check vertical
    for start_row in range(max(0, row-4), min(row+1, 2)):
        if all(board[start_row + i, col] in [player, 0] for i in range(5)):
            if sum(1 for i in range(5) if board[start_row + i, col] == player) >= 1:
                count += 1
    
    # Check diagonal (top-left to bottom-right)
    for start_r in range(max(0, row-4), min(row+1, 2)):
        start_c = col - (row - start_r)
        if 0 <= start_c <= 2 and all(board[start_r + i, start_c + i] in [player, 0] for i in range(5)):
            if sum(1 for i in range(5) if board[start_r + i, start_c + i] == player) >= 1:
                count += 1
    
    # Check diagonal (top-right to bottom-left)
    for start_r in range(max(0, row-4), min(row+1, 2)):
        start_c = col + (row - start_r)
        if 3 <= start_c <= 5 and all(board[start_r + i, start_c - i] in [player, 0] for i in range(5)):
            if sum(1 for i in range(5) if board[start_r + i, start_c - i] == player) >= 1:
                count += 1
    
    return count

def evaluate_quadrant_rotation(board, quad, direction, player):
    """Heuristic score for how good a rotation is"""
    # Get the 3x3 quadrant
    if quad == 0:  # top-left
        quad_board = board[0:3, 0:3]
    elif quad == 1:  # top-right
        quad_board = board[0:3, 3:6]
    elif quad == 2:  # bottom-left
        quad_board = board[3:6, 0:3]
    else:  # quad == 3, bottom-right
        quad_board = board[3:6, 3:6]
    
    # Simulate rotation
    if direction == 'R':  # clockwise
        rotated = np.rot90(quad_board, k=3)  # 90 degrees clockwise
    else:  # 'L', counterclockwise
        rotated = np.rot90(quad_board, k=1)  # 90 degrees counterclockwise
    
    # Score based on potential lines after rotation
    score = 0
    
    # Check if rotation creates 4-in-a-row possibilities or connects pieces
    for r in range(3):
        # Check horizontal potential in rotated quadrant
        if sum(rotated[r, :] == player) >= 3:
            # Convert back to board coordinates for line checking
            real_r = r + (0 if quad < 2 else 3)
            real_c_start = 0 if quad % 2 == 0 else 3
            for c_start in range(2):
                if sum(rotated[r, c_start:c_start+5] == player if c_start+5 <= 3 else 
                      [rotated[r, c] if c < 3 and c_start <= c < c_start+5 else 0 for c in range(3)]) >= 4:
                    score += 1
    
    # Add a small bonus for center rotations (more influence)
    if quad in [0, 3]:  # top-left and bottom-right - more central influence
        score += 0.5
    
    return score
