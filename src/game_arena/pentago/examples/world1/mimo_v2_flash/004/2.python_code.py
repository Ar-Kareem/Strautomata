
def policy(you, opponent) -> str:
    import numpy as np
    from copy import deepcopy
    
    # Convert to numpy arrays for easier manipulation
    you_board = np.array(you)
    opp_board = np.array(opponent)
    empty_mask = (you_board == 0) & (opp_board == 0)
    
    # Helper functions
    def get_quad_coords(quad):
        """Get the row and column ranges for a quadrant"""
        if quad == 0: return range(0, 3), range(0, 3)  # top-left
        if quad == 1: return range(0, 3), range(3, 6)  # top-right
        if quad == 2: return range(3, 6), range(0, 3)  # bottom-left
        if quad == 3: return range(3, 6), range(3, 6)  # bottom-right
    
    def rotate_quadrant(board, quad, direction):
        """Rotate a quadrant in the board"""
        rows, cols = get_quad_coords(quad)
        quad_view = board[np.ix_(rows, cols)].copy()
        
        if direction == 'L':  # anticlockwise
            rotated = np.rot90(quad_view, -1)
        else:  # clockwise
            rotated = np.rot90(quad_view, 1)
        
        result = board.copy()
        result[np.ix_(rows, cols)] = rotated
        return result
    
    def count_in_line(board, r, c, dr, dc):
        """Count consecutive marbles starting from (r,c) in direction (dr,dc)"""
        count = 0
        while 0 <= r < 6 and 0 <= c < 6 and board[r, c] == 1:
            count += 1
            r += dr
            c += dc
        return count
    
    def check_win(board, r, c):
        """Check if placing at (r,c) creates a win"""
        if board[r, c] != 1:
            return False
        
        # Check all 4 directions: horizontal, vertical, two diagonals
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            # Count in both directions
            count_forward = count_in_line(board, r + dr, c + dc, dr, dc)
            count_backward = count_in_line(board, r - dr, c - dc, -dr, -dc)
            total = 1 + count_forward + count_backward
            
            if total >= 5:
                return True
        return False
    
    def evaluate_position(board, player):
        """Evaluate the position from player's perspective"""
        score = 0
        
        # Check for 4-in-a-row threats (win on next move)
        for r in range(6):
            for c in range(6):
                if board[r, c] == 1:
                    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
                    for dr, dc in directions:
                        count_forward = count_in_line(board, r + dr, c + dc, dr, dc)
                        count_backward = count_in_line(board, r - dr, c - dc, -dr, -dc)
                        total = 1 + count_forward + count_backward
                        
                        if total == 4:
                            score += 50
                        elif total >= 5:
                            score += 1000
        
        return score
    
    def evaluate_move(row, col, quad, direction, my_board, opp_board):
        """Evaluate a specific move"""
        # Simulate move
        new_my_board = my_board.copy()
        new_my_board[row, col] = 1
        
        # Rotate quadrant
        new_my_board = rotate_quadrant(new_my_board, quad, direction)
        new_opp_board = rotate_quadrant(opp_board, quad, direction)
        
        # Check if I win
        if check_win(new_my_board, row, col):
            return 10000
        
        # Check if opponent wins (bad - should avoid)
        # Check all opponent positions
        for r in range(6):
            for c in range(6):
                if new_opp_board[r, c] == 1:
                    if check_win(new_opp_board, r, c):
                        return -10000
        
        # Evaluate position
        score = evaluate_position(new_my_board, True)
        
        # Bonus for center quadrant
        if quad in [0, 3]:
            score += 5
        
        # Penalty for rotating opponent's quadrant that has their marbles
        rows, cols = get_quad_coords(quad)
        opp_in_quad = np.sum(new_opp_board[np.ix_(rows, cols)])
        score -= opp_in_quad * 2
        
        return score
    
    # Get all empty positions
    empty_positions = [(r, c) for r in range(6) for c in range(6) if empty_mask[r, c]]
    
    best_score = -float('inf')
    best_move = None
    
    # Try all possible moves
    for r, c in empty_positions:
        for quad in range(4):
            for direction in ['L', 'R']:
                score = evaluate_move(r, c, quad, direction, you_board, opp_board)
                
                if score > best_score:
                    best_score = score
                    best_move = (r, c, quad, direction)
    
    # Fallback: if no good move found, pick first available
    if best_move is None and empty_positions:
        r, c = empty_positions[0]
        best_move = (r, c, 0, 'L')
    
    # Convert to 1-indexed string format
    r, c, quad, direction = best_move
    return f"{r+1},{c+1},{quad},{direction}"
