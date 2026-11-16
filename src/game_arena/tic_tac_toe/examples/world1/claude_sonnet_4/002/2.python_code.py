
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(b):
        # Check rows
        for row in b:
            if row[0] == row[1] == row[2] != 0:
                return row[0]
        
        # Check columns
        for col in range(3):
            if b[0][col] == b[1][col] == b[2][col] != 0:
                return b[0][col]
        
        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2] != 0:
            return b[0][0]
        if b[0][2] == b[1][1] == b[2][0] != 0:
            return b[0][2]
        
        return 0
    
    def is_full(b):
        for row in b:
            if 0 in row:
                return False
        return True
    
    def get_empty_cells(b):
        cells = []
        for i in range(3):
            for j in range(3):
                if b[i][j] == 0:
                    cells.append((i, j))
        return cells
    
    def minimax(b, depth, is_maximizing, alpha, beta):
        winner = check_winner(b)
        
        # Terminal states
        if winner == 1:  # I win
            return 1
        elif winner == -1:  # Opponent wins
            return -1
        elif is_full(b):  # Draw
            return 0
        
        if is_maximizing:  # My turn
            max_eval = -2
            for row, col in get_empty_cells(b):
                b[row][col] = 1
                eval_score = minimax(b, depth + 1, False, alpha, beta)
                b[row][col] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:  # Opponent's turn
            min_eval = 2
            for row, col in get_empty_cells(b):
                b[row][col] = -1
                eval_score = minimax(b, depth + 1, True, alpha, beta)
                b[row][col] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Find the best move
    best_score = -2
    best_move = None
    
    for row, col in get_empty_cells(board):
        board[row][col] = 1
        score = minimax(board, 0, False, -2, 2)
        board[row][col] = 0
        
        if score > best_score:
            best_score = score
            best_move = (row, col)
    
    return best_move
