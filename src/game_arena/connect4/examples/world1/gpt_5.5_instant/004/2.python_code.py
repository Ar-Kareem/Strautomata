
import time
import math
from functools import lru_cache

ROWS = 6
COLS = 7
CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]
INF = 10**12


def policy(board: list[list[int]]) -> int:
    start = time.perf_counter()
    TIME_LIMIT = 0.92

    try:
        b = tuple(tuple(int(x) for x in row) for row in board)
        legal = legal_moves(b)
        if not legal:
            return 0

        # Immediate win
        for c in CENTER_ORDER:
            if c in legal:
                nb = make_move(b, c, 1)
                if is_win(nb, 1):
                    return c

        # Immediate block
        for c in CENTER_ORDER:
            if c in legal:
                nb = make_move(b, c, -1)
                if is_win(nb, -1):
                    return c

        # Prefer center on empty-ish boards
        if count_pieces(b) <= 1 and 3 in legal:
            return 3

        best_move = legal[0]
        best_score = -INF

        # Dynamic depth: deeper in late game
        empties = sum(row.count(0) for row in b)
        max_depth = 7
        if empties <= 18:
            max_depth = 9
        if empties <= 12:
            max_depth = 11

        cache = {}

        def timed_out():
            return time.perf_counter() - start > TIME_LIMIT

        def minimax(pos, depth, alpha, beta, player):
            # player is side to move: 1 for us, -1 for opponent
            if timed_out():
                raise TimeoutError

            key = (pos, depth, player)
            if key in cache:
                return cache[key]

            lm = legal_moves(pos)

            # Terminal checks via previous position
            if is_win(pos, 1):
                return INF - (42 - sum(r.count(0) for r in pos))
            if is_win(pos, -1):
                return -INF + (42 - sum(r.count(0) for r in pos))
            if depth == 0 or not lm:
                val = evaluate(pos)
                cache[key] = val
                return val

            ordered = ordered_moves(pos, lm, player)

            if player == 1:
                value = -INF
                for col in ordered:
                    child = make_move(pos, col, 1)

                    # Avoid moves that allow opponent immediate win unless forced
                    if depth >= 2:
                        opp_legal = legal_moves(child)
                        bad = False
                        for oc in opp_legal:
                            if is_win(make_move(child, oc, -1), -1):
                                bad = True
                                break
                        if bad:
                            score = -INF // 2
                        else:
                            score = minimax(child, depth - 1, alpha, beta, -1)
                    else:
                        score = minimax(child, depth - 1, alpha, beta, -1)

                    if score > value:
                        value = score
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        break
            else:
                value = INF
                for col in ordered:
                    child = make_move(pos, col, -1)
                    score = minimax(child, depth - 1, alpha, beta, 1)
                    if score < value:
                        value = score
                    beta = min(beta, value)
                    if alpha >= beta:
                        break

            cache[key] = value
            return value

        # Iterative deepening
        for depth in range(3, max_depth + 1):
            if time.perf_counter() - start > TIME_LIMIT:
                break
            current_best = best_move
            current_score = -INF

            for col in ordered_moves(b, legal, 1):
                if time.perf_counter() - start > TIME_LIMIT:
                    raise TimeoutError

                child = make_move(b, col, 1)
                if is_win(child, 1):
                    return col

                score = minimax(child, depth - 1, -INF, INF, -1)

                if score > current_score:
                    current_score = score
                    current_best = col

            best_move = current_best
            best_score = current_score

            if best_score > INF // 2:
                break

        if best_move in legal:
            return int(best_move)
        return int(fallback_move(b))

    except Exception:
        return int(fallback_move(tuple(tuple(int(x) for x in row) for row in board)))


def legal_moves(b):
    return [c for c in CENTER_ORDER if b[0][c] == 0]


def make_move(b, col, player):
    board = [list(r) for r in b]
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            board[r][col] = player
            break
    return tuple(tuple(r) for r in board)


