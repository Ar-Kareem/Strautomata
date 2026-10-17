
import math
from typing import List, Tuple

def policy(my_men, my_kings, opp_men, opp_kings, color):
    """
    Return a legal move ((from_row, from_col), (to_row, to_col)).
    Captures are mandatory when available.
    """
    # Convert to lists if not already
    my_men = list(my_men)
    my_kings = list(my_kings)
    opp_men = list(opp_men)
    opp_kings = list(opp_kings)

    moves = get_moves(my_men, my_kings, opp_men, opp_kings, color)
    if not moves:
        # No legal move; but should not happen in arena
        return ((0,0),(0,0))
    # Minimax depth 2
    best_move = moves[0]
    best_score = -math.inf
    opp_color = 'w' if color == 'b' else 'b'
    for mv in moves:
        n_my_men, n_my_kings, n_opp_men, n_opp_kings = apply_move(
            my_men, my_kings, opp_men, opp_kings, color, mv
        )
        opp_moves = get_moves(n_opp_men, n_opp_kings, n_my_men, n_my_kings, opp_color)
        if not opp_moves:
            score = 9999  # winning
        else:
            # opponent minimizes
            worst = math.inf
            for omv in opp_moves:
                o_my_men, o_my_kings, o_opp_men, o_opp_kings = apply_move(
                    n_opp_men, n_opp_kings, n_my_men, n_my_kings, opp_color, omv
                )
                # evaluate from original player's perspective
                score_eval = evaluate(o_opp_men, o_opp_kings, o_my_men, o_my_kings)
                if score_eval < worst:
                    worst = score_eval
            score = worst
        if score > best_score:
            best_score = score
            best_move = mv
    return best_move


def evaluate(my_men, my_kings, opp_men, opp_kings):
    return len(my_men) + 1.5*len(my_kings) - (len(opp_men) + 1.5*len(opp_kings))

def get_moves(my_men, my_kings, opp_men, opp_kings, color):
    """Generate legal moves for side color."""
    my_set = set(my_men) | set(my_kings)
    opp_set = set(opp_men) | set(opp_kings)
    captures = []
    moves = []
    # directions
    if color == 'b':
        fwd = -1
        promote_row = 0
    else:
        fwd = 1
        promote_row = 7

    # men
    for (r,c) in my_men:
        for dc in (-1,1):
            # simple move
            nr, nc = r+fwd, c+dc
            if on_board(nr,nc) and (nr,nc) not in my_set and (nr,nc) not in opp_set:
                moves.append(((r,c),(nr,nc)))
            # capture
            jr, jc = r+2*fwd, c+2*dc
            mid = (r+fwd, c+dc)
            if on_board(jr,jc) and (jr,jc) not in my_set and (jr,jc) not in opp_set:
                if mid in opp_set:
                    captures.append(((r,c),(jr,jc)))
    # kings
    for (r,c) in my_kings:
        for dr in (-1,1):
            for dc in (-1,1):
                nr, nc = r+dr, c+dc
                if on_board(nr,nc) and (nr,nc) not in my_set and (nr,nc) not in opp_set:
                    moves.append(((r,c),(nr,nc)))
                jr, jc = r+2*dr, c+2*dc
                mid = (r+dr, c+dc)
                if on_board(jr,jc) and (jr,jc) not in my_set and (jr,jc) not in opp_set:
                    if mid in opp_set:
                        captures.append(((r,c),(jr,jc)))
    return captures if captures else moves

def apply_move(my_men, my_kings, opp_men, opp_kings, color, move):
    """Return new lists after applying move for color."""
    my_men = list(my_men)
    my_kings = list(my_kings)
    opp_men = list(opp_men)
    opp_kings = list(opp_kings)

    (fr,fc),(tr,tc) = move
    is_king = (fr,fc) in my_kings
    if is_king:
        my_kings.remove((fr,fc))
    else:
        my_men.remove((fr,fc))

    # capture?
    if abs(tr-fr) == 2:
        mr, mc = (fr+tr)//2, (fc+tc)//2
        if (mr,mc) in opp_men:
            opp_men.remove((mr,mc))
        elif (mr,mc) in opp_kings:
            opp_kings.remove((mr,mc))

    # promotion
    if not is_king:
        if color == 'b' and tr == 0:
            my_kings.append((tr,tc))
        elif color == 'w' and tr == 7:
            my_kings.append((tr,tc))
        else:
            my_men.append((tr,tc))
    else:
        my_kings.append((tr,tc))

    return my_men, my_kings, opp_men, opp_kings

def on_board(r,c):
    return 0 <= r <= 7 and 0 <= c <= 7
