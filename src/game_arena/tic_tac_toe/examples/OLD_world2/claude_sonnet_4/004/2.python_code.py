
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(board):
        # Check rows
        for row in board:
            if all(cell == 1 for cell in row):
                return 1
            if all(cell == -1 for cell in row):
                return -1
        
        # Check columns
        for col in range(4):
            if all(board[row][col] == 1 for row in range(4)):
                return 1
            if all(board[row][col] == -1 for row in range(4)):
                return -1
        
        # Check diagonals
        if all(board[i][i] == 1 for i in range(4)):
            return 1
        if all(board[i][i] == -1 for i in range(4)):
            return -1
        if all(board[i][3-i] == 1 for i in range(4)):
            return 1
        if all(board[i][3-i] == -1 for i in range(4)):
            return -1
        
        return 0
    
    def count_line_potential(board, player):
        score = 0
        
        # Check rows
        for row in board:
            count = sum(1 for cell in row if cell == player)
            empty = sum(1 for cell in row if cell == 0)
            if count > 0 and empty + count == 4:  # No opponent pieces
                score += count ** 2
        
        # Check columns
        for col in range(4):
            count = sum(1 for row in range(4) if board[row][col] == player)
            empty = sum(1 for row in range(4) if board[row][col] == 0)
            if count > 0 and empty + count == 4:
                score += count ** 2
        
        # Check diagonals
        count = sum(1 for i in range(4) if board[i][i] == player)
        empty = sum(1 for i in range(4) if board[i][i] == 0)
        if count > 0 and empty + count == 4:
            score += count ** 2
            
        count = sum(1 for i in range(4) if board[i][3-i] == player)
        empty = sum(1 for i in range(4) if board[i][3-i] == 0)
        if count > 0 and empty + count == 4:
            score += count ** 2
        
        return score
    
    def evaluate_board(board):
        winner = check_winner(board)
        if winner == 1:
            return 1000
        elif winner == -1:
            return -1000
        
        # Position values - center and inner positions are more valuable
        position_values = [
            [3, 4, 4, 3],
            [4, 6, 6, 4],
            [4, 6, 6, 4],
            [3, 4, 4, 3]
        ]
        
        score = 0
        for i in range(4):
            for j in range(4):
                if board[i][j] == 1:
                    score += position_values[i][j]
                elif board[i][j] == -1:
                    score -= position_values[i][j]
        
        # Add line potential
        score += count_line_potential(board, 1) * 5
        score -= count_line_potential(board, -1) * 5
        
        return score
    
    def get_empty_positions(board):
        return [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        winner = check_winner(board)
        if winner != 0:
            return winner * 1000
        
        empty_positions = get_empty_positions(board)
        if not empty_positions or depth == 0:
            return evaluate_board(board)
        
        if maximizing_player:
            max_eval = float('-inf')
            for row, col in empty_positions:
                board[row][col] = 1
                eval_score = minimax(board, depth - 1, alpha, beta, False)
                board[row][col] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for row, col in empty_positions:
                board[row][col] = -1
                eval_score = minimax(board, depth - 1, alpha, beta, True)
                board[row][col] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Check for immediate win
    empty_positions = get_empty_positions(board)
    for row, col in empty_positions:
        board[row][col] = 1
        if check_winner(board) == 1:
            board[row][col] = 0
            return (row, col)
        board[row][col] = 0
    
    # Check for blocking opponent win
    for row, col in empty_positions:
        board[row][col] = -1
        if check_winner(board) == -1:
            board[row][col] = 0
            return (row, col)
        board[row][col] = 0
    
    # Use minimax for best move
    best_score = float('-inf')
    best_move = empty_positions[0]
    
    # Adjust depth based on game state
    empty_count = len(empty_positions)
    if empty_count <= 8:
        depth = 6
    elif empty_count <= 12:
        depth = 4
    else:
        depth = 3
    
    for row, col in empty_positions:
        board[row][col] = 1
        score = minimax(board, depth, float('-inf'), float('inf'), False)
        board[row][col] = 0
        
        if score > best_score:
            best_score = score
            best_move = (row, col)
    
    return best_move
