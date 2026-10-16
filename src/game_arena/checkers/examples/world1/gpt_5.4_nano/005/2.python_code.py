
from functools import lru_cache

def policy(my_men, my_kings, opp_men, opp_kings, color):
    my_men = tuple(my_men)
    my_kings = tuple(my_kings)
    opp_men = tuple(opp_men)
    opp_kings = tuple(opp_kings)

    # Board helpers
    def is_dark(r, c):
        return (r + c) % 2 == 1

    def in_bounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8 and is_dark(r, c)

    my_set = set(my_men) | set(my_kings)
    opp_set = set(opp_men) | set(opp_kings)

    # Movement directions
    # b moves down (decreasing row). w moves up (increasing row).
    if color == 'b':
        forward = -1
        opp_forward = +1
    else:
        forward = +1
        opp_forward = -1

    # Determine if a move should be king-legal
    def is_king_at(pos):
        return pos in set(my_kings)

    def king_positions_set():
        return set(my_kings)

    def occupant(pos):
        if pos in my_set:
            return 'me'
        if pos in opp_set:
            return 'opp'
        return None

    # Simple function to list basic non-capture moves
    def gen_simple_moves():
        moves = []
        my_kset = set(my_kings)
        for r, c in my_set:
            is_king = (r, c) in my_kset
            # directions
            dirs = []
            if is_king:
                dirs = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
            else:
                dirs = [(forward, -1), (forward, +1)]
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and (nr, nc) not in my_set and (nr, nc) not in opp_set:
                    moves.append(((r, c), (nr, nc)))
        return moves

    # Generate all capture sequences for a given piece.
    # Returns list of sequences, each as (start, path_end, captured_positions_set)
    # Here we only need first move out of start->next; policy returns a single step for the turn.
    def gen_capture_sequences_for_piece(start_pos, piece_is_king):
        sr, sc = start_pos
        sequences = []

        @lru_cache(maxsize=None)
        def dfs(r, c, my_remaining_mask, king_flag, captured_mask):
            # Not used with masks; kept for future. We'll implement non-memoized due to small state.
            return

        # We'll implement iterative recursion with sets (small branching).
        def rec(pos, local_my_set, local_opp_set, last_captured, path, captured_list):
            found = False
            r, c = pos
            # capture directions allowed
            if piece_is_king:
                dirs = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
            else:
                dirs = [(forward, -1), (forward, +1)]
                # Non-king men cannot capture backwards in standard checkers.
                # If your variant allows backward captures for men, you can remove this restriction.
                # The provided engine likely follows standard rules, so we keep it.
            for dr, dc in dirs:
                mr, mc = r + dr, c + dc
                tr, tc = r + 2 * dr, c + 2 * dc
                if in_bounds(mr, mc) and in_bounds(tr, tc):
                    mid = (mr, mc)
                    landing = (tr, tc)
                    if mid in local_opp_set and landing not in local_my_set and landing not in local_opp_set:
                        found = True
                        # simulate capture
                        new_local_my_set = set(local_my_set)
                        new_local_opp_set = set(local_opp_set)
                        new_local_opp_set.remove(mid)
                        new_local_my_set.remove((r, c))
                        new_local_my_set.add(landing)
                        captured_list.append(mid)
                        path.append(landing)
                        # Kinging during jump: in most rules, kinging applies after move completes,
                        # not mid-jump. We'll assume standard: don't change capture directions mid-jump.
                        rec(landing, new_local_my_set, new_local_opp_set, mid, path, captured_list)
                        path.pop()
                        captured_list.pop()

            if not found:
                # End of sequence
                if len(captured_list) > 0:
                    sequences.append((start_pos, tuple(path[-1]) if path else start_pos, tuple(captured_list)))
                return

        # local sets
        local_my_set = set(my_set)
        local_opp_set = set(opp_set)
        # remove start from my local and place as it moves, handled in rec
        path = [start_pos]
        captured_list = []
        rec(start_pos, local_my_set, local_opp_set, None, path, captured_list)

        # sequences are for all possible endpoints; need unique endpoints + captured list.
        # It's fine; we score based on captures count.
        return sequences

    def gen_all_capture_moves():
        all_sequences = []
        my_kset = set(my_kings)
        for pos in my_set:
            piece_is_king = pos in my_kset
            seqs = gen_capture_sequences_for_piece(pos, piece_is_king)
            for start, end, captured in seqs:
                # determine the first step (from start to next square)
                # We need the immediate landing after first capture (path length >=2).
                # Our sequence generator only stores endpoint and captured list, not the intermediate path.
                # So re-generate to obtain first step deterministically:
                # We'll do a targeted DFS that returns first step along with all completions.
                pass
        return []

    # Because we need a legal single move, we must know first hop for multi-jump sequences.
    # We'll generate capture moves that return the immediate to-square and full capture set by DFS.
    def gen_capture_hops():
        hops = []  # entries: (from, to, captured_set, captures_count)
        my_kset = set(my_kings)

        # Recursive generation that tracks first landing square.
        def rec(first_to, current_pos, local_my_set, local_opp_set, captured_list, start_pos, piece_is_king):
            r, c = current_pos
            found = False
            if piece_is_king:
                dirs = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
            else:
                dirs = [(forward, -1), (forward, +1)]

            for dr, dc in dirs:
                mr, mc = r + dr, c + dc
                tr, tc = r + 2 * dr, c + 2 * dc
                if in_bounds(mr, mc) and in_bounds(tr, tc):
                    mid = (mr, mc)
                    landing = (tr, tc)
                    if mid in local_opp_set and landing not in local_my_set and landing not in local_opp_set:
                        found = True
                        new_my = set(local_my_set)
                        new_opp = set(local_opp_set)
                        new_opp.remove(mid)
                        new_my.remove((r, c))
                        new_my.add(landing)
                        captured_list.append(mid)
                        rec(first_to, landing, new_my, new_opp, captured_list, start_pos, piece_is_king)
                        captured_list.pop()

            if not found and len(captured_list) > 0:
                hops.append((start_pos, first_to, frozenset(captured_list), len(captured_list)))

        for pos in my_set:
            piece_is_king = pos in my_kset
            sr, sc = pos
            if piece_is_king:
                dirs = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
            else:
                dirs = [(forward, -1), (forward, +1)]

            local_my = set(my_set)
            local_opp = set(opp_set)
            # try all first captures
            for dr, dc in dirs:
                mr, mc = sr + dr, sc + dc
                tr, tc = sr + 2 * dr, sc + 2 * dc
                if in_bounds(mr, mc) and in_bounds(tr, tc):
                    mid = (mr, mc)
                    landing = (tr, tc)
                    if mid in local_opp and landing not in local_my and landing not in local_opp:
                        # simulate first capture
                        new_my = set(local_my)
                        new_opp = set(local_opp)
                        new_opp.remove(mid)
                        new_my.remove((sr, sc))
                        new_my.add(landing)
                        captured_list = [mid]
                        rec(landing, landing, new_my, new_opp, captured_list, pos, piece_is_king)

        # De-duplicate by (from,to,captured_set)
        uniq = {}
        for f, t, capset, n in hops:
            uniq[(f, t, capset)] = n
        return [(f, t, capset, uniq[(f, t, capset)]) for (f, t, capset) in uniq.keys()]

    capture_hops = gen_capture_hops()
    if capture_hops:
        # Heuristic scoring
        def score_move(frm, to, capset, capcount):
            s = 0
            # prefer more captures strongly
            s += 100 * capcount
            # prefer capturing kings
            s += 30 * sum(1 for p in capset if p in set(opp_kings))
            # kinging preference (man reaching back rank after the first hop is not guaranteed mid-jump,
            # but in many engines it's applied at end; we still add a small bonus for moving toward king row)
            back_rank = 0 if color == 'b' else 7
            if to[0] == back_rank:
                s += 18
            # positional: centralization
            s += 3 * (3.5 - abs(to[1] - 3.5))
            # small penalty if the moved piece lands where it can be captured immediately
            # approximate by checking opponent captures after this single hop (ignoring that multi-jump might continue)
            # We'll simulate just the first hop; still a good tactical deterrent.
            my_after = set(my_set)
            opp_after = set(opp_set)

            my_after.remove(frm)
            my_after.add(to)
            for p in capset:
                opp_after.discard(p)

            # determine resulting piece king flag: if a man reaches back rank, assume becomes king (for the sake of safety check)
            is_king_after = (frm in set(my_kings)) or (to[0] == back_rank)

            # generate opponent capture availability against the landing piece
            # If opponent can capture landing piece immediately, penalize.
            opp_color_forward = opp_forward  # opponent men forward dir relative to current color
            dirs_opp = []
            if is_king_after:
                dirs_opp = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
            else:
                # if it's a man, it's captureable by opponent in their forward (men capture like move in standard)
                # opponent captures in their forward directions (relative to their movement)
                dirs_opp = [(opp_color_forward, -1), (opp_color_forward, +1)]

            # But we need actual opponent piece types to capture it.
            # We'll scan opponent pieces and see if any can capture the landing square in one move.
            # This is still cheap.
            opp_kset = set(opp_kings)
            can_capture_back = False
            for orr, oc in opp_after:
                if (orr, oc) in opp_kset:
                    odirs = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
                else:
                    odirs = [(opp_color_forward, -1), (opp_color_forward, +1)]
                for dr, dc in odirs:
                    mr, mc = orr + dr, oc + dc
                    tr, tc = orr + 2 * dr, oc + 2 * dc
                    if in_bounds(mr, mc) and in_bounds(tr, tc):
                        if (tr, tc) == to and (mr, mc) == ((to[0] + ( -dr)//2) if False else mr, mc):
                            # above line is nonsensical; skip. We'll just check if mid square contains our piece
                            pass
            # Replace with correct logic:
            can_capture_back = False
            landing = to
            for opp_pos in set(opp_set):
                if opp_pos not in opp_after:
                    continue
                orr, oc = opp_pos
                if opp_pos in set(opp_kings):
                    odirs = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
                else:
                    odirs = [(opp_forward, -1), (opp_forward, +1)]
                for dr, dc in odirs:
                    mr, mc = orr + dr, oc + dc
                    tr, tc = orr + 2 * dr, oc + 2 * dc
                    if in_bounds(tr, tc) and (tr, tc) == landing and (mr, mc) == ((landing[0] - dr), (landing[1] - dc)):
                        # mid square relative to landing
                        if (landing[0] - dr, landing[1] - dc) == (mr, mc):
                            # and landing is empty except our piece, so capture would land there
                            can_capture_back = True
                            break
                if can_capture_back:
                    break
            if can_capture_back:
                s -= 55
            return s

        # One-ply lookahead: among top few, also consider opponent best capture count response (approx).
        def opp_best_capture_count(my_after, opp_after, current_color):
            # Only count immediate captures available to opponent.
            # Generate opponent capture hops similarly but simpler: check if any opponent piece can capture any of my pieces.
            # We'll just compute maximum capture count by checking available single captures (not multi).
            # For speed and because scoring already favors captures.
            maxc = 0
            my_pos = set(my_after)
            opp_pos = set(opp_after)
            opp_kset = set(opp_kings)
            dirs_for_opp_men = [(opp_forward, -1), (opp_forward, +1)]
            for pr, pc in opp_pos:
                if (pr, pc) in opp_kset:
                    dirs = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
                else:
                    dirs = dirs_for_opp_men
                for dr, dc in dirs:
                    mr, mc = pr + dr, pc + dc
                    tr, tc = pr + 2*dr, pc + 2*dc
                    if in_bounds(tr, tc):
                        if (mr, mc) in my_pos and (tr, tc) not in my_pos and (tr, tc) not in opp_pos:
                            maxc = max(maxc, 1)
            return maxc

        scored = []
        for frm, to, capset, capcount in capture_hops:
            scored.append((score_move(frm, to, capset, capcount), frm, to, capset, capcount))

        scored.sort(reverse=True, key=lambda x: x[0])
        best = scored[0]
        # light lookahead on top 5
        top = scored[:5]
        best_choice = (best[1], best[2])
        best_eval = -10**9
        for _, frm, to, capset, capcount in top:
            my_after = set(my_set)
            opp_after = set(opp_set)
            my_after.remove(frm)
            my_after.add(to)
            for p in capset:
                opp_after.discard(p)
            opp_c = opp_best_capture_count(my_after, opp_after, color)
            evalv = _ - 35 * opp_c
            if evalv > best_eval:
                best_eval = evalv
                best_choice = (frm, to)
        return (best_choice[0], best_choice[1])

    # If no captures, select best simple move
    simple = gen_simple_moves()
    if not simple:
        # no legal moves (shouldn't happen in arena), return any legal dummy (pick first)
        # But must be legal: fallback to stay unavailable; instead choose first piece to adjacent if possible.
        # We'll just return first move if exists; otherwise return (0,0)->(0,0) (may be illegal).
        return ((0, 0), (0, 0))

    my_kset = set(my_kings)
    back_rank = 0 if color == 'b' else 7

    def score_simple(frm, to):
        s = 0
        r, c = to
        # prefer moving toward kinging
        s += (r if color == 'w' else 7 - r) * 2.5
        # center preference
        s += 3 * (3.5 - abs(c - 3.5))
        # kinging
        if r == back_rank:
            s += 25
        # avoid stepping into immediate capture
        # simulate quickly
        my_after = set(my_set)
        opp_after = set(opp_set)
        my_after.remove(frm)
        my_after.add(to)

        can_be_captured = False
        opp_kset2 = set(opp_kings)
        for pr, pc in opp_after:
            if (pr, pc) in opp_kset2:
                odirs = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
            else:
                odirs = [(opp_forward, -1), (opp_forward, +1)]
            for dr, dc in odirs:
                mr, mc = pr + dr, pc + dc
                tr, tc = pr + 2*dr, pc + 2*dc
                if in_bounds(tr, tc) and (tr, tc) == to:
                    if (mr, mc) in my_after:
                        can_be_captured = True
                        break
            if can_be_captured:
                break
        if can_be_captured:
            s -= 30
        return s

    best = max(simple, key=lambda mv: score_simple(mv[0], mv[1]))
    return best
