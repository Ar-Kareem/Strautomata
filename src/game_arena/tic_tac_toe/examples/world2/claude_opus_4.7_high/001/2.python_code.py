
import time

LINES = []
for i in range(4):
    LINES.append([(i,j) for j in range(4)])
    LINES.append([(j,i) for j in range(4)])
LINES.append([(i,i) for i in range(4)])
LINES.append([(i,3-i) for i in range(4)])

LINE_WEIGHTS = [0, 1, 10, 100, 10000]

def check_win(board, player):
    for line in LINES:
        if all(board[r][c] == player for r, c in line):
            return True
    return False

def evaluate(board):
    score = 0
    for line in LINES:
        c1 = 0; cm = 0
        for r, c in line:
            v = board[r][c]
            if v == 1: c1 += 1
            elif v == -1: cm += 1
        if c1 > 0 and cm > 0:
            continue
        if c1 > 0:
            score += LINE_WEIGHTS[c1]
        elif cm > 0:
            score -= LINE_WEIGHTS[cm]
    return score

def get_moves(board):
    return [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]

class TimeUp(Exception):
    pass

_start = 0.0
_limit = 0.8

def negamax(board, player, depth, alpha, beta):
    if time.time() - _start > _limit:
        raise TimeUp()
    moves = get_moves(board)
    if not moves:
        return 0
    if depth == 0:
        return player * evaluate(board)
    # order moves: closer to center first
    moves.sort(key=lambda m: abs(m[0]-1.5) + abs(m[1]-1.5))
    best = -10**9
    for r, c in moves:
        board[r][c] = player
        if check_win(board, player):
            board[r][c] = 0
            return 100000 + depth
        val = -negamax(board, -player, depth-1, -beta, -alpha)
        board[r][c] = 0
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(board):
    global _start
    _start = time.time()
    b = [row[:] for row in board]
    moves = get_moves(b)
    if not moves:
        return (0, 0)
    if len(moves) == 16:
        return (1, 1)
    # Immediate win check
    for r, c in moves:
        b[r][c] = 1
        if check_win(b, 1):
            b[r][c] = 0
            return (r, c)
        b[r][c] = 0
    # Immediate block check
    for r, c in moves:
        b[r][c] = -1
        if check_win(b, -1):
            b[r][c] = 0
            return (r, c)
        b[r][c] = 0

    best_move = moves[0]
    moves.sort(key=lambda m: abs(m[0]-1.5) + abs(m[1]-1.5))

    try:
        for depth in range(1, 17):
            current_best = None
            current_val = -10**9
            alpha = -10**9
            beta = 10**9
            for r, c in moves:
                b[r][c] = 1
                if check_win(b, 1):
                    b[r][c] = 0
                    return (r, c)
                val = -negamax(b, -1, depth-1, -beta, -alpha)
                b[r][c] = 0
                if val > current_val:
                    current_val = val
                    current_best = (r, c)
                if current_val > alpha:
                    alpha = current_val
            if current_best is not None:
                best_move = current_best
                # Move best to front for next iteration
                moves.remove(best_move)
                moves.insert(0, best_move)
            if current_val >= 90000:
                break
            if time.time() - _start > _limit * 0.6:
                break
    except TimeUp:
        pass
    return best_move
