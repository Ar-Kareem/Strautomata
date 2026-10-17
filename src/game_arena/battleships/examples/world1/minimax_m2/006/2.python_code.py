
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Total candidates list: each element is (priority, row, col)
    candidate_moves = []

    # Step 1: Check for gaps in rows and columns (priority 0)
    # Gaps: when we have two consecutive hits in the same row (or column) with exactly one cell in between.
    # For each row, find sorted list of hit columns.
    for row in range(10):
        hit_cols = []
        for col in range(10):
            if board[row][col] == 1:
                hit_cols.append(col)
        hit_cols.sort()
        for i in range(len(hit_cols)-1):
            col1 = hit_cols[i]
            col2 = hit_cols[i+1]
            if col2 - col1 == 2:  # exactly one gap
                gap_col = col1 + 1
                if board[row][gap_col] == 0:  # ensure unknown
                    candidate_moves.append((0, row, gap_col))

    # Similarly for columns: find sorted list of hit rows.
    for col in range(10):
        hit_rows = []
        for row in range(10):
            if board[row][col] == 1:
                hit_rows.append(row)
        hit_rows.sort()
        for i in range(len(hit_rows)-1):
            row1 = hit_rows[i]
            row2 = hit_rows[i+1]
            if row2 - row1 == 2:
                gap_row = row1 + 1
                if board[gap_row][col] == 0:
                    candidate_moves.append((0, gap_row, col))

    # Step 2: Check for contiguous runs (length>=2) in rows and columns (priority 1)
    # Row runs
    for row in range(10):
        col = 0
        while col < 10:
            if board[row][col] == 1:
                start_col = col
                while col < 10 and board[row][col] == 1:
                    col += 1
                end_col = col - 1
                length = end_col - start_col + 1
                if length >= 2:
                    # Extend left if possible
                    if start_col > 0 and board[row][start_col-1] == 0:
                        candidate_moves.append((1, row, start_col-1))
                    # Extend right if possible
                    if end_col < 9 and board[row][end_col+1] == 0:
                        candidate_moves.append((1, row, end_col+1))
            col += 1

    # Column runs
    for col in range(10):
        row = 0
        while row < 10:
            if board[row][col] == 1:
                start_row = row
                while row < 10 and board[row][col] == 1:
                    row += 1
                end_row = row - 1
                length = end_row - start_row + 1
                if length >= 2:
                    # Extend up if possible
                    if start_row > 0 and board[start_row-1][col] == 0:
                        candidate_moves.append((1, start_row-1, col))
                    # Extend down if possible
                    if end_row < 9 and board[end_row+1][col] == 0:
                        candidate_moves.append((1, end_row+1, col))
            row += 1

    # Step 3: For every hit (even isolated), consider adjacent cells (priority 2)
    # Collect all hit positions
    hit_positions = [(i, j) for i in range(10) for j in range(10) if board[i][j] == 1]
    for (i, j) in hit_positions:
        # Check adjacent cells: up, down, left, right
        if i > 0 and board[i-1][j] == 0:
            candidate_moves.append((2, i-1, j))
        if i < 9 and board[i+1][j] == 0:
            candidate_moves.append((2, i+1, j))
        if j > 0 and board[i][j-1] == 0:
            candidate_moves.append((2, i, j-1))
        if j < 9 and board[i][j+1] == 0:
            candidate_moves.append((2, i, j+1))

    # Now, we have candidate_moves that may contain duplicates? But we want to avoid duplicates and keep the best priority for each cell.
    # We will use a dictionary to store the best (lowest) priority for each cell (i,j)
    best_candidate = {}
    for pr, i, j in candidate_moves:
        # We only consider if the cell is still 0? Actually, we built from 0? 
        # But to be safe, we check: if we haven't seen (i,j) or we found a lower priority
        key = (i, j)
        if key not in best_candidate or pr < best_candidate[key]:
            best_candidate[key] = pr

    if best_candidate:
        # Sort the keys by (priority, row, col)
        sorted_candidates = sorted(best_candidate.items(), key=lambda x: (x[1], x[0][0], x[0][1]))
        # The first element is (key, priority) where key=(i,j). We want the move.
        move = sorted_candidates[0][0]
        return (move[0], move[1])

    else:
        # No candidate moves? Then we go to hunt mode: use checkerboard pattern
        # First, try even parity (i+j even)
        for i in range(10):
            for j in range(10):
                if board[i][j] == 0 and (i + j) % 2 == 0:
                    return (i, j)
        # Then try odd parity
        for i in range(10):
            for j in range(10):
                if board[i][j] == 0 and (i + j) % 2 == 1:
                    return (i, j)

    # This should not happen if there are still unknown cells, but just in case
    raise ValueError("No available move found")
