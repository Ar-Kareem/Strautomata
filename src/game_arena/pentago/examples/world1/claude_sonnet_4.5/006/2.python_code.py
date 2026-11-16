
import numpy as np

def policy(you, opponent) -> str:
    you_arr = np.array(you, dtype=int)
    opp_arr = np.array(opponent, dtype=int)
    
    # Find all legal placements
    legal_placements = []
    for r in range(6):
        for c in range(6):
            if you_arr[r][c] == 0 and opp_arr[r][c] == 0:
                legal_placements.append((r+1, c+1))  # 1-indexed
    
    if not legal_placements:
        return "1,1,0,L"  # Fallback (shouldn't happen)
    
    best_move = None
    best_score = float('-inf')
    
    # Try each legal placement with each rotation
    for row, col in legal_placements:
        for quad in range(4):
            for direction in ['L', 'R']:
                # Simulate the move
                you_copy = you_arr.copy()
                opp_copy = opp_arr.copy()
                
                # Place marble
                you_copy[row-1][col-1] = 1
                
                # Rotate quadrant
                you_copy, opp_copy = rotate_quadrant(you_copy, opp_copy, quad, direction)
                
                # Check if we win
                if check_win(you_copy):
                    return f"{row},{col},{quad},{direction}"
                
                # Evaluate the position
                score = evaluate_position(you_copy, opp_copy)
                
                if score > best_score:
                    best_score = score
                    best_move = f"{row},{col},{quad},{direction}"
    
    # Check if opponent can win on next move - prioritize blocking
    for row, col in legal_placements:
        for quad in range(4):
            for direction in ['L', 'R']:
                you_copy = you_arr.copy()
                opp_copy = opp_arr.copy()
                
                you_copy[row-1][col-1] = 1
                you_copy, opp_copy = rotate_quadrant(you_copy, opp_copy, quad, direction)
                
                # Check all opponent responses
                blocks_win = False
                for r2, c2 in legal_placements:
                    if r2-1 == row-1 and c2-1 == col-1:
                        continue
                    for q2 in range(4):
                        for d2 in ['L', 'R']:
                            opp_test = opp_copy.copy()
                            you_test = you_copy.copy()
                            opp_test[r2-1][c2-1] = 1
                            you_test, opp_test = rotate_quadrant(you_test, opp_test, q2, d2)
                            if check_win(opp_test):
                                blocks_win = True
                                break
                        if blocks_win:
                            break
                    if blocks_win:
                        break
    
    return best_move if best_move else f"{legal_placements[0][0]},{legal_placements[0][1]},0,L"

def rotate_quadrant(you, opp, quad, direction):
    you_new = you.copy()
    opp_new = opp.copy()
    
    # Define quadrant boundaries
    if quad == 0:
        r_start, c_start = 0, 0
    elif quad == 1:
        r_start, c_start = 0, 3
    elif quad == 2:
        r_start, c_start = 3, 0
    else:  # quad == 3
        r_start, c_start = 3, 3
    
    # Extract 3x3 sub-boards
    you_quad = you[r_start:r_start+3, c_start:c_start+3].copy()
    opp_quad = opp[r_start:r_start+3, c_start:c_start+3].copy()
    
    # Rotate
    if direction == 'L':
        you_quad = np.rot90(you_quad, k=1)  # Counter-clockwise
        opp_quad = np.rot90(opp_quad, k=1)
    else:  # 'R'
        you_quad = np.rot90(you_quad, k=-1)  # Clockwise
        opp_quad = np.rot90(opp_quad, k=-1)
    
    # Place back
    you_new[r_start:r_start+3, c_start:c_start+3] = you_quad
    opp_new[r_start:r_start+3, c_start:c_start+3] = opp_quad
    
    return you_new, opp_new

def check_win(board):
    # Check all lines for 5+ in a row
    for r in range(6):
        for c in range(6):
            if board[r][c] == 0:
                continue
            # Horizontal
            if c <= 1 and np.sum(board[r, c:c+5]) == 5:
                return True
            # Vertical
            if r <= 1 and np.sum(board[r:r+5, c]) == 5:
                return True
            # Diagonal (down-right)
            if r <= 1 and c <= 1:
                if sum(board[r+i][c+i] for i in range(5)) == 5:
                    return True
            # Diagonal (down-left)
            if r <= 1 and c >= 4:
                if sum(board[r+i][c-i] for i in range(5)) == 5:
                    return True
    return False

def evaluate_position(you, opp):
    score = 0
    
    # Count sequences of various lengths
    for length in [4, 3, 2]:
        score += count_sequences(you, length) * (10 ** length)
        score -= count_sequences(opp, length) * (10 ** length) * 1.2
    
    # Center control bonus
    center_positions = [(2,2), (2,3), (3,2), (3,3)]
    for r, c in center_positions:
        if you[r][c] == 1:
            score += 50
        if opp[r][c] == 1:
            score -= 50
    
    return score

def count_sequences(board, length):
    count = 0
    # Horizontal
    for r in range(6):
        for c in range(6-length+1):
            if np.sum(board[r, c:c+length]) == length:
                count += 1
    # Vertical
    for r in range(6-length+1):
        for c in range(6):
            if np.sum(board[r:r+length, c]) == length:
                count += 1
    # Diagonal
    for r in range(6-length+1):
        for c in range(6-length+1):
            if sum(board[r+i][c+i] for i in range(length)) == length:
                count += 1
        for c in range(length-1, 6):
            if sum(board[r+i][c-i] for i in range(length)) == length:
                count += 1
    return count
