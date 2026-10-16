
def policy(you, opponent):
    import numpy as np
    
    you = np.array(you)
    opponent = np.array(opponent)
    
    def rotate_quadrant(board, quad, direction):
        """Rotate a quadrant on the board."""
        b = board.copy()
        if quad == 0:
            sub = b[0:3, 0:3]
        elif quad == 1:
            sub = b[0:3, 3:6]
        elif quad == 2:
            sub = b[3:6, 0:3]
        else:
            sub = b[3:6, 3:6]
        
        if direction == 'L':
            rotated = np.rot90(sub, 1)
        else:
            rotated = np.rot90(sub, -1)
        
        if quad == 0:
            b[0:3, 0:3] = rotated
        elif quad == 1:
            b[0:3, 3:6] = rotated
        elif quad == 2:
            b[3:6, 0:3] = rotated
        else:
            b[3:6, 3:6] = rotated
        
        return b
    
    def check_winner(board):
        """Check if board has 5 in a row."""
        # Horizontal and vertical
        for i in range(6):
            for j in range(2):
                if np.sum(board[i, j:j+5]) == 5:
                    return True
                if np.sum(board[j:j+5, i]) == 5:
                    return True
        
        # Diagonals
        for i in range(2):
            for j in range(2):
                if np.sum([board[i+k, j+k] for k in range(5)]) == 5:
                    return True
                if np.sum([board[i+k, j+4-k] for k in range(5)]) == 5:
                    return True
        
        return False
    
    def count_sequences(board, length):
        """Count sequences of given length."""
        count = 0
        # Horizontal
        for i in range(6):
            for j in range(6 - length + 1):
                if np.sum(board[i, j:j+length]) == length:
                    count += 1
        # Vertical
        for i in range(6 - length + 1):
            for j in range(6):
                if np.sum(board[i:i+length, j]) == length:
                    count += 1
        # Diagonals
        for i in range(6 - length + 1):
            for j in range(6 - length + 1):
                if np.sum([board[i+k, j+k] for k in range(length)]) == length:
                    count += 1
                if np.sum([board[i+k, j+length-1-k] for k in range(length)]) == length:
                    count += 1
        return count
    
    def evaluate_board(my_board, opp_board):
        """Evaluate board position."""
        my_score = 0
        opp_score = 0
        
        my_score += count_sequences(my_board, 4) * 100
        my_score += count_sequences(my_board, 3) * 10
        my_score += count_sequences(my_board, 2) * 1
        
        opp_score += count_sequences(opp_board, 4) * 100
        opp_score += count_sequences(opp_board, 3) * 10
        opp_score += count_sequences(opp_board, 2) * 1
        
        return my_score - opp_score
    
    # Find all legal moves
    legal_moves = []
    for r in range(6):
        for c in range(6):
            if you[r, c] == 0 and opponent[r, c] == 0:
                for quad in range(4):
                    for direction in ['L', 'R']:
                        legal_moves.append((r, c, quad, direction))
    
    if not legal_moves:
        return "1,1,0,L"
    
    best_move = None
    best_score = -float('inf')
    
    for r, c, quad, direction in legal_moves:
        # Simulate move
        my_new = you.copy()
        my_new[r, c] = 1
        my_rotated = rotate_quadrant(my_new, quad, direction)
        opp_rotated = rotate_quadrant(opponent, quad, direction)
        
        # Check if we win
        if check_winner(my_rotated):
            return f"{r+1},{c+1},{quad},{direction}"
        
        # Evaluate position
        score = evaluate_board(my_rotated, opp_rotated)
        
        # Check if opponent would win (defensive priority)
        opp_can_win = False
        for rr in range(6):
            for cc in range(6):
                if my_rotated[rr, cc] == 0 and opp_rotated[rr, cc] == 0:
                    for qq in range(4):
                        for dd in ['L', 'R']:
                            opp_test = opp_rotated.copy()
                            opp_test[rr, cc] = 1
                            opp_test = rotate_quadrant(opp_test, qq, dd)
                            if check_winner(opp_test):
                                opp_can_win = True
                                break
                        if opp_can_win:
                            break
                if opp_can_win:
                    break
            if opp_can_win:
                break
        
        if opp_can_win:
            score -= 1000
        
        # Prefer center positions early
        center_bonus = 0
        if r in [2, 3] and c in [2, 3]:
            center_bonus = 5
        score += center_bonus
        
        if score > best_score:
            best_score = score
            best_move = (r, c, quad, direction)
    
    if best_move:
        r, c, quad, direction = best_move
        return f"{r+1},{c+1},{quad},{direction}"
    
    # Fallback
    r, c, quad, direction = legal_moves[0]
    return f"{r+1},{c+1},{quad},{direction}"
