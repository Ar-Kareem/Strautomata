
import math
import time

def policy(board):
    start_time = time.time()
    depth = 1
    best_move = None
    time_limit = 0.9

    while time.time() - start_time < time_limit:
        moves = ordered_moves(board)
        if not moves:
            return 0

        best_col = None
        best_value = -math.inf
        alpha = -math.inf
        beta = math.inf

        for col in moves:
            new_board = make_move(board, col, 1)
            value = minimax(new_board, depth-1, alpha, beta, False)

            if value > best_value:
                best_value = value
                best_col = col

            alpha = max(alpha, value)

            if time.time() - start_time >= time_limit:
                break

        best_move = best_col
        depth += 1

    return best_move

def ordered_moves(board):
    order = [3, 2, 4, 1, 5, 0, 6]
    moves = []
    for col in order:
        if board[0][col] == 0:
            moves.append(col)
    return moves

def make_move(board, col, player):
    new_board = [row[:] for row in board]
    for r in range(5, -1, -1):
        if new_board[r][col] == 0:
            new_board[r][col] = player
            break
    return new_board

def check_win(board, player):
    # Horizontal
    for r in range(6):
        for c in range(4):
            if board[r][c] == player and board[r][c+1] == player and board[r][c+2] == player and board[r][c+3] == player:
                return True
    # Vertical
    for r in range(3):
        for c in range(7):
            if board[r][c] == player and board[r+1][c] == player and board[r+2][c] == player and board[r+3][c] == player:
                return True
    # Diagonal down-right
    for r in range(3):
        for c in range(4):
            if board[r][c] == player and board[r+1][c+1] == player and board[r+2][c+2] == player and board[r+3][c+3] == player:
                return True
    # Diagonal up-right
    for r in range(3, 6):
        for c in range(4):
            if board[r][c] == player and board[r-1][c+1] == player and board[r-2][c+2] == player and board[r-3][c+3] == player:
                return True
    return False

def terminal_value(board):
    if check_win(board, 1):
        return 100000
    if check_win(board, -1):
        return -100000
    for r in range(6):
        for c in range(7):
            if board[r][c] == 0:
                return None
    return 0

def heuristic(board):
    score = 0
    
    # Center column bonus
    center_col = 3
    for r in range(6):
        if board[r][center_col] == 1:
            score += 1
        elif board[r][center_col] == -1:
            score -= 1

    # Horizontal windows
    for r in range(6):
        for c in range(4):
            window = [board[r][c], board[r][c+1], board[r][c+2], board[r][c+3]]
            score += score_window(window)

    # Vertical windows
    for r in range(3):
        for c in range(7):
            window = [board[r][c], board[r+1][c], board[r+2][c], board[r+3][c]]
            score += score_window(window)

    # Diagonal down-right windows
    for r in range(3):
        for c in range(4):
            window = [board[r][c], board[r+1][c+1], board[r+2][c+2], board[r+3][c+3]]
            score += score_window(window)

    # Diagonal up-right windows
    for r in range(3, 6):
        for c in range(4):
            window = [board[r][c], board[r-1][c+1], board[r-2][c+2], board[r-3][c+3]]
            score += score_window(window)

    return score

def score_window(window):
    count1 = window.count(1)
    count_minus1 = window.count(-1)
    empty = 4 - count1 - count_minus1
    score = 0

    if count1 == 4:
        score += 100
    elif count1 == 3 and empty == 1:
        score += 5
    elif count1 == 2 and empty == 2:
        score += 2
    elif count1 == 1 and empty == 3:
        score += 0.5

    if count_minus1 == 4:
        score -= 100
    elif count_minus1 == 3 and empty == 1:
        score -= 6
    elif count_minus1 == 2 and empty == 2:
        score -= 2
    elif count_minus1 == 1 and empty == 3:
        score -= 0.5

    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    value = terminal_value(board)
    if value is not None:
        return value

    if depth == 0:
        return heuristic(board)

    if maximizing_player:
        max_eval = -math.inf
        for col in ordered_moves(board):
            new_board = make_move(board, col, 1)
            eval = minimax(new_board, depth-1, alpha, beta, False)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for col in ordered_moves(board):
            new_board = make_move(board, col, -1)
            eval = minimax(new_board, depth-1, alpha, beta, True)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval
