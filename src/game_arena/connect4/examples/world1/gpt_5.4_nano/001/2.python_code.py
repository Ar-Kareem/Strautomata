
import math
import random
from typing import List

ROWS = 6
COLS = 7

def policy(board: list[list[int]]) -> int:
    me = 1
    opp = -1

    def legal_moves(b):
        return [c for c in range(COLS) if b[0][c] == 0]

    def drop_row(b, c, player):
        for r in range(ROWS-1, -1, -1):
            if b[r][c] == 0:
                return r
        return None

    def make_move(b, c, player):
        r = drop_row(b, c, player)
        if r is None:
            return None
        nb = [row[:] for row in b]
        nb[r][c] = player
        return nb

    def in_bounds(r, c):
        return 0 <= r < ROWS and 0 <= c < COLS

    def check_winner(b, player):
        # horizontal
        for r in range(ROWS):
            for c in range(COLS-3):
                if b[r][c] == player and b[r][c+1] == player and b[r][c+2] == player and b[r][c+3] == player:
                    return True
        # vertical
        for r in range(ROWS-3):
            for c in range(COLS):
                if b[r][c] == player and b[r+1][c] == player and b[r+2][c] == player and b[r+3][c] == player:
                    return True
        # diag down-right
        for r in range(ROWS-3):
            for c in range(COLS-3):
                if b[r][c] == player and b[r+1][c+1] == player and b[r+2][c+2] == player and b[r+3][c+3] == player:
                    return True
        # diag up-right
        for r in range(3, ROWS):
            for c in range(COLS-3):
                if b[r][c] == player and b[r-1][c+1] == player and b[r-2][c+2] == player and b[r-3][c+3] == player:
                    return True
        return False

    def score_window(count_me, count_opp, count_empty):
        # Heuristic for a 4-cell window.
        if count_me == 4:
            return 10_000_000
        if count_opp == 4:
            return 9_000_000  # large but slightly less than winning for me
        score = 0
        if count_me > 0 and count_opp == 0:
            # Only my discs in window
            if count_me == 3 and count_empty == 1:
                score += 5000
            elif count_me == 2 and count_empty == 2:
                score += 500
            elif count_me == 1 and count_empty == 3:
                score += 50
        elif count_opp > 0 and count_me == 0:
            # Only opponent discs in window (block threat)
            if count_opp == 3 and count_empty == 1:
                score += 1200
            elif count_opp == 2 and count_empty == 2:
                score += 100
            elif count_opp == 1 and count_empty == 3:
                score += 10
        return score

    def evaluate(b):
        # Center preference + window scoring.
        s = 0
        center_col = COLS // 2
        center_count = sum(1 for r in range(ROWS) if b[r][center_col] == me)
        s += center_count * 30

        # Additional slight preference for columns closer to center
        for c in range(COLS):
            col_pref = 6 - abs(center_col - c)  # 1..7
            s += (col_pref * sum(1 for r in range(ROWS) if b[r][c] == me)) * 1

        # Windows of length 4
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS-3):
                window = [b[r][c+i] for i in range(4)]
                cm = window.count(me)
                co = window.count(opp)
                ce = window.count(0)
                s += score_window(cm, co, ce)
        # Vertical
        for r in range(ROWS-3):
            for c in range(COLS):
                window = [b[r+i][c] for i in range(4)]
                cm = window.count(me)
                co = window.count(opp)
                ce = window.count(0)
                s += score_window(cm, co, ce)
        # Diag down-right
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = [b[r+i][c+i] for i in range(4)]
                cm = window.count(me)
                co = window.count(opp)
                ce = window.count(0)
                s += score_window(cm, co, ce)
        # Diag up-right
        for r in range(3, ROWS):
            for c in range(COLS-3):
                window = [b[r-i][c+i] for i in range(4)]
                cm = window.count(me)
                co = window.count(opp)
                ce = window.count(0)
                s += score_window(cm, co, ce)

        # Mild penalty if opponent already has a near-winning pattern: handled via windows,
        # but add a small direct check to stabilize.
        if check_winner(b, opp):
            s -= 50_000

        return s

    # 1) Immediate win
    for c in legal_moves(board):
        nb = make_move(board, c, me)
        if nb is not None and check_winner(nb, me):
            return c

    # 2) Immediate block (opponent win next move)
    opp_winning_cols = []
    for c in legal_moves(board):
        nb = make_move(board, c, opp)
        if nb is not None and check_winner(nb, opp):
            opp_winning_cols.append(c)
    if opp_winning_cols:
        # If multiple, prefer the one that also gives us best evaluation after blocking
        best_c = None
        best_s = -math.inf
        for c in opp_winning_cols:
            nb = make_move(board, c, me)
            s = evaluate(nb)
            # small random tie-breaker for variety
            s += random.random() * 1e-6
            if s > best_s:
                best_s = s
                best_c = c
        return best_c

    # 3) Lookahead depth-2 (my move, then best response by opponent) with strong pruning
    # Keep it fast: evaluate top candidate moves by heuristic first.
    moves = legal_moves(board)
    # order moves by quick heuristic
    scored = []
    for c in moves:
        nb = make_move(board, c, me)
        scored.append((evaluate(nb), c))
    scored.sort(reverse=True)

    top_k = min(4, len(scored))
    best_move = scored[0][1]
    best_value = -math.inf

    for _, c in scored[:top_k]:
        nb = make_move(board, c, me)
        # If this move lets opponent win immediately, discourage heavily
        opp_moves = legal_moves(nb)
        bad = False
        worst_case = math.inf  # opponent best (max) since it's from their perspective
        # Evaluate opponent responses; if they can win immediately, mark as bad and break.
        for oc in opp_moves:
            nnb = make_move(nb, oc, opp)
            if nnb is not None and check_winner(nnb, opp):
                bad = True
                worst_case = -math.inf
                break
            # opponent chooses move maximizing our negative advantage
            val = evaluate(nnb)
            # opponent tries to maximize their success, which corresponds to minimizing our eval
            worst_case = min(worst_case, val)
        if bad:
            value = -1e12
        else:
            # my advantage after worst opponent response
            value = worst_case
        # small boost for center-like moves
        value += (6 - abs((COLS // 2) - c)) * 2
        if value > best_value:
            best_value = value
            best_move = c

    return best_move
