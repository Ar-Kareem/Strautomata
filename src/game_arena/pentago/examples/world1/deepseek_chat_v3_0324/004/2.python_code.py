
import numpy as np
import random
from collections import defaultdict

def policy(you, opponent):
    # Convert inputs to numpy arrays for easier manipulation
    you_board = np.array(you)
    opp_board = np.array(opponent)
    empty = 1 - (you_board + opp_board)
    
    # First check if we can win immediately
    for r in range(6):
        for c in range(6):
            if empty[r, c]:
                # Try placing our marble here
                temp_you = you_board.copy()
                temp_you[r, c] = 1
                # Check all possible rotations
                for quad in range(4):
                    for dir in ['L', 'R']:
                        rotated_you, rotated_opp = apply_rotation(temp_you, opp_board, quad, dir)
                        if check_win(rotated_you):
                            return f"{r+1},{c+1},{quad},{dir}"
    
    # Then check if opponent can win next move and block them
    for r in range(6):
        for c in range(6):
            if empty[r, c]:
                # Simulate opponent placing here
                temp_opp = opp_board.copy()
                temp_opp[r, c] = 1
                # Check all possible rotations
                for quad in range(4):
                    for dir in ['L', 'R']:
                        rotated_you, rotated_opp = apply_rotation(you_board, temp_opp, quad, dir)
                        if check_win(rotated_opp):
                            # Block by placing here and choosing any rotation (preferably helpful to us)
                            # Find the best rotation for us after blocking
                            best_score = -float('inf')
                            best_move = None
                            for q in range(4):
                                for d in ['L', 'R']:
                                    new_you, new_opp = apply_rotation(temp_you, opp_board, q, d)
                                    score = evaluate_position(new_you, new_opp)
                                    if score > best_score:
                                        best_score = score
                                        best_move = f"{r+1},{c+1},{q},{d}"
                            if best_move:
                                return best_move
                            else:
                                return f"{r+1},{c+1},{0},L"  # default if no good rotation found
    
    # If no immediate threats, evaluate all possible moves
    best_score = -float('inf')
    best_moves = []
    
    for r in range(6):
        for c in range(6):
            if empty[r, c]:
                temp_you = you_board.copy()
                temp_you[r, c] = 1
                
                for quad in range(4):
                    for dir in ['L', 'R']:
                        rotated_you, rotated_opp = apply_rotation(temp_you, opp_board, quad, dir)
                        score = evaluate_position(rotated_you, rotated_opp)
                        
                        # Add some randomness for equally good moves
                        if score == best_score:
                            best_moves.append(f"{r+1},{c+1},{quad},{dir}")
                        elif score > best_score:
                            best_score = score
                            best_moves = [f"{r+1},{c+1},{quad},{dir}"]
    
    # Return a random move among the best options
    if best_moves:
        return random.choice(best_moves)
    
    # Fallback: return first valid move found (shouldn't reach here)
    for r in range(6):
        for c in range(6):
            if empty[r, c]:
                return f"{r+1},{c+1},{0},L"

def apply_rotation(you_board, opp_board, quad, direction):
    """Apply rotation to the specified quadrant"""
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
    
    # Extract quadrant for both players
    you_quad = you[rows, cols]
    opp_quad = opp[rows, cols]
    
    # Rotate
    if direction == 'L':  # counter-clockwise
        you_quad = np.rot90(you_quad, 1)
        opp_quad = np.rot90(opp_quad, 1)
    else:  # clockwise
        you_quad = np.rot90(you_quad, -1)
        opp_quad = np.rot90(opp_quad, -1)
    
    # Put back rotated quadrants
    you[rows, cols] = you_quad
    opp[rows, cols] = opp_quad
    
    return you, opp

def check_win(board):
    """Check if board has 5-in-a-row"""
    # Check horizontal
    for r in range(6):
        for c in range(2):
            if np.all(board[r, c:c+5] == 1):
                return True
    
    # Check vertical
    for r in range(2):
        for c in range(6):
            if np.all(board[r:r+5, c] == 1):
                return True
    
    # Check diagonals
    for r in range(2):
        for c in range(2):
            if (board[r, c] == 1 and board[r+1, c+1] == 1 and 
                board[r+2, c+2] == 1 and board[r+3, c+3] == 1 and 
                board[r+4, c+4] == 1):
                return True
            if (board[r, 5-c] == 1 and board[r+1, 4-c] == 1 and 
                board[r+2, 3-c] == 1 and board[r+3, 2-c] == 1 and 
                board[r+4, 1-c] == 1):
                return True
    
    return False

def evaluate_position(you, opp):
    """Evaluate the board position with various heuristics"""
    score = 0
    
    # Count potential lines
    score += count_lines(you) * 10
    score -= count_lines(opp) * 8
    
    # Center control
    center = [(2,2), (2,3), (3,2), (3,3)]
    for r, c in center:
        if you[r, c] == 1:
            score += 2
        if opp[r, c] == 1:
            score -= 1
    
    # Mobility - empty spaces adjacent to our pieces
    for r in range(6):
        for c in range(6):
            if you[r, c] == 1:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if 0 <= r+dr < 6 and 0 <= c+dc < 6:
                            if you[r+dr, c+dc] == 0 and opp[r+dr, c+dc] == 0:
                                score += 0.5
    
    return score

def count_lines(board):
    """Count potential lines (3 or 4 in a row)"""
    count = 0
    
    # Horizontal
    for r in range(6):
        for c in range(2):
            line = board[r, c:c+5]
            sum_line = np.sum(line)
            if sum_line >= 3:
                count += sum_line
    
    # Vertical
    for r in range(2):
        for c in range(6):
            line = board[r:r+5, c]
            sum_line = np.sum(line)
            if sum_line >= 3:
                count += sum_line
    
    # Diagonals
    for r in range(2):
        for c in range(2):
            line = [board[r+i, c+i] for i in range(5)]
            sum_line = sum(line)
            if sum_line >= 3:
                count += sum_line
            
            line = [board[r+i, 4-c+i] for i in range(5)]
            sum_line = sum(line)
            if sum_line >= 3:
                count += sum_line
    
    return count
