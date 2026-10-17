
import numpy as np
import time

DIRS = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]
DIR_DELTA = {
    'U': (-1, 0),
    'D': (1, 0),
    'L': (0, -1),
    'R': (0, 1)
}

start_time = 0

class TimeoutException(Exception):
    pass

def check_time():
    if time.perf_counter() - start_time > 0.9:
        raise TimeoutException()

def policy(you, opponent):
    global start_time
    start_time = time.perf_counter()

    # Parse input: support both flat list of 30 and list of 5 lists
    if isinstance(you, list) and len(you) == 5 and isinstance(you[0], list):
        you_arr = np.array(you, dtype=int)
        opp_arr = np.array(opponent, dtype=int)
    else:
        you_arr = np.array(you, dtype=int).reshape(5, 6)
        opp_arr = np.array(opponent, dtype=int).reshape(5, 6)

    board = np.zeros((5, 6), dtype=int)
    board[you_arr == 1] = 1
    board[opp_arr == 1] = -1

    moves = get_legal_moves(board, 1)
    if not moves:
        return "0,0,U"  # fallback (should never be reached if we have a move)

    # Order root moves for better pruning
    moves.sort(key=lambda m: evaluate(apply_move(board, m, 1)), reverse=True)

    best_move = moves[0]
    depth = 1
    try:
        while True:
            current_best = None
            value = -float('inf')
            alpha = -float('inf')
            beta = float('inf')
            for move in moves:
                new_board = apply_move(board, move, 1)
                move_val = minimax(new_board, depth - 1, alpha, beta, False)
                if move_val > value:
                    value = move_val
                    current_best = move
                alpha = max(alpha, value)
            if current_best is not None:
                best_move = current_best
            depth += 1
    except TimeoutException:
        pass

    return f"{best_move[0]},{best_move[1]},{best_move[2]}"

def get_legal_moves(board, player):
    moves = []
    rows, cols = board.shape
    opp = -player
    for r in range(rows):
        for c in range(cols):
            if board[r, c] == player:
                for dr, dc, d in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and board[nr, nc] == opp:
                        moves.append((r, c, d))
    return moves

def apply_move(board, move, player):
    r, c, d = move
    dr, dc = DIR_DELTA[d]
    new_board = board.copy()
    new_board[r, c] = 0
    new_board[r + dr, c + dc] = player
    return new_board

def evaluate(board):
    us = np.count_nonzero(board == 1)
    opp = np.count_nonzero(board == -1)
    material = us - opp
    our_moves = len(get_legal_moves(board, 1))
    opp_moves = len(get_legal_moves(board, -1))
    mobility = (our_moves - opp_moves) * 0.1
    return material + mobility

def minimax(board, depth, alpha, beta, maximizing):
    check_time()
    if depth == 0:
        return evaluate(board)

    player = 1 if maximizing else -1
    moves = get_legal_moves(board, player)

    if not moves:
        # Player to move has no legal moves: they lose
        return -1000 if maximizing else 1000

    if maximizing:
        value = -float('inf')
        moves.sort(key=lambda m: evaluate(apply_move(board, m, player)), reverse=True)
        for move in moves:
            new_board = apply_move(board, move, player)
            value = max(value, minimax(new_board, depth - 1, alpha, beta, False))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = float('inf')
        moves.sort(key=lambda m: evaluate(apply_move(board, m, player)), reverse=False)
        for move in moves:
            new_board = apply_move(board, move, player)
            value = min(value, minimax(new_board, depth - 1, alpha, beta, True))
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value
