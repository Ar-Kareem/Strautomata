
import numpy as np
import time
from collections import deque

def policy(you, opponent) -> str:
    # Convert to numpy arrays for easier manipulation
    you_arr = np.array(you, dtype=np.int8)
    opponent_arr = np.array(opponent, dtype=np.int8)
    
    # Start timing for the move
    start_time = time.time()
    
    # Get all possible moves
    empty_cells = []
    for r in range(6):
        for c in range(6):
            if you_arr[r][c] == 0 and opponent_arr[r][c] == 0:
                empty_cells.append((r, c))
    
    # If no empty cells (shouldn't happen per constraints), return fallback
    if not empty_cells:
        return "1,1,0,L"
    
    # Define quadrants (0-3)
    # We'll try to make a smart decision with limited search depth due to time constraints
    
    # First, check for immediate win moves
    for r, c in empty_cells:
        # Try placing at (r,c) and then each rotation
        for quad in range(4):
            for direction in ['L', 'R']:
                # Simulate move and check if it wins
                if is_winning_move(r, c, quad, direction, you_arr, opponent_arr):
                    return f"{r+1},{c+1},{quad},{direction}"
    
    # Check for opponent win blocking
    for r, c in empty_cells:
        for quad in range(4):
            for direction in ['L', 'R']:
                # Simulate opponent's potential winning move after we place here
                # We need to check if opponent could win on their next turn if we don't block
                # But since we're placing, we need to see if after our move, opponent has win
                # So simulate placing our piece, then check if opponent has any winning moves immediately
                temp_you = you_arr.copy()
                temp_opponent = opponent_arr.copy()
                temp_you[r][c] = 1
                
                # Check if opponent has any winning move on next turn
                is_opponent_can_win = False
                for or_, oc in empty_cells:
                    if or_ == r and oc == c:
                        continue
                    # Try if opponent could win by placing at (or_, oc)
                    temp_opponent[or_][oc] = 1
                    if has_five_in_a_row(temp_opponent):
                        is_opponent_can_win = True
                    temp_opponent[or_][oc] = 0
                
                # However, we also need to consider that after our move and rotation, opponent might have win
                # So simulate the full move (place + rotate)
                simulated_you = you_arr.copy()
                simulated_opponent = opponent_arr.copy()
                simulated_you[r][c] = 1
                rotate_quadrant(simulated_you, simulated_opponent, quad, direction)
                
                if has_five_in_a_row(simulated_opponent):
                    # This move blocks an immediate opponent win
                    return f"{r+1},{c+1},{quad},{direction}"
    
    # If no immediate win or block, use heuristic search
    # Limited depth search due to time constraints
    
    best_score = float('-inf')
    best_move = None
    
    # Try each possible move with limited search depth (depth 2 to 3)
    # We'll use a simple evaluation function and limited depth due to time
    
    # Sort moves by potential
    potential_moves = []
    
    for r, c in empty_cells:
        for quad in range(4):
            for direction in ['L', 'R']:
                # Evaluate this move
                score = evaluate_move(r, c, quad, direction, you_arr, opponent_arr)
                potential_moves.append((score, r, c, quad, direction))
    
    # Sort by score descending
    potential_moves.sort(key=lambda x: x[0], reverse=True)
    
    # Take top N moves to search (10-15) to stay within time limit
    top_moves = potential_moves[:min(15, len(potential_moves))]
    
    # Search the most promising moves
    for score, r, c, quad, direction in top_moves:
        # Skip if we already found a guaranteed win (should be caught above)
        if best_move is not None and best_score > 1000:  # If we already found a very good move
            break
            
        # Simulate this move
        simulated_you = you_arr.copy()
        simulated_opponent = opponent_arr.copy()
        simulated_you[r][c] = 1
        rotate_quadrant(simulated_you, simulated_opponent, quad, direction)
        
        # Evaluate the resulting position
        move_score = evaluate_position(simulated_you, simulated_opponent, True)
        
        # Also check opponent's best response (very shallow search)
        opponent_best_response_score = float('-inf')
        empty_after_move = []
        for or_, oc in range(6):
            if simulated_you[or_][oc] == 0 and simulated_opponent[or_][oc] == 0:
                empty_after_move.append((or_, oc))
        
        # If opponent can win immediately after our move
        if has_five_in_a_row(simulated_opponent):
            # This is bad for us - avoid this move
            move_score = -1000
        else:
            # Check if opponent has any immediate winning moves
            opponent_can_win = False
            for or_, oc in empty_after_move:
                temp_opponent = simulated_opponent.copy()
                temp_opponent[or_][oc] = 1
                if has_five_in_a_row(temp_opponent):
                    opponent_can_win = True
                    break
            
            if opponent_can_win:
                # Our move didn't block opponent's win - very bad
                move_score = -900
            
            # For simplicity, do a depth 1 search
            # Try one step of opponent's response
            if len(empty_after_move) > 0:
                # Try the most promising opponent response
                opp_potential = []
                for or_, oc in empty_after_move:
                    # Evaluate opponent's potential move
                    temp_you = simulated_you.copy()
                    temp_opponent = simulated_opponent.copy()
                    temp_opponent[or_][oc] = 1
                    
                    # Find best rotation for opponent
                    opp_best_score = float('-inf')
                    for q in range(4):
                        for d in ['L', 'R']:
                            temp_you_copy = temp_you.copy()
                            temp_opponent_copy = temp_opponent.copy()
                            rotate_quadrant(temp_you_copy, temp_opponent_copy, q, d)
                            
                            if has_five_in_a_row(temp_opponent_copy):
                                opp_best_score = 1000
                                break
                            else:
                                opp_score = evaluate_position(temp_you_copy, temp_opponent_copy, False)
                                opp_best_score = max(opp_best_score, opp_score)
                        
                        if opp_best_score == 1000:
                            break
                    
                    opp_potential.append(opp_best_score)
                
                if opp_potential:
                    worst_case_score = max(opp_potential)  # opponent's best response
                    move_score -= worst_case_score * 0.5  # penalize by opponent's potential
        
        if move_score > best_score:
            best_score = move_score
            best_move = (r, c, quad, direction)
        
        # Check time - don't exceed 1 second
        if time.time() - start_time > 0.9:
            break
    
    # Fallback if no good move found
    if best_move is None:
        # Pick first available move
        r, c = empty_cells[0]
        best_move = (r, c, 0, 'L')
    
    r, c, quad, direction = best_move
    return f"{r+1},{c+1},{quad},{direction}"

