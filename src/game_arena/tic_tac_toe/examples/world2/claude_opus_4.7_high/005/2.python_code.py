
import time

WIN_LINES = []
for r in range(4):
    WIN_LINES.append([(r, c) for c in range(4)])
for c in range(4):
    WIN_LINES.append([(r, c) for r in range(4)])
WIN_LINES.append([(i, i) for i in range(4)])
WIN_LINES.append([(i, 3 - i) for i in range(4)])

CELL_LINES = {}
for r in range(4):
    for c in range(4):
        CELL_LINES[(r, c)] = [i for i, line in enumerate(WIN_LINES) if (r, c) in line]


def check_winner(board):
    for line in WIN_LINES:
        s = board[line[0][0]][line[0][1]] + board[line[1][0]][line[1][1]] + \
            board[line[2][0]][line[2][1]] + board[line[3][0]][line[3][1]]
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0


def evaluate(board):
    score = 0
    weights = [0, 1, 10, 100, 0]
    for line in WIN_LINES:
        p = 0
        o = 0
        for r, c in line:
            v = board[r][c]
            if v == 1:
                p += 1
            elif v == -1:
                o += 1
        if p and o:
            continue
        if p:
            score += weights[p]
        elif o:
            score -= weights[o]
    return score


def get_moves(board):
    moves = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                moves.append((r, c))
    moves.sort(key=lambda m: abs(m[0] - 1.5) + abs(m[1] - 1.5))
    return moves


class Timeout(Exception):
    pass


def negamax(board, depth, alpha, beta, player, deadline):
    if time.time() > deadline:
        raise Timeout
    w = check_winner(board)
    if w != 0:
        return -100000 * (depth + 1)  # previous player won => loss for current
    if depth == 0:
        return evaluate(board) * player
    moves = get_moves(board)
    if not moves:
        return 0
    best = -10 ** 9
    for r, c in moves:
        board[r][c] = player
        val = -negamax(board, depth - 1, -beta, -alpha, -player, deadline)
        board[r][c] = 0
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def policy(board):
    b = [row[:] for row in board]
    moves = get_moves(b)
    if not moves:
        return (0, 0)

    # Opening: take a strong center cell
    empty_count = sum(1 for r in range(4) for c in range(4) if b[r][c] == 0)
    if empty_count == 16:
        return (1, 1)
    if empty_count == 15 and b[1][1] == 0:
        return (1, 1)

    # Immediate win
    for r, c in moves:
        b[r][c] = 1
        if check_winner(b) == 1:
            b[r][c] = 0
            return (r, c)
        b[r][c] = 0
    # Immediate block
    for r, c in moves:
        b[r][c] = -1
        if check_winner(b) == -1:
            b[r][c] = 0
            return (r, c)
        b[r][c] = 0

    deadline = time.time() + 0.85
    best_move = moves[0]

    try:
        for depth in range(1, 17):
            current_best = None
            current_best_val = -10 ** 9
            alpha = -10 ** 9
            beta = 10 ** 9
            for r, c in moves:
                b[r][c] = 1
                val = -negamax(b, depth - 1, -beta, -alpha, -1, deadline)
                b[r][c] = 0
                if val > current_best_val:
                    current_best_val = val
                    current_best = (r, c)
                if val > alpha:
                    alpha = val
            if current_best is not None:
                best_move = current_best
                moves.remove(best_move)
                moves.insert(0, best_move)
            if current_best_val >= 90000:
                break
    except Timeout:
        pass

    return best_move
