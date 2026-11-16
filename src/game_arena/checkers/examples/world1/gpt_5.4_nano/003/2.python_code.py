
import random
from collections import defaultdict

def policy(my_men, my_kings, opp_men, opp_kings, color):
    my_men = list(my_men)
    my_kings = list(my_kings)
    opp_men = list(opp_men)
    opp_kings = list(opp_kings)

    my_pieces = {tuple(p): 0 for p in my_men}  # 0 = man
    for p in my_kings:
        my_pieces[tuple(p)] = 1  # 1 = king

    opp_pieces = set(map(tuple, opp_men)) | set(map(tuple, opp_kings))
    my_all = set(my_pieces.keys())

    # Board helpers
    DARK = lambda r, c: (r + c) % 2 == 1

    def in_bounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    # Directions: for men, black moves down (r-1), white moves up (r+1)
    # Since our coordinate system has 0 bottom to 7 top:
    # color 'b' moves toward decreasing row values, color 'w' toward increasing row values.
    if color == 'b':
        fwd = -1
        king_row = 0
    else:
        fwd = +1
        king_row = 7

    # Capture move generation with multi-jumps
    # We return sequences as list of (from,to) for each jump step, but policy needs first->last.
    # For scoring we also need total captured count and landing position.
    def man_dirs():
        # A man can capture forward only in standard checkers (no backward captures for men).
        return [(fwd, -1), (fwd, +1)]

    def king_dirs():
        return [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]

    def piece_dirs(is_king):
        return king_dirs() if is_king else man_dirs()

    # For move ordering / speed
    all_moves_capture = []

    def make_board_blocking(my_set, opp_set):
        occ = my_set | opp_set
        return occ

    def dfs_captures(start, is_king, landing_board_my, landing_board_opp):
        # landing_board_my: set of my positions at current simulated state
        # landing_board_opp: set of opp positions at current simulated state
        # We will explore sequences and collect best sequences.
        # Returns list of sequences: each sequence is (steps, captured_count, final_pos, promoted_flag)
        results = []

        # Determine if king after this move? For multi-jump, promotion usually ends the turn immediately in many rules,
        # but some variants allow continued jumping after kinging. We'll assume common American rules:
        # reaching king row during a jump sequence ends the move (no further captures as king).
        # This is conservative; legality may vary, but it keeps move generation consistent with typical rule sets.
        def is_promoted(pos):
            r, _ = pos
            return r == king_row

        # Use local variables
        start_pos = start

        def rec(cur_pos, cur_is_king, my_set, opp_set, steps, captured_ct):
            nonlocal results
            moved = False
            r, c = cur_pos
            dirs = piece_dirs(cur_is_king)
            for dr, dc in dirs:
                mid = (r + dr, c + dc)
                nxt = (r + 2*dr, c + 2*dc)
                if in_bounds(*nxt) and DARK(*nxt):
                    if mid in opp_set and nxt not in my_set and nxt not in opp_set:
                        moved = True
                        # simulate
                        new_my = set(my_set)
                        new_opp = set(opp_set)
                        new_my.remove(cur_pos)
                        new_my.add(nxt)
                        new_opp.remove(mid)

                        new_steps = steps + [(cur_pos, nxt)]
                        new_captured = captured_ct + 1

                        # Promotion check
                        will_promote = (not cur_is_king) and (nxt[0] == king_row)
                        if will_promote:
                            # stop further captures for this turn
                            results.append((new_steps, new_captured, nxt, True))
                        else:
                            rec(nxt, cur_is_king or will_promote, new_my, new_opp, new_steps, new_captured)

            if not moved:
                # no further captures
                if steps:
                    # If any capture already happened, record sequence
                    results.append((steps, captured_ct, cur_pos, cur_is_king))

        # initial state
        # Ensure we start with correct is_king (kings in input)
        rec(start_pos, is_king, set(landing_board_my), set(landing_board_opp), [], 0)
        return results

    # Generate all capture sequences for all pieces
    occ_my = my_all
    occ_opp = opp_pieces

    for pos, is_king in my_pieces.items():
        if is_king not in (0,1):
            is_king = 1 if is_king else 0
        seqs = dfs_captures(pos, bool(is_king), occ_my, occ_opp)
        for steps, captured_ct, final_pos, _ in seqs:
            # Steps list length = captured_ct
            all_moves_capture.append({
                "from": steps[0][0],
                "to": steps[-1][1],
                "steps": steps,
                "captured": captured_ct,
                "final": final_pos
            })

    # Helper: determine if a given square is capturable by opponent next move
    def opponent_can_capture_from_square(target, opp_is_king):
        # Not used directly. We'll compute vulnerability by generating opponent captures
        pass

    def generate_opponent_captures(my_set, opp_set, opp_color):
        # Returns list of capture landings: (from,to,captured_count) for next player from a given state.
        # We'll just compute any capture moves available for opponent from current simulated sets.
        # Since we only need to know if target is capturable, we generate all capture sequences quickly.
        opp_dirs_fwd = -1 if opp_color == 'b' else +1
        opp_king_row = 0 if opp_color == 'b' else 7

        # build opp pieces map: determine kings by using input? We'll approximate:
        # We don't have king identity in simulated board. To be accurate, we would need full king state updates.
        # But for vulnerability heuristic, we can use a simpler and safe approximation:
        # treat opponent pieces as men unless they were kings initially.
        # Therefore, in the main policy we compute vulnerability using actual initial king sets only
        # (no mid-turn promotions/changes). That's sufficient for heuristic selection.
        # Here, my_set and opp_set are just for occupancy; king-ness is handled by using original lists.
        return []  # placeholder

    # For heuristic vulnerability we will do exact next capture check using original king/mens sets
    # by constructing hypothetical placements after our single move (no multi-jump complexity for opponent turn)
    # because we only compare candidate first-to-last moves.
    def compute_vulnerable_after_move(move_from, move_to, is_jump):
        # Simulate single-move board after our chosen move (for captures, remove the jumped piece(s) by replaying the sequence).
        # But we are not given the full sequence in this function; we will pass in sequence when needed.
        return False

    # We'll instead compute vulnerability exactly for capture candidates using their stored steps.
    def opponent_can_capture_target_after_state(my_after, opp_after, target_pos):
        # Determine if opponent has any capture that lands on target_pos in one move.
        # We'll generate opponent legal capture sequences (depth=1 for performance) using actual piece types.
        # We need current positions split into opponent men/kings.
        # To keep it robust, we'll simulate by tracking types based on initial types + promotion during our move.
        # We'll do simplified exact for immediate capture:
        # - Men capture forward only; kings capture both ways.
        # - Promotion during our move may affect opponent's ability; but since we stop at kinging end of move,
        #   promotion happens at the end, so opponent sees it as king. We'll implement that.
        opp_men_set = set(map(tuple, opp_men))
        opp_kings_set = set(map(tuple, opp_kings))

        my_set = set(my_after)  # just occupancy
        opp_men_curr = set(opp_men_set)
        opp_kings_curr = set(opp_kings_set)

        # Update our moved piece type: target might be man->king, but that doesn't matter for opponent capturing rules
        # except regarding whether capturing piece is king. So ignore; only my pieces can be captured either way.
        # So only need opponent's piece types.

        if color == 'b':
            opp_color = 'w'
            opp_fwd = +1
            opp_king_row = 7
        else:
            opp_color = 'b'
            opp_fwd = -1
            opp_king_row = 0

        def inb(r,c): return 0<=r<8 and 0<=c<8 and DARK(r,c)

        # For men, capture forward only
        men_dirs = [(opp_fwd, -1), (opp_fwd, +1)]
        king_dirs = [(-1,-1),(-1,+1),(+1,-1),(+1,+1)]

        # Check each opponent piece for immediate capture landing on target_pos
        tr, tc = target_pos
        # men
        for r,c in opp_men_curr:
            for dr, dc in men_dirs:
                mid = (r+dr, c+dc)
                nxt = (r+2*dr, c+2*dc)
                if in_bounds(*nxt) and DARK(*nxt):
                    if nxt == (tr,tc) and mid in my_set:
                        # landing is empty and mid holds my piece (so capture is legal)
                        if nxt not in my_set and nxt not in opp_men_curr and nxt not in opp_kings_curr:
                            return True
        # kings
        for r,c in opp_kings_curr:
            for dr, dc in king_dirs:
                mid = (r+dr, c+dc)
                nxt = (r+2*dr, c+2*dc)
                if in_bounds(*nxt) and DARK(*nxt):
                    if nxt == (tr,tc) and mid in my_set:
                        if nxt not in my_set and nxt not in opp_men_curr and nxt not in opp_kings_curr:
                            return True
        return False

    # If captures exist, choose best according to multi-capture length, safety, and promotion.
    if all_moves_capture:
        # Build a scoring function
        def score_capture(mv):
            captured = mv["captured"]
            to = mv["to"]
            from_pos = mv["from"]
            final_r, _ = to

            # Promotion preference
            promote = 1 if final_r == king_row else 0

            # Safety: would opponent be able to capture us immediately landing on our landing square?
            # For occupancy after capture, we need to remove captured pieces.
            # We'll reconstruct from steps: start from current sets.
            my_after = set(my_all)
            opp_after = set(opp_pieces)

            # Move our piece along the multi-jump sequence
            # Remove from start, add to end
            my_after.remove(from_pos)
            my_after.add(to)
            # Remove captured pieces by step
            for (s, e) in mv["steps"]:
                sr, sc = s
                er, ec = e
                mid = ((sr+er)//2, (sc+ec)//2)
                if mid in opp_after:
                    opp_after.remove(mid)

            # Check vulnerability (opponent can capture the landing square)
            vulnerable = opponent_can_capture_target_after_state(my_after, opp_after, to)
            safety_score = 0 if vulnerable else 1

            # Slight center preference
            center = 3.5
            center_bonus = - (abs(to[1] - center) * 0.01)

            # Tie-breaking random noise
            return (captured, safety_score, promote, center_bonus)

        # Sort by tuple score descending
        best = max(all_moves_capture, key=score_capture)

        return (best["from"], best["to"])

    # Otherwise, choose quiet move.
    # Generate all legal single-step moves (no captures).
    quiet_moves = []

    def gen_quiet_from(pos, is_king):
        r,c = pos
        dirs = king_dirs() if is_king else man_dirs()
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if in_bounds(nr,nc) and DARK(nr,nc):
                if (nr,nc) not in occ_my and (nr,nc) not in occ_opp:
                    yield (pos, (nr,nc))

    for pos, is_king in my_pieces.items():
        for frm, to in gen_quiet_from(pos, bool(is_king)):
            quiet_moves.append((frm, to))

    # Heuristic safety for quiet: avoid moves where opponent can capture that destination immediately.
    def score_quiet(frm, to):
        tr, tc = to
        # Advancement
        advance = (tr if color == 'w' else (7 - tr))  # larger is better toward king
        promote = 1 if tr == king_row else 0

        # Simulate single-step occupancy
        my_after = set(my_all)
        my_after.remove(frm)
        my_after.add(to)
        opp_after = set(occ_opp)
        vulnerable = opponent_can_capture_target_after_state(my_after, opp_after, to)
        safety = 0 if vulnerable else 1

        center = 3.5
        center_bonus = -abs(tc - center) * 0.01
        return (safety, promote, advance, center_bonus, random.random()*1e-6)

    best = max(quiet_moves, key=lambda m: score_quiet(m[0], m[1])) if quiet_moves else None

    # Fallback: if something went wrong, return a random legal move from quiet generation.
    if best is None:
        # try any move that fits board
        for pos, is_king in my_pieces.items():
            for frm, to in gen_quiet_from(pos, bool(is_king)):
                return (frm, to)
        # No legal moves: return first piece staying put (should not happen in valid games)
        any_piece = next(iter(my_all))
        return (any_piece, any_piece)

    return best
