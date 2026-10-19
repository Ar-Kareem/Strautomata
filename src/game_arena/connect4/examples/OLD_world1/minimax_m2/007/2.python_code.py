
WINDOWS = []

def generate_windows():
    global WINDOWS
    WINDOWS = []
    # Horizontal windows
    for r in range(6):
        for c in range(4):
            WINDOWS.append([(r, c), (r, c+1), (r, c+2), (r, c+3)])
    # Vertical windows
    for r in range(3):
        for c in range(7):
            WINDOWS.append([(r, c), (r+1, c), (r+2, c), (r+3, c)])
    # Diagonal down-right
    for r in range(3):
        for c in range(4):
            WINDOWS.append([(r, c), (r+1, c+1), (r+2, c+2), (r+3, c+3)])
    # Diagonal up-right
    for r in range(3, 6):
        for c in range(4):
            WINDOWS.append([(r, c), (r-1, c+1), (r-2, c+2), (r-3, c+3)])

generate_windows()

def evaluate(board, player):
    score = 0
    for window in WINDOWS:
        vals = []
        for r, c in window:
            vals.append(board[r][c])
        cnt_player = vals.count(player)
        cnt_opponent = vals.count(-player)
        cnt_empty = vals.count(0)
        
        if cnt_player == 4:
            score += 100000
        elif cnt_opponent == 4:
            score -= 100000
        else:
            if cnt_player == 3 and cnt_empty == 1:
                score += 100
            elif cnt_player == 2 and cnt_empty == 2:
                score += 10
            elif cnt_player == 1 and cnt_empty == 3:
                score += 1
                
            if cnt_opponent == 3 and cnt_empty == 1:
                score -= 100
            elif cnt_opponent == 2 and cnt_empty == 2:
                score -= 10
            elif cnt_opponent == 1 and cnt_empty == 3:
                score -= 1
    return score

def has_won(board, player):
    for window in WINDOWS:
        vals = []
        for r, c in window:
            vals.append(board[r][c])
        if vals.count(player) == 4:
            return True
    return False

def drop_disc(board, col, player):
    for r in range(5, -1, -1):
        if board[r][col] == 0:
            new_board = [row[:] for row in board]
            new_board[r][col] = player
            return new_board
    return None

def policy(board):
    for col in range(7):
        new_board = drop_disc(board, col, 1)
        if new_board is not None and has_won(new_board, 1):
            return col
            
    best_score = -10**9
    best_col = 0
    for col in range(7):
        new_board = drop_disc(board, col, 1)
        if new_board is None:
            continue
            
        min_opp_score = 10**9
        found_blocked = False
        for opp_col in range(7):
            opp_board = drop_disc(new_board, opp_col, -1)
            if opp_board is None:
                continue
            if has_won(opp_board, -1):
                min_opp_score = -10**9
                found_blocked = True
                break
            else:
                score = evaluate(opp_board, 1)
                if score < min_opp_score:
                    min_opp_score = score
                    
        if not found_blocked:
            if min_opp_score > best_score:
                best_score = min_opp_score
                best_col = col
            elif min_opp_score == best_score:
                if abs(col - 3) < abs(best_col - 3):
                    best_col = col
                    
    return best_col
