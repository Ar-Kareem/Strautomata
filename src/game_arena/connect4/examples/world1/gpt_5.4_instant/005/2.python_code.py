
from typing import List, Optional
import math
import time

ROWS = 6
COLS = 7
WIN_SCORE = 10**9
ORDER = [3, 2, 4, 1, 5, 0, 6]


def policy(board: List[List[int]]) -> int:
    start = time.time()
    time_limit = 0.92  # keep some safety margin

    def legal_moves(b):
        return [c for c in ORDER if b[0][c] == 0]

    def drop_row(b, col):
        for r in range(ROWS - 1, -1, -1):
            if b[r][col] == 0:
                return r
        return -1

    def make_move(b, col, player):
        r = drop_row(b, col)
        if r == -1:
            return None
        nb = [row[:] for row in b]
        nb[r][col] = player
        return nb, r

    def is_full(b):
        for c in range(COLS):
            if b[0][c] == 0:
                return False
        return True

    def check_win_from(b, r, c, player):
        dirs = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dr, dc in dirs:
            cnt = 1
            rr, cc = r + dr, c + dc
            while 0 <= rr < ROWS and 0 <= cc < COLS and b[rr][cc] == player:
                cnt += 1
                rr += dr
                cc += dc
            rr, cc = r - dr, c - dc
            while 0 <= rr < ROWS and 0 <= cc < COLS and b[rr][cc] == player:
                cnt += 1
                rr -= dr
                cc -= dc
            if cnt >= 4:
                return True
        return False

    def winning_moves(b, player):
        wins = []
        for c in legal_moves(b):
            res = make_move(b, c, player)
            if res is None:
                continue
            nb, r = res
            if check_win_from(nb, r, c, player):
                wins.append(c)
        return wins

    def terminal_value(b, last_move_player=None, last_r=None, last_c=None):
        if last_move_player is not None and last_r is not None and last_c is not None:
            if check_win_from(b, last_r, last_c, last_move_player):
                return last_move_player
        return 0 if not is_full(b) else 2  # 2 = draw

    def evaluate_window(window):
        me = window.count(1)
        opp = window.count(-1)
        empty = window.count(0)

        if me and opp:
            return 0
        if me == 4:
            return 100000
        if opp == 4:
            return -100000
        if me == 3 and empty == 1:
            return 120
        if me == 2 and empty == 2:
            return 12
        if opp == 3 and empty == 1:
            return -150
        if opp == 2 and empty == 2:
            return -15
        if me == 1 and empty == 3:
            return 1
        if opp == 1 and empty == 3:
            return -1
        return 0

    def evaluate(b):
        score = 0

        center_col = [b[r][3] for r in range(ROWS)]
        score += center_col.count(1) * 10
        score -= center_col.count(-1) * 10

        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = [b[r][c + i] for i in range(4)]
                score += evaluate_window(window)

        # Vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                window = [b[r + i][c] for i in range(4)]
                score += evaluate_window(window)

        # Diagonal down-right
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [b[r + i][c + i] for i in range(4)]
                score += evaluate_window(window)

        # Diagonal down-left
        for r in range(ROWS - 3):
            for c in range(3, COLS):
                window = [b[r + i][c - i] for i in range(4)]
                score += evaluate_window(window)

        return score

    def safe_moves(b):
        moves = legal_moves(b)
        good = []
        bad = []
        for c in moves:
            res = make_move(b, c, 1)
            if res is None:
                continue
            nb, r = res
            if check_win_from(nb, r, c, 1):
                good.append(c)
                continue
            opp_wins = winning_moves(nb, -1)
            if opp_wins:
                bad.append(c)
            else:
                good.append(c)
        return good if good else moves

    def negamax(b, depth, alpha, beta, player, last_r=None, last_c=None, last_player=None):
        if time.time() - start > time_limit:
            raise TimeoutError

        term = terminal_value(b, last_player, last_r, last_c)
        if term == 1:
            return WIN_SCORE + depth, None
        if term == -1:
            return -WIN_SCORE - depth, None
        if term == 2:
            return 0, None

        moves = legal_moves(b)
        if depth == 0 or not moves:
            return player * evaluate(b), None

        # Strong tactical shortcut
        current_wins = winning_moves(b, player)
        if current_wins:
            return WIN_SCORE + depth - 1, current_wins[0]

        best_score = -math.inf
        best_move = moves[0]

        ordered = moves[:]
        ordered.sort(key=lambda c: abs(c - 3))

        for c in ordered:
            res = make_move(b, c, player)
            if res is None:
                continue
            nb, r = res

            # If move gives opponent immediate win(s), de-prioritize unless necessary
            opp_immediate = winning_moves(nb, -player)
            penalty = 0
            if opp_immediate:
                penalty = 500000

            score, _ = negamax(nb, depth - 1, -beta, -alpha, -player, r, c, player)
            score = -score - penalty

            if score > best_score:
                best_score = score
                best_move = c
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        return best_score, best_move

    moves = legal_moves(board)
    if not moves:
        return 0

    # 1. Immediate win
    my_wins = winning_moves(board, 1)
    if my_wins:
        return my_wins[0]

    # 2. Immediate block
    opp_wins = winning_moves(board, -1)
    if opp_wins:
        for c in ORDER:
            if c in opp_wins and c in moves:
                return c

    # 3. Prefer safe tactical moves
    candidate_moves = safe_moves(board)
    if len(candidate_moves) == 1:
        return candidate_moves[0]

    # 4. Iterative deepening negamax
    best_move = candidate_moves[0]
    max_depth = 7
    if sum(cell != 0 for row in board for cell in row) >= 20:
        max_depth = 9

    try:
        for depth in range(1, max_depth + 1):
            score, move = negamax(board, depth, -math.inf, math.inf, 1)
            if move is not None and move in moves:
                best_move = move
            if abs(score) >= WIN_SCORE // 2:
                break
    except TimeoutError:
        pass

    if best_move in moves:
        return best_move

    # Fallback: center-first legal move
    for c in ORDER:
        if c in moves:
            return c
    return moves[0]
