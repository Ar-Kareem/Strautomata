
import math
import random
from typing import List, Tuple

ROWS = 6
COLS = 7

def policy(board: List[List[int]]) -> int:
    me = 1  # current player is always 1
    opp = -1

    def legal_cols(b):
        return [c for c in range(COLS) if b[0][c] == 0]

    def next_row(b, c):
        for r in range(ROWS-1, -1, -1):
            if b[r][c] == 0:
                return r
        return None

    def make_move(b, c, player):
        r = next_row(b, c)
        if r is None:
            return None
        nb = [row[:] for row in b]
        nb[r][c] = player
        return nb

    def winner(b):
        # Return me, opp, or 0 (none)
        # Check all 4-length lines
        for r in range(ROWS):
            for c in range(COLS-3):
                s = b[r][c] + b[r][c+1] + b[r][c+2] + b[r][c+3]
                if s == 4: return 1
                if s == -4: return -1

        for c in range(COLS):
            for r in range(ROWS-3):
                s = b[r][c] + b[r+1][c] + b[r+2][c] + b[r+3][c]
                if s == 4: return 1
                if s == -4: return -1

        for r in range(ROWS-3):
            for c in range(COLS-3):
                s = b[r][c] + b[r+1][c+1] + b[r+2][c+2] + b[r+3][c+3]
                if s == 4: return 1
                if s == -4: return -1

        for r in range(ROWS-3):
            for c in range(3, COLS):
                s = b[r][c] + b[r+1][c-1] + b[r+2][c-2] + b[r+3][c-3]
                if s == 4: return 1
                if s == -4: return -1

        return 0

    def board_full(b):
        return all(b[0][c] != 0 for c in range(COLS))

    # Scoring helpers: count 4-segments
    def evaluate(b):
        w = winner(b)
        if w == me:
            return 10**9
        if w == opp:
            return -10**9

        score = 0

        # Center preference
        center_col = COLS // 2
        center_count = sum(1 for r in range(ROWS) if b[r][center_col] == me)
        score += center_count * 18

        # Mild preference for columns next to center
        for c, weight in [(2, 8), (4, 8), (1, 4), (5, 4), (0, 2), (6, 2)]:
            score += sum(1 for r in range(ROWS) if b[r][c] == me) * weight

        def score_segment(cells):
            # cells: length 4 list of ints
            s = sum(cells)
            # Since values are in {-1,0,1}, we can detect compositions:
            # For me:
            if s == 4:  # already handled as win, but keep safe
                return 10**6
            if s == 3:  # 3 me + 1 empty
                if cells.count(0) == 1:
                    return 200
            if s == 2:
                if cells.count(0) == 2 and cells.count(me) == 2:
                    return 30
            # For opponent: subtract similarly
            if s == -3:
                if cells.count(0) == 1:
                    return -220
            if s == -2:
                if cells.count(0) == 2 and cells.count(opp) == 2:
                    return -35
            return 0

        # Horizontal
        for r in range(ROWS):
            for c in range(COLS-3):
                cells = [b[r][c+i] for i in range(4)]
                score += score_segment(cells)
        # Vertical
        for c in range(COLS):
            for r in range(ROWS-3):
                cells = [b[r+i][c] for i in range(4)]
                score += score_segment(cells)
        # Diagonal /
        for r in range(ROWS-3):
            for c in range(COLS-3):
                cells = [b[r+i][c+i] for i in range(4)]
                score += score_segment(cells)
        # Diagonal \
        for r in range(ROWS-3):
            for c in range(3, COLS):
                cells = [b[r+i][c-i] for i in range(4)]
                score += score_segment(cells)

        return score

    # Move ordering: center first
    col_order = [3, 2, 4, 1, 5, 0, 6]

    # Immediate win / block
    legal = legal_cols(board)
    # If no legal moves (shouldn't happen), return 0
    if not legal:
        return 0

    # Check immediate win
    for c in col_order:
        if c in legal:
            nb = make_move(board, c, me)
            if winner(nb) == me:
                return c

    # Check immediate block (opponent win next)
    for c in col_order:
        if c in legal:
            nb = make_move(board, c, me)
            # Opponent to move: if any opponent move wins, we must block by choosing c that prevents it.
            # Equivalent: try opponent wins in one after our tentative move.
            if any(winner(make_move(nb, oc, opp)) == opp for oc in legal_cols(nb)):
                # We don't know if this is the only win, but this blocks at least one.
                # We'll still confirm with a stricter check below.
                pass

    # More direct block: find columns where opponent would win immediately; block them if possible.
    opp_winning_cols = []
    for c in legal_cols(board):
        nb_opp = make_move(board, c, opp)
        if winner(nb_opp) == opp:
            opp_winning_cols.append(c)
    if opp_winning_cols:
        # Prefer blocking in the most central among those
        for c in col_order:
            if c in opp_winning_cols:
                return c

    # Minimax with alpha-beta
    def minimax(b, depth, alpha, beta, player):
        w = winner(b)
        if w == me:
            return 10**7 + depth  # faster win better
        if w == opp:
            return -10**7 - depth
        if depth == 0 or board_full(b):
            return evaluate(b)

        legal_here = legal_cols(b)
        # Order moves by preference
        legal_here.sort(key=lambda x: col_order.index(x))

        if player == me:
            value = -math.inf
            for c in legal_here:
                nb = make_move(b, c, player)
                value = max(value, minimax(nb, depth-1, alpha, beta, opp))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = math.inf
            for c in legal_here:
                nb = make_move(b, c, player)
                value = min(value, minimax(nb, depth-1, alpha, beta, me))
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    # Choose best move at root with small iterative deepening depth selection
    best_score = -math.inf
    best_moves = []

    # Depth 4 is usually strong within time; can bump to 5 if desired but risk time.
    depth = 4

    legal_root = legal_cols(board)
    legal_root.sort(key=lambda x: col_order.index(x))

    # Slight randomization among equal scores to avoid deterministic traps
    for c in legal_root:
        nb = make_move(board, c, me)
        score = minimax(nb, depth-1, -math.inf, math.inf, opp)
        if score > best_score:
            best_score = score
            best_moves = [c]
        elif score == best_score:
            best_moves.append(c)

    # Tie-break centrally
    best_moves.sort(key=lambda x: col_order.index(x))
    return best_moves[0]
