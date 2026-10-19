
import time
import math

ROWS = 6
COLS = 7
WIN_SCORE = 1_000_000
CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]


def policy(board: list[list[int]]) -> int:
    start = time.time()
    time_limit = 0.92

    legal = legal_moves(board)
    if not legal:
        return 0

    # Immediate win
    for c in CENTER_ORDER:
        if c in legal and is_winning_move(board, c, 1):
            return c

    # Immediate block
    for c in CENTER_ORDER:
        if c in legal and is_winning_move(board, c, -1):
            return c

    # If board is nearly empty, take center.
    if board[5][3] == 0:
        return 3

    best_move = legal[0]
    best_score = -math.inf

    empties = sum(row.count(0) for row in board)

    # Practical depth cap for 1 second.
    if empties > 28:
        max_depth = 6
    elif empties > 16:
        max_depth = 8
    else:
        max_depth = 10

    # Iterative deepening.
    for depth in range(1, max_depth + 1):
        if time.time() - start > time_limit:
            break

        current_best_move = best_move
        current_best_score = -math.inf

        alpha = -math.inf
        beta = math.inf

        for col in ordered_moves(board):
            if time.time() - start > time_limit:
                break

            child = make_move_next_perspective(board, col)
            score = -negamax(child, depth - 1, -beta, -alpha, start, time_limit, 1)

            if score > current_best_score:
                current_best_score = score
                current_best_move = col

            alpha = max(alpha, score)

        if time.time() - start <= time_limit:
            best_move = current_best_move
            best_score = current_best_score

            if best_score >= WIN_SCORE // 2:
                break

    if best_move in legal:
        return best_move

    # Absolute safety fallback.
    for c in CENTER_ORDER:
        if c in legal:
            return c

    return legal[0]


def legal_moves(board):
    return [c for c in range(COLS) if board[0][c] == 0]


def ordered_moves(board):
    legal = legal_moves(board)

    winning = []
    blocking = []
    safe_centered = []

    for c in CENTER_ORDER:
        if c not in legal:
            continue
        if is_winning_move(board, c, 1):
            winning.append(c)
        elif is_winning_move(board, c, -1):
            blocking.append(c)
        else:
            safe_centered.append(c)

    return winning + blocking + safe_centered


def drop_row(board, col):
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return -1


def is_winning_move(board, col, player):
    r = drop_row(board, col)
    if r < 0:
        return False

    board[r][col] = player
    won = has_won(board, player)
    board[r][col] = 0
    return won


def make_move_next_perspective(board, col):
    new_board = [row[:] for row in board]
    r = drop_row(new_board, col)
    if r >= 0:
        new_board[r][col] = 1

    # Convert to the next player's perspective:
    # next player sees their discs as 1 and ours as -1.
    for i in range(ROWS):
        for j in range(COLS):
            new_board[i][j] = -new_board[i][j]

    return new_board


def negamax(board, depth, alpha, beta, start, time_limit, ply):
    if time.time() - start > time_limit:
        return evaluate(board)

    # If opponent just won, this position is losing for side to move.
    if has_won(board, -1):
        return -WIN_SCORE + ply

    if has_won(board, 1):
        return WIN_SCORE - ply

    legal = legal_moves(board)

    if not legal:
        return 0

    if depth == 0:
        return evaluate(board)

    # Tactical shortcuts.
    for c in legal:
        if is_winning_move(board, c, 1):
            return WIN_SCORE - ply

    # If opponent has multiple immediate wins, usually losing.
    opp_wins = 0
    forced_block = None
    for c in legal:
        if is_winning_move(board, c, -1):
            opp_wins += 1
            forced_block = c

    if opp_wins >= 2:
        return -WIN_SCORE + ply

    moves = ordered_moves(board)

    # If there is exactly one immediate opponent threat, consider blocking first.
    if opp_wins == 1 and forced_block in moves:
        moves.remove(forced_block)
        moves = [forced_block] + moves

    value = -math.inf

    for col in moves:
        if time.time() - start > time_limit:
            break

        child = make_move_next_perspective(board, col)
        score = -negamax(child, depth - 1, -beta, -alpha, start, time_limit, ply + 1)

        if score > value:
            value = score

        alpha = max(alpha, score)

        if alpha >= beta:
            break

    return value


def has_won(board, player):
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if (
                board[r][c] == player
                and board[r][c + 1] == player
                and board[r][c + 2] == player
                and board[r][c + 3] == player
            ):
                return True

    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            if (
                board[r][c] == player
                and board[r + 1][c] == player
                and board[r + 2][c] == player
                and board[r + 3][c] == player
            ):
                return True

    # Diagonal down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if (
                board[r][c] == player
                and board[r + 1][c + 1] == player
                and board[r + 2][c + 2] == player
                and board[r + 3][c + 3] == player
            ):
                return True

    # Diagonal up-right
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if (
                board[r][c] == player
                and board[r - 1][c + 1] == player
                and board[r - 2][c + 2] == player
                and board[r - 3][c + 3] == player
            ):
                return True

    return False


def evaluate(board):
    if has_won(board, 1):
        return WIN_SCORE
    if has_won(board, -1):
        return -WIN_SCORE

    score = 0

    # Center control is very valuable in Connect 4.
    center_col = [board[r][3] for r in range(ROWS)]
    score += center_col.count(1) * 7
    score -= center_col.count(-1) * 7

    # Slightly reward near-center columns too.
    for r in range(ROWS):
        score += 3 * board[r][2]
        score += 3 * board[r][4]
        score += 1 * board[r][1]
        score += 1 * board[r][5]

    # Score all windows of four.
    for window in all_windows(board):
        score += score_window(window)

    # Penalize moves that allow many immediate opponent wins.
    opp_threats = 0
    my_threats = 0
    for c in legal_moves(board):
        if is_winning_move(board, c, -1):
            opp_threats += 1
        if is_winning_move(board, c, 1):
            my_threats += 1

    score += my_threats * 120
    score -= opp_threats * 180

    return score


def all_windows(board):
    windows = []

    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            windows.append([board[r][c], board[r][c + 1], board[r][c + 2], board[r][c + 3]])

    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            windows.append([board[r][c], board[r + 1][c], board[r + 2][c], board[r + 3][c]])

    # Diagonal down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            windows.append([board[r][c], board[r + 1][c + 1], board[r + 2][c + 2], board[r + 3][c + 3]])

    # Diagonal up-right
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            windows.append([board[r][c], board[r - 1][c + 1], board[r - 2][c + 2], board[r - 3][c + 3]])

    return windows


def score_window(window):
    mine = window.count(1)
    opp = window.count(-1)
    empty = window.count(0)

    if mine > 0 and opp > 0:
        return 0

    if mine == 4:
        return WIN_SCORE
    if opp == 4:
        return -WIN_SCORE

    score = 0

    if mine == 3 and empty == 1:
        score += 100
    elif mine == 2 and empty == 2:
        score += 12
    elif mine == 1 and empty == 3:
        score += 1

    if opp == 3 and empty == 1:
        score -= 120
    elif opp == 2 and empty == 2:
        score -= 14
    elif opp == 1 and empty == 3:
        score -= 1

    return score
