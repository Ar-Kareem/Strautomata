
def check_winner(board_tuple):
    lines = [
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6)
    ]
    for a, b, c in lines:
        if board_tuple[a] != 0 and board_tuple[a] == board_tuple[b] == board_tuple[c]:
            return board_tuple[a]
    if 0 not in board_tuple:
        return 0
    return None

from functools import lru_cache

@lru_cache(maxsize=None)
def minimax(board_tuple, current_player):
    result = check_winner(board_tuple)
    if result is not None:
        return result

    if current_player == 1:
        best_score = -2
        for i in range(9):
            if board_tuple[i] == 0:
                new_board = list(board_tuple)
                new_board[i] = 1
                new_board_tuple = tuple(new_board)
                score = minimax(new_board_tuple, -1)
                if score > best_score:
                    best_score = score
                if best_score == 1:
                    break
        return best_score
    else:
        best_score = 2
        for i in range(9):
            if board_tuple[i] == 0:
                new_board = list(board_tuple)
                new_board[i] = -1
                new_board_tuple = tuple(new_board)
                score = minimax(new_board_tuple, 1)
                if score < best_score:
                    best_score = score
                if best_score == -1:
                    break
        return best_score

def policy(board):
    board_list = []
    for row in board:
        board_list.extend(row)
    board_tuple = tuple(board_list)
    
    for i in range(9):
        if board_tuple[i] == 0:
            new_board = list(board_tuple)
            new_board[i] = 1
            new_board_tuple = tuple(new_board)
            if check_winner(new_board_tuple) == 1:
                return (i // 3, i % 3)
    
    for i in range(9):
        if board_tuple[i] == 0:
            new_board = list(board_tuple)
            new_board[i] = -1
            new_board_tuple = tuple(new_board)
            if check_winner(new_board_tuple) == -1:
                return (i // 3, i % 3)
    
    best_move = None
    best_score = -2
    for i in range(9):
        if board_tuple[i] == 0:
            new_board = list(board_tuple)
            new_board[i] = 1
            new_board_tuple = tuple(new_board)
            score = minimax(new_board_tuple, -1)
            if score > best_score:
                best_score = score
                best_move = (i // 3, i % 3)
    
    return best_move
