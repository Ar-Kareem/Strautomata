
import math
import random
from copy import deepcopy
from typing import List

ROWS = 6
COLS = 7
PLAYER = 1
OPP = -1

def policy(board: List[List[int]]) -> int:
    """
    Choose a column (0-6) to drop a disc for the current player (1).
    Board is a 6x7 list of lists, 0 empty, 1 our disc, -1 opponent disc.
    """
    # Defensive copy not strictly necessary here, we won't modify input.
    b = board

    # Helper functions
    def valid_moves(bd):
        return [c for c in range(COLS) if bd[0][c] == 0]

    def get_next_row(bd, col):
        for r in range(ROWS-1, -1, -1):
            if bd[r][col] == 0:
                return r
        return None

    def drop_piece(bd, col, piece):
        r = get_next_row(bd, col)
        if r is None:
            return None
        newb = [row[:] for row in bd]
        newb[r][col] = piece
        return newb

    def winning_move(bd, piece):
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS-3):
                if all(bd[r][c+i] == piece for i in range(4)):
                    return True
        # Vertical
        for c in range(COLS):
            for r in range(ROWS-3):
                if all(bd[r+i][c] == piece for i in range(4)):
                    return True
        # Positive diag (/)
        for r in range(3, ROWS):
            for c in range(COLS-3):
                if all(bd[r-i][c+i] == piece for i in range(4)):
                    return True
        # Negative diag (\)
        for r in range(ROWS-3):
            for c in range(COLS-3):
                if all(bd[r+i][c+i] == piece for i in range(4)):
                    return True
        return False

    # Immediate winning move?
    moves = valid_moves(b)
    if not moves:
        return 0  # should not happen, but return valid int

    for col in moves:
        nb = drop_piece(b, col, PLAYER)
        if nb is not None and winning_move(nb, PLAYER):
            return col

    # Block opponent immediate win
    opp_wins = []
    for col in moves:
        nb = drop_piece(b, col, OPP)
        if nb is not None and winning_move(nb, OPP):
            opp_wins.append(col)
    if opp_wins:
        # If multiple, choose one that is also a good heuristic choice (center pref)
        center = COLS // 2
        opp_wins.sort(key=lambda c: abs(c - center))
        return opp_wins[0]

    # Heuristic evaluation
    def score_window(window, piece):
        score = 0
        opp_piece = OPP if piece == PLAYER else PLAYER
        count_piece = window.count(piece)
        count_opp = window.count(opp_piece)
        count_empty = window.count(0)

        if count_piece == 4:
            score += 10000
        elif count_piece == 3 and count_empty == 1:
            score += 50
        elif count_piece == 2 and count_empty == 2:
            score += 10

        if count_opp == 3 and count_empty == 1:
            score -= 80
        elif count_opp == 2 and count_empty == 2:
            score -= 5
        return score

    def evaluate_position(bd, piece):
        score = 0
        # Center column preference
        center_array = [bd[r][COLS//2] for r in range(ROWS)]
        center_count = center_array.count(piece)
        score += center_count * 6

        # Horizontal
        for r in range(ROWS):
            row_array = bd[r]
            for c in range(COLS-3):
                window = row_array[c:c+4]
                score += score_window(window, piece)
        # Vertical
        for c in range(COLS):
            col_array = [bd[r][c] for r in range(ROWS)]
            for r in range(ROWS-3):
                window = col_array[r:r+4]
                score += score_window(window, piece)
        # Positive diagonal (/)
        for r in range(3, ROWS):
            for c in range(COLS-3):
                window = [bd[r-i][c+i] for i in range(4)]
                score += score_window(window, piece)
        # Negative diagonal (\)
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = [bd[r+i][c+i] for i in range(4)]
                score += score_window(window, piece)

        return score

    # Negamax with alpha-beta
    def is_terminal_node(bd):
        return winning_move(bd, PLAYER) or winning_move(bd, OPP) or len(valid_moves(bd)) == 0

    # Order moves by center proximity
    def order_moves(mv_list):
        center = COLS // 2
        return sorted(mv_list, key=lambda c: abs(c - center))

    # Depth selection: shall be moderate to fit time. 5 might be heavy; use 5 when few moves, else 4
    # Determine branching factor
    possible = len(moves)
    max_depth = 5 if possible <= 5 else 4

    # To avoid extremely long searches, set a hard bound on nodes (not time but helps)
    node_limit = 100000
    node_counter = [0]

    def negamax(bd, depth, alpha, beta, piece):
        node_counter[0] += 1
        if node_counter[0] > node_limit:
            # fallback heuristic
            return evaluate_position(bd, PLAYER if piece == PLAYER else -piece)
        if depth == 0 or is_terminal_node(bd):
            if winning_move(bd, PLAYER):
                return math.inf
            elif winning_move(bd, OPP):
                return -math.inf
            else:
                return evaluate_position(bd, piece)
        value = -math.inf
        for col in order_moves(valid_moves(bd)):
            nb = drop_piece(bd, col, piece)
            if nb is None:
                continue
            score = -negamax(nb, depth-1, -beta, -alpha, -piece)
            if score > value:
                value = score
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        return value

    # Evaluate each possible move by performing negamax
    best_score = -math.inf
    best_cols = []
    for col in order_moves(moves):
        nb = drop_piece(b, col, PLAYER)
        if nb is None:
            continue
        score = -negamax(nb, max_depth-1, -math.inf, math.inf, OPP)
        # Slight tie-breaker by center proximity
        if score > best_score:
            best_score = score
            best_cols = [col]
        elif score == best_score:
            best_cols.append(col)
    if not best_cols:
        # fallback: pick a random valid move, favor center
        center = COLS // 2
        moves.sort(key=lambda c: abs(c-center))
        return moves[0]
    # Choose among best columns; prefer center-most
    center = COLS // 2
    best_cols.sort(key=lambda c: abs(c - center))
    return best_cols[0]


# If run as main, include a small random-play test (not used by graders).
if __name__ == "__main__":
    # Empty board test
    empty = [[0]*COLS for _ in range(ROWS)]
    print("Policy on empty board:", policy(empty))
