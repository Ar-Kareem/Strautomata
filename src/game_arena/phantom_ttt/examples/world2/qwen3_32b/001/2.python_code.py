
def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_winning_move(row, col):
        temp_board = [[board[i][j] for j in range(3)] for i in range(3)]
        temp_board[row][col] = 1
        for i in range(3):
            if all(temp_board[i][j] == 1 for j in range(3)) or all(temp_board[j][i] == 1 for j in range(3)):
                return True
        if all(temp_board[i][i] == 1 for i in range(3)) or all(temp_board[i][2 - i] == 1 for i in range(3)):
            return True
        return False

    def count_potential_winning_lines(row, col):
        temp_board = [[board[i][j] for j in range(3)] for i in range(3)]
        temp_board[row][col] = 1

        count = 0
        row_vals = temp_board[row]
        if sum(1 for x in row_vals if x == 1) == 2:
            count += 1

        col_vals = [temp_board[i][col] for i in range(3)]
        if sum(1 for x in col_vals if x == 1) == 2:
            count += 1

        if row == col:
            diag_vals = [temp_board[i][i] for i in range(3)]
            if sum(1 for x in diag_vals if x == 1) == 2:
                count += 1

        if row + col == 2:
            diag_vals = [temp_board[i][2 - i] for i in range(3)]
            if sum(1 for x in diag_vals if x == 1) == 2:
                count += 1

        return count

    def get_default_move():
        if board[1][1] == 0:
            return (1, 1)
        for r, c in [(0,0), (0,2), (2,0), (2,2)]:
            if board[r][c] == 0:
                return (r, c)
        for r, c in [(0,1), (1,0), (1,2), (2,1)]:
            if board[r][c] == 0:
                return (r, c)
        return (0, 0)

    candidates = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]

    for i, j in candidates:
        if is_winning_move(i, j):
            return (i, j)

    for i, j in candidates:
        if count_potential_winning_lines(i, j) >= 2:
            return (i, j)

    for i, j in candidates:
        if count_potential_winning_lines(i, j) >= 1:
            return (i, j)

    return get_default_move()
