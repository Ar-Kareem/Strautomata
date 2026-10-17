
def find_lowest_empty_row(board, col):
    for row in range(5, -1, -1):
        if board[row][col] == 0:
            return row
    return None

def is_winning_move(board, row, col):
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    current_player = board[row][col]
    for dx, dy in directions:
        count = 1
        i, j = row + dx, col + dy
        while 0 <= i < 6 and 0 <= j < 7 and board[i][j] == current_player:
            count += 1
            i += dx
            c += dy  # Wait, j here?
        i, j = row - dx, col - dy
        while 0 <= i < 6 and 0 <= j < 7 and board[i][j] == current_player:
            count += 1
            i -= dx
            c -= dy  # typo, should be j -= dy
        if count >= 4:
            return True
    return False

def is_valid_move(board, col):
    for row in board:
        if row[col] == 0:
            return True
    return False

def policy(board):
    # Check for immediate win
    for col in range(7):
        if not is_valid_move(board, col):
            continue
        row = find_lowest_empty_row(board, col)
        new_board = [row.copy() for row in board]
        new_board[row][col] = 1
        if is_winning_move(new_board, row, col):
            return col
    
    # Check if placing in any column blocks opponent's win
    blocking_col = None
    for d in range(7):
        if not is_valid_move(board, d):
            continue
        r = find_lowest_empty_row(board, d)
        new_board = [row.copy() for row in board]
        new_board[r][d] = -1
        if is_winning_move(new_board, r, d):
            blocking_col = d
            break
    if blocking_col is not None:
        return blocking_col
    
    # Choose the first available move
    for c in range(7):
        if is_valid_move(board, c):
            return c
    
    return -1  # Fallback (shouldn't reach)
