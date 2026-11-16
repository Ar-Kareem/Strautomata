
from functools import lru_cache

def check_win_tuple(board_tuple, player):
    # Check rows
    for i in range(3):
        if board_tuple[i][0] == player and board_tuple[i][1] == player and board_tuple[i][2] == player:
            return True
    # Check columns
    for i in range(3):
        if board_tuple[0][i] == player and board_tuple[1][i] == player and board_tuple[2][i] == player:
            return True
    # Check diagonals
    if board_tuple[0][0] == player and board_tuple[1][1] == player and board_tuple[2][2] == player:
        return True
    if board_tuple[0][2] == player and board_tuple[1][1] == player and board_tuple[2][0] == player:
        return True
    return False

def available_moves_tuple(board_tuple):
    moves = []
    for i in range(3):
        for j in range(3):
            if board_tuple[i][j] == 0:
                moves.append((i, j))
    return moves

def make_move_tuple(board_tuple, move, player):
    row, col = move
    new_board = [list(row) for row in board_tuple]
    new_board[row][col] = player
    return tuple(tuple(row) for row in new_board)

@lru_cache(maxsize=None)
def minimax(board_tuple, is_our_turn):
    # Check terminal conditions
    if check_win_tuple(board_tuple, 1):
        return 1
    if check_win_tuple(board_tuple, -1):
        return -1
    moves = available_moves_tuple(board_tuple)
    if not moves:
        return 0

    if is_our_turn:
        best_score = -2
        for move in moves:
            new_board = make_move_tuple(board_tuple, move, 1)
            score = minimax(new_board, False)
            if score == 1:
                return 1
            if score > best_score:
                best_score = score
        return best_score
    else:
        best_score = 2
        for move in moves:
            new_board = make_move_tuple(board_tuple, move, -1)
            score = minimax(new_board, True)
            if score == -1:
                return -1
            if score < best_score:
                best_score = score
        return best_score

def policy(board):
    board_tuple = tuple(tuple(row) for row in board)
    moves = available_moves_tuple(board_tuple)
    best_score = -2
    best_move = None
    for move in moves:
        new_board = make_move_tuple(board_tuple, move, 1)
        score = minimax(new_board, False)
        if score == 1:
            return move
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
