
def policy(board: list[list[int]]) -> int:
    def is_valid_move(board, col):
        return board[0][col] == 0
    
    def get_valid_moves(board):
        return [col for col in range(7) if is_valid_move(board, col)]
    
    def make_move(board, col, player):
        new_board = [row[:] for row in board]
        for row in range(5, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                break
        return new_board
    
    def check_win(board, player):
        # Check horizontal
        for row in range(6):
            for col in range(4):
                if all(board[row][col + i] == player for i in range(4)):
                    return True
        
        # Check vertical
        for row in range(3):
            for col in range(7):
                if all(board[row + i][col] == player for i in range(4)):
                    return True
        
        # Check diagonal (positive slope)
        for row in range(3, 6):
            for col in range(4):
                if all(board[row - i][col + i] == player for i in range(4)):
                    return True
        
        # Check diagonal (negative slope)
        for row in range(3):
            for col in range(4):
                if all(board[row + i][col + i] == player for i in range(4)):
                    return True
        
        return False
    
    def evaluate_window(window, player):
        score = 0
        opponent = -player
        
        player_count = window.count(player)
        opponent_count = window.count(opponent)
        empty_count = window.count(0)
        
        if player_count == 4:
            score += 100
        elif player_count == 3 and empty_count == 1:
            score += 10
        elif player_count == 2 and empty_count == 2:
            score += 2
        
        if opponent_count == 3 and empty_count == 1:
            score -= 80
        elif opponent_count == 2 and empty_count == 2:
            score -= 3
        
        return score
    
    def evaluate_board(board, player):
        score = 0
        
        # Center column preference
        center_col = [board[row][3] for row in range(6)]
        score += center_col.count(player) * 3
        
        # Horizontal
        for row in range(6):
            for col in range(4):
                window = [board[row][col + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Vertical
        for row in range(3):
            for col in range(7):
                window = [board[row + i][col] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Positive diagonal
        for row in range(3, 6):
            for col in range(4):
                window = [board[row - i][col + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Negative diagonal
        for row in range(3):
            for col in range(4):
                window = [board[row + i][col + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        return score
    
    def minimax(board, depth, alpha, beta, maximizing_player, player):
        valid_moves = get_valid_moves(board)
        
        # Terminal conditions
        if check_win(board, player):
            return 10000
        elif check_win(board, -player):
            return -10000
        elif len(valid_moves) == 0 or depth == 0:
            return evaluate_board(board, player)
        
        if maximizing_player:
            max_eval = float('-inf')
            for col in valid_moves:
                new_board = make_move(board, col, player)
                eval_score = minimax(new_board, depth - 1, alpha, beta, False, player)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for col in valid_moves:
                new_board = make_move(board, col, -player)
                eval_score = minimax(new_board, depth - 1, alpha, beta, True, player)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Main policy logic
    player = 1  # We are always player 1
    valid_moves = get_valid_moves(board)
    
    if not valid_moves:
        return 0  # Fallback, shouldn't happen
    
    # Check for immediate win
    for col in valid_moves:
        test_board = make_move(board, col, player)
        if check_win(test_board, player):
            return col
    
    # Check for immediate block
    for col in valid_moves:
        test_board = make_move(board, col, -player)
        if check_win(test_board, -player):
            return col
    
    # Use minimax for best move
    best_col = valid_moves[0]
    best_score = float('-inf')
    
    for col in valid_moves:
        new_board = make_move(board, col, player)
        score = minimax(new_board, 6, float('-inf'), float('inf'), False, player)
        
        if score > best_score:
            best_score = score
            best_col = col
    
    return best_col
