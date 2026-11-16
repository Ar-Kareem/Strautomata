
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(b):
        """Check if there's a winner. Returns 1, -1, or 0."""
        # Check rows
        for row in b:
            if sum(row) == 4:
                return 1
            if sum(row) == -4:
                return -1
        
        # Check columns
        for col in range(4):
            s = sum(b[row][col] for row in range(4))
            if s == 4:
                return 1
            if s == -4:
                return -1
        
        # Check diagonals
        diag1 = sum(b[i][i] for i in range(4))
        diag2 = sum(b[i][3-i] for i in range(4))
        if diag1 == 4 or diag2 == 4:
            return 1
        if diag1 == -4 or diag2 == -4:
            return -1
        
        return 0
    
    def get_empty_cells(b):
        """Get all empty cells."""
        return [(i, j) for i in range(4) for j in range(4) if b[i][j] == 0]
    
    def evaluate(b):
        """Evaluate board position."""
        winner = check_winner(b)
        if winner != 0:
            return winner * 10000
        
        score = 0
        
        # Evaluate all lines (rows, cols, diagonals)
        lines = []
        # Rows
        for i in range(4):
            lines.append([b[i][j] for j in range(4)])
        # Columns
        for j in range(4):
            lines.append([b[i][j] for i in range(4)])
        # Diagonals
        lines.append([b[i][i] for i in range(4)])
        lines.append([b[i][3-i] for i in range(4)])
        
        for line in lines:
            ones = line.count(1)
            minus_ones = line.count(-1)
            zeros = line.count(0)
            
            # Line is still winnable
            if ones > 0 and minus_ones == 0:
                score += ones ** 2
            if minus_ones > 0 and ones == 0:
                score -= minus_ones ** 2
        
        return score
    
    def minimax(b, depth, alpha, beta, is_maximizing):
        """Minimax with alpha-beta pruning."""
        winner = check_winner(b)
        if winner != 0:
            return winner * (10000 + depth)  # Prefer faster wins
        
        empty = get_empty_cells(b)
        if not empty or depth == 0:
            return evaluate(b)
        
        if is_maximizing:
            max_eval = -float('inf')
            for i, j in empty:
                b[i][j] = 1
                eval_score = minimax(b, depth - 1, alpha, beta, False)
                b[i][j] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for i, j in empty:
                b[i][j] = -1
                eval_score = minimax(b, depth - 1, alpha, beta, True)
                b[i][j] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Find best move
    empty_cells = get_empty_cells(board)
    
    if not empty_cells:
        return (0, 0)
    
    # Adjust depth based on number of empty cells
    num_empty = len(empty_cells)
    if num_empty > 12:
        depth = 3
    elif num_empty > 8:
        depth = 4
    elif num_empty > 4:
        depth = 5
    else:
        depth = 8
    
    best_move = empty_cells[0]
    best_score = -float('inf')
    
    for i, j in empty_cells:
        board[i][j] = 1
        score = minimax(board, depth - 1, -float('inf'), float('inf'), False)
        board[i][j] = 0
        
        if score > best_score:
            best_score = score
            best_move = (i, j)
    
    return best_move
