
def policy(board: list[list[int]]) -> int:
    def is_winning_move(b, col, player):
        # Simulate the move
        for row in range(5, -1, -1):
            if b[row][col] == 0:
                b[row][col] = player
                break

        # Check horizontal, vertical, and diagonal connections
        for r in range(6):
            for c in range(7):
                # Horizontal
                if c < 4 and all(b[r][c+i] == player for i in range(4)):
                    return True
                # Vertical
                if r < 3 and all(b[r+i][c] == player for i in range(4)):
                    return True
                # Diagonal /
                if r < 3 and c < 4 and all(b[r+i][c+i] == player for i in range(4)):
                    return True
                # Diagonal \
                if r >= 3 and c < 4 and all(b[r-i][c+i] == player for i in range(4)):
                    return True

        # Undo the move
        for r in range(6):
            if b[r][col] == player:
                b[r][col] = 0
                break
        
        return False

    # Check for winning move
    for col in range(7):
        if board[0][col] == 0:  # Column must not be full
            if is_winning_move(board, col, 1):  # Check if the move wins
                return col

    # Check for blocking opponent's winning move
    for col in range(7):
        if board[0][col] == 0:  # Column must not be full
            if is_winning_move(board, col, -1):  # Check if the move blocks opponent's win
                return col

    # If no winning or blocking moves, choose center column preferentially
    for col in [3, 2, 4, 1, 5, 0, 6]:  # Prioritize center first
        if board[0][col] == 0:  # Column must not be full
            return col

    return 0  # Fallback, though we should always have a valid move
