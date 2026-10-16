
def policy(board: list[list[int]]) -> int:
    def is_valid_move(board, col):
        return board[0][col] == 0
    
    def get_valid_moves(board):
        return [col for col in range(7) if is_valid_move(board, col)]
    
    def drop_disc(board, col, player):
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
    
    def evaluate_position(board, player):
        if check_win(board, player):
            return 1000
        if check_win(board, -player):
            return -1000
        
        score = 0
        
        # Evaluate all possible 4-in-a-row positions
        def evaluate_window(window, player):
            score = 0
            player_count = window.count(player)
            opponent_count = window.count(-player)
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
                score -= 5
            
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
        
        # Check diagonal windows (positive slope)
        for row in range(3, 6):
            for col in range(4):
                window = [board[row - i][col + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Check diagonal windows (negative slope)
        for row in range(3):
            for col in range(4):
                window = [board[row + i][col + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Prefer center columns
        center_array = [board[row][3] for row in range(6)]
        center_count = center_array.count(player)
        score += center_count * 3
        
        return score
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        valid_moves = get_valid_moves(board)
        is_terminal = len(valid_moves) == 0 or check_win(board, 1) or check_win(board, -1)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if check_win(board, 1):
                    return None, 10000
                elif check_win(board, -1):
                    return None, -10000
                else:
                    return None, 0
            else:
                return None, evaluate_position(board, 1)
        
        if maximizing_player:
            value = float('-inf')
            best_col = valid_moves[0]
            for col in valid_moves:
                new_board = drop_disc(board, col, 1)
                _, new_score = minimax(new_board, depth - 1, alpha, beta, False)
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return best_col, value
        else:
            value = float('inf')
            best_col = valid_moves[0]
            for col in valid_moves:
                new_board = drop_disc(board, col, -1)
                _, new_score = minimax(new_board, depth - 1, alpha, beta, True)
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return best_col, value
    
    # Check for immediate winning move
    for col in get_valid_moves(board):
        temp_board = drop_disc(board, col, 1)
        if check_win(temp_board, 1):
            return col
    
    # Check for blocking opponent's winning move
    for col in get_valid_moves(board):
        temp_board = drop_disc(board, col, -1)
        if check_win(temp_board, -1):
            return col
    
    # Use minimax with alpha-beta pruning
    best_col, _ = minimax(board, 5, float('-inf'), float('inf'), True)
    return best_col
