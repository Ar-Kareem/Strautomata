
from typing import List, Tuple
import copy

Pos = Tuple[int, int]

def is_promotion(to_row: int, color: str) -> bool:
    return to_row == 0 if color == 'b' else to_row == 7

def get_legal_moves(my_men, my_kings, opp_men, opp_kings, color: str) -> List[Tuple[Pos, Pos]]:
    all_my = my_men + my_kings
    occupied = set(all_my + opp_men + opp_kings)
    opp_set = set(opp_men + opp_kings)
    moves = []
    forward_dirs = [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]
    king_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    has_captures = False

    for is_king, pieces in [(False, my_men), (True, my_kings)]:
        dirs = king_dirs if is_king else forward_dirs
        for r, c in pieces:
            for dr, dc in dirs:
                # Simple move
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in occupied:
                    moves.append(((r, c), (nr, nc)))

                # Capture
                njr, njc = r + 2 * dr, c + 2 * dc
                mid = (r + dr, c + dc)
                if (0 <= njr < 8 and 0 <= njc < 8 and 
                    mid in opp_set and (njr, njc) not in occupied):
                    moves.append(((r, c), (njr, njc)))
                    has_captures = True

    # If captures exist, keep only captures
    if has_captures:
        moves = [m for m in moves if abs(m[1][0] - m[0][0]) == 2]
    return moves

def apply_move(my_men, my_kings, opp_men, opp_kings, from_: Pos, to: Pos, color: str):
    new_my_men = copy.copy(my_men)
    new_my_kings = copy.copy(my_kings)
    new_opp_men = copy.copy(opp_men)
    new_opp_kings = copy.copy(opp_kings)

    # Determine piece type
    if from_ in new_my_men:
        moving_men = True
        new_my_men.remove(from_)
    elif from_ in new_my_kings:
        moving_men = False
        new_my_kings.remove(from_)
    else:
        raise ValueError("Invalid from position")

    # Apply move
    if abs(to[0] - from_[0]) == 2:  # Jump
        mid = ((from_[0] + to[0]) // 2, (from_[1] + to[1]) // 2)
        if mid in new_opp_men:
            new_opp_men.remove(mid)
        elif mid in new_opp_kings:
            new_opp_kings.remove(mid)
        
        promote = moving_men and is_promotion(to[0], color)
        if moving_men and promote:
            new_my_kings.append(to)
        else:
            if moving_men:
                new_my_men.append(to)
            else:
                new_my_kings.append(to)
    else:  # Simple move
        promote = moving_men and is_promotion(to[0], color)
        if moving_men and promote:
            new_my_kings.append(to)
        else:
            if moving_men:
                new_my_men.append(to)
            else:
                new_my_kings.append(to)

    return new_my_men, new_my_kings, new_opp_men, new_opp_kings

def evaluate(my_men, my_kings, opp_men, opp_kings, color: str) -> float:
    my_material = len(my_men) + 2 * len(my_kings)
    opp_material = len(opp_men) + 2 * len(opp_kings)
    position_bonus = 0.0
    # Bonus: advancement towards promotion
    for r, c in my_men:
        position_bonus += (7 - r) if color == 'b' else r
    for r, c in opp_men:
        position_bonus -= (7 - r) if color != 'b' else r
    return my_material - opp_material + 0.1 * position_bonus

def policy(my_men: List[Pos], my_kings: List[Pos], opp_men: List[Pos], opp_kings: List[Pos], color: str) -> Tuple[Pos, Pos]:
    legal_moves = get_legal_moves(my_men, my_kings, opp_men, opp_kings, color)
    if not legal_moves:
        raise ValueError("No legal moves available")

    best_move = None
    best_score = -float('inf')
    for move in legal_moves:
        nm, nk, om, ok = apply_move(my_men, my_kings, opp_men, opp_kings, move[0], move[1], color)
        score = evaluate(nm, nk, om, ok, color)
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
