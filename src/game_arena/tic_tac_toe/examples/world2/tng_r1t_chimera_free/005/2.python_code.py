
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Generate all possible winning lines (rows, columns, diagonals)
    lines = []
    for i in range(4):
        lines.append([(i, j) for j in range(4)])  # Rows
    for j in range(4):
        lines.append([(i, j) for i in range(4)])  # Columns
    lines.append([(i, i) for i in range(4)])      # Main diagonal
    lines.append([(i, 3 - i) for i in range(4)])  # Anti-diagonal

    # Precompute lines for each cell
    lines_for_cell = {}
    for line in lines:
        for (r, c) in line:
            if (r, c) not in lines_for_cell:
                lines_for_cell[(r, c)] = []
            lines_for_cell[(r, c)].append(line)

    # Check for immediate win
    for line in lines:
        my_count = 0
        empty = None
        for (r, c) in line:
            if board[r][c] == 1:
                my_count += 1
            elif board[r][c] == 0:
                empty = (r, c)
            else:
                break
        else:
            if my_count == 3 and empty is not None:
                return empty

    # Check for opponent's immediate win
    for line in lines:
        opp_count = 0
        empty = None
        for (r, c) in line:
            if board[r][c] == -1:
                opp_count += 1
            elif board[r][c] == 0:
                empty = (r, c)
            else:
                break
        else:
            if opp_count == 3 and empty is not None:
                return empty

    # Evaluate best strategic cell
    max_score = -1
    best_cell = None
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                score = 0
                for line in lines_for_cell.get((r, c), []):
                    my = 0
                    opp = 0
                    for (x, y) in line:
                        if board[x][y] == 1:
                            my += 1
                        elif board[x][y] == -1:
                            opp += 1
                    if opp == 0:
                        score += my
                # Prefer center cells
                if 1 <= r <= 2 and 1 <= c <= 2:
                    score += 0.1
                if score > max_score or best_cell is None:
                    max_score = score
                    best_cell = (r, c)
    return best_cell
