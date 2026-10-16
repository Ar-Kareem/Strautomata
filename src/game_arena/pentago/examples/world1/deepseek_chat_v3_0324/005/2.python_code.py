
import numpy as np

def policy(you, opponent):
    # Convert inputs to numpy arrays for easier manipulation
    you_board = np.array(you)
    opp_board = np.array(opponent)
    empty_mask = (you_board == 0) & (opp_board == 0)
    
    # First, check for immediate winning moves
    for r in range(6):
        for c in range(6):
            if empty_mask[r, c]:
                for quad in range(4):
                    for dir in ['L', 'R']:
                        # Test placing marble here and rotating
                        test_you = you_board.copy()
                        test_you[r, c] = 1
                        rotated_you, rotated_opp = rotate_quadrants(test_you, opp_board, quad, dir)
                        if has_five_in_row(rotated_you):
                            return f"{r+1},{c+1},{quad},{dir}"
    
    # Then, block opponent's immediate winning moves
    for r in range(6):
        for c in range(6):
            if empty_mask[r, c]:
                test_opp = opp_board.copy()
                test_opp[r, c] = 1
                for quad in range(4):
                    for dir in ['L', 'R']:
                        rotated_you, rotated_opp = rotate_quadrants(you_board, test_opp, quad, dir)
                        if has_five_in_row(rotated_opp):
                            # Find a rotation that doesn't give them the win
                            # Try to find a rotation that blocks and also helps us
                            for block_quad in range(4):
                                for block_dir in ['L', 'R']:
                                    block_you = you_board.copy()
                                    block_you[r, c] = 1
                                    final_you, final_opp = rotate_quadrants(block_you, opp_board, block_quad, block_dir)
                                    if not has_five_in_row(final_opp):
                                        return f"{r+1},{c+1},{block_quad},{block_dir}"
                            # If all rotations still give them win, at least delay
                            return f"{r+1},{c+1},{0},R"
    
    # If no immediate threats or wins, use scoring system
    best_score = -float('inf')
    best_move = "1,1,0,R"  # default move
    
    # Try all possible placements
    for r in range(6):
        for c in range(6):
            if empty_mask[r, c]:
                # Try all possible rotations
                for quad in range(4):
                    for dir in ['L', 'R']:
                        score = evaluate_move(you_board, opp_board, r, c, quad, dir)
                        if score > best_score:
                            best_score = score
                            best_move = f"{r+1},{c+1},{quad},{dir}"
    
    return best_move

def rotate_quadrants(you_board, opp_board, quad, direction):
    """Rotate a quadrant and return new boards"""
    you = you_board.copy()
    opp = opp_board.copy()
    
    # Determine quadrant boundaries
    if quad == 0:
        rows, cols = slice(0, 3), slice(0, 3)
    elif quad == 1:
        rows, cols = slice(0, 3), slice(3, 6)
    elif quad == 2:
        rows, cols = slice(3, 6), slice(0, 3)
    else:  # quad == 3
        rows, cols = slice(3, 6), slice(3, 6)
    
    # Rotate the quadrant
    you_quad = you[rows, cols]
    opp_quad = opp[rows, cols]
    
    if direction == 'L':
        # Rotate left (counter-clockwise)
        you[rows, cols] = np.rot90(you_quad, 1)
        opp[rows, cols] = np.rot90(opp_quad, 1)
    else:
        # Rotate right (clockwise)
        you[rows, cols] = np.rot90(you_quad, -1)
        opp[rows, cols] = np.rot90(opp_quad, -1)
    
    return you, opp

def has_five_in_row(board):
    """Check for any 5-in-a-row on the board"""
    # Check horizontal
    for r in range(6):
        for c in range(2):
            if np.all(board[r, c:c+5] == 1):
                return True
    
    # Check vertical
    for c in range(6):
        for r in range(2):
            if np.all(board[r:r+5, c] == 1):
                return True
    
    # Check diagonals
    for r in range(2):
        for c in range(2):
            if np.all([board[r+i, c+i] for i in range(5)] == 1):
                return True
            if np.all([board[r+i, c+4-i] for i in range(5)] == 1):
                return True
    
    return False

