
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
        for i in range(3):
            for j in range(3):
                if b[i][j] == 0:
                    return False
        return True
    
    def get_empty_cells(b):
        empty = []
        for i in range(3):
            for j in range(3):
                if b[i][j] == 0:
                    empty.append((i, j))
        return empty
    
    def minimax(b, depth, is_maximizing, alpha, beta):
        winner = check_winner(b)
        
        # Terminal states
        if winner == 1:  # I win
            return 1
        elif winner == -1:  # Opponent wins
            return -1
        elif is_full(b):  # Draw
            return 0
        
        if is_maximizing:  # My turn (player 1)
            max_eval = float('-inf')
            for i, j in get_empty_cells(b):
                b[i][j] = 1
                eval_score = minimax(b, depth + 1, False, alpha, beta)
                b[i][j] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:  # Opponent's turn (player -1)
            min_eval = float('inf')
            for i, j in get_empty_cells(b):
                b[i][j] = -1
                eval_score = minimax(b, depth + 1, True, alpha, beta)
                b[i][j] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Find the best move
    best_score = float('-inf')
    best_move = None
    
    empty_cells = get_empty_cells(board)
    
    # If it's the first move, take center or corner for efficiency
    if len(empty_cells) == 9:
        return (1, 1)  # Center
    
    for i, j in empty_cells:
        board[i][j] = 1
        score = minimax(board, 0, False, float('-inf'), float('inf'))
        board[i][j] = 0
        
        if score > best_score:
            best_score = score
            best_move = (i, j)
    
    return best_move
