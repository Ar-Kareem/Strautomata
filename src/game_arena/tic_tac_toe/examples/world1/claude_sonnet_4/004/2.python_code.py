
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(board):
        # Check rows
        for row in board:
            if row[0] == row[1] == row[2] != 0:
                return row[0]
        
        # Check columns
        for col in range(3):
            if board[0][col] == board[1][col] == board[2][col] != 0:
                return board[0][col]
        
        # Check diagonals
        if board[0][0] == board[1][1] == board[2][2] != 0:
            return board[0][0]
        if board[0][2] == board[1][1] == board[2][0] != 0:
            return board[0][2]
        
        return 0
    
    def is_board_full(board):
        return all(board[i][j] != 0 for i in range(3) for j in range(3))
    
    def minimax(board, depth, is_maximizing, alpha, beta):
        winner = check_winner(board)
        
        # Terminal conditions
        if winner == 1:  # I win
            return 10 - depth
        elif winner == -1:  # Opponent wins
            return -10 + depth
        elif is_board_full(board):  # Draw
            return 0
        
        if is_maximizing:  # My turn
            max_eval = float('-inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = 1
                        eval_score = minimax(board, depth + 1, False, alpha, beta)
                        board[i][j] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return max_eval
        else:  # Opponent's turn
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = -1
                        eval_score = minimax(board, depth + 1, True, alpha, beta)
                        board[i][j] = 0
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return min_eval
    
    # Find the best move
    best_score = float('-inf')
    best_moves = []
    
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, 0, False, float('-inf'), float('inf'))
                board[i][j] = 0
                
                if score > best_score:
                    best_score = score
                    best_moves = [(i, j)]
                elif score == best_score:
                    best_moves.append((i, j))
    
    # If multiple moves have the same score, prefer center, then corners, then edges
    priority_positions = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]
    
    for pos in priority_positions:
        if pos in best_moves:
            return pos
    
    return best_moves[0] if best_moves else (0, 0)
