
from typing import List
import math
import time

ROWS = 6
COLS = 7
WIN_SCORE = 10**9

def policy(board: list[list[int]]) -> int:
    start = time.time()
    time_limit = 0.92  # stay safely under 1 second

    def legal_moves(b):
        return [c for c in range(COLS) if b[0][c] == 0]

    def next_open_row(b, col):
        for r in range(ROWS - 1, -1, -1):
            if b[r][col] == 0:
                return r
        return None

    def make_move(b, col, piece):
        r = next_open_row(b, col)
        if r is None:
            return None
        nb = [row[:] for row in b]
        nb[r][col] = piece
        return nb, r

    def winning_move(b, piece):
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if b[r][c] == piece and b[r][c+1] == piece and b[r][c+2] == piece and b[r][c+3] == piece:
                    return True
        # Vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                if b[r][c] == piece and b[r+1][c] == piece and b[r+2][c] == piece and b[r+3][c] == piece:
                    return True
        # Diagonal down-right
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if b[r][c] == piece and b[r+1][c+1] == piece and b[r+2][c+2] == piece and b[r+3][c+3] == piece:
                    return True
        # Diagonal up-right
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if b[r][c] == piece and b[r-1][c+1] == piece and b[r-2][c+2] == piece and b[r-3][c+3] == piece:
                    return True
        return False

    def terminal_node(b):
        return winning_move(b, 1) or winning_move(b, -1) or len(legal_moves(b)) == 0

    def evaluate_window(window):
        score = 0
        own = window.count(1)
        opp = window.count(-1)
        empty = window.count(0)

        if own == 4:
            score += 100000
        elif own == 3 and empty == 1:
            score += 120
        elif own == 2 and empty == 2:
            score += 12

        if opp == 4:
            score -= 100000
        elif opp == 3 and empty == 1:
            score -= 150
        elif opp == 2 and empty == 2:
            score -= 15

        return score

    def score_position(b):
        score = 0

        # Center preference
        center_col = COLS // 2
        center_array = [b[r][center_col] for r in range(ROWS)]
        score += center_array.count(1) * 10
        score -= center_array.count(-1) * 10

        # Additional column preference
        col_weights = [3, 4, 5, 7, 5, 4, 3]
        for r in range(ROWS):
            for c in range(COLS):
                if b[r][c] == 1:
                    score += col_weights[c]
                elif b[r][c] == -1:
                    score -= col_weights[c]

        # Horizontal
        for r in range(ROWS):
            row_array = b[r]
            for c in range(COLS - 3):
                score += evaluate_window(row_array[c:c+4])

        # Vertical
        for c in range(COLS):
            col_array = [b[r][c] for r in range(ROWS)]
            for r in range(ROWS - 3):
                score += evaluate_window(col_array[r:r+4])

        # Diagonal down-right
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [b[r+i][c+i] for i in range(4)]
                score += evaluate_window(window)

        # Diagonal up-right
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [b[r-i][c+i] for i in range(4)]
                score += evaluate_window(window)

        return score

    def count_immediate_wins_for_player(b, piece):
        count = 0
        for c in legal_moves(b):
            result = make_move(b, c, piece)
            if result is None:
                continue
            nb, _ = result
            if winning_move(nb, piece):
                count += 1
        return count

    def move_order(b, moves):
        center = COLS // 2
        scored = []
        for c in moves:
            result = make_move(b, c, 1)
            if result is None:
                continue
            nb, _ = result
            s = score_position(nb) - abs(c - center) * 2
            scored.append((s, c))
        scored.sort(reverse=True)
        ordered = [c for _, c in scored]
        # ensure all legal moves included
        seen = set(ordered)
        for c in sorted(moves, key=lambda x: abs(x - center)):
            if c not in seen:
                ordered.append(c)
        return ordered

    def safe_moves(b, piece):
        # Moves that do not allow opponent an immediate win after playing them
        moves = legal_moves(b)
        safe = []
        opp = -piece
        for c in moves:
            result = make_move(b, c, piece)
            if result is None:
                continue
            nb, _ = result
            opp_wins = False
            for oc in legal_moves(nb):
                r2 = make_move(nb, oc, opp)
                if r2 is None:
                    continue
                nb2, _ = r2
                if winning_move(nb2, opp):
                    opp_wins = True
                    break
            if not opp_wins:
                safe.append(c)
        return safe

    def minimax(b, depth, alpha, beta, maximizing):
        if time.time() - start > time_limit:
            raise TimeoutError

        valid_locations = legal_moves(b)
        is_terminal = terminal_node(b)

        if depth == 0 or is_terminal:
            if is_terminal:
                if winning_move(b, 1):
                    return None, WIN_SCORE
                elif winning_move(b, -1):
                    return None, -WIN_SCORE
                else:
                    return None, 0
            return None, score_position(b)

        center = COLS // 2

        if maximizing:
            value = -math.inf
            best_col = None
            for col in move_order(b, valid_locations):
                result = make_move(b, col, 1)
                if result is None:
                    continue
                nb, _ = result

                # Strong tactical pruning: avoid giving immediate opponent win if alternatives exist
                opp_immediate = count_immediate_wins_for_player(nb, -1)
                penalty = 0
                if opp_immediate > 0:
                    penalty = 50000 * opp_immediate

                _, new_score = minimax(nb, depth - 1, alpha, beta, False)
                new_score -= penalty
                new_score += (3 - abs(col - center))

                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            if best_col is None:
                lm = legal_moves(b)
                best_col = lm[0] if lm else 0
            return best_col, value
        else:
            value = math.inf
            best_col = None
            for col in sorted(valid_locations, key=lambda x: abs(x - center)):
                result = make_move(b, col, -1)
                if result is None:
                    continue
                nb, _ = result
                _, new_score = minimax(nb, depth - 1, alpha, beta, True)
                new_score -= (3 - abs(col - center))
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            if best_col is None:
                lm = legal_moves(b)
                best_col = lm[0] if lm else 0
            return best_col, value

    valid = legal_moves(board)
    if not valid:
        return 0  # should not happen in a normal game; fallback

    center = COLS // 2

    # 1. Immediate winning move
    for c in sorted(valid, key=lambda x: abs(x - center)):
        result = make_move(board, c, 1)
        if result is None:
            continue
        nb, _ = result
        if winning_move(nb, 1):
            return c

    # 2. Immediate block of opponent winning move
    opp_winning_cols = []
    for c in valid:
        result = make_move(board, c, -1)
        if result is None:
            continue
        nb, _ = result
        if winning_move(nb, -1):
            opp_winning_cols.append(c)
    if opp_winning_cols:
        # If multiple threats exist, choose one if possible; otherwise game may be lost.
        # Prefer directly blocking in a central column.
        opp_winning_cols.sort(key=lambda x: abs(x - center))
        for c in opp_winning_cols:
            if c in valid:
                return c

    # 3. Prefer safe moves
    safe = safe_moves(board, 1)
    candidate_moves = safe if safe else valid

    # 4. Iterative deepening minimax
    best_move = sorted(candidate_moves, key=lambda x: abs(x - center))[0]
    try:
        for depth in range(1, 8):
            # Search on original board; minimax itself considers all legal moves.
            col, _ = minimax(board, depth, -math.inf, math.inf, True)
            if col is not None and col in valid:
                if (not safe) or (col in candidate_moves):
                    best_move = col
                else:
                    # if search picked unsafe move but safe moves exist, keep safe fallback
                    pass
            if time.time() - start > time_limit:
                break
    except TimeoutError:
        pass

    if best_move in valid:
        return best_move

    # Final guaranteed legal fallback
    for c in sorted(valid, key=lambda x: abs(x - center)):
        return c
    return 0
