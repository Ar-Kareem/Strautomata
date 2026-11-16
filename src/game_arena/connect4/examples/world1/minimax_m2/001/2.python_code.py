
def policy(board):
    lines = []
    # Horizontal lines
    for i in range(6):
        for j in range(4):
            lines.append([(i, j), (i, j+1), (i, j+2), (i, j+3)])
    # Vertical lines
    for j in range(7):
        for i in range(3):
            lines.append([(i, j), (i+1, j), (i+2, j), (i+3, j)])
    # Diagonal down-right
    for i in range(3):
        for j in range(4):
            lines.append([(i, j), (i+1, j+1), (i+2, j+2), (i+3, j+3)])
    # Diagonal up-right
    for i in range(3, 6):
        for j in range(4):
            lines.append([(i, j), (i-1, j+1), (i-2, j+2), (i-3, j+3)])
    
    def get_available_columns(board):
        available = []
        for col in range(7):
            if board[0][col] == 0:
                available.append(col)
        return available
    
    def make_move(board, col, player):
        new_board = [row[:] for row in board]
        for row in range(5, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                break
        return new_board
    
    def evaluate(board):
        for line in lines:
            count_current = 0
            count_opponent = 0
            for (i, j) in line:
                cell = board[i][j]
                if cell == 1:
                    count_current += 1
                elif cell == -1:
                    count_opponent += 1
            if count_current == 4:
                return 100000
            if count_opponent == 4:
                return -100000
        
        score = 0
        for line in lines:
            count_current = 0
            count_opponent = 0
            for (i, j) in line:
                cell = board[i][j]
                if cell == 1:
                    count_current += 1
                elif cell == -1:
                    count_opponent += 1
            if count_current == 3:
                score += 1000
            elif count_current == 2:
                score += 30
            elif count_current == 1:
                score += 10
            if count_opponent == 3:
                score -= 1000
            elif count_opponent == 2:
                score -= 30
            elif count_opponent == 1:
                score -= 10
        return score
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        if depth == 0:
            return evaluate(board)
        available_columns = get_available_columns(board)
        if maximizing_player:
            max_eval = -float('inf')
            for col in available_columns:
                new_board = make_move(board, col, 1)
                eval_score = minimax(new_board, depth-1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for col in available_columns:
                new_board = make_move(board, col, -1)
                eval_score = minimax(new_board, depth-1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    available_columns = get_available_columns(board)
    best_col = None
    best_score = -float('inf')
    for col in available_columns:
        new_board = make_move(board, col, 1)
        score = minimax(new_board, 1, -float('inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_col = col
    return best_col
