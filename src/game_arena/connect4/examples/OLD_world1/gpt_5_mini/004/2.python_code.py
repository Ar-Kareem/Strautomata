
from copy import deepcopy

ROWS = 6
COLS = 7
PLAYER = 1
OPP = -1

def get_drop_row(board, col):
    """Return the row index where a disc would land if dropped into col, or None if full."""
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return None

def make_move(board, col, piece):
    """Return a new board with piece dropped into col. Assumes col is not full."""
    r = get_drop_row(board, col)
    if r is None:
        return None
    newb = [row[:] for row in board]
    newb[r][col] = piece
    return newb

def check_win(board, piece):
    """Return True if piece has four in a row on board."""
    # horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c + i] == piece for i in range(4)):
                return True
    # vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            if all(board[r + i][c] == piece for i in range(4)):
                return True
    # diag down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r + i][c + i] == piece for i in range(4)):
                return True
    # diag up-right
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(board[r - i][c + i] == piece for i in range(4)):
                return True
    return False

def evaluate_board_simple(board):
    """Heuristic evaluation favoring windows where PLAYER can connect and penalizing opponent threats."""
    score = 0
    # weights
    w3 = 100
    w2 = 10
    w1 = 1
    opp_w3 = 80
    opp_w2 = 8

    # center column preference
    center_col = COLS // 2
    center_count = sum(1 for r in range(ROWS) if board[r][center_col] == PLAYER)
    score += center_count * 3

    # iterate windows
    def eval_window(cells):
        nonlocal score
        pcount = sum(1 for v in cells if v == PLAYER)
        ocount = sum(1 for v in cells if v == OPP)
        if ocount == 0 and pcount > 0:
            if pcount == 3:
                score += w3
            elif pcount == 2:
                score += w2
            elif pcount == 1:
                score += w1
        elif pcount == 0 and ocount > 0:
            if ocount == 3:
                score -= opp_w3
            elif ocount == 2:
                score -= opp_w2

    # horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            eval_window([board[r][c + i] for i in range(4)])
    # vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            eval_window([board[r + i][c] for i in range(4)])
    # diag down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            eval_window([board[r + i][c + i] for i in range(4)])
    # diag up-right
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            eval_window([board[r - i][c + i] for i in range(4)])

    return score

def opponent_immediate_wins(board):
    """Return list of columns where opponent can drop and win immediately."""
    wins = []
    for c in range(COLS):
        if get_drop_row(board, c) is None:
            continue
        sim = make_move(board, c, OPP)
        if check_win(sim, OPP):
            wins.append(c)
    return wins

def legal_columns(board):
    return [c for c in range(COLS) if board[0][c] == 0]

def causes_opponent_win(board, col):
    """Return True if dropping our piece in col allows opponent an immediate win next move."""
    sim = make_move(board, col, PLAYER)
    if sim is None:
        return True  # treat illegal as bad
    # if we win immediately, it's fine (we'd choose it earlier)
    if check_win(sim, PLAYER):
        return False
    for c in range(COLS):
        if get_drop_row(sim, c) is None:
            continue
        sim2 = make_move(sim, c, OPP)
        if check_win(sim2, OPP):
            return True
    return False

def policy(board):
    # Validate and extract legal columns
    cols = legal_columns(board)
    if not cols:
        # fallback
        return 0

    # 1) winning move for us
    for c in cols:
        sim = make_move(board, c, PLAYER)
        if sim is not None and check_win(sim, PLAYER):
            return c

    # 2) block opponent's immediate win(s)
    opp_wins = opponent_immediate_wins(board)
    if opp_wins:
        # If multiple opponent immediate wins, try to play a winning move (already checked) or block one.
        # Prefer blocking in same column if available.
        for c in opp_wins:
            if c in cols:
                return c
        # if none of the winning columns are available (shouldn't happen), just pick first legal
        return cols[0]

    # 3) choose among safe moves (that don't give opponent immediate win). Score them.
    safe_moves = []
    for c in cols:
        if not causes_opponent_win(board, c):
            safe_moves.append(c)

    candidates = safe_moves if safe_moves else cols  # if no safe moves, must pick something

    # score candidates by heuristic
    best_score = None
    best_col = None
    for c in candidates:
        sim = make_move(board, c, PLAYER)
        if sim is None:
            continue
        sc = evaluate_board_simple(sim)
        # tie-breaker: prefer center closeness
        center_pref = -abs(c - (COLS // 2))
        sc = sc * 10 + center_pref
        if best_score is None or sc > best_score:
            best_score = sc
            best_col = c

    if best_col is not None:
        return best_col

    # fallback
    return cols[0]
