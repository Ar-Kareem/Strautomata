
import copy

def is_win(board, player):
    rows = len(board)
    cols = len(board[0])
    
    # Check horizontal wins
    for r in range(rows):
        for c in range(cols - 3):
            if board[r][c] == player and board[r][c+1] == player and board[r][c+2] == player and board[r][c+3] == player:
                return True
    
    # Check vertical wins
    for r in range(rows - 3):
        for c in range(cols):
            if board[r][c] == player and board[r+1][c] == player and board[r+2][c] == player and board[r+3][c] == player:
                return True
    
    # Check diagonal down-right wins
    for r in range(rows - 3):
        for c in range(cols - 3):
            if board[r][c] == player and board[r+1][c+1] == player and board[r+2][c+2] == player and board[r+3][c+3] == player:
                return True
    
    # Check diagonal up-right wins
    for r in range(3, rows):
        for c in range(cols - 3):
            if board[r][c] == player and board[r-1][c+1] == player and board[r-2][c+2] == player and board[r-3][c+3] == player:
                return True
    
    return False

def evaluate_board(board):
    score = 0
    rows = len(board)
    cols = len(board[0])
    
    def score_window(window):
        count_me = 0
        count_opponent = 0
        count_empty = 0
        for cell in window:
            if cell == 1:
                count_me += 1
            elif cell == -1:
                count_opponent += 1
            else:
                count_empty += 1
        
        if count_me == 4:
            return 100000
        elif count_opponent == 4:
            return -100000
        elif count_me == 3 and count_empty == 1:
            return 100
        elif count_opponent == 3 and count_empty == 1:
            return -100
        elif count_me == 2 and count_empty == 2:
            return 10
        elif count_opponent == 2 and count_empty == 2:
            return -10
        elif count_me == 1 and count_empty == 3:
            return 1
        elif count_opponent == 1 and count_empty == 3:
            return -1
        else:
            return 0
    
    # Horizontal windows
    for r in range(rows):
        for c in range(cols - 3):
            window = [board[r][c], board[r][c+1], board[r][c+2], board[r][c+3]]
            score += score_window(window)
    
    # Vertical windows
    for r in range(rows - 3):
        for c in range(cols):
            window = [board[r][c], board[r+1][c], board[r+2][c], board[r+3][c]]
            score += score_window(window)
    
    # Diagonal down-right windows
    for r in range(rows - 3):
        for c in range(cols - 3):
            window = [board[r][c], board[r+1][c+1], board[r+2][c+2], board[r+3][c+3]]
            score += score_window(window)
    
    # Diagonal up-right windows
    for r in range(3, rows):
        for c in range(cols - 3):
            window = [board[r][c], board[r-1][c+1], board[r-2][c+2], board[r-3][c+3]]
            score += score_window(window)
    
    return score

def find_row(board, col):
    rows = len(board)
    for r in range(rows - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return None

def policy(board: list[list[int]]) -> int:
    rows = len(board)
    cols = len(board[0])
    
    valid_columns = []
    for c in range(cols):
        for r in range(rows):
            if board[r][c] == 0:
                valid_columns.append(c)
                break
    
    best_col = None
    best_score = -float('inf')
    
    for col in valid_columns:
        temp_board = copy.deepcopy(board)
        row_to_drop = find_row(board, col)
        if row_to_drop is None:
            continue  # skip if column is full, though it shouldn't be
        temp_board[row_to_drop][col] = 1
        
        if is_win(temp_board, 1):
            return col
        
        score = evaluate_board(temp_board)
        
        if score > best_score:
            best_score = score
            best_col = col
    
    return best_col if best_col is not None else valid_columns[0]  # fallback to first valid column
