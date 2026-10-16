
from functools import lru_cache

def check_winner(board_tuple):
    # Check rows
    for i in range(4):
        row_start = i * 4
        row = board_tuple[row_start:row_start+4]
        if all(x == row[0] and x != 0 for x in row):
            return row[0]
    # Check columns
    for j in range(4):
        col = [board_tuple[j + i*4] for i in range(4)]
        if all(x == col[0] and x != 0 for x in col):
            return col[0]
    # Check main diagonal
    diag1 = [board_tuple[i*5] for i in range(4)]
    if all(x == diag1[0] and x != 0 for x in diag1):
        return diag1[0]
    # Check anti-diagonal
    diag2 = [board_tuple[i*4 + (3-i)] for i in range(4)]
    if all(x == diag2[0] and x != 0 for x in diag2):
        return diag2[0]
    return 0

def is_board_full(board_tuple):
    return all(cell != 0 for cell in board_tuple)

@lru_cache(maxsize=None)
def minimax(board_tuple, player):
    winner = check_winner(board_tuple)
    if winner == 1:
        return (1, None)
    elif winner == -1:
        return (-1, None)
    elif is_board_full(board_tuple):
        return (0, None)

    best_value = float('-inf') if player == 1 else float('inf')
    best_move_index = None
    for i, cell in enumerate(board_tuple):
        if cell == 0:
            new_board = list(board_tuple)
            new_board[i] = player
            new_board_tuple = tuple(new_board)
            value, _ = minimax(new_board_tuple, -player)
            if player == 1:  # Maximize for player 1
                if value > best_value:
                    best_value = value
                    best_move_index = i
            else:  # Minimize for player -1
                if value < best_value:
                    best_value = value
                    best_move_index = i

    return (best_value, best_move_index)

def policy(board):
    board_tuple = tuple(board[i][j] for i in range(4) for j in range(4))
    value, move_index = minimax(board_tuple, 1)
    row = move_index // 4
    col = move_index % 4
    return (row, col)
