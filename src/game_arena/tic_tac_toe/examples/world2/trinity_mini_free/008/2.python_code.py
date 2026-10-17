
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Helper function to get all possible lines (rows, columns, diagonals)
    def get_lines():
        lines = []
        # Rows
        for i in range(4):
            lines.append([(i, j) for j in range(4)])
        # Columns
        for j in range(4):
            lines.append([(i, j) for i in range(4)])
        # Diagonals
        lines.append([(i, i) for i in range(4)])
        lines.append([(i, 3 - i) for i in range(4)])
        return lines

    # Helper function to check if a move creates a winning line
    def check_win(line):
        count_1 = sum(1 for (i, j) in line if board[i][j] == 1)
        count_empty = sum(1 for (i, j) in line if board[i][j] == 0)
        return count_1 == 3 and count_empty == 1

    # Helper function to check if a move blocks an opponent's winning line
    def check_block(line):
        count_opp = sum(1 for (i, j) in line if board[i][j] == -1)
        count_empty = sum(1 for (i, j) in line if board[i][j] == 0)
        return count_opp == 3 and count_empty == 1

    # Helper function to check if a move creates a fork (two threats)
    def check_fork(move):
        lines = get_lines()
        fork_count = 0
        for line in lines:
            if move in line:
                count_1 = sum(1 for (i, j) in line if board[i][j] == 1)
                count_empty = sum(1 for (i, j) in line if board[i][j] == 0)
                if count_1 == 1 and count_empty == 2:
                    fork_count += 1
        return fork_count >= 2

    # Priority 1: Check for winning moves
    lines = get_lines()
    for line in lines:
        if check_win(line):
            for (i, j) in line:
                if board[i][j] == 0:
                    return (i, j)

    # Priority 2: Check for blocking moves
    for line in lines:
        if check_block(line):
            for (i, j) in line:
                if board[i][j] == 0:
                    return (i, j)

    # Priority 3: Check for fork opportunities
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                if check_fork((i, j)):
                    return (i, j)

    # Priority 4: Center cells (most flexible)
    center_cells = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for cell in center_cells:
        if board[cell[0]][cell[1]] == 0:
            return cell

    # Priority 5: Corner cells (strategic control)
    corner_cells = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for cell in corner_cells:
        if board[cell[0]][cell[1]] == 0:
            return cell

    # Priority 6: Side cells (edge positions)
    side_cells = [(0, 1), (0, 2), (1, 0), (1, 3), (2, 0), (2, 3), (3, 1), (3, 2)]
    for cell in side_cells:
        if board[cell[0]][cell[1]] == 0:
            return cell

    # Fallback: Random empty cell (should not occur if board is not full)
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                return (i, j)
