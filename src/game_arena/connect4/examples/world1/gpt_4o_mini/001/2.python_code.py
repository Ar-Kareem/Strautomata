
def policy(board: list[list[int]]) -> int:
    def check_win(player):
        """Check if the player has a winning line."""
        # Check horizontal, vertical, and diagonal for a winning condition.
        for row in range(6):
            for col in range(7):
                if col + 3 < 7 and all(board[row][col + i] == player for i in range(4)):  # Horizontal
                    return True
                if row + 3 < 6 and all(board[row + i][col] == player for i in range(4)):  # Vertical
                    return True
                if row + 3 < 6 and col + 3 < 7 and all(board[row + i][col + i] == player for i in range(4)):  # Diagonal down
                    return True
                if row - 3 >= 0 and col + 3 < 7 and all(board[row - i][col + i] == player for i in range(4)):  # Diagonal up
                    return True
        return False

    def valid_moves():
        """Return a list of valid column indices where a move can be made."""
        return [c for c in range(7) if board[0][c] == 0]
    
    valid_columns = valid_moves()
    
    # Check for a winning move for me (1)
    for col in valid_columns:
        row = next(r for r in range(6) if board[r][col] == 0)  # Find the lowest empty row
        board[row][col] = 1  # Temporarily place my disc
        if check_win(1):  # Check if I won
            return col
        board[row][col] = 0  # Remove my disc (backtrack)
    
    # Check for blocking opponent's winning move (-1)
    for col in valid_columns:
        row = next(r for r in range(6) if board[r][col] == 0)  # Find the lowest empty row
        board[row][col] = -1  # Temporarily place opponent's disc
        if check_win(-1):  # Check if opponent would win
            board[row][col] = 0  # Remove their disc (backtrack)
            return col
        board[row][col] = 0  # Remove their disc (backtrack)

    # Otherwise, pick a random column from valid_columns
    return valid_columns[0] if valid_columns else -1  # Just a fallback case (shouldn't happen due to check)
