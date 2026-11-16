
import math

def drop_disc(board, col, player):
    # Create a deep copy of the board
    new_board = [row[:] for row in board]
    # Find the lowest available row in the column
    for r in range(5, -1, -1):
        if new_board[r][col] == 0:
            new_board[r][col] = player
            break
    return new_board

def check_win(board, player):
    # Check horizontal
    for r in range(6):
        for c in range(4):
            if (board[r][c] == player and board[r][c+1] == player and 
                board[r][c+2] == player and board[r][c+3] == player):
                return True
    # Check vertical
    for c in range(7):
        for r in range(3):
            if (board[r][c] == player and board[r+1][c] == player and 
                board[r+2][c] == player and board[r+3][c] == player):
                return True
    # Check down-right diagonals
    for r in range(3):
        for c in range(4):
            if (board[r][c] == player and board[r+1][c+1] == player and 
                board[r+2][c+2] == player and board[r+3][c+3] == player):
                return True
    # Check down-left diagonals
    for r in range(3):
        for c in range(3,7):
            if (board[r][c] == player and board[r+1][c-1] == player and 
                board[r+2][c-2] == player and board[r+3][c-3] == player):
                return True
    return False

def evaluate_window(window, root_player):
    score = 0
    opp = -root_player
    count_p = window.count(root_player)
    count_o = window.count(opp)

    if count_p == 4:
        score += 100000
    elif count_p == 3:
        score += 1000
    elif count_p == 2:
        score += 100
    elif count_p == 1:
        score += 10

    if count_o == 4:
        score -= 100000
    elif count_o == 3:
        score -= 1000
    elif count_o == 2:
        score -= 100
    elif count_o == 1:
        score -= 10

    return score

def evaluate_board(board, root_player):
    score = 0
    # Center column bonus (column index 3)
    center_array = [board[i][3] for i in range(6)]
    center_count = center_array.count(root_player)
    score += center_count * 3

    # Horizontal windows
    for r in range(6):
        for c in range(4):
            window = [board[r][c], board[r][c+1], board[r][c+2], board[r][c+3]]
            score += evaluate_window(window, root_player)

    # Vertical windows
    for c in range(7):
        for r in range(3):
            window = [board[r][c], board[r+1][c], board[r+2][c], board[r+3][c]]
            score += evaluate_window(window, root_player)

    # Down-right diagonals
    for r in range(3):
        for c in range(4):
            window = [board[r][c], board[r+1][c+1], board[r+2][c+2], board[r+3][c+3]]
            score += evaluate_window(window, root_player)

    # Down-left diagonals
    for r in range(3):
        for c in range(3,7):
            window = [board[r][c], board[r+1][c-1], board[r+2][c-2], board[r+3][c-3]]
            score += evaluate_window(window, root_player)

    return score

def minimax(board, depth, alpha, beta, current_player, root_player=1):
    # Check for terminal states: win for root_player or opponent, or depth==0
    if check_win(board, root_player):
        return 100000
    if check_win(board, -root_player):
        return -100000

    if depth == 0:
        return evaluate_board(board, root_player)

    # Generate all valid moves (columns not full)
    moves = [c for c in range(7) if board[0][c] == 0]
    if len(moves) == 0:
        return 0  # draw

    # We'll use the negamax style
    best_score = -math.inf
    for col in moves:
        new_board = drop_disc(board, col, current_player)
        # We use the negated score because we are in the opponent's perspective for the next level
        score = -minimax(new_board, depth-1, -beta, -alpha, -current_player, root_player)
        best_score = max(best_score, score)
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    return best_score

def policy(board):
    depth = 4
    best_score = -math.inf
    best_col = None
    for col in range(7):
        if board[0][col] == 0:  # column not full
            new_board = drop_disc(board, col, 1)  # our move
            score = minimax(new_board, depth-1, -math.inf, math.inf, -1, 1)
            if score > best_score:
                best_score = score
                best_col = col
    return best_col
