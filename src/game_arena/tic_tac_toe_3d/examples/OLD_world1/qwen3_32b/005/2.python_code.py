
def compute_line_counts():
    line_counts = [[[0 for _ in range(3)] for _ in range(3)] for _ in range(3)]

    # Axis-aligned lines (x, y, z)
    for y in range(3):
        for z in range(3):
            for x in range(3):
                line_counts[x][y][z] += 1
    for x in range(3):
        for z in range(3):
            for y in range(3):
                line_counts[x][y][z] += 1
    for x in range(3):
        for y in range(3):
            for z in range(3):
                line_counts[x][y][z] += 1

    # Face diagonals
    for z in range(3):
        for i in range(3):
            line_counts[i][i][z] += 1
        for i in range(3):
            line_counts[i][2 - i][z] += 1
    for x in range(3):
        for i in range(3):
            line_counts[x][i][i] += 1
        for i in range(3):
            line_counts[x][i][2 - i] += 1
    for y in range(3):
        for i in range(3):
            line_counts[i][y][i] += 1
        for i in range(3):
            line_counts[i][y][2 - i] += 1

    # Space diagonals
    for i in range(3):
        line_counts[i][i][i] += 1
    for i in range(3):
        line_counts[i][i][2 - i] += 1
    for i in range(3):
        line_counts[i][2 - i][i] += 1
    for i in range(3):
        line_counts[i][2 - i][2 - i] += 1

    return line_counts

LINE_COUNTS = compute_line_counts()

def check_win(board, player):
    # Check all winning lines for the given player
    for y in range(3):
        for z in range(3):
            if all(board[x][y][z] == player for x in range(3)):
                return True
    for x in range(3):
        for z in range(3):
            if all(board[x][y][z] == player for y in range(3)):
                return True
    for x in range(3):
        for y in range(3):
            if all(board[x][y][z] == player for z in range(3)):
                return True

    for z in range(3):
        if all(board[i][i][z] == player for i in range(3)):
            return True
        if all(board[i][2-i][z] == player for i in range(3)):
            return True

    for x in range(3):
        if all(board[x][i][i] == player for i in range(3)):
            return True
        if all(board[x][i][2-i] == player for i in range(3)):
            return True

    for y in range(3):
        if all(board[i][y][i] == player for i in range(3)):
            return True
        if all(board[i][y][2-i] == player for i in range(3)):
            return True

    if all(board[i][i][i] == player for i in range(3)):
        return True
    if all(board[i][i][2-i] == player for i in range(3)):
        return True
    if all(board[i][2-i][i] == player for i in range(3)):
        return True
    if all(board[i][2-i][2-i] == player for i in range(3)):
        return True

    return False

def is_win_after_move(board, x, y, z, player):
    if board[x][y][z] != 0:
        return False
    original = board[x][y][z]
    board[x][y][z] = player
    win = check_win(board, player)
    board[x][y][z] = original
    return win

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Step 1: Try to win
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0 and is_win_after_move(board, x, y, z, 1):
                    return (x, y, z)

    # Step 2: Block opponent win
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0 and is_win_after_move(board, x, y, z, -1):
                    return (x, y, z)

    # Step 3: Choose the best move based on strategic value (line counts)
    empty_cells = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    empty_cells.append((x, y, z))

    empty_cells.sort(key=lambda cell: (-LINE_COUNTS[cell[0]][cell[1]][cell[2]], cell[0], cell[1], cell[2]))
    return empty_cells[0]
