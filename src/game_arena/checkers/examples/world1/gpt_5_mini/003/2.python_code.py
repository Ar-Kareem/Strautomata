
#!/usr/bin/env python3
# Checkers policy for 8x8 English/American-style draughts.
# Implements mandatory captures, multi-jumps, promotion-on-last-row (promotion ends turn),
# depth-limited alpha-beta search with a heuristic.
from typing import List, Tuple, Optional
import math
import time

Pos = Tuple[int, int]
Move = Tuple[Pos, Pos]

# Heuristic weights
MAN_VAL = 100
KING_VAL = 180
ADVANCE_BONUS = 5
MOBILITY_BONUS = 2

# Time safety: ensure we don't exceed ~0.9s
TIME_LIMIT = 0.90

def policy(my_men: List[Pos], my_kings: List[Pos], opp_men: List[Pos], opp_kings: List[Pos], color: str) -> Move:
    start_time = time.time()

    # Board helpers
    def in_bounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    # Occupancy set for quick checks
    def make_occupancy(my_men, my_kings, opp_men, opp_kings):
        occ = {}
        for p in my_men: occ[p] = 'm'
        for p in my_kings: occ[p] = 'k'
        for p in opp_men: occ[p] = 'o'
        for p in opp_kings: occ[p] = 'O'
        return occ

    # Determine forward direction for men
    forward_dir = 1 if color == 'w' else -1
    opp_color = 'b' if color == 'w' else 'w'
    opp_forward_dir = 1 if opp_color == 'w' else -1

    # Check if a square is occupied
    occ = make_occupancy(my_men, my_kings, opp_men, opp_kings)

    # Generate capture sequences (multi-jumps) for a piece
    def find_captures_from(pos: Pos, is_king: bool, my_men_l, my_kings_l, opp_men_l, opp_kings_l) -> List[Tuple[Pos, List[Pos]]]:
        # Return list of (final_pos, captured_list)
        captures = []

        occ_local = make_occupancy(my_men_l, my_kings_l, opp_men_l, opp_kings_l)

        r0, c0 = pos

        # Directions for capturing: kings can capture all 4 diagonals, men capture forward only
        dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if is_king else [(forward_dir, -1), (forward_dir, 1)]

        found_any = False
        for dr, dc in dirs:
            midr = r0 + dr
            midc = c0 + dc
            landr = r0 + 2*dr
            landc = c0 + 2*dc
            if not (in_bounds(midr, midc) and in_bounds(landr, landc)):
                continue
            mid = (midr, midc)
            land = (landr, landc)
            if land in occ_local:
                continue
            # mid must contain an opponent piece
            if mid in opp_men_l or mid in opp_kings_l:
                # simulate jump: remove captured mid, move piece from pos to land
                new_my_men = list(my_men_l)
                new_my_kings = list(my_kings_l)
                new_opp_men = [p for p in opp_men_l if p != mid]
                new_opp_kings = [p for p in opp_kings_l if p != mid]

                # remove original piece
                if pos in new_my_men:
                    new_my_men.remove(pos)
                if pos in new_my_kings:
                    new_my_kings.remove(pos)

                promoted = False
                # if non-king and reaches promotion row -> promotion happens and convention: promotion ends turn
                if not is_king:
                    if (color == 'w' and landr == 7) or (color == 'b' and landr == 0):
                        # promote and end capture sequence (promotion ends turn)
                        new_my_kings.append(land)
                        captures.append((land, [mid]))
                        found_any = True
                        continue
                    else:
                        # move as man
                        new_my_men.append(land)
                else:
                    # move king
                    new_my_kings.append(land)

                # recursively search for further captures from landing square
                further = find_captures_from(land, is_king or promoted, new_my_men, new_my_kings, new_opp_men, new_opp_kings)
                if further:
                    for final_pos, cap_list in further:
                        captures.append((final_pos, [mid] + cap_list))
                else:
                    captures.append((land, [mid]))
                found_any = True

        return captures

    # Generate all capture moves for side to move
    def all_capture_moves(my_men_l, my_kings_l, opp_men_l, opp_kings_l):
        moves = []
        for m in list(my_men_l):
            caps = find_captures_from(m, False, my_men_l, my_kings_l, opp_men_l, opp_kings_l)
            for final_pos, caplist in caps:
                moves.append((m, final_pos, caplist))
        for k in list(my_kings_l):
            caps = find_captures_from(k, True, my_men_l, my_kings_l, opp_men_l, opp_kings_l)
            for final_pos, caplist in caps:
                moves.append((k, final_pos, caplist))
        return moves

    # Generate simple (non-capture) moves
    def all_quiet_moves(my_men_l, my_kings_l, opp_men_l, opp_kings_l):
        moves = []
        occ_local = make_occupancy(my_men_l, my_kings_l, opp_men_l, opp_kings_l)
        for m in list(my_men_l):
            r, c = m
            for dr, dc in [(forward_dir, -1), (forward_dir, 1)]:
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and (nr, nc) not in occ_local:
                    moves.append((m, (nr, nc), []))
        for k in list(my_kings_l):
            r, c = k
            for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and (nr, nc) not in occ_local:
                    moves.append((k, (nr, nc), []))
        return moves

    # Apply a move to produce new board lists (does not handle opponent turn; only moves for current color)
    def apply_move(my_men_l, my_kings_l, opp_men_l, opp_kings_l, move_from: Pos, move_to: Pos, captured: List[Pos]):
        new_my_men = [p for p in my_men_l]
        new_my_kings = [p for p in my_kings_l]
        new_opp_men = [p for p in opp_men_l if p not in captured]
        new_opp_kings = [p for p in opp_kings_l if p not in captured]

        # remove original piece
        is_king_piece = False
        if move_from in new_my_men:
            new_my_men.remove(move_from)
        elif move_from in new_my_kings:
            new_my_kings.remove(move_from)
            is_king_piece = True

        # promotion?
        r_to, _ = move_to
        promoted = False
        if not is_king_piece:
            if (color == 'w' and r_to == 7) or (color == 'b' and r_to == 0):
                # promote
                new_my_kings.append(move_to)
                promoted = True
            else:
                new_my_men.append(move_to)
        else:
            new_my_kings.append(move_to)

        return new_my_men, new_my_kings, new_opp_men, new_opp_kings

    # For opponent moves (to simulate both sides), need symmetrical functions with reversed color/directions.
    # We'll create a generic apply for arbitrary side given a flag indicating whose turn it is.
    def apply_move_general(my_men_l, my_kings_l, opp_men_l, opp_kings_l, move_from: Pos, move_to: Pos, captured: List[Pos], side_color: str):
        # side_color is the side being moved (the 'my' lists belong to that side)
        new_my_men = [p for p in my_men_l]
        new_my_kings = [p for p in my_kings_l]
        new_opp_men = [p for p in opp_men_l if p not in captured]
        new_opp_kings = [p for p in opp_kings_l if p not in captured]

        is_king_piece = False
        if move_from in new_my_men:
            new_my_men.remove(move_from)
        elif move_from in new_my_kings:
            new_my_kings.remove(move_from)
            is_king_piece = True

        r_to, _ = move_to
        promoted = False
        if not is_king_piece:
            if (side_color == 'w' and r_to == 7) or (side_color == 'b' and r_to == 0):
                new_my_kings.append(move_to)
                promoted = True
            else:
                new_my_men.append(move_to)
        else:
            new_my_kings.append(move_to)

        return new_my_men, new_my_kings, new_opp_men, new_opp_kings

    # Evaluate board from perspective of 'color' (positive is good for us)
    def evaluate(my_men_l, my_kings_l, opp_men_l, opp_kings_l):
        val = 0
        # material
        val += MAN_VAL * len(my_men_l) + KING_VAL * len(my_kings_l)
        val -= MAN_VAL * len(opp_men_l) + KING_VAL * len(opp_kings_l)
        # advancement bonus for men
        for (r, c) in my_men_l:
            # reward moving toward promotion
            if color == 'w':
                val += ADVANCE_BONUS * r
            else:
                val += ADVANCE_BONUS * (7 - r)
        for (r, c) in opp_men_l:
            if color == 'w':
                val -= ADVANCE_BONUS * r
            else:
                val -= ADVANCE_BONUS * (7 - r)
        # mobility: number of legal quiet moves (approx)
        my_moves = len(all_quiet_moves(my_men_l, my_kings_l, opp_men_l, opp_kings_l))
        # For opponent mobility, generate by swapping roles and using opposite forward dir
        opp_moves = len(all_quiet_moves(opp_men_l, opp_kings_l, my_men_l, my_kings_l))
        val += MOBILITY_BONUS * (my_moves - opp_moves)
        return val

    # Alpha-beta search
    def generate_moves_for_side(my_men_l, my_kings_l, opp_men_l, opp_kings_l, side_color):
        # generate capture moves first (mandatory)
        # But need to use forward direction appropriate to side_color
        nonlocal forward_dir, opp_forward_dir
        saved_forward = forward_dir
        if side_color == color:
            forward_dir_local = 1 if side_color == 'w' else -1
        else:
            forward_dir_local = 1 if side_color == 'w' else -1
        # Temporarily set forward_dir used by find_captures_from and quiet moves via closure?
        # Instead of messing with closure, we'll call specialized generators below.
        # To avoid complexity, we produce captures and quiet moves by writing small local versions.
        def find_captures_from_local(pos: Pos, is_king: bool, my_men_ll, my_kings_ll, opp_men_ll, opp_kings_ll, s_color):
            # same logic as earlier but using s_color as side color, and promotion ends turn
            results = []
            occ_local = make_occupancy(my_men_ll, my_kings_ll, opp_men_ll, opp_kings_ll)
            r0, c0 = pos
            dir_forward = 1 if s_color == 'w' else -1
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if is_king else [(dir_forward, -1), (dir_forward, 1)]
            for dr, dc in dirs:
                midr = r0 + dr
                midc = c0 + dc
                landr = r0 + 2*dr
                landc = c0 + 2*dc
                if not (in_bounds(midr, midc) and in_bounds(landr, landc)):
                    continue
                mid = (midr, midc)
                land = (landr, landc)
                if land in occ_local:
                    continue
                if mid in opp_men_ll or mid in opp_kings_ll:
                    new_my_men = list(my_men_ll)
                    new_my_kings = list(my_kings_ll)
                    new_opp_men = [p for p in opp_men_ll if p != mid]
                    new_opp_kings = [p for p in opp_kings_ll if p != mid]
                    if pos in new_my_men:
                        new_my_men.remove(pos)
                    if pos in new_my_kings:
                        new_my_kings.remove(pos)
                    # promotion ends turn
                    if not is_king:
                        if (s_color == 'w' and landr == 7) or (s_color == 'b' and landr == 0):
                            new_my_kings.append(land)
                            results.append((land, [mid]))
                            continue
                        else:
                            new_my_men.append(land)
                    else:
                        new_my_kings.append(land)
                    further = find_captures_from_local(land, is_king, new_my_men, new_my_kings, new_opp_men, new_opp_kings, s_color)
                    if further:
                        for final_pos, caplist in further:
                            results.append((final_pos, [mid] + caplist))
                    else:
                        results.append((land, [mid]))
            return results

        moves = []
        # captures
        for p in my_men_l:
            caps = find_captures_from_local(p, False, my_men_l, my_kings_l, opp_men_l, opp_kings_l, side_color)
            for final_pos, caplist in caps:
                moves.append((p, final_pos, caplist))
        for p in my_kings_l:
            caps = find_captures_from_local(p, True, my_men_l, my_kings_l, opp_men_l, opp_kings_l, side_color)
            for final_pos, caplist in caps:
                moves.append((p, final_pos, caplist))
        if moves:
            return moves
        # quiet moves
        occ_local = make_occupancy(my_men_l, my_kings_l, opp_men_l, opp_kings_l)
        dir_forward = 1 if side_color == 'w' else -1
        for m in my_men_l:
            r, c = m
            for dr, dc in [(dir_forward, -1), (dir_forward, 1)]:
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and (nr, nc) not in occ_local:
                    moves.append((m, (nr, nc), []))
        for k in my_kings_l:
            r, c = k
            for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and (nr, nc) not in occ_local:
                    moves.append((k, (nr, nc), []))
        return moves

    # Choose search depth based on piece count to tradeoff speed/strength
    total_pieces = len(my_men) + len(my_kings) + len(opp_men) + len(opp_kings)
    if total_pieces <= 8:
        max_depth = 8
    elif total_pieces <= 14:
        max_depth = 6
    else:
        max_depth = 4

    # Alpha-beta with simple time check
    def alphabeta(my_men_l, my_kings_l, opp_men_l, opp_kings_l, depth, alpha, beta, maximizing_player, current_color, start_time_local):
        # time cutoff
        if time.time() - start_time_local > TIME_LIMIT:
            # return heuristic immediately
            return evaluate(my_men_l, my_kings_l, opp_men_l, opp_kings_l), None

        # Terminal tests: if one side has no pieces or no legal moves
        my_moves = generate_moves_for_side(my_men_l, my_kings_l, opp_men_l, opp_kings_l, current_color)
        if not my_moves:
            # If no moves for current_color, they lose
            if current_color == color:
                return -1000000 - depth, None
            else:
                return 1000000 + depth, None

        if depth == 0:
            return evaluate(my_men_l, my_kings_l, opp_men_l, opp_kings_l), None

        best_move = None
        if maximizing_player:
            value = -math.inf
            # order moves: captures first and by captured count desc, promotion preference
            def move_key(mv):
                frm, to, caps = mv
                # promotion?
                pr = 0
                if frm in my_men_l:
                    if (current_color == 'w' and to[0] == 7) or (current_color == 'b' and to[0] == 0):
                        pr = 1
                return (len(caps), pr)
            moves = generate_moves_for_side(my_men_l, my_kings_l, opp_men_l, opp_kings_l, current_color)
            moves.sort(key=move_key, reverse=True)
            for mv in moves:
                frm, to, caps = mv
                # apply move
                new_my_men, new_my_kings, new_opp_men, new_opp_kings = apply_move_general(my_men_l, my_kings_l, opp_men_l, opp_kings_l, frm, to, caps, current_color)
                # next turn swaps roles
                # Recursively call with opponent as maximizing/minimizing flip
                next_my_men = new_opp_men
                next_my_kings = new_opp_kings
                next_opp_men = new_my_men
                next_opp_kings = new_my_kings
                score, _ = alphabeta(next_my_men, next_my_kings, next_opp_men, next_opp_kings, depth - 1, alpha, beta, False, ('b' if current_color == 'w' else 'w'), start_time_local)
                # score is from perspective of 'current' next call, so invert because we swapped sides
                score = -score
                if score > value:
                    value = score
                    best_move = mv
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value, best_move
        else:
            value = math.inf
            # minimizing player
            def move_key_min(mv):
                frm, to, caps = mv
                pr = 0
                if frm in opp_men_l:
                    if (current_color == 'w' and to[0] == 7) or (current_color == 'b' and to[0] == 0):
                        pr = 1
                return (len(caps), pr)
            moves = generate_moves_for_side(my_men_l, my_kings_l, opp_men_l, opp_kings_l, current_color)
            moves.sort(key=move_key_min, reverse=True)
            for mv in moves:
                frm, to, caps = mv
                new_my_men, new_my_kings, new_opp_men, new_opp_kings = apply_move_general(my_men_l, my_kings_l, opp_men_l, opp_kings_l, frm, to, caps, current_color)
                next_my_men = new_opp_men
                next_my_kings = new_opp_kings
                next_opp_men = new_my_men
                next_opp_kings = new_my_kings
                score, _ = alphabeta(next_my_men, next_my_kings, next_opp_men, next_opp_kings, depth - 1, alpha, beta, True, ('b' if current_color == 'w' else 'w'), start_time_local)
                score = -score
                if score < value:
                    value = score
                    best_move = mv
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value, best_move

    # Root: generate legal moves for our color
    root_moves = all_capture_moves(my_men, my_kings, opp_men, opp_kings)
    if not root_moves:
        # quiet moves
        root_moves = all_quiet_moves(my_men, my_kings, opp_men, opp_kings)
    # If still no moves, return a dummy but valid move (shouldn't happen)
    if not root_moves:
        # try to scan for any piece and any neighbor empty square
        occ_now = make_occupancy(my_men, my_kings, opp_men, opp_kings)
        for p in my_men + my_kings:
            r, c = p
            for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and (nr, nc) not in occ_now:
                    return (p, (nr, nc))
        # fallback: return first piece to itself (should not be allowed but just for safety)
        if my_men:
            return (my_men[0], my_men[0])
        if my_kings:
            return (my_kings[0], my_kings[0])
        # no pieces at all (shouldn't happen)
        return ((0, 1), (0, 1))

    # Quick heuristic-only selection to have a fallback
    best_simple = None
    best_simple_score = -1e9
    for frm, to, caps in root_moves:
        # quick evaluate immediate result
        new_my_men, new_my_kings, new_opp_men, new_opp_kings = apply_move(my_men, my_kings, opp_men, opp_kings, frm, to, caps)
        s = evaluate(new_my_men, new_my_kings, new_opp_men, new_opp_kings)
        # prefer more captures
        s += 50 * len(caps)
        if s > best_simple_score:
            best_simple_score = s
            best_simple = (frm, to, caps)

    # Now run alpha-beta search from root with chosen depth
    chosen_move = None
    try:
        val, mv = alphabeta(my_men, my_kings, opp_men, opp_kings, max_depth, -1e9, 1e9, True, color, start_time)
        if mv is not None:
            chosen_move = mv
        else:
            # fallback to simple best
            chosen_move = best_simple
    except Exception:
        # in case of timeouts or other issues, pick best_simple
        chosen_move = best_simple

    if chosen_move is None:
        # fallback
        frm, to, caps = root_moves[0]
        return (frm, to)
    frm, to, caps = chosen_move
    return (frm, to)

# The file exposes policy(...) as required.
if __name__ == "__main__":
    # simple self-test
    # starting position example: black pieces on rows 5-7, white on 0-2 depending on representation.
    # This test is not exhaustive.
    my_men = [(2,1),(2,3)]
    my_kings = []
    opp_men = [(3,2)]
    opp_kings = []
    mv = policy(my_men, my_kings, opp_men, opp_kings, 'w')
    print("Selected move:", mv)
