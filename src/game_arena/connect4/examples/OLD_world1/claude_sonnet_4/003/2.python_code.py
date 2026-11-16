
def policy(board: list[list[int]]) -> int:
    """
    Connect 4 targeting policy using minimax with alpha-beta pruning.
    """
    
    def is_valid_move(board, col):
        return board[0][col] == 0
    
    def get_valid_moves(board):
        return [col for col in range(7) if is_valid_move(board, col)]
    
    def drop_disc(board, col, player):
        new_board = [row[:] for row in board]
        for row in range(5, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                return new_board
        return None
    
    def check_winner(board):
        # Check horizontal
        for row in range(6):
            for col in range(4):
                if board[row][col] != 0 and all(board[row][col] == board[row][col + i] for i in range(4)):
                    return board[row][col]
        
        # Check vertical
        for row in range(3):
            for col in range(7):
                if board[row][col] != 0 and all(board[row][col] == board[row + i][col] for i in range(4)):
                    return board[row][col]
        
        # Check diagonal (top-left to bottom-right)
        for row in range(3):
            for col in range(4):
                if board[row][col] != 0 and all(board[row][col] == board[row + i][col + i] for i in range(4)):
                    return board[row][col]
        
        # Check diagonal (top-right to bottom-left)
        for row in range(3):
            for col in range(3, 7):
                if board[row][col] != 0 and all(board[row][col] == board[row + i][col - i] for i in range(4)):
                    return board[row][col]
        
        return 0
    
    def is_terminal(board):
        return check_winner(board) != 0 or len(get_valid_moves(board)) == 0
    
    def evaluate_position(board, player):
        winner = check_winner(board)
        if winner == player:
            return 1000000
        elif winner == -player:
            return -1000000
        
        score = 0
        
        # Evaluate all possible 4-in-a-row positions
        def evaluate_window(window, player):
            score = 0
            opp_player = -player
            
            if window.count(player) == 4:
                score += 100
            elif window.count(player) == 3 and window.count(0) == 1:
                score += 10
            elif window.count(player) == 2 and window.count(0) == 2:
                score += 2
            
            if window.count(opp_player) == 3 and window.count(0) == 1:
                score -= 80
            
            return score
        
        # Check horizontal windows
        for row in range(6):
            for col in range(4):
                window = [board[row][col + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Check vertical windows
        for row in range(3):
            for col in range(7):
                window = [board[row + i][col] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Check diagonal windows (top-left to bottom-right)
        for row in range(3):
            for col in range(4):
                window = [board[row + i][col + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Check diagonal windows (top-right to bottom-left)
        for row in range(3):
            for col in range(3, 7):
                window = [board[row + i][col - i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Favor center columns
        center_col = 3
        center_count = sum(1 for row in range(6) if board[row][center_col] == player)
        score += center_count * 3
        
        return score
    
    def minimax(board, depth, alpha, beta, maximizing_player, player):
        if depth == 0 or is_terminal(board):
            return evaluate_position(board, player)
        
        valid_moves = get_valid_moves(board)
        
        if maximizing_player:
            max_eval = float('-inf')
            for col in valid_moves:
                new_board = drop_disc(board, col, player)
                if new_board:
                    eval_score = minimax(new_board, depth - 1, alpha, beta, False, player)
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
            return max_eval
        else:
            min_eval = float('inf')
            for col in valid_moves:
                new_board = drop_disc(board, col, -player)
                if new_board:
                    eval_score = minimax(new_board, depth - 1, alpha, beta, True, player)
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            return min_eval
    
    # Main policy logic
    player = 1
    valid_moves = get_valid_moves(board)
    
    if not valid_moves:
        return 0
    
    # Check for immediate winning move
    for col in valid_moves:
        temp_board = drop_disc(board, col, player)
        if temp_board and check_winner(temp_board) == player:
            return col
    
    # Check for blocking opponent's winning move
    for col in valid_moves:
        temp_board = drop_disc(board, col, -player)
        if temp_board and check_winner(temp_board) == -player:
            return col
    
    # Use minimax to find best move
    best_col = valid_moves[0]
    best_score = float('-inf')
    depth = 6
    
    for col in valid_moves:
        temp_board = drop_disc(board, col, player)
        if temp_board:
            score = minimax(temp_board, depth - 1, float('-inf'), float('inf'), False, player)
            if score > best_score:
                best_score = score
                best_col = col
    
    return best_col
