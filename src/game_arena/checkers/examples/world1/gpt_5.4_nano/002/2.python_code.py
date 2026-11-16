
from functools import lru_cache

def policy(my_men, my_kings, opp_men, opp_kings, color):
    my_men = tuple(my_men)
    my_kings = tuple(my_kings)
    opp_men = tuple(opp_men)
    opp_kings = tuple(opp_kings)

    my_pieces = set(my_men) | set(my_kings)
    opp_pieces = set(opp_men) | set(opp_kings)

    def is_dark(r, c):
        return (r + c) % 2 == 1

    def inb(r, c):
        return 0 <= r < 8 and 0 <= c < 8 and is_dark(r, c)

    def piece_at(pos):
        # returns: 'my_man','my_king','opp_man','opp_king' or None
        if pos in my_kings:
            return 'my_king'
        if pos in my_men:
            return 'my_man'
        if pos in opp_kings:
            return 'opp_king'
        if pos in opp_men:
            return 'opp_man'
        return None

    # Movement direction for men
    # black moves downwards (to lower rows), white upwards (to higher rows)
    dir_my = -1 if color == 'b' else 1

    # For kings, they can move/capture in both diagonal directions
    king_dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]

    # Man movement dirs
    man_dirs = [(dir_my, 1), (dir_my, -1)]

    occupied = my_pieces | opp_pieces

    def get_simple_moves(pos):
        # non-capturing moves: for men one step forward, for kings one step any diagonal
        r, c = pos
        moves = []
        if pos in my_kings:
            dirs = king_dirs
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if inb(nr, nc) and (nr, nc) not in occupied:
                    moves.append(((r, c), (nr, nc)))
        else:
            for dr, dc in man_dirs:
                nr, nc = r + dr, c + dc
                if inb(nr, nc) and (nr, nc) not in occupied:
                    moves.append(((r, c), (nr, nc)))
        return moves

    def get_capture_sequences_from(start_pos, start_state):
        """
        start_state: tuple(frozenset(my_kings), frozenset(my_men), frozenset(opp_kings), frozenset(opp_men))
        We'll compute capture sequences for the piece at start_pos.
        Returns list of sequences, each sequence as (final_to_pos, captured_positions_set)
        Note: We only consider single piece moving multiple jumps (standard checkers rules).
        For kinging: a man that reaches the back rank during a capture sequence becomes a king
        and can continue capturing as a king in subsequent jumps.
        """
        my_kings_s, my_men_s, opp_kings_s, opp_men_s = start_state
        # Determine piece type
        is_king = start_pos in my_kings_s
        is_man = start_pos in my_men_s

        if not (is_king or is_man):
            return []

        # Determine current dirs based on kinging status during sequence
        def piece_dirs(at_pos, currently_king):
            if currently_king:
                return king_dirs
            else:
                return man_dirs

        # Board occupancy in this hypothetical state
        my_all_s = set(my_kings_s) | set(my_men_s)
        opp_all_s = set(opp_kings_s) | set(opp_men_s)

        def is_back_rank(for_color, r):
            return (for_color == 'b' and r == 0) or (for_color == 'w' and r == 7)

        best = []

        @lru_cache(None)
        def dfs(cur_r, cur_c, kinged):
            cur_pos = (cur_r, cur_c)
            # build local occupancy from state but with removed/added as per recursion:
            # We'll pass captured set via parameters indirectly by storing remaining opp? Not feasible with caching.
            # Instead, do recursion without caching on board sets; caching will be limited.
            return None

        # We'll implement DFS without heavy caching, but depth is limited by board size.
        # To avoid copying sets too much, we'll represent captured positions in a set and update.
        results = []

        # mutable tracking
        def rec(cur_pos, currently_king, captured_list, my_kings_mut, my_men_mut, opp_kings_mut, opp_men_mut):
            r, c = cur_pos
            dirs = piece_dirs(cur_pos, currently_king)

            any_capture = False
            # For each diagonal adjacent enemy, check jump landing square.
            for dr, dc in dirs:
                mid = (r + dr, c + dc)
                land = (r + 2 * dr, c + 2 * dc)
                if not inb(land[0], land[1]):
                    continue
                if mid in (opp_kings_mut | opp_men_mut) and land not in (my_kings_mut | my_men_mut | opp_kings_mut | opp_men_mut):
                    any_capture = True
                    # simulate capture
                    # remove captured enemy from appropriate set
                    new_opp_kings = set(opp_kings_mut)
                    new_opp_men = set(opp_men_mut)
                    if mid in new_opp_kings:
                        new_opp_kings.remove(mid)
                    else:
                        new_opp_men.remove(mid)

                    # move our piece: update my sets
                    new_my_kings = set(my_kings_mut)
                    new_my_men = set(my_men_mut)

                    if currently_king:
                        new_my_kings.remove((r, c))
                    else:
                        new_my_men.remove((r, c))

                    # kinging check for men only when they move to back rank
                    new_currently_king = currently_king
                    if not currently_king and is_back_rank(color, land[0]):
                        new_currently_king = True

                    if new_currently_king:
                        new_my_kings.add(land)
                    else:
                        new_my_men.add(land)

                    rec(land, new_currently_king, captured_list + [mid],
                        frozenset(new_my_kings), frozenset(new_my_men),
                        frozenset(new_opp_kings), frozenset(new_opp_men))

            if not any_capture:
                # end of sequence
                results.append((cur_pos, set(captured_list)))

        # initialize mutables
        rec(start_pos, is_king, [], frozenset(my_kings_s), frozenset(my_men_s),
            frozenset(opp_kings_s), frozenset(opp_men_s))

        return results

    def all_captures():
        # For each own piece, generate all capture sequences. Return moves as single-step-of-first-jump.
        # But if multi-jump exists, the legal move is the first jump in that sequence.
        start_state = (frozenset(my_kings), frozenset(my_men), frozenset(opp_kings), frozenset(opp_men))
        sequences = []
        for pos in my_pieces:
            if piece_at(pos) and (pos in my_kings or pos in my_men):
                seqs = get_capture_sequences_from(pos, start_state)
                # Convert each sequence into a candidate based on first jump landing square
                for final_pos, captured in seqs:
                    # if no capture happened, skip
                    if not captured:
                        continue
                    # Determine the first landing square from start_pos to final_pos isn't enough;
                    # we need actual first jump. Reconstruct by simulating: choose any capture neighbor pair?
                    # We'll do another small search to get first-jump possibilities that lead to max captures.
                    # To keep it correct, compute all first jumps and their resulting max continuation captures.
                    # Approach: enumerate all possible first captures, then compute max continuation length from there.
                    r0, c0 = pos
                    is_start_king = pos in my_kings
                    def dirs_for(kingflag):
                        return king_dirs if kingflag else man_dirs
                    first_dir_set = dirs_for(is_start_king)
                    for dr, dc in first_dir_set:
                        mid = (r0 + dr, c0 + dc)
                        land = (r0 + 2 * dr, c0 + 2 * dc)
                        if not inb(land[0], land[1]):
                            continue
                        if mid in opp_pieces and land not in my_pieces and land not in opp_pieces:
                            # Check if after this first jump, we can reach a sequence ending with same captured set and final_pos
                            # We'll verify by generating sequences starting from land with updated board state.
                            # Build updated state after first capture.
                            new_my_k = set(my_kings)
                            new_my_m = set(my_men)
                            new_opp_k = set(opp_kings)
                            new_opp_m = set(opp_men)
                            # remove start
                            if is_start_king:
                                new_my_k.remove(pos)
                            else:
                                new_my_m.remove(pos)
                            # remove captured
                            if mid in new_opp_k:
                                new_opp_k.remove(mid)
                            else:
                                new_opp_m.remove(mid)
                            # kinging after first landing
                            current_king = is_start_king
                            if not is_start_king and ((color == 'b' and land[0] == 0) or (color == 'w' and land[0] == 7)):
                                current_king = True
                            if current_king:
                                new_my_k.add(land)
                            else:
                                new_my_m.add(land)

                            # Now generate all continuations from land in this updated state, and see if one matches final/captured.
                            cont_state = (frozenset(new_my_k), frozenset(new_my_m), frozenset(new_opp_k), frozenset(new_opp_m))
                            cont_seqs = get_capture_sequences_from(land, cont_state)
                            for cont_final, cont_captured in cont_seqs:
                                total_captured = set([mid]) | cont_captured
                                if cont_final == final_pos and total_captured == captured:
                                    sequences.append((((r0, c0), (land[0], land[1])), final_pos, captured))
                                    break
            # Note: even if multiple sequences match same first jump, we keep them as separate entries.
        # Deduplicate by first move + captured set size
        dedup = {}
        for mv, final_pos, captured in sequences:
            key = (mv[0], mv[1], len(captured), final_pos, tuple(sorted(captured))[:1] if captured else 0)
            # not great; but enough. We'll just keep maximum by captured size later.
            dedup[mv] = (mv, final_pos, captured)
        return list(dedup.values())

    captures = all_captures()
    if captures:
        # choose best based on max captures, promotion preference, and safety heuristic
        def would_promote(to_pos, is_king_start, move_piece_is_king, from_pos):
            # promotion happens only for men
            if from_pos in my_kings:
                return False
            return (color == 'b' and to_pos[0] == 0) or (color == 'w' and to_pos[0] == 7)

        # Build quick occupancy for recapture heuristic after first jump
        # We'll approximate safety: after move landing, check if opponent has a capture of that square next turn.
        def opponent_can_capture_landing(after_from, after_to):
            # simulate only first jump result for heuristic
            from_pos, to_pos = after_from, after_to
            # Determine which enemy was captured by the first move
            fr, fc = from_pos
            tr, tc = to_pos
            dr = (tr - fr) // 2
            dc = (tc - fc) // 2
            mid = (fr + dr, fc + dc)
            if mid not in opp_pieces:
                return False
            # simulate board after first capture
            sim_my_k = set(my_kings)
            sim_my_m = set(my_men)
            sim_opp_k = set(opp_kings)
            sim_opp_m = set(opp_men)

            if from_pos in sim_my_k:
                sim_my_k.remove(from_pos)
            else:
                sim_my_m.remove(from_pos)
            if mid in sim_opp_k:
                sim_opp_k.remove(mid)
            else:
                sim_opp_m.remove(mid)

            # kinging after first landing
            if from_pos in my_kings or ((color == 'b' and tr == 0) or (color == 'w' and tr == 7)):
                sim_my_k.add(to_pos)
            else:
                sim_my_m.add(to_pos)

            # now see if opponent can capture that piece at to_pos
            my_all = sim_my_k | sim_my_m
            opp_all = sim_opp_k | sim_opp_m

            opp_dir = 1 if color == 'b' else -1  # opponent moves opposite
            for opp_pos in opp_all:
                opp_is_king = opp_pos in sim_opp_k
                dirs = king_dirs if opp_is_king else [(opp_dir, 1), (opp_dir, -1)]
                r, c = opp_pos
                for rdr, rdc in dirs:
                    mid2 = (r + rdr, c + rdc)
                    land2 = (r + 2 * rdr, c + 2 * rdc)
                    if not inb(land2[0], land2[1]):
                        continue
                    if mid2 == to_pos and land2 not in my_all and land2 not in opp_all:
                        return True
            return False

        best = None
        best_score = None
        for mv, final_pos, captured in captures:
            (from_pos, to_pos) = mv
            k_start = from_pos in my_kings
            promo = 1 if ((not k_start) and ((color == 'b' and to_pos[0] == 0) or (color == 'w' and to_pos[0] == 7))) else 0
            numcap = len(captured)

            # safety: penalize if opponent can capture the landing immediately
            unsafe = 1 if opponent_can_capture_landing(from_pos, to_pos) else 0

            # advancement bonus
            adv = to_pos[0] * (1 if color == 'w' else -1)

            # Prefer more captures heavily
            score = (numcap * 1000) + (promo * 50) + (-unsafe * 80) + adv
            if best is None or score > best_score:
                best = mv
                best_score = score
        return best

    # No captures: choose a safe forward move (or king move) with best advancement
    moves = []
    for pos in my_pieces:
        moves.extend(get_simple_moves(pos))

    if not moves:
        # Should not happen in legal game, but return a dummy (must be legal; fallback to first king move if exists)
        # We'll just return the first available simple move from any piece (already checked).
        return ((0, 0), (0, 0))

    def move_score(mv):
        (fr, fc), (tr, tc) = mv
        is_king = fr in my_kings
        # prefer advancement
        adv = tr * (1 if color == 'w' else -1)
        # avoid moving into squares where opponent can capture immediately (approx)
        # simulate landing only
        # determine captured? none.
        sim_my_k = set(my_kings)
        sim_my_m = set(my_men)
        sim_opp_k = set(opp_kings)
        sim_opp_m = set(opp_men)
        if fr in sim_my_k:
            sim_my_k.remove(fr)
            sim_my_k.add((tr, tc))
        else:
            sim_my_m.remove(fr)
            # kinging
            if (color == 'b' and tr == 0) or (color == 'w' and tr == 7):
                sim_my_k.add((tr, tc))
            else:
                sim_my_m.add((tr, tc))
        my_all = sim_my_k | sim_my_m
        opp_all = sim_opp_k | sim_opp_m
        opp_dir = 1 if color == 'b' else -1
        # check if opponent has immediate capture to this square
        for opp_pos in opp_all:
            opp_is_king = opp_pos in sim_opp_k
            dirs = king_dirs if opp_is_king else [(opp_dir, 1), (opp_dir, -1)]
            r, c = opp_pos
            for dr, dc in dirs:
                mid2 = (r + dr, c + dc)
                land2 = (r + 2 * dr, c + 2 * dc)
                if mid2 == (tr, tc) and land2 not in my_all and land2 not in opp_all and inb(land2[0], land2[1]):
                    return adv - 5000  # big penalty
        return adv

    best_move = max(moves, key=move_score)
    return best_move
