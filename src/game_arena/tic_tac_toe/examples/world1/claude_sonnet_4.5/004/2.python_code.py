
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(b):
        # Check rows, columns, and diagonals
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] != 0:
                return b[i][0]
            if b[0][i] == b[1][i] == b[2][i] != 0:
                return b[0][i]
        if b[0][0] == b[1][1] == b[2][2] != 0:
            return b[0][0]
        if b[0][2] == b[1][1] == b[2][0] != 0:
            return b[0][2]
        return 0
    
    def is_full(b):
        return all(b[i][j] != 0 for i in range(3) for j in range(3))
    
    def minimax(b, is_maximizing):
        winner = check_winner(b)
        if winner == 1:
            return 10
        if winner == -1:
            return -10
        if is_full(b):
            return 0
        
        if is_maximizing:
            best_score = -float('inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = 1
                        score = minimax(b, False)
                        b[i][j] = 0
                        best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = -1
                        score = minimax(b, True)
                        b[i][j] = 0
                        best_score = min(score, best_score)
            return best_score
    
    # Find the best move
    best_score = -float('inf')
    best_move = None
    
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, False)
                board[i][j] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    # If no move found (shouldn't happen), return first empty cell
    if best_move is None:
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return (i, j)
    
    return best_move
