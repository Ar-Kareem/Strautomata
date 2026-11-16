
import numpy as np
import random

def rotate_quadrant(board, quad, clockwise=True):
    if quad == 0:
        sub = board[:3, :3]
    elif quad == 1:
        sub = board[:3, 3:]
    elif quad == 2:
        sub = board[3:, :3]
    else:
        sub = board[3:, 3:]
    sub[:] = np.rot90(sub, -1 if clockwise else 1)

def has_win(board):
    for row in range(6):
        for col in range(6):
            player = board[row, col]
            if player == 0:
                continue
            # horizontal
            if col + 4 < 6 and np.all(board[row, col:col+5] == player):
                return player
            # vertical
            if row + 4 < 6 and np.all(board[row:row+5, col] == player):
                return player
            # diag1 \
            if row + 4 < 6 and col + 4 < 6 and np.all([board[row+i, col+i] == player for i in range(5)]):
                return player
            # diag2 /
            if row + 4 < 6 and col - 4 >= 0 and np.all([board[row+i, col-i] == player for i in range(5)]):
                return player
    return 0

def count_threats(board, player):
    counts = 0
    # Horizontal
    for r in range(6):
        for c in range(2):  # 0 to 1, to check c to c+4
            line = board[r, c:c+5]
            if np.count_nonzero(line == player) == 4 and np.count_nonzero(line == 0) == 1:
                counts += 1
    # Vertical
    for c in range(6):
        for r in range(2):
            line = board[r:r+5, c]
            if np.count_nonzero(line == player) == 4 and np.count_nonzero(line == 0) == 1:
                counts += 1
    # Diag1 \
    for r in range(2):
        for c in range(2):
            line = np.array([board[r+i, c+i] for i in range(5)])
            if np.count_nonzero(line == player) == 4 and np.count_nonzero(line == 0) == 1:
                counts += 1
    # Diag2 /
    for r in range(2):
        for c in range(4, 6):
            line = np.array([board[r+i, c-i] for i in range(5)])
            if np.count_nonzero(line == player) == 4 and np.count_nonzero(line == 0) == 1:
                counts += 1
    return counts

def evaluate(board):
    win = has_win(board)
    if win == 1:
        return 1000
    elif win == -1:
        return -1000
    else:
        return count_threats(board, 1) - count_threats(board, -1)

def get_legal_moves(board):
    moves = []
    empty = np.where(board == 0)
    for r, c in zip(empty[0], empty[1]):
        for quad in range(4):
            for dir_ in ['L', 'R']:
                moves.append((r, int(c), quad, dir_))  # r is np.int64, convert
    return moves

def apply_move(board, move):
    r, c, quad, dir_str = move
    board[r, c] = 1
    rotate_quadrant(board, quad, dir_str == 'R')

def policy(you, opponent) -> str:
    board = np.array(you) - np.array(opponent)
    moves = get_legal_moves(board)
    best_moves = []
    best_val = -float('inf')
    for move in moves:
        board_copy = board.copy()
        apply_move(board_copy, move)
        val = evaluate(board_copy)
        if val > best_val:
            best_val = val
            best_moves = [move]
        elif val == best_val:
            best_moves.append(move)
    if best_moves:
        chosen_move = random.choice(best_moves)
        r, c, q, d = chosen_move
        return f"{r+1},{c+1},{q},{d}"
    else:
        # Should not happen, but fallback
        return "1,1,0,L"
