
import time

# ----------------------------------------------------------------------
# Pre‑compute all possible 4‑in‑a‑row lines (horizontal, vertical, diagonal)
# ----------------------------------------------------------------------
WIN_LINES = []

# Horizontal lines (6 rows × 4 start columns)
for r in range(6):
    for c in range(4):
        WIN_LINES.append([(r, c + i) for i in range(4)])

# Vertical lines (3 start rows × 7 columns)
for r in range(3):
    for c in range(7):
        WIN_LINES.append([(r + i, c) for i in range(4)])

# Diagonal down‑right (3 start rows × 4 start columns)
for r in range(3):
    for c in range(4):
        WIN_LINES.append([(r + i, c + i) for i in range(4)])

# Diagonal up‑right (3 start rows (from row 3‑5) × 4 start columns)
for r in range(3, 6):
    for c in range(4):
        WIN_LINES.append([(r - i, c + i) for i in range(4)])

INF = 10 ** 9  # Large number to represent +/- infinity

# ----------------------------------------------------------------------
# Helpers for board manipulation
# ----------------------------------------------------------------------
def _open_row(board, col):
    """Return the lowest empty row index in column `col`, or None if full."""
    for r in range(5, -1, -1):
        if board[r][col] == 0:
            return r
    return None

def _drop(board, col, player):
    """Place `player`'s disc in column `col` and return the row used."""
    row = _open_row(board, col)
    board[row][col] = player
    return row

def _undo(board, row, col):
    """Remove a disc from the given position."""
    board[row][col] = 0

def _win(board, player):
    """Check if `player` has four in a row."""
    target = 4 * player
    for line in WIN_LINES:
        s = sum(board[r][c] for r, c in line)
        if s == target:
            return True
    return False

def _terminal(board):
    """Return (is_terminal, winner) where winner is 1, -1, or 0 for draw."""
    if _win(board, 1):
        return True, 1
    if _win(board, -1):
        return True, -1
    if all(board[0][c] != 0 for c in range(7)):
        return True, 0
    return False, None

def _evaluate(board):
    """
    Heuristic score of `board` from the viewpoint of player 1.
    Counts non‑blocked potential lines and adds a tiny central‑column bonus.
    """
    score = 0
    for line in WIN_LINES:
        has_one = False
        has_minus_one = False
        line_sum = 0
        for r, c in line:
            v = board[r][c]
            line_sum += v
            if v == 1:
                has_one = True
            elif v == -1:
                has_minus_one = True
        # Skip lines that contain both players – they are already blocked
        if has_one and has_minus_one:
            continue
        if has_one:
            # only our discs are in this line -> reward
            score += 10 ** (line_sum - 1)  # line_sum == number of our discs
        if has_minus_one:
            # only opponent discs -> penalty
            score -= 10 ** (-line_sum - 1)  # -line_sum == number of opponent discs

    # Central‑column bonus (columns 3 and 4)
    for r in range(6):
        for c in (3, 4):
            v = board[r][c]
            if v == 1:
                score += 5
            elif v == -1:
                score -= 5
    return score

def _ordered_moves(board):
    """Return valid columns ordered by centrality (best first)."""
    order = [3, 2, 4, 1, 5, 0, 6]
    return [c for c in order if board[0][c] == 0]

# ----------------------------------------------------------------------
# Minimax with alpha‑beta and a time‑out guard
# ----------------------------------------------------------------------
def _minimax(board, depth, alpha, beta, maximizing, start):
    """Recursive minimax; raises TimeoutError if >0.9 s have passed."""
    if time.time() - start > 0.9:
        raise TimeoutError()

    term, winner = _terminal(board)
    if term:
        if winner == 1:
            return None, INF
        if winner == -1:
            return None, -INF
        return None, 0  # draw
    if depth == 0:
        return None, _evaluate(board)

    if maximizing:
        best_val = -INF
        best_move = None
        for col in _ordered_moves(board):
            row = _drop(board, col, 1)
            _, val = _minimax(board, depth - 1, alpha, beta, False, start)
            _undo(board, row, col)

            if val > best_val:
                best_val = val
                best_move = col
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return best_move, best_val
    else:
        best_val = INF
        best_move = None
        for col in _ordered_moves(board):
            row = _drop(board, col, -1)
            _, val = _minimax(board, depth - 1, alpha, beta, True, start)
            _undo(board, row, col)

            if val < best_val:
                best_val = val
                best_move = col
            beta = min(beta, val)
            if beta <= alpha:
                break
        return best_move, best_val

# ----------------------------------------------------------------------
# Public policy API
# ----------------------------------------------------------------------
def policy(board):
    """
    Return a column index (0‑6) for the current player (player 1) on the given 6×7 board.
    The board is a list of six rows, each a list of seven ints (0, 1, ‑1).
    """
    start = time.time()
    # ---- 1. Quick checks for forced win/block ---------------------------------
    valid = [c for c in range(7) if board[0][c] == 0]
    if not valid:
        return 0  # Should never happen, but guarantees a legal move

    if len(valid) == 1:
        return valid[0]

    # Immediate win?
    for c in valid:
        r = _open_row(board, c)
        board[r][c] = 1
        if _win(board, 1):
            board[r][c] = 0
            return c
        board[r][c] = 0

    # Immediate block?
    for c in valid:
        r = _open_row(board, c)
        board[r][c] = -1
        if _win(board, -1):
            board[r][c] = 0
            return c
        board[r][c] = 0

    # ---- 2. Iterative‑deepening minimax --------------------------------------
    best = _ordered_moves(board)[0]  # Fallback move
    depth = 1
    while depth <= 10:  # reasonable maximal depth
        if time.time() - start > 0.9:
            break
        try:
            move, _ = _minimax(board, depth, -INF, INF, True, start)
            if move is not None:
                best = move
        except TimeoutError:
            break
        depth += 1

    return best
