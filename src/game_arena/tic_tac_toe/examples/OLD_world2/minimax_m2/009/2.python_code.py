
def policy(board: list[list[int]]) -> tuple[int, int]:
    lines = [
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(3, 0), (3, 1), (3, 2), (3, 3)],
        [(0, 0), (1, 0), (2, 0), (3, 0)],
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(0, 3), (1, 3), (2, 3), (3, 3)],
        [(0, 0), (1, 1), (2, 2), (3, 3)],
        [(0, 3), (1, 2), (2, 1), (3, 0)]
    ]
    
    def is_game_over(board):
        for line in lines:
            count_our = 0
            count_opp = 0
            for (r, c) in line:
                if board[r][c] == 1:
                    count_our += 1
                elif board[r][c] == -1:
                    count_opp += 1
            if count_our == 4:
                return 1
            if count_opp == 4:
                return -1
        return 0
    
    def evaluate(board):
        score = 0
        for line in lines:
            count_our = 0
            count_opp = 0
            for (r, c) in line:
                if board[r][c] == 1:
                    count_our += 1
                elif board[r][c] == -1:
                    count_opp += 1
            if count_our == 4:
                score += 1000000
            elif count_our == 3:
                score += 1000
            elif count_our == 2:
                score += 100
            elif count_our == 1:
                score += 10
            if count_opp == 4:
                score -= 1000000
            elif count_opp == 3:
                score -= 1000
            elif count_opp == 2:
                score -= 100
            elif count_opp == 1:
                score -= 10
        return score
    
    def minimax(board, depth, alpha, beta, is_maximizing):
        game_result = is_game_over(board)
        if game_result != 0:
            return 1000000 if game_result == 1 else -1000000
        if depth == 0:
            return evaluate(board)
            
        if is_maximizing:
            max_eval = -float('inf')
            for r in range(4):
                for c in range(4):
                    if board[r][c] == 0:
                        board[r][c] = 1
                        eval_score = minimax(board, depth-1, alpha, beta, False)
                        board[r][c] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for r in range(4):
                for c in range(4):
                    if board[r][c] == 0:
                        board[r][c] = -1
                        eval_score = minimax(board, depth-1, alpha, beta, True)
                        board[r][c] = 0
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return min_eval
    
    # Check for our immediate win
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = 1
                if is_game_over(board) == 1:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0
    
    # Check for opponent's immediate win and block
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = -1
                if is_game_over(board) == -1:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0
    
    # Use minimax to find the best move
    best_move = None
    best_score = -float('inf')
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = 1
                score = minimax(board, depth=3, alpha=-float('inf'), beta=float('inf'), is_maximizing=False)
                board[r][c] = 0
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    
    if best_move is None:
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    return (r, c)
    return best_move