def rotate_quadrant(you_arr, opponent_arr, quad, direction):
    """Rotate the specified quadrant 90 degrees in the given direction"""
    # Quadrants: 0=TL, 1=TR, 2=BL, 3=BR
    # Convert to 0-indexed coordinates
    row_start, col_start = 0, 0
    if quad == 0:  # top-left
        row_start, col_start = 0, 0
    elif quad == 1:  # top-right
        row_start, col_start = 0, 3
    elif quad == 2:  # bottom-left
        row_start, col_start = 3, 0
    else:  # bottom-right
        row_start, col_start = 3, 3
    
    # Extract 3x3 quadrant
    quadrant_you = you_arr[row_start:row_start+3, col_start:col_start+3].copy()
    quadrant_opponent = opponent_arr[row_start:row_start+3, col_start:col_start+3].copy()
    
    # Rotate 90 degrees
    if direction == 'R':  # clockwise
        rotated_you = np.rot90(quadrant_you, k=3)  # 90 degrees clockwise = 3x90 ccw
        rotated_opponent = np.rot90(quadrant_opponent, k=3)
    else:  # 'L' - anticlockwise
        rotated_you = np.rot90(quadrant_you, k=1)
        rotated_opponent = np.rot90(quadrant_opponent, k=1)
    
    # Put back
    you_arr[row_start:row_start+3, col_start:col_start+3] = rotated_you
    opponent_arr[row_start:row_start+3, col_start:col_start+3] = rotated_opponent

def has_five_in_a_row(arr):
    """Check if the array has 5 or more in a row (horizontal, vertical, diagonal)"""
    if arr.shape != (6,6):
        return False
    
    # Check horizontal
    for r in range(6):
        for c in range(2):  # can start from 0 to 2 (5 consecutive: 0-4, 1-5)
            if all(arr[r, c+i] == 1 for i in range(5)):
                return True
    
    # Check vertical
    for c in range(6):
        for r in range(2):  # can start from 0 to 2
            if all(arr[r+i, c] == 1 for i in range(5)):
                return True
    
    # Check main diagonal (top-left to bottom-right)
    for r in range(2):
        for c in range(2):
            if all(arr[r+i, c+i] == 1 for i in range(5)):
                return True
    
    # Check anti-diagonal (top-right to bottom-left)
    for r in range(2):
        for c in range(2):
            if all(arr[r+i, c+4-i] == 1 for i in range(5)):  # c+4-i: c+4, c+3, c+2, c+1, c
                return True
    
    return False

