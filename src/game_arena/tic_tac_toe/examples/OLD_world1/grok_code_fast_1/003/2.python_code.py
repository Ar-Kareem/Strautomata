
import copy

def check_winner(board):
    # Check rows
    for row in board:
        if row == [1, 1, 1]:
            return (1, True)
        if row == [-1, -1, -1]:
            return (-1, True)
    # Check columns
    for c in range(3):
        col = [board[i][c] for i in range(3)]
        if col == [1, 1, 1]:
            return (1, True)
        if col == [-1, -1, -1]:
            return (-1, True)
    # Check diagonals
    diag = [board[i][i] for i in range(3)]
    if diag == [1, 1, 1]:
        return (1, True)
    if diag == [-1, -1, -1]:
        return (-1, True)
    anti = [board[i][2 - i] for i in range(3)]
    if anti == [1, 1, 1]:
        return (1, True)
    if anti == [-1, -1, -1]:
        return (-1, True)
    # Check for draw
    if all(board[i][j] != 0 for i in range(3) for j in range(3)):
        return (0, True)
    return (0, False)

def minimax(board, is_maximizing):
    winner, terminal = check_winner(board)
    if terminal:
        return winner

    if is_maximizing:
        max_eval = float('-inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    eval_val = minimax(board, False)
                    board[i][j] = 0
                    max_eval = max(max_eval, eval_val)
        return max_eval
    else:
        min_eval = float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    eval_val = minimax(board, True)
                    board[i][j] = 0
                    min_eval = min(min_eval, eval_val)
        return min_eval

def policy(board: list[list[int]]) -> tuple[int, int]:
    empty_positions = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    best_move = None
    best_value = float('-inf')
    for r, c in empty_positions:
        temp_board = copy.deepcopy(board)
        temp_board[r][c] = 1
        move_value = minimax(temp_board, False)
        if move_value > best_value:
            best_value = move_value
            best_move = (r, c)
    return best_move
