
def policy(board: list[list[int]]) -> int:
    def get_valid_moves(board):
        """Return list of valid column indices."""
        return [col for col in range(7) if board[0][col] == 0]
    
    def drop_disc(board, col, player):
        """Return new board state after dropping disc in column."""
        new_board = [row[:] for row in board]
        for row in range(5, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                break
        return new_board
    
    def check_four_in_row(board, player):
        """Check if player has 4 in a row anywhere on board."""
        rows, cols = 6, 7
        
        # Check horizontal
        for row in range(rows):
            for col in range(cols - 3):
                if all(board[row][col + i] == player for i in range(4)):
                    return True
        
        # Check vertical
        for row in range(rows - 3):
            for col in range(cols):
                if all(board[row + i][col] == player for i in range(4)):
                    return True
        
        # Check diagonal (top-left to bottom-right)
        for row in range(rows - 3):
            for col in range(cols - 3):
                if all(board[row + i][col + i] == player for i in range(4)):
                    return True
        
        # Check diagonal (top-right to bottom-left)
        for row in range(rows - 3):
            for col in range(3, cols):
                if all(board[row + i][col - i] == player for i in range(4)):
                    return True
        
        return False
    
    def evaluate_position(board, player):
        """Evaluate board position for player."""
        score = 0
        opponent = -player
        rows, cols = 6, 7
        
        # Check all possible 4-cell windows
        # Horizontal
        for row in range(rows):
            for col in range(cols - 3):
                window = [board[row][col + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Vertical
        for row in range(rows - 3):
            for col in range(cols):
                window = [board[row + i][col] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Diagonal (positive slope)
        for row in range(rows - 3):
            for col in range(cols - 3):
                window = [board[row + i][col + i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Diagonal (negative slope)
        for row in range(rows - 3):
            for col in range(3, cols):
                window = [board[row + i][col - i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Prefer center columns
        center_col = cols // 2
        for row in range(rows):
            if board[row][center_col] == player:
                score += 3
        
        return score
    
    def evaluate_window(window, player):
        """Evaluate a 4-cell window."""
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
            score -= 80  # Block opponent
        
        return score
    
    valid_moves = get_valid_moves(board)
    if not valid_moves:
        return 0
    
    # Check for immediate win
    for col in valid_moves:
        test_board = drop_disc(board, col, 1)  # We are player 1
        if check_four_in_row(test_board, 1):
            return col
    
    # Check for blocking opponent win
    for col in valid_moves:
        test_board = drop_disc(board, col, -1)  # Opponent is player -1
        if check_four_in_row(test_board, -1):
            return col
    
    # Evaluate all moves and pick the best one
    best_score = float('-inf')
    best_col = valid_moves[0]
    
    for col in valid_moves:
        test_board = drop_disc(board, col, 1)
        score = evaluate_position(test_board, 1)
        
        if score > best_score:
            best_score = score
            best_col = col
    
    return best_col
