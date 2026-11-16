
def policy(board: list[list[int]]) -> tuple[int, int]:
    def get_empty_cells(b):
        return [(i, j) for i in range(4) for j in range(4) if b[i][j] == 0]
    
    def check_winner(b):
        # Check rows
        for i in range(4):
            if b[i][0] != 0 and b[i][0] == b[i][1] == b[i][2] == b[i][3]:
                return b[i][0]
        # Check columns
        for j in range(4):
            if b[0][j] != 0 and b[0][j] == b[1][j] == b[2][j] == b[3][j]:
                return b[0][j]
        # Check diagonals
        if b[0][0] != 0 and b[0][0] == b[1][1] == b[2][2] == b[3][3]:
            return b[0][0]
        if b[0][3] != 0 and b[0][3] == b[1][2] == b[2][1] == b[3][0]:
            return b[0][3]
        return 0
    
    def evaluate_line(line):
        ones = line.count(1)
        neg_ones = line.count(-1)
        if ones > 0 and neg_ones > 0:
            return 0  # Blocked line
        if ones > 0:
            return 10 ** ones
        if neg_ones > 0:
            return -(10 ** neg_ones)
        return 0
    
    def evaluate(b):
        score = 0
        # Rows
        for i in range(4):
            score += evaluate_line([b[i][j] for j in range(4)])
        # Columns
        for j in range(4):
            score += evaluate_line([b[i][j] for i in range(4)])
        # Diagonals
        score += evaluate_line([b[i][i] for i in range(4)])
        score += evaluate_line([b[i][3-i] for i in range(4)])
        return score
    
    def minimax(b, depth, alpha, beta, is_maximizing):
        winner = check_winner(b)
        if winner == 1:
            return 100000 + depth
        if winner == -1:
            return -100000 - depth
        
        empty = get_empty_cells(b)
        if not empty:
            return 0  # Draw
        if depth == 0:
            return evaluate(b)
        
        if is_maximizing:
            max_eval = float('-inf')
            for (i, j) in empty:
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
            for (i, j) in empty:
                b[i][j] = -1
                eval_score = minimax(b, depth - 1, alpha, beta, True)
                b[i][j] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    empty_cells = get_empty_cells(board)
    
    if not empty_cells:
        return (0, 0)  # Should not happen
    
    # Adjust depth based on number of empty cells
    num_empty = len(empty_cells)
    if num_empty > 12:
        depth = 5
    elif num_empty > 8:
        depth = 6
    elif num_empty > 5:
        depth = 8
    else:
        depth = 12
    
    best_move = empty_cells[0]
    best_score = float('-inf')
    
    # Move ordering: prioritize center and corners
    def move_priority(cell):
        i, j = cell
        if (i, j) in [(1, 1), (1, 2), (2, 1), (2, 2)]:
            return 0
        if (i, j) in [(0, 0), (0, 3), (3, 0), (3, 3)]:
            return 1
        return 2
    
    sorted_cells = sorted(empty_cells, key=move_priority)
    
    for (i, j) in sorted_cells:
        board[i][j] = 1
        score = minimax(board, depth, float('-inf'), float('inf'), False)
        board[i][j] = 0
        if score > best_score:
            best_score = score
            best_move = (i, j)
        # Early exit if we found a winning move
        if best_score >= 100000:
            break
    
    return best_move
