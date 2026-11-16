
import random
from typing import List, Tuple, Set

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def in_board(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8

def playable(r: int, c: int) -> bool:
    # (0,0) is a dark square → playable squares have even parity
    return (r + c) % 2 == 0

def opponent_set(my_men, my_kings, opp_men, opp_kings) -> Set[Tuple[int, int]]:
    return set(opp_men) | set(opp_kings)

def my_set(my_men, my_kings) -> Set[Tuple[int, int]]:
    return set(my_men) | set(my_kings)

# ----------------------------------------------------------------------
# Capture generation (multi‑jump)
# ----------------------------------------------------------------------
def generate_captures(pos: Tuple[int, int],
                      is_king: bool,
                      my_pieces: Set[Tuple[int, int]],
                      opp_pieces: Set[Tuple[int, int]],
                      visited: Set[Tuple[int, int]]) -> List[Tuple[List[Tuple[int, int]], Set[Tuple[int, int]]]]:
    """
    Returns a list of (path, captured_set) where
    path[0] == pos and the last element is the final landing square.
    """
    r, c = pos
    results = []

    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    for dr, dc in directions:
        # men can capture backwards as well, so we do not restrict dr
        mid_r, mid_c = r + dr, c + dc
        landing_r, landing_c = r + 2 * dr, c + 2 * dc

        if not (in_board(mid_r, mid_c) and in_board(landing_r, landing_c)):
            continue
        if not playable(landing_r, landing_c):
            continue

        mid_sq = (mid_r, mid_c)
        landing_sq = (landing_r, landing_c)

        if mid_sq not in opp_pieces:
            continue
        if landing_sq in my_pieces or landing_sq in opp_pieces:
            continue
        if mid_sq in visited:
            continue  # cannot capture the same piece twice

        # perform this jump
        new_visited = visited | {mid_sq}
        sub_paths = generate_captures(
            landing_sq,
            is_king,
            my_pieces | {landing_sq},
            opp_pieces - {mid_sq},
            new_visited,
        )
        if sub_paths:
            for sub_path, sub_capt in sub_paths:
                results.append(
                    ([pos] + sub_path, {mid_sq} | sub_capt)
                )
        else:
            # end of this capture line
            results.append(([pos, landing_sq], {mid_sq}))

    return results

# ----------------------------------------------------------------------
# Safety evaluation for non‑capture moves
# ----------------------------------------------------------------------
def is_square_safe(target: Tuple[int, int],
                   my_pieces: Set[Tuple[int, int]],
                   opp_pieces: Set[Tuple[int, int]]) -> bool:
    """Check if opponent could capture `target` on their next turn."""
    tr, tc = target
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    for dr, dc in directions:
        opp_r, opp_c = tr + dr, tc + dc
        land_r, land_c = tr - dr, tc - dc
        if not (in_board(opp_r, opp_c) and in_board(land_r, land_c)):
            continue
        if not playable(land_r, land_c):
            continue
        opp_sq = (opp_r, opp_c)
        land_sq = (land_r, land_c)

        if opp_sq in opp_pieces and land_sq not in my_pieces and land_sq not in opp_pieces:
            # opponent could jump over our piece
            return False
    return True

# ----------------------------------------------------------------------
# Main policy function
# ----------------------------------------------------------------------
def policy(my_men: List[Tuple[int, int]],
           my_kings: List[Tuple[int, int]],
           opp_men: List[Tuple[int, int]],
           opp_kings: List[Tuple[int, int]],
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Returns a legal move ((from_r, from_c), (to_r, to_c)).
    Captures are mandatory and the longest capture chain is chosen.
    """

    # Build sets for fast queries
    my_pieces = my_set(my_men, my_kings)
    opp_pieces = opponent_set(my_men, my_kings, opp_men, opp_kings)

    # ------------------------------------------------------------------
    # 1) Look for captures
    # ------------------------------------------------------------------
    all_captures = []  # each element: (path, captured_set)
    for piece in my_men:
        caps = generate_captures(piece, False, my_pieces, opp_pieces, set())
        all_captures.extend(caps)
    for piece in my_kings:
        caps = generate_captures(piece, True, my_pieces, opp_pieces, set())
        all_captures.extend(caps)

    if all_captures:
        # Determine the best capture according to the policy
        # 1) maximal number of captured opponent pieces
        max_len = max(len(captured) for _, captured in all_captures)
        best = [p for p in all_captures if len(p[1]) == max_len]

        # 2) Prefer captures that promote the piece
        promotion_row = 0 if color == 'b' else 7
        def promotes(path):
            return path[-1][0] == promotion_row and path[0] not in my_kings
        promo = [p for p in best if promotes(p[0])]
        if promo:
            best = promo

        # 3) If still multiple, pick the one that ends closest to promotion
        def distance_to_promotion(path):
            r, _ = path[-1]
            return abs(r - promotion_row)
        best.sort(key=lambda x: distance_to_promotion(x[0]))
        chosen_path = best[0][0]

        return (chosen_path[0], chosen_path[-1])

    # ------------------------------------------------------------------
    # 2) No captures – generate ordinary moves
    # ------------------------------------------------------------------
    normal_moves = []  # each element: ((from), (to))
    forward_dir = -1 if color == 'b' else 1

    for piece in my_men:
        r, c = piece
        for dc in (-1, 1):
            nr, nc = r + forward_dir, c + dc
            if not (in_board(nr, nc) and playable(nr, nc)):
                continue
            if (nr, nc) in my_pieces or (nr, nc) in opp_pieces:
                continue
            normal_moves.append((piece, (nr, nc)))

    for piece in my_kings:
        r, c = piece
        for dr in (-1, 1):
            for dc in (-1, 1):
                nr, nc = r + dr, c + dc
                if not (in_board(nr, nc) and playable(nr, nc)):
                    continue
                if (nr, nc) in my_pieces or (nr, nc) in opp_pieces:
                    continue
                normal_moves.append((piece, (nr, nc)))

    # ------------------------------------------------------------------
    # 3) Score the ordinary moves
    # ------------------------------------------------------------------
    promotion_row = 0 if color == 'b' else 7
    best_score = -10**9
    best_move = None

    for frm, to in normal_moves:
        score = 0

        # safety
        if is_square_safe(to, my_pieces - {frm} | {to}, opp_pieces):
            score += 30
        else:
            score -= 20  # risky move

        # promotion
        if to[0] == promotion_row:
            score += 40

        # distance to promotion for men (encourage forward movement)
        if frm in my_men:
            score += (abs(frm[0] - promotion_row) - abs(to[0] - promotion_row)) * 5

        # tie‑breaker deterministic ordering
        if score > best_score or (score == best_score and (to < best_move[1] if best_move else True)):
            best_score = score
            best_move = (frm, to)

    # It should never happen that we have no legal move (game over), but guard anyway
    if best_move is None:
        # fallback: just return the first possible move (there must be one)
        if normal_moves:
            return normal_moves[0]
        else:
            # No move possible – return a dummy move (should never be used)
            return ((0, 0), (0, 0))

    return best_move
