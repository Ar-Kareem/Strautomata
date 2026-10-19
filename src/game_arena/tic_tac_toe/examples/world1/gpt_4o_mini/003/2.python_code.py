
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_line(a, b, c, player):
        # Check if a line can be completed by 'player'
        line = [board[a][b], board[b][c], board[c][a]]
        if line.count(player) == 2 and line.count(0) == 1:
            return True
        return False

    # Check winning moves for myself (1) and for the opponent (-1)
    for i in range(3):
        # Check rows and columns
        if check_line(i, (i + 1) % 3, (i + 2) % 3, 1):
            return (i, [x for x in range(3) if board[i][x] == 0][0])
        if check_line((i + 1) % 3, (i + 2) % 3, i, -1):
            return (i, [x for x in range(3) if board[i][x] == 0][0])
    
    for j in range(3):
        if check_line((j + 1) % 3, (j + 2) % 3, j, 1):
            return ([x for x in range(3) if board[x][j] == 0][0], j)
        if check_line(j, (j + 1) % 3, (j + 2) % 3, -1):
            return ([x for x in range(3) if board[x][j] == 0][0], j)

    # Check diagonals
    if check_line(0, 1, 2, 1):
        for x in [0, 1, 2]:
            if board[x][x] == 0:
                return (x, x)
    if check_line(0, 2, 1, -1):
        return (1, 1)  # blocking the center move

    # Optionally, play in the center if available
    if board[1][1] == 0:
        return (1, 1)

    # Check for corners if no other option is available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for corner in corners:
        if board[corner[0]][corner[1]] == 0:
            return corner
    
    # Default to the first empty cell if no winning or blocking moves apply
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)

    # Ideally, this should never be reached in a proper game scenario
    raise ValueError("No valid moves available")