def is_winning_move(place_row, place_col, quad, direction, you_arr, opponent_arr):
    """Check if placing at (place_row, place_col) and rotating quad in direction creates a win"""
    # Create a copy
    test_you = you_arr.copy()
    test_opponent = opponent_arr.copy()
    
    # Place the marble
    test_you[place_row][place_col] = 1
    
    # Rotate the quadrant
    rotate_quadrant(test_you, test_opponent, quad, direction)
    
    # Check if we have 5 in a row
    return has_five_in_a_row(test_you)

def evaluate_move(place_row, place_col, quad, direction, you_arr, opponent_arr):
    """Evaluate the potential of a move"""
    # Simulate the move
    test_you = you_arr.copy()
    test_opponent = opponent_arr.copy()
    test_you[place_row][place_col] = 1
    rotate_quadrant(test_you, test_opponent, quad, direction)
    
    # Basic evaluation: count potential lines
    score = 0
    
    # Immediate win
    if has_five_in_a_row(test_you):
        return 1000
    
    # Check if opponent gets immediate win (bad)
    if has_five_in_a_row(test_opponent):
        return -800
    
    # Count 4-in-a-row potential for us
    score += count_potential_lines(test_you, 4) * 50
    score += count_potential_lines(test_you, 3) * 20
    
    # Count 4-in-a-row potential for opponent (penalize)
    score -= count_potential_lines(test_opponent, 4) * 30
    score -= count_potential_lines(test_opponent, 3) * 10
    
    # Center control
    center_scores = {
        (2,2): 10, (2,3): 10, (3,2): 10, (3,3): 10,
        (2,1): 5, (2,4): 5, (1,2): 5, (1,3): 5, 
        (3,1): 5, (3,4): 5, (4,2): 5, (4,3): 5
    }
    
    if (place_row, place_col) in center_scores:
        score += center_scores[(place_row, place_col)]
    
    # Avoid edge moves if possible
    if place_row in [0,5] or place_col in [0,5]:
        score -= 3
    
    # Rotation effect
    # Check if rotation improves our position
    score += evaluate_rotation_effect(quad, direction, test_you, test_opponent)
    
    return score

def evaluate_position(you_arr, opponent_arr, is_your_turn):
    """Evaluate the overall position"""
    score = 0
    
    # Winning position
    if has_five_in_a_row(you_arr):
        return 1000
    if has_five_in_a_row(opponent_arr):
        return -1000
    
    # Count patterns
    score += count_potential_lines(you_arr, 4) * 40
    score += count_potential_lines(you_arr, 3) * 15
    score += count_potential_lines(you_arr, 2) * 5
    
    score -= count_potential_lines(opponent_arr, 4) * 30
    score -= count_potential_lines(opponent_arr, 3) * 12
    score -= count_potential_lines(opponent_arr, 2) * 3
    
    # Center control for you
    center_scores = {
        (2,2): 8, (2,3): 8, (3,2): 8, (3,3): 8,
        (2,1): 4, (2,4): 4, (1,2): 4, (1,3): 4, 
        (3,1): 4, (3,4): 4, (4,2): 4, (4,3): 4
    }
    
    for r in range(6):
        for c in range(6):
            if you_arr[r][c] == 1 and (r,c) in center_scores:
                score += center_scores[(r,c)]
            if opponent_arr[r][c] == 1 and (r,c) in center_scores:
                score -= center_scores[(r,c)]
    
    # Avoid edge positions
    for r in range(6):
        for c in range(6):
            if you_arr[r][c] == 1 and (r == 0 or r == 5 or c == 0 or c == 5):
                score -= 2
            if opponent_arr[r][c] == 1 and (r == 0 or r == 5 or c == 0 or c == 5):
                score += 2
    
    return score

