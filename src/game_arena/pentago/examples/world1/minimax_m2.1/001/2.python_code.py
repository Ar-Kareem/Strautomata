
import numpy as np

def policy(you, opponent) -> str:
    """
    Pentago AI Policy
    Implements a smart multi-layered strategy prioritizing wins, blocks, and strategic positioning.
    """
    # Convert to numpy arrays for efficient computation
    board = np.array(you) + np.array(opponent)
    you_board = np.array(you)
    opp_board = np.array(opponent)
    
    # Find all empty positions
    empty_positions = []
    for r in range(6):
        for c in range(6):
            if board[r][c] == 0:
                empty_positions.append((r, c))
    
    if not empty_positions:
        return "1,1,0,R"  # Fallback (shouldn't happen)
    
    # Priority 1: Check for immediate winning moves
    for r, c in empty_positions:
        temp_you = you_board.copy()
        temp_you[r][c] = 1
        
        for quad in range(4):
            for dir in ['L', 'R']:
                temp_board = apply_rotation(temp_you + opp_board, quad, dir)
                if check_win(temp_board, 1):
                    return f"{r+1},{c+1},{quad},{dir}"
    
    # Priority 2: Block opponent's immediate winning moves
    for r, c in empty_positions:
        temp_opp = opp_board.copy()
        temp_opp[r][c] = 1
        
        for quad in range(4):
            for dir in ['L', 'R']:
                temp_board = apply_rotation(you_board + temp_opp, quad, dir)
                if check_win(temp_board, 2):
                    return f"{r+1},{c+1},{quad},{dir}"
    
    # Priority 3: Evaluate and select best strategic move
    best_move = None
    best_score = float('-inf')
    
    for r, c in empty_positions:
        for quad in range(4):
            for dir in ['L', 'R']:
                score = evaluate_position(r, c, quad, dir, you_board, opp_board, board)
                if score > best_score:
                    best_score = score
                    best_move = (r, c, quad, dir)
    
    if best_move:
        r, c, quad, dir = best_move
        return f"{r+1},{c+1},{quad},{dir}"
    
    # Fallback: Play center with safe rotation
    return "3,3,0,R"


def check_win(board, player):
    """Check if player has 5+ in a row (horizontal, vertical, or diagonal)"""
    # Check all rows
    for r in range(6):
        for c in range(2):
            if all(board[r, c:c+5] == player):
                return True
    
    # Check all columns
    for c in range(6):
        for r in range(2):
            if all(board[r:r+5, c] == player):
                return True
    
    # Check diagonals (top-left to bottom-right)
    for r in range(2):
        for c in range(2):
            if all(board[r+i, c+i] == player for i in range(5)):
                return True
    
    # Check diagonals (top-right to bottom-left)
    for r in range(2):
        for c in range(4):
            if all(board[r+i, c-i] == player for i in range(5)):
                return True
    
    return False


def count_potential_wins(board, player):
    """Count sequences of 4 that can become 5 (for threat evaluation)"""
    count = 0
    
    # Check rows for sequences of 4
    for r in range(6):
        for c in range(3):
            segment = board[r, c:c+4]
            if np.sum(segment == player) == 4 and np.sum(segment == 0) == 0:
                count += 1
    
    # Check columns for sequences of 4
    for c in range(6):
        for r in range(3):
            segment = board[r:r+4, c]
            if np.sum(segment == player) == 4 and np.sum(segment == 0) == 0:
                count += 1
    
    # Check diagonals for sequences of 4
    for r in range(3):
        for c in range(3):
            if all(board[r+i, c+i] == player for i in range(4)):
                count += 1
    
    for r in range(3):
        for c in range(3, 6):
            if all(board[r+i, c-i] == player for i in range(4)):
                count += 1
    
    return count


def evaluate_position(r, c, quad, dir, you_board, opp_board, board):
    """
    Evaluate the strategic value of a move
    Returns a score representing how good the move is
    """
    score = 0
    
    # 1. Placement score
    # Prefer center positions (more lines pass through)
    center_dist = abs(r - 2.5) + abs(c - 2.5)
    score += (5 - center_dist) * 2  # Center preference
    
    # 2. Strategic position bonuses
    # Center 2x2 is very valuable
    if 1 <= r <= 2 and 1 <= c <= 2:
        score += 5
    if 1 <= r <= 2 and 3 <= c <= 4:
        score += 5
    if 3 <= r <= 4 and 1 <= c <= 2:
        score += 5
    if 3 <= r <= 4 and 3 <= c <= 4:
        score += 5
    
    # 3. Simulate the move and evaluate resulting board state
    temp_you = you_board.copy()
    temp_you[r, c] = 1
    temp_board = apply_rotation(temp_you + opp_board, quad, dir)
    
    # Count potential winning lines created
    potential_wins = count_potential_wins(temp_board, 1)
    score += potential_wins * 10
    
    # 4. Check if move creates immediate threat (4 in a row)
    if count_potential_wins(temp_board, 1) > 0:
        score += 20
    
    # 5. Block opponent threats (reduce their potential wins)
    opp_potential_wins = count_potential_wins(temp_board, 2)
    score -= opp_potential_wins * 8
    
    # 6. Bonus for creating multiple threats
    if potential_wins >= 2:
        score += 15
    
    # 7. Prefer not to break our own lines
    # Check if rotation destroys our existing lines
    original_potential = count_potential_wins(board, 1)
    if potential_wins < original_potential:
        score -= 10
    
    # 8. Board coverage - prefer spreading out
    your_marbles = np.sum(you_board)
    if your_marbles > 0:
        # Calculate spread of your marbles
        rows_with_marbles = np.sum(np.any(you_board == 1, axis=1))
        cols_with_marbles = np.sum(np.any(you_board == 1, axis=0))
        spread = rows_with_marbles + cols_with_marbles
        score += spread * 2
    
    return score


def apply_rotation(board, quad, dir):
    """Rotate quadrant 90 degrees: L=anticlockwise, R=clockwise"""
    # Define quadrant boundaries (0-indexed)
    quad_bounds = {
        0: (0, 3, 0, 3),   # top-left
        1: (0, 3, 3, 6),   # top-right
        2: (3, 6, 0, 3),   # bottom-left
        3: (3, 6, 3, 6)    # bottom-right
    }
    
    r_start, r_end, c_start, c_end = quad_bounds[quad]
    
    # Extract the 3x3 quadrant
    quadrant = board[r_start:r_end, c_start:c_end].copy()
    
    # Rotate the quadrant
    if dir == 'L':  # 90 degrees anticlockwise
        rotated = np.rot90(quadrant, 1)
    else:  # 'R' 90 degrees clockwise
        rotated = np.rot90(quadrant, 3)
    
    # Create new board with rotated quadrant
    new_board = board.copy()
    new_board[r_start:r_end, c_start:c_end] = rotated
    
    return new_board
