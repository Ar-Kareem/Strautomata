
import numpy as np
import time

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
START_TIME = 0
TIME_LIMIT = 0.9


def time_out():
    return time.time() - START_TIME > TIME_LIMIT


def get_moves(board, player):
    moves = []
    amazons = np.argwhere(board == player)
    for fr, fc in amazons:
        for dr, dc in DIRS:
            r, c = fr + dr, fc + dc
            while 0 <= r < 6 and 0 <= c < 6 and board[r, c] == 0:
                for adr, adc in DIRS:
                    ar, ac = r + adr, c + adc
                    while 0 <= ar < 6 and 0 <= ac < 6:
                        if (ar, ac) == (fr, fc):
                            moves.append((fr, fc, r, c, ar, ac))
                            ar += adr
                            ac += adc
                            continue
                        if board[ar, ac] != 0:
                            break
                        moves.append((fr, fc, r, c, ar, ac))
                        ar += adr
                        ac += adc
                r += dr
                c += dc
    return moves


def apply_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    new_board = board.copy()
    new_board[fr, fc] = 0
    new_board[tr, tc] = player
    new_board[ar, ac] = -1
    return new_board


def mobility(board, player):
    count = 0
    amazons = np.argwhere(board == player)
    for fr, fc in amazons:
        for dr, dc in DIRS:
            r, c = fr + dr, fc + dc
            while 0 <= r < 6 and 0 <= c < 6 and board[r, c] == 0:
                count += 1
                r += dr
                c += dc
    return count


def evaluate(board):
    return mobility(board, 1) - mobility(board, 2)


def minimax(board, depth, alpha, beta, maximizing_player, player):
    if time_out():
        return evaluate(board)
    if depth == 0:
        return evaluate(board)
    moves = get_moves(board, player)
    if not moves:
        if player == 1:
            return -10000
        else:
            return 10000
    if maximizing_player:
        max_eval = -float('inf')
        for move in moves:
            new_board = apply_move(board, move, player)
            eval = minimax(new_board, depth - 1, alpha, beta, False, 3 - player)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
            if time_out():
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            new_board = apply_move(board, move, player)
            eval = minimax(new_board, depth - 1, alpha, beta, True, 3 - player)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
            if time_out():
                break
        return min_eval


def policy(board):
    global START_TIME, TIME_LIMIT
    START_TIME = time.time()
    TIME_LIMIT = 0.9
    moves = get_moves(board, 1)
    if not moves:
        # fallback (should not be reached)
        return "0,0:0,1:0,2"
    # sort moves for better pruning
    moves.sort(key=lambda m: evaluate(apply_move(board, m, 1)), reverse=True)
    best_move = moves[0]
    depth = 1
    while True:
        if time_out():
            break
        current_best_move = None
        alpha = -float('inf')
        beta = float('inf')
        for move in moves:
            if time_out():
                break
            new_board = apply_move(board, move, 1)
            val = minimax(new_board, depth - 1, alpha, beta, False, 2)
            if val > alpha:
                alpha = val
                current_best_move = move
        if current_best_move is not None:
            best_move = current_best_move
        depth += 1
        if depth > 10:
            break
    fr, fc, tr, tc, ar, ac = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
