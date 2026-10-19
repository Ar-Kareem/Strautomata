
def policy(board: list[list[int]]) -> tuple[int, int]:
    
    def check_winner(b):
        # Check rows
        for i in range(4):
            if sum(b[i]) == 4:
                return 1
            if sum(b[i]) == -4:
                return -1
        # Check columns
        for j in range(4):
            col_sum = sum(b[i][j] for i in range(4))
            if col_sum == 4:
                return 1
            if col_sum == -4:
                return -1
        # Check diagonals
        diag1 = sum(b[i][i] for i in range(4))
        if diag1 == 4:
            return 1
        if diag1 == -4:
            return -1
        diag2 = sum(b[i][3-i] for i in range(4))
        if diag2 == 4:
            return 1
        if diag2 == -4:
            return -1
        return 0
    
    def get_empty_cells(b):
        return [(i, j) for i in range(4) for j in range(4) if b[i][j] == 0]
    
    def evaluate(b):
        score = 0
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
            neg_ones = line.count(-1)
            if neg_ones == 0 and ones > 0:
                score += ones ** 2
            if ones == 0 and neg_ones > 0:
                score -= neg_ones ** 2
        return score
    
    def minimax(b, depth, alpha, beta, maximizing):
        winner = check_winner(b)
        if winner == 1:
            return 10000 + depth
        if winner == -1:
            return -10000 - depth
        
        empty = get_empty_cells(b)
        if not empty or depth == 0:
            return evaluate(b)
        
        if maximizing:
            max_eval = float('-inf')
            for (i, j) in empty:
                b[i][j] = 1
                eval_score = minimax(b, depth-1, alpha, beta, False)
                b[i][j] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for (i, j) in empty:
                b[i][j] = -1
                eval_score = minimax(b, depth-1, alpha, beta, True)
                b[i][j] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    empty = get_empty_cells(board)
    
    if not empty:
        return (0, 0)
    
    # Check immediate wins and blocks
    for (i, j) in empty:
        board[i][j] = 1
        if check_winner(board) == 1:
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0
    
    for (i, j) in empty:
        board[i][j] = -1
        if check_winner(board) == -1:
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0
    
    # Adaptive depth based on remaining empty cells
    num_empty = len(empty)
    if num_empty > 12:
        depth = 5
    elif num_empty > 8:
        depth = 6
    elif num_empty > 5:
        depth = 7
    else:
        depth = 10
    
    best_move = empty[0]
    best_val = float('-inf')
    
    # Prioritize center cells
    center_priority = [(1,1), (1,2), (2,1), (2,2)]
    sorted_empty = sorted(empty, key=lambda x: (0 if x in center_priority else 1))
    
    for (i, j) in sorted_empty:
        board[i][j] = 1
        val = minimax(board, depth, float('-inf'), float('inf'), False)
        board[i][j] = 0
        if val > best_val:
            best_val = val
            best_move = (i, j)
        if best_val > 9000:  # Found winning path
            break
    
    return best_move
