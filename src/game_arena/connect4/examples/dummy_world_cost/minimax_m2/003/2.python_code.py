
import random
import sys
import copy

# ----------------------------------------------------------------------
# Heuristic evaluation
# ----------------------------------------------------------------------
WINNING_SCORE = 100_000
THREE_OPEN_SCORE = 500
THREE_CLOSED_SCORE = 50
TWO_OPEN_SCORE = 10
TWO_CLOSED_SCORE = 2
CENTER_WEIGHT = 3

def evaluate(board, player):
    """
    Return a score for the board from the perspective of `player` (1 for us,
    -1 for opponent). Positive scores are good for `player`.
    """
    opponent = -player
    score = 0

    # ----- horizontal windows -----
    for r in range(6):
        for c in range(4):
            window = [board[r][c + i] for i in range(4)]
            score += _score_window(window, player, opponent)

    # ----- vertical windows -----
    for c in range(7):
        for r in range(3):
            window = [board[r + i][c] for i in range(4)]
            score += _score_window(window, player, opponent)

    # ----- diagonal (\) windows -----
    for r in range(3):
        for c in range(4):
            window = [board[r + i][c + i] for i in range(4)]
            score += _score_window(window, player, opponent)

    # ----- diagonal (/) windows -----
    for r in range(3):
        for c in range(4):
            window = [board[r + 3 - i][c + i] for i in range(4)]
            score += _score_window(window, player, opponent)

    # ----- centre column bonus -----
    for r in range(6):
        if board[r][3] == player:
            score += CENTER_WEIGHT
        elif board[r][3] == opponent:
            score -= CENTER_WEIGHT

    return score


def _score_window(window, player, opponent):
    p = window.count(player)
    o = window.count(opponent)
    e = window.count(0)

    if o == 4:
        return -WINNING_SCORE
    if p == 4:
        return WINNING_SCORE

    if p == 3 and e == 1:
        return THREE_OPEN_SCORE
    if o == 3 and e == 1:
        return -THREE_OPEN_SCORE

    if p == 2 and e == 2:
        return TWO_OPEN_SCORE
    if o == 2 and e == 2:
        return -TWO_OPEN_SCORE

    if p == 2 and e == 2:
        # already handled
        pass

    # closed three / two pieces give smaller scores
    if p == 3 and e == 0:
        return THREE_CLOSED_SCORE
    if o == 3 and e == 0:
        return -THREE_CLOSED_SCORE

    if p == 2 and e == 1:
        return TWO_CLOSED_SCORE
    if o == 2 and e == 1:
        return -TWO_CLOSED_SCORE

    return 0


# ----------------------------------------------------------------------
# Game logic helpers
# ----------------------------------------------------------------------
def get_valid_moves(board):
    """Return list of column indices that are not full (top cell is 0)."""
    return [c for c in range(7) if board[0][c] == 0]


def make_move(board, col, player):
    """Return a new board with `player`‘s disc placed in column `col`."""
    new_board = [row[:] for row in board]
    for r in range(5, -1, -1):
        if new_board[r][col] == 0:
            new_board[r][col] = player
            break
    return new_board


def is_win(board, player):
    """Check whether `player` has a four‑in‑a‑row on the board."""
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
    # diagonal \
    for r in range(3):
        for c in range(4):
            if all(board[r + i][c + i] == player for i in range(4)):
                return True
    # diagonal /
    for r in range(3):
        for c in range(4):
            if all(board[r + 3 - i][c + i] == player for i in range(4)):
                return True
    return False


# ----------------------------------------------------------------------
# Minimax with alpha‑beta pruning
# ----------------------------------------------------------------------
def minimax(board, depth, alpha, beta, maximizing):
    """Recursive minimax. `maximizing` = True for our player (1)."""
    player = 1 if maximizing else -1
    valid = get_valid_moves(board)

    # Terminal conditions
    if depth == 0 or not valid:
        return evaluate(board, 1)

    if is_win(board, 1):
        return WINNING_SCORE + depth   # prefer faster win
    if is_win(board, -1):
        return -WINNING_SCORE - depth   # avoid losing faster

    if maximizing:
        max_eval = -10**9
        # Order moves to improve pruning
        ordered = order_moves(board, valid, 1)
        for col in ordered:
            new_board = make_move(board, col, 1)
            eval_score = minimax(new_board, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = 10**9
        ordered = order_moves(board, valid, -1)
        for col in ordered:
            new_board = make_move(board, col, -1)
            eval_score = minimax(new_board, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval


def order_moves(board, moves, player):
    """
    Return `moves` reordered:
      1) immediate winning move for `player`,
      2) moves that block an immediate opponent win,
      3) remaining moves sorted by static evaluation.
    """
    winning = []
    blocking = []
    others = []

    for col in moves:
        # try to win now
        nb = make_move(board, col, player)
        if is_win(nb, player):
            winning.append(col)
            continue

        # does the opponent win next if we play here?
        opp_win = False
        for c in get_valid_moves(nb):
            if is_win(make_move(nb, c, -player), -player):
                opp_win = True
                break
        if opp_win:
            blocking.append(col)
        else:
            others.append(col)

    # sort remaining moves by evaluation
    others_sorted = sorted(others,
                           key=lambda c: evaluate(make_move(board, c, player), player),
                           reverse=True)

    return winning + blocking + others_sorted


# ----------------------------------------------------------------------
# Main policy entry point
# ----------------------------------------------------------------------
def policy(board):
    # ------------------------------------------------------------------
    # 1. Immediate winning move?
    # ------------------------------------------------------------------
    for col in get_valid_moves(board):
        if is_win(make_move(board, col, 1), 1):
            return col

    # ------------------------------------------------------------------
    # 2. Block opponent's immediate win
    # ------------------------------------------------------------------
    for col in get_valid_moves(board):
        if is_win(make_move(board, col, -1), -1):
            return col

    # ------------------------------------------------------------------
    # 3. Depth‑limited minimax (depth 5)
    # ------------------------------------------------------------------
    best_move = get_valid_moves(board)[0]
    best_score = -10**9

    # Order moves for the root to increase chance of early cutoff
    ordered = order_moves(board, get_valid_moves(board), 1)

    for col in ordered:
        new_board = make_move(board, col, 1)
        score = minimax(new_board, 4, -10**9, 10**9, False)
        if score > best_score:
            best_score = score
            best_move = col
        # If we already see a winning score we can stop searching
        if best_score >= WINNING_SCORE:
            break

    return best_move
