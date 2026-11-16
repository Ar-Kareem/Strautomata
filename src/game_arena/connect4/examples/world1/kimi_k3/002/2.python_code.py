
import time

INF = 10**12
WIN_SCORE = 10**9
DEADLINE = 0.0
NODES = 0

ORDER = (3, 2, 4, 1, 5, 0, 6)
HEURISTIC = (0, 2, 20, 150, 100000)

WINDOWS = []
for r in range(6):
    for c in range(4):
        WINDOWS.append(((r, c), (r, c + 1), (r, c + 2), (r, c + 3)))
for r in range(3):
    for c in range(7):
        WINDOWS.append(((r, c), (r + 1, c), (r + 2, c), (r + 3, c)))
for r in range(3):
    for c in range(4):
        WINDOWS.append(((r, c), (r + 1, c + 1), (r + 2, c + 2), (r + 3, c + 3)))
for r in range(3):
    for c in range(3, 7):
        WINDOWS.append(((r, c), (r + 1, c - 1), (r + 2, c - 2), (r + 3, c - 3)))

class SearchTimeout(Exception):
    pass

def legal_moves(board):
    return [c for c in ORDER if board[0][c] == 0]

def drop_row(board, col):
    for r in range(5, -1, -1):
        if board[r][col] == 0:
            return r
    return -1

def wins_from(board, row, col, player):
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        total = 1
        rr, cc = row + dr, col + dc
        while 0 <= rr < 6 and 0 <= cc < 7 and board[rr][cc] == player:
            total += 1
            rr += dr
            cc += dc
        rr, cc = row - dr, col - dc
        while 0 <= rr < 6 and 0 <= cc < 7 and board[rr][cc] == player:
            total += 1
            rr -= dr
            cc -= dc
        if total >= 4:
            return True
    return False

def evaluate(board):
    score = 0
    for r in range(6):
        v = board[r][3]
        if v == 1:
            score += 3
        elif v == -1:
            score -= 3

    for window in WINDOWS:
        ours = 0
        opps = 0
        for r, c in window:
            v = board[r][c]
            if v == 1:
                ours += 1
            elif v == -1:
                opps += 1
        if opps == 0 and ours:
            score += HEURISTIC[ours]
        elif ours == 0 and opps:
            score -= HEURISTIC[opps]
    return score

def order_moves(board, moves, preferred=None):
    def key(c):
        return (c != preferred if preferred is not None else False, abs(c - 3))
    if preferred is None:
        return moves[:]
    return sorted(moves, key=key)

def search(board, depth, alpha, beta, player):
    global NODES, DEADLINE
    NODES += 1
    if (NODES & 1023) == 0 and time.time() > DEADLINE:
        raise SearchTimeout

    moves = legal_moves(board)
    if not moves:
        return 0
    if depth == 0:
        return evaluate(board)

    if player == 1:
        value = -INF
        for c in order_moves(board, moves):
            r = drop_row(board, c)
            board[r][c] = 1
            if wins_from(board, r, c, 1):
                child = WIN_SCORE + depth
            else:
                child = search(board, depth - 1, alpha, beta, -1)
            board[r][c] = 0
            if child > value:
                value = child
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
        return value
    else:
        value = INF
        for c in order_moves(board, moves):
            r = drop_row(board, c)
            board[r][c] = -1
            if wins_from(board, r, c, -1):
                child = -WIN_SCORE - depth
            else:
                child = search(board, depth - 1, alpha, beta, 1)
            board[r][c] = 0
            if child < value:
                value = child
            if value < beta:
                beta = value
            if beta <= alpha:
                break
        return value

def policy(board: list[list[int]]) -> int:
    global DEADLINE, NODES
    DEADLINE = time.time() + 0.88
    NODES = 0

    moves = legal_moves(board)
    if not moves:
        return 0

    fallback = 3 if board[0][3] == 0 else moves[0]

    # Win immediately.
    for c in moves:
        r = drop_row(board, c)
        board[r][c] = 1
        ok = wins_from(board, r, c, 1)
        board[r][c] = 0
        if ok:
            return c

    # Block the opponent's only immediate win.
    opponent_wins = []
    for c in moves:
        r = drop_row(board, c)
        board[r][c] = -1
        if wins_from(board, r, c, -1):
            opponent_wins.append(c)
        board[r][c] = 0
    if len(opponent_wins) == 1:
        return opponent_wins[0]

    best_move = fallback
    try:
        for depth in range(1, 13):
            if time.time() > DEADLINE:
                break
            alpha = -INF
            beta = INF
            local_best = best_move
            local_value = -INF
            completed = True

            for c in order_moves(board, moves, preferred=best_move):
                if time.time() > DEADLINE:
                    completed = False
                    break
                r = drop_row(board, c)
                board[r][c] = 1
                if wins_from(board, r, c, 1):
                    value = WIN_SCORE + depth
                else:
                    value = search(board, depth - 1, alpha, beta, -1)
                board[r][c] = 0

                if value > local_value:
                    local_value = value
                    local_best = c
                if local_value > alpha:
                    alpha = local_value

            if completed:
                best_move = local_best
                if abs(local_value) > WIN_SCORE // 2:
                    break
    except SearchTimeout:
        pass

    if best_move in moves:
        return best_move
    return fallback
