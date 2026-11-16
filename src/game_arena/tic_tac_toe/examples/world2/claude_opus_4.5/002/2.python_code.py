
def policy(board: list[list[int]]) -> tuple[int, int]:
    # All lines that can win (4 in a row)
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
    
    def check_winner(b):
        for line in lines:
            vals = [b[r][c] for r, c in line]
            if all(v == 1 for v in vals):
                return 1
            if all(v == -1 for v in vals):
                return -1
        return 0
    
    def get_empty(b):
        return [(i, j) for i in range(4) for j in range(4) if b[i][j] == 0]
    
    def evaluate(b):
        winner = check_winner(b)
        if winner != 0:
            return winner * 100000
        
        score = 0
        for line in lines:
            vals = [b[r][c] for r, c in line]
            ones = vals.count(1)
            neg_ones = vals.count(-1)
            if neg_ones == 0 and ones > 0:
                score += 10 ** ones
            if ones == 0 and neg_ones > 0:
                score -= 10 ** neg_ones
        return score
    
    def minimax(b, depth, alpha, beta, maximizing):
        winner = check_winner(b)
        if winner != 0:
            return winner * (100000 + depth), None
        
        empty = get_empty(b)
        if not empty:
            return 0, None
        if depth == 0:
            return evaluate(b), None
        
        if maximizing:
            max_eval = float('-inf')
            best_move = empty[0]
            for (r, c) in empty:
                b[r][c] = 1
                eval_score, _ = minimax(b, depth - 1, alpha, beta, False)
                b[r][c] = 0
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = (r, c)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = empty[0]
            for (r, c) in empty:
                b[r][c] = -1
                eval_score, _ = minimax(b, depth - 1, alpha, beta, True)
                b[r][c] = 0
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = (r, c)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    # Convert board to mutable list
    board_copy = [list(row) for row in board]
    
    # Check for immediate win
    for (r, c) in get_empty(board_copy):
        board_copy[r][c] = 1
        if check_winner(board_copy) == 1:
            return (r, c)
        board_copy[r][c] = 0
    
    # Check for immediate block
    for (r, c) in get_empty(board_copy):
        board_copy[r][c] = -1
        if check_winner(board_copy) == -1:
            board_copy[r][c] = 0
            return (r, c)
        board_copy[r][c] = 0
    
    # Determine search depth based on empty squares
    empty_count = len(get_empty(board_copy))
    if empty_count <= 6:
        depth = 12
    elif empty_count <= 9:
        depth = 8
    elif empty_count <= 12:
        depth = 6
    else:
        depth = 5
    
    _, move = minimax(board_copy, depth, float('-inf'), float('inf'), True)
    return move
