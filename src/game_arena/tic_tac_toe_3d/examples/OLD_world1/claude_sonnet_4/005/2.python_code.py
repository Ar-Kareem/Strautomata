
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def get_empty_cells(board):
        empty = []
        for z in range(3):
            for y in range(3):
                for x in range(3):
                    if board[z][y][x] == 0:
                        empty.append((z, y, x))
        return empty
    
    def check_winner(board):
        # Check all possible winning lines in 3D
        lines = []
        
        # Rows (along x-axis)
        for z in range(3):
            for y in range(3):
                lines.append([(z, y, 0), (z, y, 1), (z, y, 2)])
        
        # Columns (along y-axis)
        for z in range(3):
            for x in range(3):
                lines.append([(z, 0, x), (z, 1, x), (z, 2, x)])
        
        # Verticals (along z-axis)
        for y in range(3):
            for x in range(3):
                lines.append([(0, y, x), (1, y, x), (2, y, x)])
        
        # Face diagonals (xy plane)
        for z in range(3):
            lines.append([(z, 0, 0), (z, 1, 1), (z, 2, 2)])
            lines.append([(z, 0, 2), (z, 1, 1), (z, 2, 0)])
        
        # Face diagonals (xz plane)
        for y in range(3):
            lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
            lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
        
        # Face diagonals (yz plane)
        for x in range(3):
            lines.append([(0, 0, x), (1, 1, x), (2, 2, x)])
            lines.append([(0, 2, x), (1, 1, x), (2, 0, x)])
        
        # Space diagonals
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
        
        for line in lines:
            values = [board[z][y][x] for z, y, x in line]
            if values == [1, 1, 1]:
                return 1
            elif values == [-1, -1, -1]:
                return -1
        
        return 0
    
    def evaluate_line(line_values):
        # Evaluate a line for strategic value
        if line_values.count(1) == 2 and line_values.count(0) == 1:
            return 100  # Win opportunity
        elif line_values.count(-1) == 2 and line_values.count(0) == 1:
            return -100  # Block opponent
        elif line_values.count(1) == 1 and line_values.count(0) == 2:
            return 10  # Build opportunity
        elif line_values.count(-1) == 1 and line_values.count(0) == 2:
            return -10  # Opponent building
        return 0
    
    def evaluate_board(board):
        if check_winner(board) == 1:
            return 1000
        elif check_winner(board) == -1:
            return -1000
        
        score = 0
        lines = get_all_lines()
        
        for line in lines:
            values = [board[z][y][x] for z, y, x in line]
            score += evaluate_line(values)
        
        # Bonus for center control
        if board[1][1][1] == 1:
            score += 30
        elif board[1][1][1] == -1:
            score -= 30
        
        return score
    
    def get_all_lines():
        lines = []
        
        # All the same lines as in check_winner
        for z in range(3):
            for y in range(3):
                lines.append([(z, y, 0), (z, y, 1), (z, y, 2)])
        
        for z in range(3):
            for x in range(3):
                lines.append([(z, 0, x), (z, 1, x), (z, 2, x)])
        
        for y in range(3):
            for x in range(3):
                lines.append([(0, y, x), (1, y, x), (2, y, x)])
        
        for z in range(3):
            lines.append([(z, 0, 0), (z, 1, 1), (z, 2, 2)])
            lines.append([(z, 0, 2), (z, 1, 1), (z, 2, 0)])
        
        for y in range(3):
            lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
            lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
        
        for x in range(3):
            lines.append([(0, 0, x), (1, 1, x), (2, 2, x)])
            lines.append([(0, 2, x), (1, 1, x), (2, 0, x)])
        
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
        
        return lines
    
    def minimax(board, depth, maximizing_player, alpha, beta):
        winner = check_winner(board)
        if winner != 0:
            return winner * 1000
        
        empty_cells = get_empty_cells(board)
        if not empty_cells or depth == 0:
            return evaluate_board(board)
        
        if maximizing_player:
            max_eval = float('-inf')
            for z, y, x in empty_cells:
                board[z][y][x] = 1
                eval_score = minimax(board, depth - 1, False, alpha, beta)
                board[z][y][x] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for z, y, x in empty_cells:
                board[z][y][x] = -1
                eval_score = minimax(board, depth - 1, True, alpha, beta)
                board[z][y][x] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Quick win/block check
    empty_cells = get_empty_cells(board)
    
    for z, y, x in empty_cells:
        # Check if we can win
        board[z][y][x] = 1
        if check_winner(board) == 1:
            board[z][y][x] = 0
            return (z, y, x)
        board[z][y][x] = 0
        
        # Check if we need to block
        board[z][y][x] = -1
        if check_winner(board) == -1:
            board[z][y][x] = 0
            return (z, y, x)
        board[z][y][x] = 0
    
    # Use minimax for strategic play
    best_move = None
    best_score = float('-inf')
    
    # Prioritize center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # Use minimax with limited depth for performance
    depth = min(4, len(empty_cells))
    
    for z, y, x in empty_cells:
        board[z][y][x] = 1
        score = minimax(board, depth - 1, False, float('-inf'), float('inf'))
        board[z][y][x] = 0
        
        if score > best_score:
            best_score = score
            best_move = (z, y, x)
    
    return best_move if best_move else empty_cells[0]
