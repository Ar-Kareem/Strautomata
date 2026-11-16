
def policy(board: list[list[int]]) -> int:
    def is_winning_move(board, row, col, player):
        # Check vertical, horizontal, and diagonal connections
        for d_row, d_col in [(1, 0), (0, 1), (1, 1), (1, -1)]:
            count = 0
            # Check in both directions
            for direction in [1, -1]:
                r, c = row, col
                while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                    count += 1
                    r += d_row * direction
                    c += d_col * direction
            if count >= 4:
                return True
        return False

    def get_valid_moves(board):
        return [col for col in range(7) if board[0][col] == 0]

    def drop_disc(board, col, player):
        for row in range(5, -1, -1):
            if board[row][col] == 0:
                board[row][col] = player
                return row
        return -1  # Column is full (should not happen if called correctly)

    # Check for a winning move
    for col in get_valid_moves(board):
        row = drop_disc(board, col, 1)
        if is_winning_move(board, row, col, 1):
            board[row][col] = 0  # Undo move
            return col
        board[row][col] = 0  # Undo move
    
    # Check to block opponent's winning move
    for col in get_valid_moves(board):
        row = drop_disc(board, col, -1)
        if is_winning_move(board, row, col, -1):
            board[row][col] = 0  # Undo move
            return col
        board[row][col] = 0  # Undo move

    # Prioritize center columns
    for col in [3, 2, 4, 1, 5, 0, 6]:
        if col in get_valid_moves(board):
            return col

    return -1  # This return should never be hit if the input is valid
