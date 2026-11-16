
import math

def check_valid(board, col):
    return any(board[row][col] == 0 for row in range(6))

def get_possible_moves(board):
    return [col for col in range(7) if check_valid(board, col)]

def make_move(board, col, player):
    new_board = [row[:] for row in board]
    for row in range(5, -1, -1):
        if new_board[row][col] == 0:
            new_board[row][col] = player
            break
    return new_board

def is_win(board, player):
    # Horizontal
    for row in range(6):
        for col in range(4):
            if all(board[row][c] == player for c in range(col, col + 4)):
                return True
    # Vertical
    for col in range(7):
        for row in range(3):
            if all(board[r][col] == player for r in range(row, row + 4)):
                return True
    # Diagonal (positive slope)
    for row in range(3):
        for col in range(4):
            if all(board[row + i][col + i] == player for i in range(4)):
                return True
            if all(board[row + i][col + 3 - i] == player for i in range(4)):
                return True
    return False

def is_full(board):
    return all(board[0][col] != 0 for col in range(7))

def evaluate_window(window, player):
    count_player = window.count(player)
    count_empty = window.count(0)
    if count_player == 4:
        return 1000
    elif count_player == 3 and count_empty == 1:
        return 10
    elif count_player == 2 and count_empty == 2:
        return 1
    return 0

def evaluate(board):
    score = 0
    # Horizontal
    for row in range(6):
        for col in range(4):
            window = [board[row][c] for c in range(col, col + 4)]
            score += evaluate_window(window, 1)
            score -= evaluate_window([w if w == 0 else -w for w in window], 1)  # Opponent's perspective
    # Vertical
    for col in range(7):
        for row in range(3):
            window = [board[r][col] for r in range(row, row + 4)]
            score += evaluate_window(window, 1)
            score -= evaluate_window([w if w == 0 else -w for w in window], 1)
    # Diagonal (positive slope)
    for row in range(3):
        for col in range(4):
            window = [board[row + i][col + i] for i in range(4)]
            score += evaluate_window(window, 1)
            score -= evaluate_window([w if w == 0 else -w for w in window], 1)
    # Diagonal (negative slope)
    for row in range(3):
        for col in range(4):
            window = [board[row + i][col + 3 - i] for i in range(4)]
            score += evaluate_window(window, 1)
            score -= evaluate_window([w if w == 0 else -w for w in window], 1)
    return score

def minimax(board, depth, maximizing, alpha, beta):
    if is_win(board, 1):
        return None, 100000
    if is_win(board, -1):
        return None, -100000
    if depth == 0 or is_full(board):
        return None, evaluate(board)

    possible = get_possible_moves(board)

    if maximizing:
        best_value = -math.inf
        best_col = possible[0] if possible else None
        for col in possible:
            new_board = make_move(board, col, 1)
            _, value = minimax(new_board, depth - 1, False, alpha, beta)
            if value > best_value:
                best_value = value
                best_col = col
            alpha = max(alpha, best_value)
            if alpha >= beta:
                break
        return best_col, best_value
    else:
        best_value = math.inf
        for col in possible:
            new_board = make_move(board, col, -1)
            _, value = minimax(new_board, depth - 1, True, alpha, beta)
            best_value = min(best_value, value)
            beta = min(beta, best_value)
            if beta <= alpha:
                break
        return None, best_value

def policy(board: list[list[int]]) -> int:
    col, _ = minimax(board, 5, True, -math.inf, math.inf)
    return col
