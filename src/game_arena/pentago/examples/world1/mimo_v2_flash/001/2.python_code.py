
def policy(you, opponent):
    """
    Strong Pentago AI policy that evaluates moves using:
    1. Immediate win detection
    2. Threat blocking
    3. Heuristic evaluation
    4. Rotational impact analysis
    """
    import numpy as np
    
    # Convert to numpy arrays for easier manipulation
    you_arr = np.array(you, dtype=int)
    opp_arr = np.array(opponent, dtype=int)
    
    # Get all empty positions
    empty_positions = []
    for r in range(6):
        for c in range(6):
            if you_arr[r][c] == 0 and opp_arr[r][c] == 0:
                empty_positions.append((r, c))
    
    # Quadrant definitions (0-indexed rows/cols)
    quad_ranges = {
        0: ((0, 3), (0, 3)),  # top-left
        1: ((0, 3), (3, 6)),  # top-right
        2: ((3, 6), (0, 3)),  # bottom-left
        3: ((3, 6), (3, 6))   # bottom-right
    }
    
    def check_5_in_a_row(board):
        """Check if board has 5+ in a row, returns (winner, line_count)"""
        max_len = 0
        # Check all directions: horizontal, vertical, diagonal (/), diagonal (\)
        for r in range(6):
            for c in range(6):
                if board[r][c] == 0:
                    continue
                
                # Horizontal
                if c <= 1:
                    count = 0
                    for i in range(5):
                        if c+i < 6 and board[r][c+i] == board[r][c]:
                            count += 1
                        else:
                            break
                    max_len = max(max_len, count)
                
                # Vertical
                if r <= 1:
                    count = 0
                    for i in range(5):
                        if r+i < 6 and board[r+i][c] == board[r][c]:
                            count += 1
                        else:
                            break
                    max_len = max(max_len, count)
                
                # Diagonal \
                if r <= 1 and c <= 1:
                    count = 0
                    for i in range(5):
                        if r+i < 6 and c+i < 6 and board[r+i][c+i] == board[r][c]:
                            count += 1
                        else:
                            break
                    max_len = max(max_len, count)
                
                # Diagonal /
                if r >= 4 and c <= 1:
                    count = 0
                    for i in range(5):
                        if r-i >= 0 and c+i < 6 and board[r-i][c+i] == board[r][c]:
                            count += 1
                        else:
                            break
                    max_len = max(max_len, count)
        
        return max_len
    
    def rotate_quadrant(board, quad, direction):
        """Rotate a quadrant 90 degrees (L=clockwise, R=counterclockwise)"""
        new_board = board.copy()
        r_range, c_range = quad_ranges[quad]
        quad_board = new_board[r_range[0]:r_range[1], c_range[0]:c_range[1]].copy()
        
        if direction == 'L':  # 90 degrees anticlockwise
            rotated = np.rot90(quad_board, -1)
        else:  # R - 90 degrees clockwise
            rotated = np.rot90(quad_board, 1)
        
        new_board[r_range[0]:r_range[1], c_range[0]:c_range[1]] = rotated
        return new_board
    
    def evaluate_position(board, player):
        """Heuristic evaluation of board position"""
        score = 0
        
        # Check for 4-in-a-row (very strong)
        for r in range(6):
            for c in range(6):
                if board[r][c] != player:
                    continue
                
                # Horizontal 4
                if c <= 2:
                    if all(board[r][c+i] == player for i in range(4)):
                        if c == 0 or c == 2:  # With space on one or both sides
                            if c == 0 and c+4 < 6 and board[r][4] == 0:
                                score += 100
                            elif c == 2 and board[r][6-1] == 0:
                                score += 100
                            else:
                                score += 50
                
                # Vertical 4
                if r <= 2:
                    if all(board[r+i][c] == player for i in range(4)):
                        if r == 0 or r == 2:
                            if r == 0 and r+4 < 6 and board[4][c] == 0:
                                score += 100
                            elif r == 2 and board[5][c] == 0:
                                score += 100
                            else:
                                score += 50
                
                # Diagonal \ 4
                if r <= 2 and c <= 2:
                    if all(board[r+i][c+i] == player for i in range(4)):
                        score += 50
                
                # Diagonal / 4
                if r >= 3 and c <= 2:
                    if all(board[r-i][c+i] == player for i in range(4)):
                        score += 50
        
        # Check for 3-in-a-row
        for r in range(6):
            for c in range(6):
                if board[r][c] != player:
                    continue
                
                # Horizontal 3
                if c <= 3:
                    if all(board[r][c+i] == player for i in range(3)):
                        score += 5
                
                # Vertical 3
                if r <= 3:
                    if all(board[r+i][c] == player for i in range(3)):
                        score += 5
        
        # Center control bonus
        for r in [2, 3]:
            for c in [2, 3]:
                if board[r][c] == player:
                    score += 2
        
        # Corner control
        corners = [(0,0), (0,5), (5,0), (5,5)]
        for (r, c) in corners:
            if board[r][c] == player:
                score += 3
        
        # Adjacent connections
        directions = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]
        for r in range(6):
            for c in range(6):
                if board[r][c] == player:
                    for dr, dc in directions:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == player:
                            score += 0.5
        
        return score
    
    best_score = -float('inf')
    best_move = None
    
    # Try all possible moves
    for r, c in empty_positions:
        for quad in range(4):
            for direction in ['L', 'R']:
                # Simulate move
                new_you = you_arr.copy()
                new_you[r][c] = 1
                new_opp = opp_arr.copy()
                
                # Rotate quadrant
                rotated_you = rotate_quadrant(new_you, quad, direction)
                rotated_opp = rotate_quadrant(new_opp, quad, direction)
                
                # Check if we win
                you_len = check_5_in_a_row(rotated_you)
                opp_len = check_5_in_a_row(rotated_opp)
                
                if you_len >= 5:
                    # We win - return immediately
                    return f"{r+1},{c+1},{quad},{direction}"
                
                if opp_len >= 5:
                    # Opponent would win - avoid this move
                    continue
                
                # Evaluate this position
                our_score = evaluate_position(rotated_you, 1)
                opp_score = evaluate_position(rotated_opp, -1)
                total_score = our_score - opp_score * 1.1  # Weight opponent threats
                
                # Add randomness for exploration in early game
                if len(empty_positions) > 20:
                    import random
                    total_score += random.uniform(-2, 2)
                
                if total_score > best_score:
                    best_score = total_score
                    best_move = (r, c, quad, direction)
    
    # If no good move found (shouldn't happen), return first legal move
    if best_move is None:
        r, c = empty_positions[0]
        return f"{r+1},{c+1},0,L"
    
    r, c, quad, direction = best_move
    return f"{r+1},{c+1},{quad},{direction}"
