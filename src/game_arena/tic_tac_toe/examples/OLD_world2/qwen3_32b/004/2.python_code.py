
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_win(bd, player):
        # Check rows
        for row in bd:
            if all(cell == player for cell in row):
                return True
        # Check columns
        for col in range(4):
            if all(bd[row][col] == player for row in range(4)):
                return True
        # Check diagonals
        if all(bd[i][i] == player for i in range(4)):
            return True
        if all(bd[i][3 - i] == player for i in range(4)):
            return True
        return False

    # Win strategy
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_win(board, 1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Block opponent strategy
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_win(board, -1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Heuristic selection based on strategic potential
    empty_cells = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    best_move = None
    max_potential = -1

    for (i, j) in empty_cells:
        potential = 0

        # Row potential
        row_count = 0
        for x in range(4):
            if board[i][x] == 1:
                row_count += 1
            elif board[i][x] == -1:
                break
        if row_count > 0 and row_count < 4:
            potential += row_count

        # Column potential
        col_count = 0
        for x in range(4):
            if board[x][j] == 1:
                col_count += 1
            elif board[x][j] == -1:
                break
        if col_count > 0 and col_count < 4:
            potential += col_count

        # Diagonal (\)
        if i == j:
            diag_count = 0
            for x in range(4):
                if board[x][x] == 1:
                    diag_count += 1
                elif board[x][x] == -1:
                    break
            if diag_count > 0 and diag_count < 4:
                potential += diag_count

        # Anti-diagonal (/)
        if i + j == 3:
            anti_diag_count = 0
            for x in range(4):
                if board[x][3 - x] == 1:
                    anti_diag_count += 1
                elif board[x][3 - x] == -1:
                    break
            if anti_diag_count > 0 and anti_diag_count < 4:
                potential += anti_diag_count

        if potential > max_potential or (potential == max_potential and best_move is None):
            max_potential = potential
            best_move = (i, j)

    if best_move is not None:
        return best_move

    # Last resort: pick the first empty cell
    return empty_cells[0]
