
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    4x4 Tic Tac Toe policy that tries to win, block, or make strategic moves.
    """
    
    def check_line(line):
        """Check a line (row, col, or diagonal) for winning/blocking opportunities."""
        player_count = sum(1 for x in line if x == 1)
        opponent_count = sum(1 for x in line if x == -1)
        empty_count = sum(1 for x in line if x == 0)
        return player_count, opponent_count, empty_count
    
    def get_lines_with_positions(board):
        """Get all lines (rows, cols, diags) with their positions."""
        lines = []
        
        # Rows
        for i in range(4):
            lines.append([(i, j) for j in range(4)])
        
        # Columns
        for j in range(4):
            lines.append([(i, j) for i in range(4)])
        
        # Diagonals
        lines.append([(i, i) for i in range(4)])
        lines.append([(i, 3-i) for i in range(4)])
        
        return lines
    
    def evaluate_move(row, col, board):
        """Evaluate a move based on potential winning lines."""
        if board[row][col] != 0:
            return -1000
        
        score = 0
        lines = get_lines_with_positions(board)
        
        for line_positions in lines:
            if (row, col) not in line_positions:
                continue
            
            line_values = [board[r][c] for r, c in line_positions]
            player_count = sum(1 for x in line_values if x == 1)
            opponent_count = sum(1 for x in line_values if x == -1)
            
            # Don't count mixed lines
            if player_count > 0 and opponent_count > 0:
                continue
            
            # Prioritize winning
            if player_count == 3:
                score += 10000
            elif player_count == 2:
                score += 100
            elif player_count == 1:
                score += 10
            
            # Block opponent
            if opponent_count == 3:
                score += 5000
            elif opponent_count == 2:
                score += 50
            elif opponent_count == 1:
                score += 5
        
        # Prefer center positions
        if (row, col) in [(1, 1), (1, 2), (2, 1), (2, 2)]:
            score += 3
        
        return score
    
    # Find the best move
    best_score = -1
    best_move = None
    
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                score = evaluate_move(i, j, board)
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    # Fallback: return first empty cell
    if best_move is None:
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    return (i, j)
    
    return best_move
