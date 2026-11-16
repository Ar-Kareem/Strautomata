
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(board):
        """Check if there's a winner. Returns 1, -1, or 0"""
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
    
    def get_empty_cells(board):
        """Get list of empty cell coordinates"""
        empty = []
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    empty.append((i, j))
        return empty
    
    def count_line_potential(board, player):
        """Count potential winning lines for a player"""
        score = 0
        
        # Check rows
        for row in board:
            if -player not in row:  # No opponent pieces blocking
                player_count = row.count(player)
                if player_count > 0:
                    score += player_count ** 2
        
        # Check columns
        for col in range(4):
            column = [board[row][col] for row in range(4)]
            if -player not in column:
                player_count = column.count(player)
                if player_count > 0:
                    score += player_count ** 2
        
        # Check diagonals
        diag1 = [board[i][i] for i in range(4)]
        if -player not in diag1:
            player_count = diag1.count(player)
            if player_count > 0:
                score += player_count ** 2
        
        diag2 = [board[i][3-i] for i in range(4)]
        if -player not in diag2:
            player_count = diag2.count(player)
            if player_count > 0:
                score += player_count ** 2
        
        return score
    
    def evaluate_board(board):
        """Evaluate board position"""
        winner = check_winner(board)
        if winner == 1:
            return 1000
        if winner == -1:
            return -1000
        
        # Evaluate based on potential
        my_potential = count_line_potential(board, 1)
        opp_potential = count_line_potential(board, -1)
        
        # Add center control bonus
        center_bonus = 0
        for i in [1, 2]:
            for j in [1, 2]:
                if board[i][j] == 1:
                    center_bonus += 5
                elif board[i][j] == -1:
                    center_bonus -= 5
        
        return my_potential - opp_potential + center_bonus
    
    def can_win_next(board, player):
        """Check if player can win in next move"""
        for i, j in get_empty_cells(board):
            board[i][j] = player
            if check_winner(board) == player:
                board[i][j] = 0
                return (i, j)
            board[i][j] = 0
        return None
    
    def minimax(board, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning"""
        winner = check_winner(board)
        if winner != 0 or depth == 0:
            return evaluate_board(board)
        
        empty_cells = get_empty_cells(board)
        if not empty_cells:
            return 0
        
        if maximizing:
            max_eval = float('-inf')
            for i, j in empty_cells:
                board[i][j] = 1
                eval_score = minimax(board, depth - 1, alpha, beta, False)
                board[i][j] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for i, j in empty_cells:
                board[i][j] = -1
                eval_score = minimax(board, depth - 1, alpha, beta, True)
                board[i][j] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Check for immediate win
    win_move = can_win_next(board, 1)
    if win_move:
        return win_move
    
    # Check for immediate block
    block_move = can_win_next(board, -1)
    if block_move:
        return block_move
    
    # Use minimax to find best move
    empty_cells = get_empty_cells(board)
    if not empty_cells:
        return (0, 0)  # Should not happen in valid game
    
    best_move = empty_cells[0]
    best_score = float('-inf')
    
    # Limit search depth based on remaining moves
    depth = min(4, len(empty_cells))
    
    for i, j in empty_cells:
        board[i][j] = 1
        score = minimax(board, depth - 1, float('-inf'), float('inf'), False)
        board[i][j] = 0
        
        if score > best_score:
            best_score = score
            best_move = (i, j)
    
    return best_move