def count_pieces(b):
    return sum(1 for r in range(ROWS) for c in range(COLS) if b[r][c] != 0)


def is_win(b, player):
    # Horizontal
    for r in range(ROWS):
        row = b[r]
        for c in range(COLS - 3):
            if row[c] == player and row[c+1] == player and row[c+2] == player and row[c+3] == player:
                return True

    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            if b[r][c] == player and b[r+1][c] == player and b[r+2][c] == player and b[r+3][c] == player:
                return True

    # Down-right diagonal
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if b[r][c] == player and b[r+1][c+1] == player and b[r+2][c+2] == player and b[r+3][c+3] == player:
                return True

    # Down-left diagonal
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            if b[r][c] == player and b[r+1][c-1] == player and b[r+2][c-2] == player and b[r+3][c-3] == player:
                return True

    return False


def evaluate_window(window):
    own = window.count(1)
    opp = window.count(-1)
    emp = window.count(0)

    if own and opp:
        return 0
    if own == 4:
        return 10000000
    if opp == 4:
        return -10000000
    if own == 3 and emp == 1:
        return 1200
    if own == 2 and emp == 2:
        return 80
    if own == 1 and emp == 3:
        return 5
    if opp == 3 and emp == 1:
        return -1500
    if opp == 2 and emp == 2:
        return -100
    if opp == 1 and emp == 3:
        return -4
    return 0


def evaluate(b):
    if is_win(b, 1):
        return INF
    if is_win(b, -1):
        return -INF

    score = 0

    # Center control
    center_col = [b[r][3] for r in range(ROWS)]
    score += center_col.count(1) * 45
    score -= center_col.count(-1) * 45

    # Adjacent center control
    for c, w in [(2, 18), (4, 18), (1, 7), (5, 7), (0, 2), (6, 2)]:
        cnt1 = sum(1 for r in range(ROWS) if b[r][c] == 1)
        cnt2 = sum(1 for r in range(ROWS) if b[r][c] == -1)
        score += w * (cnt1 - cnt2)

    # Horizontal windows
    for r in range(ROWS):
        for c in range(COLS - 3):
            score += evaluate_window([b[r][c+i] for i in range(4)])

    # Vertical windows
    for c in range(COLS):
        for r in range(ROWS - 3):
            score += evaluate_window([b[r+i][c] for i in range(4)])

    # Diagonal down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            score += evaluate_window([b[r+i][c+i] for i in range(4)])

    # Diagonal down-left
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            score += evaluate_window([b[r+i][c-i] for i in range(4)])

    # Bonus for immediate threats, penalty for opponent threats
    score += 350 * count_immediate_wins(b, 1)
    score -= 500 * count_immediate_wins(b, -1)

    return score


def count_immediate_wins(b, player):
    n = 0
    for c in legal_moves(b):
        if is_win(make_move(b, c, player), player):
            n += 1
    return n


def ordered_moves(b, moves, player):
    scored = []
    for c in moves:
        child = make_move(b, c, player)
        s = 0
        if is_win(child, player):
            s += 10**9
        s += 100 - abs(c - 3) * 10
        # Prefer moves creating multiple threats
        s += 2000 * count_immediate_wins(child, player)
        # Strongly consider blocking opponent threats
        if player == 1:
            s -= 2500 * count_immediate_wins(child, -1)
        else:
            s += 2500 * count_immediate_wins(child, 1)
        scored.append((s, c))
    scored.sort(reverse=True)
    return [c for _, c in scored]


def fallback_move(b):
    legal = [c for c in CENTER_ORDER if b[0][c] == 0]
    if not legal:
        return 0

    # Win if possible
    for c in legal:
        if is_win(make_move(b, c, 1), 1):
            return c

    # Block if needed
    for c in legal:
        if is_win(make_move(b, c, -1), -1):
            return c

    return legal[0]
