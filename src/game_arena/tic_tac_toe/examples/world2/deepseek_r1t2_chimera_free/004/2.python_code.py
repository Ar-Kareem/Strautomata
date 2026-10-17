
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Step 1: Check for immediate wins or blocks
    all_lines = []
    # Add rows
    for i in range(4):
        all_lines.append([(i, j) for j in range(4)])
    # Add columns
    for j in range(4):
        all_lines.append([(i, j) for i in range(4)])
    # Add diagonals
    all_lines.append([(i, i) for i in range(4)])
    all_lines.append([(i, 3 - i) for i in range(4)])
    
    # Check for winning or blocking moves
    for line in all_lines:
        values = [board[i][j] for (i, j) in line]
        count_1 = values.count(1)
        count_neg1 = values.count(-1)
        count_0 = values.count(0)
        if count_1 == 3 and count_0 == 1:
            for (i, j) in line:
                if board[i][j] == 0:
                    return (i, j)
        if count_neg1 == 3 and count_0 == 1:
            for (i, j) in line:
                if board[i][j] == 0:
                    return (i, j)
    
    # Step 2: Evaluate all empty cells with heuristic scoring
    best_score = -1
    best_move = None
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                score = 0
                # Central bonus
                if 1 <= i <= 2 and 1 <= j <= 2:
                    score += 1
                
                # Collect relevant lines for this cell
                lines = []
                lines.append([(i, col) for col in range(4)])  # Row
                lines.append([(row, j) for row in range(4)])  # Column
                if i == j:
                    lines.append([(k, k) for k in range(4)])  # Main diagonal
                if i + j == 3:
                    lines.append([(k, 3 - k) for k in range(4)])  # Anti-diagonal
                
                # Evaluate each line
                for line in lines:
                    vals = [board[x][y] for (x, y) in line]
                    count_1 = vals.count(1)
                    count_neg1 = vals.count(-1)
                    
                    if count_1 > 0 and count_neg1 > 0:
                        continue  # Line is blocked
                    elif count_neg1 == 0:
                        if count_1 == 2:
                            score += 5
                        elif count_1 == 1:
                            score += 2
                    elif count_1 == 0:
                        if count_neg1 == 2:
                            score += 4
                        elif count_neg1 == 1:
                            score += 1
                
                # Update best move
                if score > best_score or best_move is None:
                    best_score = score
                    best_move = (i, j)
    
    return best_move
