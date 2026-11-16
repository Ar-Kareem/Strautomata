
def policy(board: list[list[int]]) -> int:
    # Check for immediate winning moves
    for col in range(7):
        if board[0][col] != 0:  # Skip full columns
            continue
        row = 0
        while row < 6 and board[row][col] == 0:
            row += 1
        row -= 1  # Lowest available row
        if check_win(board, row, col, 1):  # Check if this move wins
            return col
    
    # Check for blocking opponent's winning moves
    for col in range(7):
        if board[0][col] != 0:
            continue
        row = 0
        while row < 6 and board[row][col] == 0:
            row += 1
        row -= 1
        if check_win(board, row, col, -1):  # Check if this blocks opponent
            return col
    
    # Evaluate columns for potential threats
    best_col = 0
    best_score = -float('inf')
    for col in range(7):
        if board[0][col] != 0:
            continue
        row = 0
        while row < 6 and board[row][col] == 0:
            row += 1
        row -= 1
        score = evaluate_column(board, row, col, 1)
        if score > best_score:
            best_score = score
            best_col = col
    return best_col

def check_win(board: list[list[int]], row: int, col: int, player: int) -> bool:
    # Check horizontal
    for c in range(max(0, col-3), min(7, col+4)):
        if all(board[row][c+i] == player for i in range(4)):
            return True
    # Check vertical
    for r in range(max(0, row-3), min(6, row+4)):
        if all(board[r+i][col] == player for i in range(4)):
            return True
    # Check diagonal down-right
    for r in range(max(0, row-3), min(6, row+4)):
        for c in range(max(0, col-3), min(7, col+4)):
            if all(board[r+i][c+i] == player for i in range(4)):
                return True
    # Check diagonal down-left
    for r in range(max(0, row-3), min(6, row+4)):
        for c in range(max(0, col-3), min(7, col+4)):
            if all(board[r+i][c-i] == player for i in range(4)):
                return True
    return False

def evaluate_column(board: list[list[int]], row: int, col: int, player: int) -> int:
    # Score based on existing discs and potential threats
    score = 0
    # Count existing player discs in column
    for r in range(6):
        if board[r][col] == player:
            score += 1
    # Check for potential forks (two threats)
    for dr, dc in [(1,0), (0,1), (1,1), (1,-1)]:
        threats = 0
        for i in range(1,4):
            nr, nc = row + dr*i, col + dc*i
            if 0 <= nr < 6 and 0 <= nc < 7:
                if board[nr][nc] == player:
                    threats += 1
                elif board[nr][nc] == 0:
                    threats += 0.5
        if threats >= 2:
            score += 10
    return score
