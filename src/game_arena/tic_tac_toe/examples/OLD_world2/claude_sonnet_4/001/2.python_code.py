
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_line_threat(line):
        """Check if a line of 4 positions has a winning/blocking opportunity"""
        if line.count(1) == 3 and line.count(0) == 1:
            return 1  # We can win
        if line.count(-1) == 3 and line.count(0) == 1:
            return -1  # Opponent can win, we must block
        return 0
    
    def get_all_lines():
        """Get all possible winning lines (rows, columns, diagonals)"""
        lines = []
        
        # Rows
        for i in range(4):
            lines.append([(i, j) for j in range(4)])
        
        # Columns
        for j in range(4):
            lines.append([(i, j) for i in range(4)])
        
        # Main diagonal
        lines.append([(i, i) for i in range(4)])
        
        # Anti-diagonal
        lines.append([(i, 3-i) for i in range(4)])
        
        return lines
    
    def find_critical_moves():
        """Find winning moves or blocking moves"""
        winning_moves = []
        blocking_moves = []
        
        for line_positions in get_all_lines():
            line_values = [board[r][c] for r, c in line_positions]
            threat_level = check_line_threat(line_values)
            
            if threat_level != 0:
                # Find the empty position in this line
                for pos, val in zip(line_positions, line_values):
                    if val == 0:
                        if threat_level == 1:
                            winning_moves.append(pos)
                        else:
                            blocking_moves.append(pos)
                        break
        
        return winning_moves, blocking_moves
    
    def evaluate_position(row, col):
        """Evaluate how good a position is strategically"""
        if board[row][col] != 0:
            return -1000  # Invalid move
        
        score = 0
        
        # Center positions are generally better
        center_distance = abs(row - 1.5) + abs(col - 1.5)
        score += (3 - center_distance) * 2
        
        # Count how many lines this position participates in
        lines_count = 0
        for line_positions in get_all_lines():
            if (row, col) in line_positions:
                lines_count += 1
        score += lines_count * 3
        
        # Bonus for positions that could create multiple threats
        temp_board = [row[:] for row in board]
        temp_board[row][col] = 1
        
        potential_threats = 0
        for line_positions in get_all_lines():
            line_values = [temp_board[r][c] for r, c in line_positions]
            if line_values.count(1) >= 2 and line_values.count(-1) == 0:
                potential_threats += 1
        
        score += potential_threats * 5
        
        return score
    
    # First, check for winning moves
    winning_moves, blocking_moves = find_critical_moves()
    
    if winning_moves:
        return winning_moves[0]
    
    if blocking_moves:
        return blocking_moves[0]
    
    # No critical moves, find the best strategic position
    best_score = -1000
    best_move = None
    
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                score = evaluate_position(i, j)
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    return best_move if best_move else (0, 0)
