
def policy(board: list[list[int]]) -> int:
    # Precompute all possible lines (48 lines)
    lines = []
    # Horizontal lines
    for row in range(6):
        for col in range(4):
            lines.append([(row, col), (row, col+1), (row, col+2), (row, col+3)])
    # Vertical lines
    for col in range(7):
        for row in range(4):
            lines.append([(row, col), (row+1, col), (row+2, col), (row+3, col)])
    # Main diagonals
    for row in range(4):
        for col in range(4):
            lines.append([(row, col), (row+1, col+1), (row+2, col+2), (row+3, col+3)])
    # Anti-diagonals
    for row in range(4):
        for col in range(3, 7):
            lines.append([(row, col), (row+1, col-1), (row+2, col-2), (row+3, col-3)])
    
    # Helper function to check win/threat
    def is_win_or_threat(b, r, c, player):
        for line in lines:
            if (r, c) in line:
                count = 0
                empty = False
                for (i, j) in line:
                    if b[i][j] == player:
                        count += 1
                    elif b[i][j] == 0:
                        empty = True
                if count == 4:
                    return True
                elif count == 3 and empty:
                    return True
        return False

    # Check for immediate win
    for col in range(7):
        # Find lowest empty row in column
        row = next((r for r in range(5, -1, -1) if board[r][col] == 0), None)
        if row is None:
            continue
        # Simulate placement
        temp_board = [row[:] for row in board]
        temp_board[row][col] = 1
        if is_win_or_threat(temp_board, row, col, 1):
            return col

    # Check for opponent's win (block)
    for col in range(7):
        row = next((r for r in range(5, -1, -1) if board[r][col] == 0), None)
        if row is None:
            continue
        temp_board = [row[:] for row in board]
        temp_board[row][col] = -1
        if is_win_or_threat(temp_board, row, col, -1):
            return col

    # Evaluate columns for threat creation
    best_col = -1
    best_score = -1
    for col in range(7):
        row = next((r for r in range(5, -1, -1) if board[r][col] == 0), None)
        if row is None:
            continue
        # Simulate placement
        temp_board = [row[:] for row in board]
        temp_board[row][col] = 1
        if is_win_or_threat(temp_board, row, col, 1):
            score = 100  # High score for threat
        else:
            score = 0
        # Centrality bonus (column 3 is best)
        centrality = abs(col - 3)
        score += 10 - centrality
        if score > best_score:
            best_score = score
            best_col = col

    return best_col
