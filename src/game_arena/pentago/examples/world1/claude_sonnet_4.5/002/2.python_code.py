
def policy(you, opponent):
    import numpy as np
    
    you_arr = np.array(you, dtype=int)
    opp_arr = np.array(opponent, dtype=int)
    
    def rotate_quadrant(board, quad, direction):
        """Rotate a quadrant on the board."""
        result = board.copy()
        if quad == 0:
            r_start, c_start = 0, 0
        elif quad == 1:
            r_start, c_start = 0, 3
        elif quad == 2:
            r_start, c_start = 3, 0
        else:  # quad == 3
            r_start, c_start = 3, 3
        
        sub = board[r_start:r_start+3, c_start:c_start+3].copy()
        if direction == 'L':
            rotated = np.rot90(sub, k=1)
        else:  # 'R'
            rotated = np.rot90(sub, k=-1)
        result[r_start:r_start+3, c_start:c_start+3] = rotated
        return result
    
    def check_winner(board):
        """Check if there's a 5-in-a-row on the board."""
        # Check rows
        for r in range(6):
            for c in range(2):
                if np.sum(board[r, c:c+5]) == 5:
                    return True
        # Check columns
        for c in range(6):
            for r in range(2):
                if np.sum(board[r:r+5, c]) == 5:
                    return True
        # Check diagonals
        for r in range(2):
            for c in range(2):
                if np.sum([board[r+i, c+i] for i in range(5)]) == 5:
                    return True
        for r in range(2):
            for c in range(4, 6):
                if np.sum([board[r+i, c-i] for i in range(5)]) == 5:
                    return True
        return False
    
    def evaluate_position(you_board, opp_board):
        """Evaluate a board position."""
        score = 0
        
        # Check all possible lines for consecutive marbles
        def score_line(line_you, line_opp):
            s = 0
            for length in [4, 3, 2]:
                for i in range(len(line_you) - length + 1):
                    segment_you = line_you[i:i+length]
                    segment_opp = line_opp[i:i+length]
                    if np.sum(segment_opp) == 0 and np.sum(segment_you) == length:
                        s += length ** 3
                    if np.sum(segment_you) == 0 and np.sum(segment_opp) == length:
                        s -= length ** 3
            return s
        
        # Rows
        for r in range(6):
            score += score_line(you_board[r, :], opp_board[r, :])
        
        # Columns
        for c in range(6):
            score += score_line(you_board[:, c], opp_board[:, c])
        
        # Diagonals
        for r in range(2):
            for c in range(2):
                diag_you = [you_board[r+i, c+i] for i in range(5)]
                diag_opp = [opp_board[r+i, c+i] for i in range(5)]
                score += score_line(np.array(diag_you), np.array(diag_opp))
        
        for r in range(2):
            for c in range(4, 6):
                diag_you = [you_board[r+i, c-i] for i in range(5)]
                diag_opp = [opp_board[r+i, c-i] for i in range(5)]
                score += score_line(np.array(diag_you), np.array(diag_opp))
        
        return score
    
    # Find all legal placements
    empty_cells = []
    for r in range(6):
        for c in range(6):
            if you_arr[r, c] == 0 and opp_arr[r, c] == 0:
                empty_cells.append((r, c))
    
    best_move = None
    best_score = -float('inf')
    
    # Try each placement and rotation combination
    for r, c in empty_cells:
        for quad in range(4):
            for direction in ['L', 'R']:
                # Apply move
                new_you = you_arr.copy()
                new_you[r, c] = 1
                
                # Rotate
                new_you = rotate_quadrant(new_you, quad, direction)
                new_opp = rotate_quadrant(opp_arr, quad, direction)
                
                # Check if we win
                if check_winner(new_you):
                    # Immediate win - but check if opponent also wins (draw)
                    if not check_winner(new_opp):
                        return f"{r+1},{c+1},{quad},{direction}"
                    else:
                        score = 0  # Draw is neutral
                else:
                    score = evaluate_position(new_you, new_opp)
                
                if score > best_score:
                    best_score = score
                    best_move = f"{r+1},{c+1},{quad},{direction}"
    
    return best_move
