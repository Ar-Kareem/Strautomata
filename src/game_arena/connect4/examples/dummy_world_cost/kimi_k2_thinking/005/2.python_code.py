
import time

# ----------------------------------------------------------------------
# Constants and pre‑computed data
# ----------------------------------------------------------------------
ROWS = 6
COLS = 7
INF = 10 ** 6                     # large enough to dominate any heuristic
CENTER_BONUS = 3
SCORE_MAP = [0, 1, 10, 100, INF]   # scoring for 0‑4 owned cells in a line

# All possible 4‑in‑a‑row lines (horizontal, vertical, two diagonals)
LINES = []

# horizontal
for r in range(ROWS):
    for c in range(COLS - 3):
        LINES.append([(r, c + i) for i in range(4)])

# vertical
for r in range(ROWS - 3):
    for c in range(COLS):
        LINES.append([(r + i, c) for i in range(4)])

# diagonal down‑right
for r in range(ROWS - 3):
    for c in range(COLS - 3):
        LINES.append([(r + i, c + i) for i in range(4)])

# diagonal down‑left
for r in range(ROWS - 3):
    for c in range(3, COLS):
        LINES.append([(r + i, c - i) for i in range(4)])


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def get_possible_moves(board):
    """Return list of columns that still have empty cells."""
    return [c for c in range(COLS) if board[0][c] == 0]


def get_drop_row(board, col):
    """Return the lowest empty row in *col* (board is mutated later)."""
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    # Should never happen for a legal column
    return None


def is_win(board, player):
    """True if *player* (1 or -1) has a line of four on *board*."""
    for line in LINES:
        if all(board[r][c] == player for r, c in line):
            return True
    return False


def evaluate(board):
    """
    Heuristic score from the viewpoint of player 1.
    Higher values mean a better position for player 1.
    """
    score = 0
    for line in LINES:
        my = 0
        opp = 0
        for r, c in line:
            v = board[r][c]
            if v == 1:
                my += 1
            elif v == -1:
                opp += 1
        if my > 0 and opp > 0:
            continue                # blocked line
        score += SCORE_MAP[my] - SCORE_MAP[opp]

    # central column bonus
    for r in range(ROWS):
        v = board[r][3]
        if v == 1:
            score += CENTER_BONUS
        elif v == -1:
            score -= CENTER_BONUS
    return score


# ----------------------------------------------------------------------
# Minimax with α‑β pruning and a time limit
# ----------------------------------------------------------------------
def minimax(board, depth, alpha, beta, maximizing,
            start_time, time_limit, time_exceeded):
    """
    Classic depth‑limited minimax.
    *time_exceeded* is a single‑element list used as a mutable flag.
    Returns a score (int).  If the clock runs out the flag is set and the
    value 0 is returned (the caller will discard the result).
    """
    if time_exceeded[0] or (time.time() - start_time > time_limit):
        time_exceeded[0] = True
        return 0

    # Terminal tests
    if is_win(board, 1):
        return INF
    if is_win(board, -1):
        return -INF

    moves = get_possible_moves(board)
    if not moves:                     # draw
        return 0
    if depth == 0:
        return evaluate(board)

    # move ordering – centre columns first
    ordered = [c for c in (3, 2, 4, 1, 5, 0, 6) if c in moves]

    if maximizing:
        max_eval = -INF
        for col in ordered:
            row = get_drop_row(board, col)
            board[row][col] = 1
            cur = minimax(board, depth - 1, alpha, beta, False,
                          start_time, time_limit, time_exceeded)
            board[row][col] = 0
            if time_exceeded[0]:
                break
            max_eval = max(max_eval, cur)
            alpha = max(alpha, cur)
            if beta <= alpha:
                break
        return max_eval
    else:  # minimizing – opponent's turn
        min_eval = INF
        for col in ordered:
            row = get_drop_row(board, col)
            board[row][col] = -1
            cur = minimax(board, depth - 1, alpha, beta, True,
                          start_time, time_limit, time_exceeded)
            board[row][col] = 0
            if time_exceeded[0]:
                break
            min_eval = min(min_eval, cur)
            beta = min(beta, cur)
            if beta <= alpha:
                break
        return min_eval


# ----------------------------------------------------------------------
# Policy entry point
# ----------------------------------------------------------------------
def policy(board):
    """
    Return the column index (0‑6) for the next move of player 1.
    The function guarantees a legal move.
    """
    start = time.time()
    limit = 0.9                     # leave a little safety margin

    # work on a copy to avoid mutating the original board
    board = [row[:] for row in board]

    # ----------------------------------------------------------
    # 1) Immediate win or block
    # ----------------------------------------------------------
    for col in get_possible_moves(board):
        row = get_drop_row(board, col)
        board[row][col] = 1
        if is_win(board, 1):
            board[row][col] = 0
            return col
        board[row][col] = 0

    for col in get_possible_moves(board):
        row = get_drop_row(board, col)
        board[row][col] = -1
        if is_win(board, -1):
            board[row][col] = 0
            return col
        board[row][col] = 0

    # ----------------------------------------------------------
    # 2) Iterative deepening minimax
    # ----------------------------------------------------------
    best_move = None
    depth = 1
    while True:
        moves = get_possible_moves(board)
        if not moves:                     # draw – any column is illegal, but this should never happen
            break

        ordered = [c for c in (3, 2, 4, 1, 5, 0, 6) if c in moves]
        time_exceeded = [False]
        best_score_depth = -INF
        best_move_depth = None

        for col in ordered:
            row = get_drop_row(board, col)
            board[row][col] = 1
            cur = minimax(board, depth - 1, -INF, INF, False,
                          start, limit, time_exceeded)
            board[row][col] = 0
            if time_exceeded[0]:
                break
            if cur > best_score_depth:
                best_score_depth = cur
                best_move_depth = col

        if time_exceeded[0]:
            # the current depth was not finished – use the result from the previous depth
            break

        # depth completed successfully – store its result
        best_move = best_move_depth
        depth += 1
        if depth > 10:          # safety cap, normally we run out of time earlier
            break

    # ----------------------------------------------------------
    # 3) Fallback (should never be needed)
    # ----------------------------------------------------------
    if best_move is None:
        for col in (3, 2, 4, 1, 5, 0, 6):
            if board[0][col] == 0:
                return col
    return best_move
