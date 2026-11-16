
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check for winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_win(board, 1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Check for opponent winning move to block
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_win(board, -1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Check for fork opportunities (create two winning moves)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                if count_potential_wins(board, 1) >= 2:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Check for opponent fork to block
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = -1
                if count_potential_wins(board, -1) >= 2:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Center is best if available
    if board[1][1] == 0:
        return (1, 1)

    # Check corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for (i, j) in corners:
        if board[i][j] == 0:
            return (i, j)

    # Check edges
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for (i, j) in edges:
        if board[i][j] == 0:
            return (i, j)

    # Fallback (shouldn't happen on valid board)
    return (0, 0)

def check_win(board: list[list[int]], player: int) -> bool:
    # Check rows
    for i in range(3):
        if all(cell == player for cell in board[i]):
            return True

    # Check columns
    for j in range(3):
        if all(board[i][j] == player for i in range(3)):
            return True

    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] == player:
        return True
    if board[0][2] == board[1][1] == board[2][0] == player:
        return True

    return False

def count_potential_wins(board: list[list[int]], player: int) -> int:
    count = 0
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = player
                if check_win(board, player):
                    count += 1
                board[i][j] = 0
    return count
