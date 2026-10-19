
def policy(board: list[list[int]]) -> int:
    valid_columns = [col for col in range(7) if board[0][col] == 0]
    
    def make_move(current_board, move_col, player):
        new_board = [row[:] for row in current_board]
        for row in range(5, -1, -1):
            if new_board[row][move_col] == 0:
                new_board[row][move_col] = player
                break
        return new_board
    
    def is_win(current_board, player):
        # Check horizontal
        for r in range(6):
            for c in range(4):
                if current_board[r][c] == player and current_board[r][c+1] == player \
                   and current_board[r][c+2] == player and current_board[r][c+3] == player:
                    return True
        # Check vertical
        for r in range(3):
            for c in range(7):
                if current_board[r][c] == player and current_board[r+1][c] == player \
                   and current_board[r+2][c] == player and current_board[r+3][c] == player:
                    return True
        # Check diagonal (down-right)
        for r in range(3):
            for c in range(4):
                if current_board[r][c] == player and current_board[r+1][c+1] == player \
                   and current_board[r+2][c+2] == player and current_board[r+3][c+3] == player:
                    return True
        # Check diagonal (down-left)
        for r in range(3):
            for c in range(3, 7):
                if current_board[r][c] == player and current_board[r+1][c-1] == player \
                   and current_board[r+2][c-2] == player and current_board[r+3][c-3] == player:
                    return True
        return False
    
    # Check for immediate win
    for col in valid_columns:
        sim_board = make_move(board, col, 1)
        if is_win(sim_board, 1):
            return col
    
    # Block opponent's immediate win
    for col in valid_columns:
        sim_board = make_move(board, col, -1)
        if is_win(sim_board, -1):
            return col
    
    # Priority order: center columns first
    priority_order = [3, 2, 4, 1, 5, 0, 6]
    for col in priority_order:
        if col in valid_columns:
            return col
    
    return valid_columns[0]  # Fallback
