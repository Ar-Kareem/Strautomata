
def check_line(line):
    if line.count(1) == 4:
        return 1
    elif line.count(-1) == 4:
        return -1
    else:
        return 0

def evaluate(board):
    score = 0
    # Check all horizontal lines
    for row in range(6):
        for col in range(4):
            line = [board[row][col], board[row][col+1], board[row][col+2], board[row][col+3]]
            if line.count(1) == 3 and line.count(0) == 1:
                score += 1
            elif line.count(-1) == 3 and line.count(0) == 1:
                score -= 1
    # Check all vertical lines
    for col in range(7):
        for row in range(4):
            line = [board[row][col], board[row+1][col], board[row+2][col], board[row+3][col]]
            if line.count(1) == 3 and line.count(0) == 1:
                score += 1
            elif line.count(-1) == 3 and line.count(0) == 1:
                score -= 1
    # Check all down-right diagonals
    for row in range(4):
        for col in range(4):
            line = [board[row][col], board[row+1][col+1], board[row+2][col+2], board[row+3][col+3]]
            if line.count(1) == 3 and line.count(0) == 1:
                score += 1
            elif line.count(-1) == 3 and line.count(0) == 1:
                score -= 1
    # Check all down-left diagonals
    for row in range(4):
        for col in range(3, 7):
            line = [board[row][col], board[row+1][col-1], board[row+2][col-2], board[row+3][col-3]]
            if line.count(1) == 3 and line.count(0) == 1:
                score += 1
            elif line.count(-1) == 3 and line.count(0) == 1:
                score -= 1
    return score

def policy(board):
    # Check for immediate win
    for col in range(7):
        if board[5][col] == 0:
            row = 5
            while row >= 0 and board[row][col] == 0:
                row -= 1
            row += 1
            # Check horizontal
            line = [board[row][col], board[row][col+1], board[row][col+2], board[row][col+3]]
            if check_line(line) == 1:
                return col
            # Check vertical
            line = [board[row][col], board[row+1][col], board[row+2][col], board[row+3][col]]
            if check_line(line) == 1:
                return col
            # Check down-right diagonal
            line = [board[row][col], board[row+1][col+1], board[row+2][col+2], board[row+3][col+3]]
            if check_line(line) == 1:
                return col
            # Check down-left diagonal
            line = [board[row][col], board[row+1][col-1], board[row+2][col-2], board[row+3][col-3]]
            if check_line(line) == 1:
                return col
    # Check for opponent's immediate win
    for col in range(7):
        if board[5][col] == 0:
            row = 5
            while row >= 0 and board[row][col] == 0:
                row -= 1
            row += 1
            # Check horizontal
            line = [board[row][col], board[row][col+1], board[row][col+2], board[row][col+3]]
            if check_line(line) == -1:
                return col
            # Check vertical
            line = [board[row][col], board[row+1][col], board[row+2][col], board[row+3][col]]
            if check_line(line) == -1:
                return col
            # Check down-right diagonal
            line = [board[row][col], board[row+1][col+1], board[row+2][col+2], board[row+3][col+3]]
            if check_line(line) == -1:
                return col
            # Check down-left diagonal
            line = [board[row][col], board[row+1][col-1], board[row+2][col-2], board[row+3][col-3]]
            if check_line(line) == -1:
                return col
    # Evaluate each column's heuristic
    best_col = None
    best_score = -float('inf')
    for col in range(7):
        if board[5][col] == 0:
            row = 5
            while row >= 0 and board[row][col] == 0:
                row -= 1
            row += 1
            # Create a copy of the board
            new_board = [row[:] for row in board]
            new_board[row][col] = 1
            score = evaluate(new_board)
            if score > best_score:
                best_score = score
                best_col = col
    return best_col
