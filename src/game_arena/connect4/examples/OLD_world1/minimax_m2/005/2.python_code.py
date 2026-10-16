
def check_win(board, player):
    rows = len(board)
    cols = len(board[0])
    
    # Check horizontal
    for r in range(rows):
        for c in range(cols - 3):
            if (board[r][c] == player and board[r][c+1] == player and 
                board[r][c+2] == player and board[r][c+3] == player):
                return True
    
    # Check vertical
    for r in range(rows - 3):
        for c in range(cols):
            if (board[r][c] == player and board[r+1][c] == player and 
                board[r+2][c] == player and board[r+3][c] == player):
                return True
    
    # Check diagonal (positive slope)
    for r in range(rows - 3):
        for c in range(cols - 3):
            if (board[r][c] == player and board[r+1][c+1] == player and 
                board[r+2][c+2] == player and board[r+3][c+3] == player):
                return True
    
    # Check diagonal (negative slope)
    for r in range(3, rows):
        for c in range(cols - 3):
            if (board[r][c] == player and board[r-1][c+1] == player and 
                board[r-2][c+2] == player and board[r-3][c+3] == player):
                return True
    
    return False

def score_window(window):
    count_1 = window.count(1)
    count_neg1 = window.count(-1)
    count_0 = window.count(0)
    
    if count_1 == 4:
        return 100000
    if count_neg1 == 4:
        return -100000
    if count_1 == 3 and count_0 == 1:
        return 100
    if count_neg1 == 3 and count_0 == 1:
        return -100
    if count_1 == 2 and count_0 == 2:
        return 10
    if count_neg1 == 2 and count_0 == 2:
        return -10
    if count_1 == 1 and count_0 == 3:
        return 1
    if count_neg1 == 1 and count_0 == 3:
        return -1
    return 0

def evaluate(board):
    score = 0
    center_col = 3
    center_count = 0
    rows = len(board)
    cols = len(board[0])
    
    for r in range(rows):
        if board[r][center_col] == 1:
            center_count += 1
    score += center_count * 3
    
    # Horizontal windows
    for r in range(rows):
        for c in range(cols - 3):
            window = [board[r][c], board[r][c+1], board[r][c+2], board[r][c+3]]
            score += score_window(window)
    
    # Vertical windows
    for c in range(cols):
        for r in range(rows - 3):
            window = [board[r][c], board[r+1][c], board[r+2][c], board[r+3][c]]
            score += score_window(window)
    
    # Diagonal (positive slope)
    for r in range(rows - 3):
        for c in range(cols - 3):
            window = [board[r][c], board[r+1][c+1], board[r+2][c+2], board[r+3][c+3]]
            score += score_window(window)
    
    # Diagonal (negative slope)
    for r in range(3, rows):
        for c in range(cols - 3):
            window = [board[r][c], board[r-1][c+1], board[r-2][c+2], board[r-3][c+3]]
            score += score_window(window)
    
    return score

def policy(board: list[list[int]]) -> int:
    rows = len(board)
    cols = len(board[0])
    
    for col in range(cols):
        if board[0][col] != 0:
            continue
        sim_board = [row[:] for row in board]
        for r in range(rows - 1, -1, -1):
            if sim_board[r][col] == 0:
                sim_board[r][col] = 1
                break
        if check_win(sim_board, 1):
            return col
            
    for col in range(cols):
        if board[0][col] != 0:
            continue
        sim_board = [row[:] for row in board]
        for r in range(rows - 1, -1, -1):
            if sim_board[r][col] == 0:
                sim_board[r][col] = -1
                break
        if check_win(sim_board, -1):
            return col
            
    best_score = -10**18
    best_col = None
    for col in range(cols):
        if board[0][col] != 0:
            continue
        sim_board = [row[:] for row in board]
        for r in range(rows - 1, -1, -1):
            if sim_board[r][col] == 0:
                sim_board[r][col] = 1
                break
        score = evaluate(sim_board)
        if score > best_score:
            best_score = score
            best_col = col
        elif score == best_score:
            if best_col is None:
                best_col = col
            else:
                if abs(col - 3) < abs(best_col - 3):
                    best_col = col
                elif abs(col - 3) == abs(best_col - 3) and col < best_col:
                    best_col = col
                    
    if best_col is not None:
        return best_col
    return 0
