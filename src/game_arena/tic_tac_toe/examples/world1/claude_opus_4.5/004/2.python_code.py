
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Make a deep copy to avoid modifying the original
    b = [row[:] for row in board]
    
    def check_winner(board):
        # Check rows
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] != 0:
                return board[i][0]
        # Check columns
        for j in range(3):
            if board[0][j] == board[1][j] == board[2][j] != 0:
                return board[0][j]
        # Check diagonals
        if board[0][0] == board[1][1] == board[2][2] != 0:
            return board[0][0]
        if board[0][2] == board[1][1] == board[2][0] != 0:
            return board[0][2]
        return 0
    
    def is_full(board):
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return False
        return True
    
    def minimax(board, is_maximizing, alpha, beta):
        winner = check_winner(board)
        if winner == 1:
            return 1
        if winner == -1:
            return -1
        if is_full(board):
            return 0
        
        if is_maximizing:
            best = -float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = 1
                        score = minimax(board, False, alpha, beta)
                        board[i][j] = 0
                        best = max(best, score)
                        alpha = max(alpha, score)
                        if beta <= alpha:
                            return best
            return best
        else:
            best = float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = -1
                        score = minimax(board, True, alpha, beta)
                        board[i][j] = 0
                        best = min(best, score)
                        beta = min(beta, score)
                        if beta <= alpha:
                            return best
            return best
    
    # Find best move
    best_score = -float('inf')
    best_move = None
    
    for i in range(3):
        for j in range(3):
            if b[i][j] == 0:
                b[i][j] = 1
                score = minimax(b, False, -float('inf'), float('inf'))
                b[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    return best_move
