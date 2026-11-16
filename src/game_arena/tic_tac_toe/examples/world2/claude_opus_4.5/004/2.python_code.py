
def policy(board: list[list[int]]) -> tuple[int, int]:
    def get_lines():
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
    
    LINES = get_lines()
    
    def check_winner(board):
        for line in LINES:
            values = [board[r][c] for r, c in line]
            if all(v == 1 for v in values):
                return 1
            if all(v == -1 for v in values):
                return -1
        return 0
    
    def get_empty_cells(board):
        return [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    
    def is_terminal(board):
        if check_winner(board) != 0:
            return True
        return len(get_empty_cells(board)) == 0
    
    def evaluate(board):
        winner = check_winner(board)
        if winner != 0:
            return winner * 10000
        
        score = 0
        for line in LINES:
            values = [board[r][c] for r, c in line]
            my_count = values.count(1)
            opp_count = values.count(-1)
            if opp_count == 0 and my_count > 0:
                score += 10 ** my_count
            elif my_count == 0 and opp_count > 0:
                score -= 10 ** opp_count
        return score
    
    def minimax(board, depth, alpha, beta, maximizing):
        if depth == 0 or is_terminal(board):
            return evaluate(board), None
        
        empty = get_empty_cells(board)
        
        # Move ordering: prioritize center and near-winning moves
        def move_priority(move):
            r, c = move
            board[r][c] = 1 if maximizing else -1
            score = evaluate(board)
            board[r][c] = 0
            return -score if maximizing else score
        
        empty.sort(key=move_priority)
        
        if maximizing:
            max_eval = float('-inf')
            best_move = empty[0] if empty else None
            for r, c in empty:
                board[r][c] = 1
                eval_score, _ = minimax(board, depth - 1, alpha, beta, False)
                board[r][c] = 0
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = (r, c)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = empty[0] if empty else None
            for r, c in empty:
                board[r][c] = -1
                eval_score, _ = minimax(board, depth - 1, alpha, beta, True)
                board[r][c] = 0
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = (r, c)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    # Make a working copy
    board_copy = [row[:] for row in board]
    
    empty_count = len(get_empty_cells(board_copy))
    
    # Adaptive depth based on game state
    if empty_count <= 6:
        depth = empty_count  # Solve endgame exactly
    elif empty_count <= 10:
        depth = 8
    else:
        depth = 6
    
    _, best_move = minimax(board_copy, depth, float('-inf'), float('inf'), True)
    
    if best_move is None:
        empty = get_empty_cells(board_copy)
        return empty[0] if empty else (0, 0)
    
    return best_move