def evaluate_move(you_board, opp_board, r, c, quad, dir):
    """Score a potential move based on several factors"""
    score = 0
    
    # Create temporary boards with this move
    test_you = you_board.copy()
    test_you[r, c] = 1
    rotated_you, rotated_opp = rotate_quadrants(test_you, opp_board, quad, dir)
    
    # 1. Count potential 5-in-a-rows we're creating
    score += count_potential_lines(rotated_you, rotated_opp) * 20
    
    # 2. Count potential 5-in-a-rows we're blocking from opponent
    score += count_potential_lines(rotated_opp, rotated_you) * 15
    
    # 3. Central positions are more valuable
    center_bonus = 3 * (abs(2.5 - r) + abs(2.5 - c))  # Higher for more central positions
    score += 10 / center_bonus if center_bonus > 0 else 10
    
    # 4. Control of quadrants (number of our marbles in quadrants after rotation)
    q = quad
    rows, cols = (slice(0,3), slice(0,3)) if q == 0 else \
                 (slice(0,3), slice(3,6)) if q == 1 else \
                 (slice(3,6), slice(0,3)) if q == 2 else \
                 (slice(3,6), slice(3,6))
    our_in_quad = np.sum(rotated_you[rows, cols])
    their_in_quad = np.sum(rotated_opp[rows, cols])
    score += (our_in_quad - their_in_quad) * 3
    
    # 5. Potential fours that could become fives
    score += count_potential_fours(rotated_you, rotated_opp) * 5
    
    # 6. Don't complete opponent's potential fours
    score -= count_potential_fours(rotated_opp, rotated_you) * 7
    
    return score

def count_potential_lines(board, other_board):
    """Count how many open 5-in-a-row possibilities exist"""
    count = 0
    
    # Check horizontal potential
    for r in range(6):
        for c in range(2):
            window = board[r, c:c+5]
            other_window = other_board[r, c:c+5]
            if np.sum(other_window) == 0:
                count += (5 - np.sum(window))
    
    # Check vertical potential
    for c in range(6):
        for r in range(2):
            window = board[r:r+5, c]
            other_window = other_board[r:r+5, c]
            if np.sum(other_window) == 0:
                count += (5 - np.sum(window))
    
    # Check diagonal potential
    for r in range(2):
        for c in range(2):
            # Down-right diagonal
            window = np.array([board[r+i, c+i] for i in range(5)])
            other_window = np.array([other_board[r+i, c+i] for i in range(5)])
            if np.sum(other_window) == 0:
                count += (5 - np.sum(window))
            
            # Down-left diagonal
            window = np.array([board[r+i, c+4-i] for i in range(5)])
            other_window = np.array([other_board[r+i, c+4-i] for i in range(5)])
            if np.sum(other_window) == 0:
                count += (5 - np.sum(window))
    
    return count

def count_potential_fours(board, other_board):
    """Count how many potential fours exist that could become fives"""
    count = 0
    
    def check_line(line, other_line):
        if np.sum(other_line) > 0:
            return False
        if np.sum(line) == 4 and np.sum(other_line) == 0:
            return True
        return False
    
    # Check horizontal
    for r in range(6):
        for c in range(2):
            if check_line(board[r, c:c+5], other_board[r, c:c+5]):
                count += 1
    
    # Check vertical
    for c in range(6):
        for r in range(2):
            if check_line(board[r:r+5, c], other_board[r:r+5, c]):
                count += 1
    
    # Check diagonals
    for r in range(2):
        for c in range(2):
            # Down-right
            line = np.array([board[r+i, c+i] for i in range(5)])
            other_line = np.array([other_board[r+i, c+i] for i in range(5)])
            if check_line(line, other_line):
                count += 1
            
            # Down-left
            line = np.array([board[r+i, c+4-i] for i in range(5)])
            other_line = np.array([other_board[r+i, c+4-i] for i in range(5)])
            if check_line(line, other_line):
                count += 1
    
    return count
