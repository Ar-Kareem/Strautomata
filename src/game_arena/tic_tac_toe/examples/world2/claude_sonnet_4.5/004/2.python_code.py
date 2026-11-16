
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Define all possible winning lines for 4x4 board
    def get_all_lines():
        lines = []
        # Rows
        for r in range(4):
            lines.append([(r, c) for c in range(4)])
        # Columns
        for c in range(4):
            lines.append([(r, c) for r in range(4)])
        # Diagonals
        lines.append([(i, i) for i in range(4)])
        lines.append([(i, 3-i) for i in range(4)])
        return lines
    
    lines = get_all_lines()
    
    # Check if a move wins or blocks
    def check_line_threat(line, player):
        """Returns position to play if there's a winning move for player on this line"""
        values = [board[r][c] for r, c in line]
        if values.count(player) == 3 and values.count(0) == 1:
            # Found a winning/blocking opportunity
            for r, c in line:
                if board[r][c] == 0:
                    return (r, c)
        return None
    
    # First priority: Win immediately if possible
    for line in lines:
        move = check_line_threat(line, 1)
        if move:
            return move
    
    # Second priority: Block opponent's winning move
    for line in lines:
        move = check_line_threat(line, -1)
        if move:
            return move
    
    # Third priority: Evaluate all empty positions
    def evaluate_position(r, c):
        if board[r][c] != 0:
            return -1000
        
        score = 0
        # Check all lines passing through this position
        for line in lines:
            if (r, c) in line:
                values = [board[row][col] for row, col in line]
                my_count = values.count(1)
                opp_count = values.count(-1)
                empty_count = values.count(0)
                
                # If opponent has pieces, this line is blocked for us
                if opp_count == 0:
                    score += my_count ** 2  # Reward building on our lines
                # If we have no pieces, but could block opponent
                if my_count == 0 and opp_count > 0:
                    score += opp_count  # Slight reward for blocking potential
        
        # Center bias
        center_distance = abs(r - 1.5) + abs(c - 1.5)
        score += (3 - center_distance) * 0.5
        
        return score
    
    # Find best move
    best_score = -float('inf')
    best_move = None
    
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                score = evaluate_position(r, c)
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    
    # If no move found (shouldn't happen), return first empty
    if best_move is None:
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    return (r, c)
    
    return best_move
