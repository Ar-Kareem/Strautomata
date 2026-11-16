
import random
from collections import defaultdict

def policy(my_men, my_kings, opp_men, opp_kings, color):
    # --- Helpers ---
    DIRECTIONS = {
        'b': [(-1, -1), (-1, 1)],  # black moves "down" (to lower row)
        'w': [(1, -1), (1, 1)],    # white moves "up" (to higher row)
    }
    # kings can move both ways
    def piece_dirs(is_king):
        if is_king:
            return [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return DIRECTIONS[color]

    def in_bounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8 and ((r + c) % 2 == 1)

    my_set = set(my_men) | set(my_kings)
    opp_set = set(opp_men) | set(opp_kings)

    my_kings_set = set(my_kings)
    my_men_set = set(my_men)

    def is_my(r, c):
        return (r, c) in my_set

    def is_opp(r, c):
        return (r, c) in opp_set

    def is_king(r, c):
        return (r, c) in my_kings_set

    # board occupancy
    occ = {}
    for p in my_men: occ[p] = 'm'
    for p in my_kings: occ[p] = 'k'
    for p in opp_men: occ[p] = 'o'
    for p in opp_kings: occ[p] = 'K'

    # Heuristic weights
    WEIGHT_CAPTURE = 1000
    WEIGHT_MULTI = 120
    WEIGHT_KING = 260
    WEIGHT_PIECE = 45
    WEIGHT_AVOID_CAPTURE = 30
    WEIGHT_CENTER_ADV = 3  # small positional

    def kinging_row():
        return 0 if color == 'b' else 7

    king_row = kinging_row()

    # Directions for capture jumps
    def capture_moves_from(start):
        """
        Return all capture sequences as lists of landing squares:
        seq = [start, mid?, ..., final]
        along with total captured list.
        We'll explore multi-jumps by simulating captures.
        """
        sr, sc = start
        start_is_king = is_king(sr, sc)
        dirs = piece_dirs(start_is_king)

        results = []

        # stack entries: current position, removed opponent positions set, path, captured list
        stack = [(sr, sc, set(), [start], [])]

        while stack:
            r, c, removed, path, captured = stack.pop()

            found = False
            for dr, dc in piece_dirs(is_king(r, c)):  # after moving, king status may change on the fly
                mr, mc = r + dr, c + dc
                lr, lc = r + 2*dr, c + 2*dc
                if not in_bounds(lr, lc):
                    continue
                if (mr, mc) in removed:
                    continue
                if not in_bounds(mr, mc):
                    # mid square should also be dark, but even if not, check occupancy logic
                    pass
                if is_opp(mr, mc) and (mr, mc) not in removed and (lr, lc) not in my_set and (lr, lc) not in removed and (lr, lc) not in opp_set:
                    found = True
                    # simulate capture
                    new_removed = set(removed)
                    new_removed.add((mr, mc))
                    new_path = path + [(lr, lc)]
                    new_captured = captured + [(mr, mc)]
                    # determine if piece becomes king; in standard checkers, kinging typically ends the turn
                    # in American checkers, multi-jumps stop if kinging occurs? Actually depends on rules.
                    # To stay broadly legal, we'll allow continuation after kinging only if captures are possible.
                    stack.append((lr, lc, new_removed, new_path, new_captured))

            if not found and len(path) > 1:
                results.append((path, captured))

        return results

    def simple_moves_from(start):
        sr, sc = start
        dirs = piece_dirs(is_king(sr, sc))
        moves = []
        for dr, dc in dirs:
            nr, nc = sr + dr, sc + dc
            if in_bounds(nr, nc) and (nr, nc) not in my_set and (nr, nc) not in opp_set:
                moves.append(((sr, sc), (nr, nc)))
        return moves

    def all_captures():
        cap_sequences = []
        for p in my_set:
            for path, captured in capture_moves_from(p):
                cap_sequences.append((path, captured))
        return cap_sequences

    def all_non_captures():
        moves = []
        for p in my_set:
            moves.extend(simple_moves_from(p))
        return moves

    # --- Evaluate moves ---
    def immediate_threat_after(final_pos, removed_opps, kinged):
        """
        Check if opponent can capture this piece immediately.
        Since only need a coarse safety check, we test capture patterns from opponent pieces
        targeting final_pos, assuming piece is at final_pos and removed_opps are empty.
        """
        fr, fc = final_pos
        board_occ = set(my_set) | set(opp_set) - removed_opps
        # final position should be occupied by us
        if fr == -1:  # unused
            return False

        # Determine if our piece is king after move
        our_is_king = kinged

        # For each opponent piece, see if it can jump over one of our squares into final_pos.
        opp_pieces = list(opp_men) + list(opp_kings)
        opp_kings_set_local = set(opp_kings)

        for pr, pc in opp_pieces:
            if (pr, pc) in opp_kings_set_local:
                dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            else:
                dirs = DIRECTIONS['b' if color == 'w' else 'w']  # opponent direction
            # opponent direction depends on opponent color: if we are w, opponent b moves down
            opp_color = 'b' if color == 'w' else 'w'
            dirs = piece_dirs(True) if (pr, pc) in opp_kings_set_local else DIRECTIONS[opp_color]

            for dr, dc in dirs:
                mr, mc = pr + dr, pc + dc
                lr, lc = pr + 2*dr, pc + 2*dc
                if (lr, lc) == (fr, fc):
                    # mid must contain our piece
                    if (mr, mc) == (fr - dr, fc - dc):
                        # ensure mid is occupied by us (it would be, since it's adjacent)
                        # Also ensure opponent landing square is dark and in bounds and empty (it is our square)
                        return True
        return False

    def score_move_capture(path, captured):
        start = path[0]
        final = path[-1]
        sr, sc = start
        fr, fc = final

        # pieces removed affects opponent material; captured are opponent positions
        captured_count = len(captured)

        # Kinging: if not already king at start and final row is king row
        became_king = False
        if not is_king(sr, sc) and fr == king_row:
            became_king = True

        # How many opponent men/kings were captured (approx)
        captured_men = sum(1 for p in captured if p in set(opp_men))
        captured_kings = sum(1 for p in captured if p in set(opp_kings))

        # Multi-jump preference
        multi_bonus = max(0, captured_count - 1) * WEIGHT_MULTI

        # Avoid immediate recapture (coarse)
        removed_opps = set(captured)
        # After capture, our piece is at final, removed opp squares empty.
        # Determine king status for safety check:
        our_is_king_after = is_king(sr, sc) or became_king
        threatened = immediate_threat_after(final, removed_opps, our_is_king_after)

        # Center/advancement: prefer moving forward (for non-king too)
        # (for black, forward decreases row; for white increases)
        adv = (abs(fr - king_row))  # smaller is closer to king
        # Convert to a bonus: closer to king => higher score
        adv_bonus = (7 - adv) * WEIGHT_CENTER_ADV

        score = 0
        score += WEIGHT_CAPTURE * captured_count
        score += multi_bonus
        score += WEIGHT_KING if became_king else 0
        score += WEIGHT_PIECE * captured_men
        score += WEIGHT_PIECE * 2 * captured_kings  # kings are worth more
        score += adv_bonus
        if threatened:
            score -= WEIGHT_AVOID_CAPTURE
        # Small random tie-break to avoid deterministic traps
        score += random.random() * 0.01
        return score, (start, final)

    def score_move_simple(move):
        (sr, sc), (fr, fc) = move
        became_king = False
        if not is_king(sr, sc) and fr == king_row:
            became_king = True

        # advancement bonus
        adv_bonus = (7 - abs(fr - king_row)) * WEIGHT_CENTER_ADV

        # safety check: can opponent capture us immediately after this move?
        # removed_opps empty
        our_is_king_after = is_king(sr, sc) or became_king
        threatened = immediate_threat_after((fr, fc), set(), our_is_king_after)

        score = 0
        score += WEIGHT_KING if became_king else 0
        score += adv_bonus
        if threatened:
            score -= WEIGHT_AVOID_CAPTURE
        score += random.random() * 0.01
        return score

    captures = all_captures()
    if captures:
        best_score = None
        best_move = None
        for path, captured in captures:
            sc, mv = score_move_capture(path, captured)
            if best_score is None or sc > best_score:
                best_score = sc
                best_move = mv
        return best_move

    # No captures: choose best simple move
    noncaps = all_non_captures()
    # Fallback (shouldn't happen): if no move, return first legal-ish (but game should always have moves)
    if not noncaps:
        # try to find any in-bound diagonal empty move
        for p in my_set:
            for mv in simple_moves_from(p):
                return mv
        # absolutely fallback
        return ((0, 1), (1, 0))

    best_score = None
    best_move = None
    for mv in noncaps:
        sc = score_move_simple(mv)
        if best_score is None or sc > best_score:
            best_score = sc
            best_move = mv
    return best_move
