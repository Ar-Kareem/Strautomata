
def policy(board: list[list[int]]) -> int:
    import random
    
    ROWS = 6
    COLS = 7
    
    def get_valid_columns(b):
        """Return list of columns that aren't full."""
        return [c for c in range(COLS) if b[0][c] == 0]
    
    def drop_disc(b, col, player):
        """Return new board with disc dropped in column. Returns None if invalid."""
        for row in range(ROWS - 1, -1, -1):
            if b[row][col] == 0:
                new_board = [row[:] for row in b]
                new_board[row][col] = player
                return new_board
        return None
    
    def check_win(b, player):
        """Check if player has won."""
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if all(b[r][c + i] == player for i in range(4)):
                    return True
        # Vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                if all(b[r + i][c] == player for i in range(4)):
                    return True
        # Diagonal (down-right)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if all(b[r + i][c + i] == player for i in range(4)):
                    return True
        # Diagonal (up-right)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if all(b[r - i][c + i] == player for i in range(4)):
                    return True
        return False
    
    def evaluate_window(window, player):
        """Evaluate a window of 4 cells."""
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
    
    def evaluate_position(b, player):
        """Evaluate board position for player."""
        score = 0
        
        # Center column preference
        center_array = [b[r][COLS // 2] for r in range(ROWS)]
        center_count = center_array.count(player)
        score += center_count * 3
        
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = [b[r][c + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                window = [b[r + i][c] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Diagonal (down-right)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [b[r + i][c + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Diagonal (up-right)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [b[r - i][c + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        return score
    
    def minimax(b, depth, alpha, beta, maximizing, player):
        """Minimax with alpha-beta pruning."""
        valid_cols = get_valid_columns(b)
        
        # Terminal conditions
        if check_win(b, player):
            return (None, 100000)
        elif check_win(b, -player):
            return (None, -100000)
        elif len(valid_cols) == 0:
            return (None, 0)
        elif depth == 0:
            return (None, evaluate_position(b, player))
        
        if maximizing:
            value = float('-inf')
            best_col = random.choice(valid_cols)
            for col in valid_cols:
                new_board = drop_disc(b, col, player)
                if new_board:
                    new_score = minimax(new_board, depth - 1, alpha, beta, False, player)[1]
                    if new_score > value:
                        value = new_score
                        best_col = col
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        break
            return best_col, value
        else:
            value = float('inf')
            best_col = random.choice(valid_cols)
            for col in valid_cols:
                new_board = drop_disc(b, col, -player)
                if new_board:
                    new_score = minimax(new_board, depth - 1, alpha, beta, True, player)[1]
                    if new_score < value:
                        value = new_score
                        best_col = col
                    beta = min(beta, value)
                    if alpha >= beta:
                        break
            return best_col, value
    
    # Main logic
    valid_moves = get_valid_columns(board)
    
    if not valid_moves:
        return 3  # Shouldn't happen, but fallback to center
    
    # Check for immediate win
    for col in valid_moves:
        test_board = drop_disc(board, col, 1)
        if test_board and check_win(test_board, 1):
            return col
    
    # Check for immediate block
    for col in valid_moves:
        test_board = drop_disc(board, col, -1)
        if test_board and check_win(test_board, -1):
            return col
    
    # Use minimax
    depth = 5  # Adjust based on performance
    col, _ = minimax(board, depth, float('-inf'), float('inf'), True, 1)
    
    return col if col is not None else random.choice(valid_moves)
