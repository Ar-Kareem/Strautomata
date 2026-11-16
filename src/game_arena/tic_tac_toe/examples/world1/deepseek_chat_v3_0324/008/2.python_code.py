
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check for immediate win
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Simulate placing a 1 here
                board[i][j] = 1
                # Check if this move wins
                if is_winner(board, 1):
                    board[i][j] = 0  # Undo simulation
                    return (i, j)
                board[i][j] = 0  # Undo simulation

    # Check for opponent's immediate win and block
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Simulate opponent placing a -1 here
                board[i][j] = -1
                # Check if this move would make opponent win
                if is_winner(board, -1):
                    board[i][j] = 0  # Undo simulation
                    return (i, j)
                board[i][j] = 0  # Undo simulation

    # Take center if available
    if board[1][1] == 0:
        return (1, 1)

    # Take any corner
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for i, j in corners:
        if board[i][j] == 0:
            return (i, j)

    # Take any edge
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for i, j in edges:
        if board[i][j] == 0:
            return (i, j)

    # Fallback (shouldn't reach here if board isn't full)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)
    return (0, 0)  # Should never happen

def is_winner(board, player):
    # Check rows
    for row in board:
        if all(cell == player for cell in row):
            return True
    # Check columns
    for col in range(3):
        if all(board[row][col] == player for row in range(3)):
            return True
    # Check diagonals
    if board[0][0] == player and board[1][1] == player and board[2][2] == player:
        return True
    if board[0][2] == player and board[1][1] == player and board[2][0] == player:
        return True
    return False
