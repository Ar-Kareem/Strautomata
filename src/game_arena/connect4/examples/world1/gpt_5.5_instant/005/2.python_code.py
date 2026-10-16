
import math
from functools import lru_cache

ROWS = 6
COLS = 7
WIN_SCORE = 10_000_000
CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]

def policy(board: list[list[int]]) -> int:
    """
    Return a legal column index for the current player (1) on a 6x7 Connect 4 board.
    board uses: 0 empty, 1 current player, -1 opponent.
    """
    try:
        b = tuple(tuple(int(x) for x in row) for row in board)
        legal = valid_moves(b)
        if not legal:
            return 0

        # Immediate win
        for c in ordered_moves(legal):
            nb = make_move(b, c, 1)
            if is_win(nb, 1):
                return c

        # Immediate block
        opp_wins = []
        for c in legal:
            nb = make_move(b, c, -1)
            if is_win(nb, -1):
                opp_wins.append(c)
        if opp_wins:
            # If multiple, choose the most central blocking move.
            return ordered_moves(opp_wins)[0]

        # Prefer safe moves: don't allow opponent immediate win.
        safe = []
        for c in legal:
            nb = make_move(b, c, 1)
            opponent_can_win = any(is_win(make_move(nb, oc, -1), -1) for oc in valid_moves(nb))
            if not opponent_can_win:
                safe.append(c)

        candidate_moves = safe if safe else legal

        # Dynamic depth: deeper when board is sparse or branching is reduced.
        empties = sum(row.count(0) for row in b)
        if empties >= 30:
            depth = 5
        elif empties >= 18:
            depth = 6
        else:
            depth = 7

        best_col = ordered_moves(candidate_moves)[0]
        best_score = -math.inf
        alpha = -math.inf
        beta = math.inf

        for c in ordered_moves(candidate_moves):
            nb = make_move(b, c, 1)
            score = minimax(nb, depth - 1, alpha, beta, False)
            # Small central tie-breaker
            score += (3 - abs(3 - c)) * 0.001
            if score > best_score:
                best_score = score
                best_col = c
            alpha = max(alpha, best_score)

        if best_col in legal:
            return int(best_col)

        return int(ordered_moves(legal)[0])
    except Exception:
        # Absolute safety fallback: return any legal move, center preferred.
        for c in CENTER_ORDER:
            try:
                if board[0][c] == 0:
                    return c
            except Exception:
                pass
        return 0


def valid_moves(b):
    return [c for c in range(COLS) if b[0][c] == 0]


def ordered_moves(moves):
    s = set(moves)
    return [c for c in CENTER_ORDER if c in s]


def make_move(b, col, player):
    rows = [list(r) for r in b]
    for r in range(ROWS - 1, -1, -1):
        if rows[r][col] == 0:
            rows[r][col] = player
            return tuple(tuple(x) for x in rows)
    return b


def is_win(b, player):
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if b[r][c] == player and b[r][c+1] == player and b[r][c+2] == player and b[r][c+3] == player:
                return True
    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            if b[r][c] == player and b[r+1][c] == player and b[r+2][c] == player and b[r+3][c] == player:
                return True
    # Diagonal down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if b[r][c] == player and b[r+1][c+1] == player and b[r+2][c+2] == player and b[r+3][c+3] == player:
                return True
    # Diagonal up-right
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if b[r][c] == player and b[r-1][c+1] == player and b[r-2][c+2] == player and b[r-3][c+3] == player:
                return True
    return False


@lru_cache(maxsize=200000)
def minimax(b, depth, alpha, beta, maximizing):
    if is_win(b, 1):
        return WIN_SCORE + depth
    if is_win(b, -1):
        return -WIN_SCORE - depth

    legal = valid_moves(b)
    if depth == 0 or not legal:
        return evaluate(b)

    if maximizing:
        value = -math.inf
        for c in ordered_moves(legal):
            nb = make_move(b, c, 1)
            value = max(value, minimax(nb, depth - 1, alpha, beta, False))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = math.inf
        for c in ordered_moves(legal):
            nb = make_move(b, c, -1)
            value = min(value, minimax(nb, depth - 1, alpha, beta, True))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


def evaluate(b):
    score = 0

    # Center control is very important in Connect 4.
    center_count = sum(1 for r in range(ROWS) if b[r][3] == 1)
    opp_center_count = sum(1 for r in range(ROWS) if b[r][3] == -1)
    score += center_count * 45
    score -= opp_center_count * 40

    # Slight preference for adjacent center columns.
    for c, weight in [(2, 12), (4, 12), (1, 4), (5, 4)]:
        score += sum(1 for r in range(ROWS) if b[r][c] == 1) * weight
        score -= sum(1 for r in range(ROWS) if b[r][c] == -1) * weight

    # Evaluate every possible 4-cell window.
    for window in all_windows(b):
        score += score_window(window)

    # Count immediate winning moves / threats.
    my_threats = count_immediate_wins(b, 1)
    opp_threats = count_immediate_wins(b, -1)
    if my_threats >= 2:
        score += 5000
    elif my_threats == 1:
        score += 900

    if opp_threats >= 2:
        score -= 7000
    elif opp_threats == 1:
        score -= 1100

    return score


def all_windows(b):
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            yield (b[r][c], b[r][c+1], b[r][c+2], b[r][c+3])
    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            yield (b[r][c], b[r+1][c], b[r+2][c], b[r+3][c])
    # Diagonal down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            yield (b[r][c], b[r+1][c+1], b[r+2][c+2], b[r+3][c+3])
    # Diagonal up-right
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            yield (b[r][c], b[r-1][c+1], b[r-2][c+2], b[r-3][c+3])


def score_window(w):
    my = w.count(1)
    opp = w.count(-1)
    empty = w.count(0)

    if my > 0 and opp > 0:
        return 0

    if my == 4:
        return WIN_SCORE
    if opp == 4:
        return -WIN_SCORE

    if my == 3 and empty == 1:
        return 120
    if my == 2 and empty == 2:
        return 18
    if my == 1 and empty == 3:
        return 2

    if opp == 3 and empty == 1:
        return -160
    if opp == 2 and empty == 2:
        return -22
    if opp == 1 and empty == 3:
        return -2

    return 0


def count_immediate_wins(b, player):
    cnt = 0
    for c in valid_moves(b):
        nb = make_move(b, c, player)
        if is_win(nb, player):
            cnt += 1
    return cnt
