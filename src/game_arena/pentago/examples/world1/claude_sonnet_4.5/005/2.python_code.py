
def policy(you, opponent) -> str:
    import numpy as np
    
    you = np.array(you, dtype=int)
    opponent = np.array(opponent, dtype=int)
    
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
    
    def check_win(board):
        """Check if there's a 5-in-a-row on the board."""
        # Horizontal
        for r in range(6):
            for c in range(2):
                if np.sum(board[r, c:c+5]) == 5:
                    return True
        # Vertical
        for r in range(2):
            for c in range(6):
                if np.sum(board[r:r+5, c]) == 5:
                    return True
        # Diagonal (top-left to bottom-right)
        for r in range(2):
            for c in range(2):
                if sum(board[r+i, c+i] for i in range(5)) == 5:
                    return True
        # Diagonal (top-right to bottom-left)
        for r in range(2):
            for c in range(4, 6):
                if sum(board[r+i, c-i] for i in range(5)) == 5:
                    return True
        return False
    
    def count_sequences(board, length):
        """Count sequences of a given length."""
        count = 0
        # Horizontal
        for r in range(6):
            for c in range(6 - length + 1):
                if np.sum(board[r, c:c+length]) == length:
                    count += 1
        # Vertical
        for r in range(6 - length + 1):
            for c in range(6):
                if np.sum(board[r:r+length, c]) == length:
                    count += 1
        # Diagonals
        for r in range(6 - length + 1):
            for c in range(6 - length + 1):
                if sum(board[r+i, c+i] for i in range(length)) == length:
                    count += 1
        for r in range(6 - length + 1):
            for c in range(length - 1, 6):
                if sum(board[r+i, c-i] for i in range(length)) == length:
                    count += 1
        return count
    
    def evaluate_board(my_board, opp_board):
        """Evaluate the board state."""
        if check_win(my_board):
            return 10000
        if check_win(opp_board):
            return -10000
        
        score = 0
        score += count_sequences(my_board, 4) * 100
        score += count_sequences(my_board, 3) * 10
        score += count_sequences(my_board, 2) * 1
        
        score -= count_sequences(opp_board, 4) * 100
        score -= count_sequences(opp_board, 3) * 10
        score -= count_sequences(opp_board, 2) * 1
        
        # Center control bonus
        center_positions = [(2, 2), (2, 3), (3, 2), (3, 3)]
        for r, c in center_positions:
            if my_board[r, c] == 1:
                score += 2
            if opp_board[r, c] == 1:
                score -= 2
        
        return score
    
    def apply_move(my_board, opp_board, r, c, quad, direction):
        """Apply a move and return new boards."""
        new_my = my_board.copy()
        new_my[r, c] = 1
        new_my = rotate_quadrant(new_my, quad, direction)
        new_opp = rotate_quadrant(opp_board, quad, direction)
        return new_my, new_opp
    
    # Get all legal moves
    legal_moves = []
    for r in range(6):
        for c in range(6):
            if you[r, c] == 0 and opponent[r, c] == 0:
                for quad in range(4):
                    for direction in ['L', 'R']:
                        legal_moves.append((r, c, quad, direction))
    
    if not legal_moves:
        return "1,1,0,L"
    
    # Evaluate all moves
    best_score = -float('inf')
    best_move = legal_moves[0]
    
    for r, c, quad, direction in legal_moves:
        new_you, new_opp = apply_move(you, opponent, r, c, quad, direction)
        
        # Check for immediate win
        if check_win(new_you):
            return f"{r+1},{c+1},{quad},{direction}"
        
        score = evaluate_board(new_you, new_opp)
        
        if score > best_score:
            best_score = score
            best_move = (r, c, quad, direction)
    
    r, c, quad, direction = best_move
    return f"{r+1},{c+1},{quad},{direction}"
