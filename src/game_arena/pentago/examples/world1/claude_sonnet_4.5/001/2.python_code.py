
def policy(you, opponent):
    import numpy as np
    
    you = np.array(you, dtype=int)
    opponent = np.array(opponent, dtype=int)
    
    def rotate_quadrant(board, quad, direction):
        """Rotate a quadrant on the board"""
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
            rotated = np.rot90(sub, k=1)
        else:
            rotated = np.rot90(sub, k=-1)
        
        if quad == 0:
            b[0:3, 0:3] = rotated
        elif quad == 1:
            b[0:3, 3:6] = rotated
        elif quad == 2:
            b[3:6, 0:3] = rotated
        else:
            b[3:6, 3:6] = rotated
        
        return b
    
    def check_win(board):
        """Check if there's a 5-in-a-row"""
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
    
    def evaluate_position(you_board, opp_board):
        """Evaluate board position with heuristic"""
        score = 0
        
        # Check for wins
        if check_win(you_board):
            return 100000
        if check_win(opp_board):
            return -100000
        
        # Count consecutive marbles
        def count_sequences(board, length):
            count = 0
            # Horizontal
            for i in range(6):
                for j in range(6 - length + 1):
                    if np.sum(board[i, j:j+length]) == length:
                        if j == 0 or board[i, j-1] == 0:
                            if j + length == 6 or board[i, j+length] == 0:
                                count += 1
            # Vertical
            for i in range(6 - length + 1):
                for j in range(6):
                    if np.sum(board[i:i+length, j]) == length:
                        if i == 0 or board[i-1, j] == 0:
                            if i + length == 6 or board[i+length, j] == 0:
                                count += 1
            # Diagonals
            for i in range(6 - length + 1):
                for j in range(6 - length + 1):
                    if np.sum([board[i+k, j+k] for k in range(length)]) == length:
                        count += 1
                    if np.sum([board[i+k, j+length-1-k] for k in range(length)]) == length:
                        count += 1
            return count
        
        # Reward our sequences, penalize opponent sequences
        score += count_sequences(you_board, 4) * 500
        score += count_sequences(you_board, 3) * 50
        score += count_sequences(you_board, 2) * 5
        
        score -= count_sequences(opp_board, 4) * 600
        score -= count_sequences(opp_board, 3) * 60
        score -= count_sequences(opp_board, 2) * 6
        
        # Center control
        center_positions = [(2, 2), (2, 3), (3, 2), (3, 3)]
        for r, c in center_positions:
            if you_board[r, c] == 1:
                score += 10
            if opp_board[r, c] == 1:
                score -= 10
        
        return score
    
    # Find all legal moves
    legal_moves = []
    for r in range(6):
        for c in range(6):
            if you[r, c] == 0 and opponent[r, c] == 0:
                legal_moves.append((r, c))
    
    if not legal_moves:
        return "1,1,0,L"
    
    best_move = None
    best_score = -float('inf')
    
    # Try each placement and rotation
    for r, c in legal_moves:
        you_new = you.copy()
        you_new[r, c] = 1
        
        for quad in range(4):
            for direction in ['L', 'R']:
                you_rotated = rotate_quadrant(you_new, quad, direction)
                opp_rotated = rotate_quadrant(opponent, quad, direction)
                
                # Check if this move wins
                if check_win(you_rotated):
                    return f"{r+1},{c+1},{quad},{direction}"
                
                # Evaluate position
                score = evaluate_position(you_rotated, opp_rotated)
                
                if score > best_score:
                    best_score = score
                    best_move = (r, c, quad, direction)
    
    if best_move:
        r, c, quad, direction = best_move
        return f"{r+1},{c+1},{quad},{direction}"
    
    # Fallback: return first legal move
    r, c = legal_moves[0]
    return f"{r+1},{c+1},0,L"
