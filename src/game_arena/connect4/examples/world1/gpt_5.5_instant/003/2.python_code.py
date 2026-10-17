
import math
import time

ROWS = 6
COLS = 7
WIN_SCORE = 10**9
CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]

def policy(board: list[list[int]]) -> int:
    start = time.time()
    time_limit = 0.92

    b = [row[:] for row in board]

    legal = valid_moves(b)
    if not legal:
        return 0

    # Opening preference: center is strongest.
    if 3 in legal and count_discs(b) <= 1:
        return 3

    # Immediate win.
    for c in CENTER_ORDER:
        if c in legal:
            r = next_row(b, c)
            b[r][c] = 1
            if is_win_from(b, r, c, 1):
                b[r][c] = 0
                return c
            b[r][c] = 0

    # Immediate block.
    for c in CENTER_ORDER:
        if c in legal:
            r = next_row(b, c)
            b[r][c] = -1
            if is_win_from(b, r, c, -1):
                b[r][c] = 0
                return c
            b[r][c] = 0

    best_move = legal[0]
    best_score = -math.inf

    # Iterative deepening. Usually reaches depth 5-7 under 1 second.
    max_depth = choose_depth(b)
    for depth in range(1, max_depth + 1):
        if time.time() - start > time_limit:
            break

        current_best = best_move
        current_score = -math.inf
        alpha = -math.inf
        beta = math.inf

        for c in ordered_moves(b):
            if time.time() - start > time_limit:
                break

            r = next_row(b, c)
            b[r][c] = 1

            if is_win_from(b, r, c, 1):
                score = WIN_SCORE - (max_depth - depth)
            else:
                score = minimax(b, depth - 1, alpha, beta, False, start, time_limit)

            b[r][c] = 0

            if score > current_score:
                current_score = score
                current_best = c

            alpha = max(alpha, current_score)

        if time.time() - start <= time_limit:
            best_move = current_best
            best_score = current_score

            if best_score >= WIN_SCORE // 2:
                break

    if best_move in valid_moves(b):
        return best_move

    return fallback_move(b)


def choose_depth(board):
    discs = count_discs(board)
    if discs < 10:
        return 6
    if discs < 24:
        return 7
    return 8


def minimax(board, depth, alpha, beta, maximizing, start, time_limit):
    if time.time() - start > time_limit:
        return evaluate(board)

    legal = valid_moves(board)
    if depth == 0 or not legal:
        return evaluate(board)

    if maximizing:
        value = -math.inf
        for c in ordered_moves(board):
            r = next_row(board, c)
            board[r][c] = 1

            if is_win_from(board, r, c, 1):
                score = WIN_SCORE + depth
            else:
                score = minimax(board, depth - 1, alpha, beta, False, start, time_limit)

            board[r][c] = 0
            value = max(value, score)
            alpha = max(alpha, value)

            if alpha >= beta:
                break

        return value
    else:
        value = math.inf
        for c in ordered_moves(board):
            r = next_row(board, c)
            board[r][c] = -1

            if is_win_from(board, r, c, -1):
                score = -WIN_SCORE - depth
            else:
                score = minimax(board, depth - 1, alpha, beta, True, start, time_limit)

            board[r][c] = 0
            value = min(value, score)
            beta = min(beta, value)

            if alpha >= beta:
                break

        return value


def valid_moves(board):
    return [c for c in range(COLS) if board[0][c] == 0]


def ordered_moves(board):
    legal_set = set(valid_moves(board))
    return [c for c in CENTER_ORDER if c in legal_set]


def next_row(board, col):
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return -1


def count_discs(board):
    total = 0
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] != 0:
                total += 1
    return total


def fallback_move(board):
    for c in CENTER_ORDER:
        if board[0][c] == 0:
            return c
    for c in range(COLS):
        if board[0][c] == 0:
            return c
    return 0


def is_win_from(board, row, col, player):
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 1
        rr, cc = row + dr, col + dc
        while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
            count += 1
            rr += dr
            cc += dc

        rr, cc = row - dr, col - dc
        while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
            count += 1
            rr -= dr
            cc -= dc

        if count >= 4:
            return True
    return False


def evaluate(board):
    score = 0

    # Center control.
    center_col = COLS // 2
    center_count = sum(1 for r in range(ROWS) if board[r][center_col] == 1)
    opp_center_count = sum(1 for r in range(ROWS) if board[r][center_col] == -1)
    score += center_count * 9
    score -= opp_center_count * 9

    # Slight preference for near-center columns.
    weights = [3, 4, 5, 7, 5, 4, 3]
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == 1:
                score += weights[c]
            elif board[r][c] == -1:
                score -= weights[c]

    # Score all four-cell windows.
    for r in range(ROWS):
        for c in range(COLS - 3):
            score += score_window([board[r][c+i] for i in range(4)])

    for c in range(COLS):
        for r in range(ROWS - 3):
            score += score_window([board[r+i][c] for i in range(4)])

    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            score += score_window([board[r+i][c+i] for i in range(4)])

    for r in range(ROWS - 3):
        for c in range(3, COLS):
            score += score_window([board[r+i][c-i] for i in range(4)])

    # Threat bonus for immediately playable winning squares.
    my_threats = immediate_wins(board, 1)
    opp_threats = immediate_wins(board, -1)
    score += 600 * len(my_threats)
    score -= 750 * len(opp_threats)

    # Multiple simultaneous threats are often decisive.
    if len(my_threats) >= 2:
        score += 2500
    if len(opp_threats) >= 2:
        score -= 3000

    return score


def score_window(window):
    my_count = window.count(1)
    opp_count = window.count(-1)
    empty_count = window.count(0)

    if my_count > 0 and opp_count > 0:
        return 0

    score = 0

    if my_count == 4:
        score += WIN_SCORE
    elif my_count == 3 and empty_count == 1:
        score += 120
    elif my_count == 2 and empty_count == 2:
        score += 18
    elif my_count == 1 and empty_count == 3:
        score += 2

    if opp_count == 4:
        score -= WIN_SCORE
    elif opp_count == 3 and empty_count == 1:
        score -= 150
    elif opp_count == 2 and empty_count == 2:
        score -= 22
    elif opp_count == 1 and empty_count == 3:
        score -= 2

    return score


def immediate_wins(board, player):
    wins = []
    for c in valid_moves(board):
        r = next_row(board, c)
        board[r][c] = player
        if is_win_from(board, r, c, player):
            wins.append(c)
        board[r][c] = 0
    return wins
