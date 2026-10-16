
from math import inf

ROWS = 6
COLS = 7
CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]


def policy(board: list[list[int]]) -> int:
    # Defensive legal fallback first
    legal = get_legal_moves(board)
    if not legal:
        return 0

    # 1) Immediate winning move
    for c in ordered_moves(board):
        if c in legal:
            nb = make_move(board, c, 1)
            if is_winner(nb, 1):
                return c

    # 2) Immediate block of opponent winning move
    opp_wins = []
    for c in ordered_moves(board):
        if c in legal:
            nb = make_move(board, c, -1)
            if is_winner(nb, -1):
                opp_wins.append(c)
    if opp_wins:
        # Prefer center-most blocking move if multiple
        return sorted(opp_wins, key=lambda x: abs(x - 3))[0]

    # 3) Search
    # Depth tuned for strength/speed balance under 1s.
    depth = choose_depth(board)
    best_col = legal[0]
    best_score = -inf

    alpha = -inf
    beta = inf

    for c in ordered_moves(board):
        if c not in legal:
            continue
        nb = make_move(board, c, 1)

        # If our move gives opponent an immediate win opportunity, search should see it,
        # but apply a light tactical penalty for stability.
        score = -negamax(flip_perspective(nb), depth - 1, -beta, -alpha)

        # Mild bias toward central columns in ties
        score += center_tiebreak(c)

        if score > best_score:
            best_score = score
            best_col = c
        alpha = max(alpha, best_score)

    # Guaranteed legal
    if best_col not in legal:
        return legal[0]
    return best_col


def choose_depth(board):
    empties = sum(cell == 0 for row in board for cell in row)
    if empties >= 30:
        return 5
    if empties >= 18:
        return 6
    if empties >= 10:
        return 7
    return 8


def get_legal_moves(board):
    return [c for c in range(COLS) if board[0][c] == 0]


def ordered_moves(board):
    legal = set(get_legal_moves(board))
    return [c for c in CENTER_ORDER if c in legal]


def make_move(board, col, piece):
    nb = [row[:] for row in board]
    for r in range(ROWS - 1, -1, -1):
        if nb[r][col] == 0:
            nb[r][col] = piece
            return nb
    return nb  # should never happen for legal move


def flip_perspective(board):
    return [[-cell for cell in row] for row in board]


def is_winner(board, piece):
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if (
                board[r][c] == piece and
                board[r][c + 1] == piece and
                board[r][c + 2] == piece and
                board[r][c + 3] == piece
            ):
                return True

    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            if (
                board[r][c] == piece and
                board[r + 1][c] == piece and
                board[r + 2][c] == piece and
                board[r + 3][c] == piece
            ):
                return True

    # Diagonal down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if (
                board[r][c] == piece and
                board[r + 1][c + 1] == piece and
                board[r + 2][c + 2] == piece and
                board[r + 3][c + 3] == piece
            ):
                return True

    # Diagonal up-right
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if (
                board[r][c] == piece and
                board[r - 1][c + 1] == piece and
                board[r - 2][c + 2] == piece and
                board[r - 3][c + 3] == piece
            ):
                return True

    return False


def is_terminal(board):
    return is_winner(board, 1) or is_winner(board, -1) or not get_legal_moves(board)


def negamax(board, depth, alpha, beta):
    if is_winner(board, 1):
        return 1000000 + depth
    if is_winner(board, -1):
        return -1000000 - depth

    legal = get_legal_moves(board)
    if depth == 0 or not legal:
        return evaluate(board)

    best = -inf
    for c in ordered_moves(board):
        nb = make_move(board, c, 1)

        # Strong tactical shortcut
        if is_winner(nb, 1):
            score = 1000000 + depth
        else:
            score = -negamax(flip_perspective(nb), depth - 1, -beta, -alpha)

        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def evaluate(board):
    # Terminal-like checks first
    if is_winner(board, 1):
        return 1000000
    if is_winner(board, -1):
        return -1000000

    score = 0

    # Center control
    center_col = [board[r][COLS // 2] for r in range(ROWS)]
    score += 6 * center_col.count(1)
    score -= 6 * center_col.count(-1)

    # Secondary center preference
    for c in range(COLS):
        weight = 3 - abs(c - 3)
        for r in range(ROWS):
            if board[r][c] == 1:
                score += weight
            elif board[r][c] == -1:
                score -= weight

    # Evaluate all 4-windows
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            score += eval_window([board[r][c + i] for i in range(4)], board)

    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            score += eval_window([board[r + i][c] for i in range(4)], board)

    # Diagonal down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            score += eval_window([board[r + i][c + i] for i in range(4)], board)

    # Diagonal up-right
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            score += eval_window([board[r - i][c + i] for i in range(4)], board)

    # Mobility / immediate threats
    legal = get_legal_moves(board)
    my_immediate = 0
    opp_immediate = 0
    for c in legal:
        if is_winner(make_move(board, c, 1), 1):
            my_immediate += 1
        if is_winner(make_move(board, c, -1), -1):
            opp_immediate += 1

    score += 80 * my_immediate
    score -= 100 * opp_immediate

    return score


def eval_window(window, board_unused=None):
    mine = window.count(1)
    opp = window.count(-1)
    empty = window.count(0)

    if mine and opp:
        return 0

    if mine == 4:
        return 100000
    if opp == 4:
        return -100000

    if mine == 3 and empty == 1:
        return 120
    if mine == 2 and empty == 2:
        return 12
    if mine == 1 and empty == 3:
        return 2

    if opp == 3 and empty == 1:
        return -140
    if opp == 2 and empty == 2:
        return -14
    if opp == 1 and empty == 3:
        return -2

    return 0


def center_tiebreak(col):
    return 0.001 * (3 - abs(col - 3))
