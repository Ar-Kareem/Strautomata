
# ------------------------------------------------------------
#  Connect‑4 policy for the arena
# ------------------------------------------------------------
from math import inf

# constants
PLAYER = 1               # our disc
OPPONENT = -1            # opponent disc
EMPTY = 0
WIN_SCORE = 1_000_000    # value of a forced win

# ordering that tries the centre columns first – helps alpha‑beta
CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]

def get_lowest_empty_row(board, col):
    """Return the row index where a disc would land in column col."""
    for r in range(5, -1, -1):
        if board[r][col] == EMPTY:
            return r
    return None  # column is full – should never be called with a full column

def drop_piece(board, col, player):
    """Return a *new* board with player's disc dropped into col."""
    new_board = [row[:] for row in board]          # shallow copy of rows
    r = get_lowest_empty_row(new_board, col)
    new_board[r][col] = player
    return new_board

def check_win(board, player):
    """Return True if player has a line of four on board."""
    # horizontal
    for r in range(6):
        for c in range(4):
            if all(board[r][c + i] == player for i in range(4)):
                return True
    # vertical
    for c in range(7):
        for r in range(3):
            if all(board[r + i][c] == player for i in range(4)):
                return True
    # diagonal down‑right
    for r in range(3):
        for c in range(4):
            if all(board[r + i][c + i] == player for i in range(4)):
                return True
    # diagonal up‑right
    for r in range(3, 6):
        for c in range(4):
            if all(board[r - i][c + i] == player for i in range(4)):
                return True
    return False

def evaluate(board):
    """
    Heuristic value of the board from PLAYER's perspective.
    Counts every window of 4 cells and awards points for our discs,
    penalises for opponent's discs (see the table in the strategy).
    """
    # weights for 1‑, 2‑, 3‑, 4‑in‑a‑row (0 is never used)
    w = [0, 1, 10, 100, WIN_SCORE]

    score = 0

    # horizontal windows
    for r in range(6):
        for c in range(4):
            window = [board[r][c + i] for i in range(4)]
            cnt_us = window.count(PLAYER)
            cnt_op = window.count(OPPONENT)
            if cnt_us and cnt_op:          # blocked window
                continue
            if cnt_us:
                score += w[cnt_us]
            elif cnt_op:
                score -= w[cnt_op]

    # vertical windows
    for c in range(7):
        for r in range(3):
            window = [board[r + i][c] for i in range(4)]
            cnt_us = window.count(PLAYER)
            cnt_op = window.count(OPPONENT)
            if cnt_us and cnt_op:
                continue
            if cnt_us:
                score += w[cnt_us]
            elif cnt_op:
                score -= w[cnt_op]

    # diagonal down‑right windows
    for r in range(3):
        for c in range(4):
            window = [board[r + i][c + i] for i in range(4)]
            cnt_us = window.count(PLAYER)
            cnt_op = window.count(OPPONENT)
            if cnt_us and cnt_op:
                continue
            if cnt_us:
                score += w[cnt_us]
            elif cnt_op:
                score -= w[cnt_op]

    # diagonal up‑right windows
    for r in range(3, 6):
        for c in range(4):
            window = [board[r - i][c + i] for i in range(4)]
            cnt_us = window.count(PLAYER)
            cnt_op = window.count(OPPONENT)
            if cnt_us and cnt_op:
                continue
            if cnt_us:
                score += w[cnt_us]
            elif cnt_op:
                score -= w[cnt_op]

    return score

def minimax(board, depth, alpha, beta, maximizing):
    """
    Recursive minimax with alpha‑beta pruning.
    *board* is modified in‑place and restored after each move.
    *depth* counts plies remaining.
    *maximizing* True → we are to move, False → opponent to move.
    The score is always from PLAYER's point of view.
    """
    # terminal positions
    if check_win(board, PLAYER):
        return WIN_SCORE
    if check_win(board, OPPONENT):
        return -WIN_SCORE
    # draw (board full)
    if all(board[0][c] != EMPTY for c in range(7)):
        return 0
    if depth == 0:
        return evaluate(board)

    if maximizing:
        max_eval = -inf
        for col in CENTER_ORDER:
            if board[0][col] != EMPTY:
                continue
            r = get_lowest_empty_row(board, col)
            board[r][col] = PLAYER
            eval_ = minimax(board, depth - 1, alpha, beta, False)
            board[r][col] = EMPTY
            max_eval = max(max_eval, eval_)
            alpha = max(alpha, eval_)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = inf
        for col in CENTER_ORDER:
            if board[0][col] != EMPTY:
                continue
            r = get_lowest_empty_row(board, col)
            board[r][col] = OPPONENT
            eval_ = minimax(board, depth - 1, alpha, beta, True)
            board[r][col] = EMPTY
            min_eval = min(min_eval, eval_)
            beta = min(beta, eval_)
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    """
    Return a legal column (0‑6) for the current player.
    The board is a 6×7 list of ints: 0 empty, 1 our disc, -1 opponent disc.
    """
    # ---- 1. Immediate win -------------------------------------------------
    for col in CENTER_ORDER:
        if board[0][col] != EMPTY:
            continue
        after = drop_piece(board, col, PLAYER)
        if check_win(after, PLAYER):
            return col

    # ---- 2. Block opponent's immediate win -------------------------------
    for col in CENTER_ORDER:
        if board[0][col] != EMPTY:
            continue
        after = drop_piece(board, col, OPPONENT)
        if check_win(after, OPPONENT):
            return col

    # ---- 3. Look‑ahead search --------------------------------------------
    # fixed depth (plies) – 6 is a safe trade‑off between strength and speed
    MAX_DEPTH = 6
    best_score = -inf
    best_col = None
    for col in CENTER_ORDER:
        if board[0][col] != EMPTY:
            continue
        child = drop_piece(board, col, PLAYER)          # board after our move
        # opponent to move next
        score = minimax(child, MAX_DEPTH - 1, -inf, inf, False)
        if score > best_score:
            best_score = score
            best_col = col

    # fall‑back: first legal column (should never happen while a move exists)
    if best_col is None:
        for col in range(7):
            if board[0][col] == EMPTY:
                return col
    return best_col
