
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_win(b, player):
        # Check rows
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] == player:
                return True
        # Check columns
        for j in range(3):
            if b[0][j] == b[1][j] == b[2][j] == player:
                return True
        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2] == player:
            return True
        if b[0][2] == b[1][1] == b[2][0] == player:
            return True
        return False

    # Check for winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Simulate placing 1 in this cell
                new_board = [row[:] for row in board]
                new_board[i][j] = 1
                if check_win(new_board, 1):
                    return (i, j)

    # Check for blocking opponent's winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                new_board = [row[:] for row in board]
                new_board[i][j] = -1
                if check_win(new_board, -1):
                    return (i, j)

    # Take center if available
    if board[1][1] == 0:
        return (1, 1)

    # Take a corner
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for i, j in corners:
        if board[i][j] == 0:
            return (i, j)

    # Take an edge
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for i, j in edges:
        if board[i][j] == 0:
            return (i, j)

    # If no moves are found (shouldn't happen in a valid game), return the first available
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)
    raise ValueError("No valid moves left")
