
def policy(board: list[list[int]]) -> int:
    """
    Connect 4 AI policy using minimax with alpha-beta pruning.
    """
    ROWS = 6
    COLS = 7
    
    def is_valid_move(board, col):
        """Check if column has space."""
        return board[0][col] == 0
    
    def get_valid_moves(board):
        """Get list of valid columns."""
        return [col for col in range(COLS) if is_valid_move(board, col)]
    
    def drop_disc(board, col, player):
        """Drop a disc in column and return the row it landed in."""
        for row in range(ROWS - 1, -1, -1):
            if board[row][col] == 0:
                board[row][col] = player
                return row
        return -1
    
    def remove_disc(board, row, col):
        """Remove a disc from position."""
        board[row][col] = 0
    
    def check_win_from_position(board, row, col, player):
        """Check if placing a disc at (row, col) creates a win for player."""
        # Directions: horizontal, vertical, diagonal /, diagonal \
        directions = [
            [(0, 1), (0, -1)],   # horizontal
            [(1, 0), (-1, 0)],   # vertical
            [(1, 1), (-1, -1)],  # diagonal \
            [(1, -1), (-1, 1)]   # diagonal /
        ]
        
        for direction_pair in directions:
            count = 1  # Count the piece at (row, col)
            for dr, dc in direction_pair:
                r, c = row + dr, col + dc
                while 0 <= r < ROWS and 0 <= c < COLS and board[r][c] == player:
                    count += 1
                    r += dr
                    c += dc
            if count >= 4:
                return True
        return False
    
    def check_winner(board, player):
        """Check if player has won."""
        for row in range(ROWS):
            for col in range(COLS):
                if board[row][col] == player:
                    if check_win_from_position(board, row, col, player):
                        return True
        return False
    
    def evaluate_window(window, player):
        """Evaluate a window of 4 positions."""
        score = 0
        opponent = -player
        
        player_count = window.count(player)
        opponent_count = window.count(opponent)
        empty_count = window.count(0)
        
        if player_count == 4:
            score += 100
        elif player_count == 3 and empty_count == 1:
            score += 5
        elif player_count == 2 and empty_count == 2:
            score += 2
        
        if opponent_count == 3 and empty_count == 1:
            score -= 4
        
        return score
    
    def evaluate_board(board, player):
        """Evaluate the board for the given player."""
        score = 0
        
        # Check if someone won
        if check_winner(board, player):
            return 10000
        if check_winner(board, -player):
            return -10000
        
        # Score center column
        center_array = [board[row][COLS // 2] for row in range(ROWS)]
        center_count = center_array.count(player)
        score += center_count * 3
        
        # Score horizontal
        for row in range(ROWS):
            for col in range(COLS - 3):
                window = [board[row][col + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Score vertical
        for col in range(COLS):
            for row in range(ROWS - 3):
                window = [board[row + i][col] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Score diagonal /
        for row in range(ROWS - 3):
            for col in range(COLS - 3):
                window = [board[row + i][col + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Score diagonal \
        for row in range(3, ROWS):
            for col in range(COLS - 3):
                window = [board[row - i][col + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        return score
    
    def minimax(board, depth, alpha, beta, maximizing_player, player):
        """Minimax with alpha-beta pruning."""
        valid_moves = get_valid_moves(board)
        
        # Terminal conditions
        if depth == 0 or len(valid_moves) == 0:
            return evaluate_board(board, player), None
        
        if check_winner(board, player):
            return 10000, None
        if check_winner(board, -player):
            return -10000, None
        
        if maximizing_player:
            max_eval = float('-inf')
            best_col = valid_moves[0] if valid_moves else None
            
            for col in valid_moves:
                row = drop_disc(board, col, player)
                eval_score, _ = minimax(board, depth - 1, alpha, beta, False, player)
                remove_disc(board, row, col)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_col = col
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_col
        else:
            min_eval = float('inf')
            best_col = valid_moves[0] if valid_moves else None
            
            for col in valid_moves:
                row = drop_disc(board, col, -player)
                eval_score, _ = minimax(board, depth - 1, alpha, beta, True, player)
                remove_disc(board, row, col)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_col = col
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_col
    
    # Main policy logic
    player = 1  # We are always player 1
    valid_moves = get_valid_moves(board)
    
    if not valid_moves:
        return 0  # Shouldn't happen
    
    # Check for immediate win
    for col in valid_moves:
        row = drop_disc(board, col, player)
        if check_win_from_position(board, row, col, player):
            remove_disc(board, row, col)
            return col
        remove_disc(board, row, col)
    
    # Check for blocking opponent's win
    for col in valid_moves:
        row = drop_disc(board, col, -player)
        if check_win_from_position(board, row, col, -player):
            remove_disc(board, row, col)
            return col
        remove_disc(board, row, col)
    
    # Use minimax for best move
    depth = 5  # Adjust based on performance
    _, best_col = minimax(board, depth, float('-inf'), float('inf'), True, player)
    
    return best_col if best_col is not None else valid_moves[0]