def count_potential_lines(arr, length):
    """Count potential lines of given length for a player (not 5)"""
    if length == 5:  # already handled by has_five_in_a_row
        return 1 if has_five_in_a_row(arr) else 0
    
    count = 0
    n = 6
    
    # Horizontal
    for r in range(n):
        for c in range(n - length + 1):
            if all(arr[r, c+i] == 1 for i in range(length)):
                # Check if the ends are potentially extendable
                if c > 0 and arr[r, c-1] == 0:
                    count += 1
                elif c + length < n and arr[r, c+length] == 0:
                    count += 1
                elif (c == 0 or arr[r, c-1] != 0) and (c + length == n or arr[r, c+length] != 0):
                    # Blocked at both ends
                    pass
                else:
                    # Can be extended at one end
                    count += 1
    
    # Vertical
    for c in range(n):
        for r in range(n - length + 1):
            if all(arr[r+i, c] == 1 for i in range(length)):
                if r > 0 and arr[r-1, c] == 0:
                    count += 1
                elif r + length < n and arr[r+length, c] == 0:
                    count += 1
                elif (r == 0 or arr[r-1, c] != 0) and (r + length == n or arr[r+length, c] != 0):
                    pass
                else:
                    count += 1
    
    # Main diagonal
    for r in range(n - length + 1):
        for c in range(n - length + 1):
            if all(arr[r+i, c+i] == 1 for i in range(length)):
                if r > 0 and c > 0 and arr[r-1, c-1] == 0:
                    count += 1
                elif r + length < n and c + length < n and arr[r+length, c+length] == 0:
                    count += 1
                elif (r == 0 or c == 0 or arr[r-1, c-1] != 0) and (r + length == n or c + length == n or arr[r+length, c+length] != 0):
                    pass
                else:
                    count += 1
    
    # Anti-diagonal
    for r in range(n - length + 1):
        for c in range(length - 1, n):
            if all(arr[r+i, c-i] == 1 for i in range(length)):
                if r > 0 and c + 1 < n and arr[r-1, c+1] == 0:
                    count += 1
                elif r + length < n and c - length >= 0 and arr[r+length, c-length] == 0:
                    count += 1
                elif (r == 0 or c + 1 == n or arr[r-1, c+1] != 0) and (r + length == n or c - length == -1 or arr[r+length, c-length] != 0):
                    pass
                else:
                    count += 1
    
    return count

def evaluate_rotation_effect(quad, direction, you_arr, opponent_arr):
    """Evaluate how much a rotation improves the position"""
    # This is a simple version - count how many potential lines are created/destroyed by rotation
    score = 0
    # We'll check the quadrants and see if rotation helps us connect pieces
    # For simplicity, just check if any 3-in-a-row is completed or created
    
    # Look at the rotated quadrant
    row_start, col_start = 0, 0
    if quad == 0:  # top-left
        row_start, col_start = 0, 0
    elif quad == 1:  # top-right
        row_start, col_start = 0, 3
    elif quad == 2:  # bottom-left
        row_start, col_start = 3, 0
    else:  # bottom-right
        row_start, col_start = 3, 3
    
    # Count potential lines within quadrant
    quad_you = you_arr[row_start:row_start+3, col_start:col_start+3]
    quad_opponent = opponent_arr[row_start:row_start+3, col_start:col_start+3]
    
    # For you
    for r in range(3):
        for c in range(4):
            if c < 3 and all(quad_you[r, c+i] == 1 for i in range(3)):
                # Check if this connects across quadrant boundaries
                if (r == 1 and c == 0 and col_start > 0) or (r == 1 and c == 1 and col_start < 3):
                    score += 5
    
    # Check columns
    for c in range(3):
        for r in range(4):
            if r < 3 and all(quad_you[r+i, c] == 1 for i in range(3)):
                if (c == 1 and r == 0 and row_start > 0) or (c == 1 and r == 1 and row_start < 3):
                    score += 5
    
    # Diagonals
    for r in range(4):
        for c in range(4):
            if r < 3 and c < 3 and all(quad_you[r+i, c+i] == 1 for i in range(3)):
                if (r == 0 and c == 0 and (row_start > 0 or col_start > 0)) or (r == 1 and c == 1 and (row_start < 3 or col_start < 3)):
                    score += 5
    
    for r in range(4):
        for c in range(2, 5):
            if r < 3 and c > 1 and all(quad_you[r+i, c-i] == 1 for i in range(3)):
                if (r == 0 and c == 2 and (row_start > 0 or col_start < 3)) or (r == 1 and c == 3 and (row_start < 3 or col_start > 0)):
                    score += 5
    
    return score
