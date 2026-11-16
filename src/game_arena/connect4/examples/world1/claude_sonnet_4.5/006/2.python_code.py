
def policy(board: list[list[int]]) -> int:
    """
    Connect 4 AI policy using minimax with alpha-beta pruning.
    """
    
    def get_valid_moves(b):
        """Returns list of valid column indices."""
        return [col for col in range(7) if b[0][col] == 0]
    
    def drop_disc(b, col, player):
        """Returns new board state after dropping disc in column."""
        new_board = [row[:] for row in b]
        for row in range(5, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                return new_board, row
        return new_board, -1
    
    def check_win(b, player):
        """Check if player has won."""
        # Horizontal
        for row in range(6):
            for col in range(4):
                if all(b[row][col+i] == player for i in range(4)):
                    return True
        
        # Vertical
        for row in range(3):
            for col in range(7):
                if all(b[row+i][col] == player for i in range(4)):
                    return True
        
        # Diagonal (down-right)
        for row in range(3):
            for col in range(4):
                if all(b[row+i][col+i] == player for i in range(4)):
                    return True
        
        # Diagonal (down-left)
        for row in range(3):
            for col in range(3, 7):
                if all(b[row+i][col-i] == player for i in range(4)):
                    return True
        
        return False
    
    def is_winning_move(b, col, player):
        """Check if dropping disc in col wins for player."""
        new_board, _ = drop_disc(b, col, player)
        return check_win(new_board, player)
    
    def count_windows(b, player):
        """Count scoring windows for evaluation."""
        score = 0
        
        # Horizontal windows
        for row in range(6):
            for col in range(4):
                window = [b[row][col+i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Vertical windows
        for row in range(3):
            for col in range(7):
                window = [b[row+i][col] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Diagonal (down-right)
        for row in range(3):
            for col in range(4):
                window = [b[row+i][col+i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Diagonal (down-left)
        for row in range(3):
            for col in range(3, 7):
                window = [b[row+i][col-i] for i in range(4)]
                score += evaluate_window(window, player)
        
        return score
    
    def evaluate_window(window, player):
        """Evaluate a 4-cell window."""
        score = 0
        opp = -player
        
        player_count = window.count(player)
        opp_count = window.count(opp)
        empty_count = window.count(0)
        
        if player_count == 4:
            score += 100
        elif player_count == 3 and empty_count == 1:
            score += 5
        elif player_count == 2 and empty_count == 2:
            score += 2
        
        if opp_count == 3 and empty_count == 1:
            score -= 4
        
        return score
    
    def evaluate_board(b):
        """Heuristic evaluation of board state."""
        if check_win(b, 1):
            return 10000
        if check_win(b, -1):
            return -10000
        
        score = count_windows(b, 1) - count_windows(b, -1)
        
        # Prefer center column
        center_count = sum(1 for row in range(6) if b[row][3] == 1)
        score += center_count * 3
        
        return score
    
    def minimax(b, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning."""
        valid_moves = get_valid_moves(b)
        
        if depth == 0 or len(valid_moves) == 0:
            return None, evaluate_board(b)
        
        if check_win(b, 1):
            return None, 10000
        if check_win(b, -1):
            return None, -10000
        
        if maximizing:
            max_eval = float('-inf')
            best_col = valid_moves[0]
            for col in valid_moves:
                new_board, _ = drop_disc(b, col, 1)
                _, eval_score = minimax(new_board, depth - 1, alpha, beta, False)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_col = col
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return best_col, max_eval
        else:
            min_eval = float('inf')
            best_col = valid_moves[0]
            for col in valid_moves:
                new_board, _ = drop_disc(b, col, -1)
                _, eval_score = minimax(new_board, depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_col = col
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return best_col, min_eval
    
    # Main logic
    valid_moves = get_valid_moves(board)
    
    if not valid_moves:
        return 3  # Shouldn't happen, but return center
    
    # Check for immediate win
    for col in valid_moves:
        if is_winning_move(board, col, 1):
            return col
    
    # Check for blocking opponent's win
    for col in valid_moves:
        if is_winning_move(board, col, -1):
            return col
    
    # Use minimax
    best_col, _ = minimax(board, depth=4, alpha=float('-inf'), beta=float('inf'), maximizing=True)
    
    return best_col if best_col is not None else valid_moves[len(valid_moves)//2]
