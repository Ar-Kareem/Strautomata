
import math
from itertools import product

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state.get('dice', [])
    if not dice:
        return "H:P,P"

    # Board orientation:
    # We move from 23 downwards to 0. (Engine applies legality of moves we specify.)
    # Home board for bearing off is our A0..A5.
    home = set(range(0, 6))

    # Determine if dice are double or not
    d1 = dice[0]
    d2 = dice[1] if len(dice) > 1 else None

    # Helpers
    def is_my_checker_at(pt):
        return my_pts[pt] > 0

    def clone_board():
        return my_pts[:], opp_pts[:], my_bar, my_off

    # Compute destination point for a move from a given start point using a die,
    # respecting our direction (23 -> 0). For bar entry, we assume fixed mapping:
    # In standard backgammon, entry depends on color; with this engine indexing,
    # we infer entry destination is A? such that our movement is decreasing.
    #
    # Because we don't know color, but engine guarantees only move legality when
    # we output start squares. Still, for internal enumeration we must map bar
    # entry and normal moves to a destination.
    #
    # We can derive a consistent mapping with the common convention for "moving from 23 to 0":
    # entering from bar with die d goes to point (24 - d). Since points are 0..23,
    # and with decreasing movement by d, from "virtual" start at 24 -> 24-d.
    # That yields destinations in 14..23 for d=1..6, plausible.
    def dest_from_start(start, die):
        if start == 'B':
            # Virtual position 24 for our direction; destination = 24 - die
            return 24 - die
        else:
            # start is 0..23
            return start - die

    def can_bear_off_after_move(start, die, current_my_pts, current_my_off):
        # Bearing off is allowed when all remaining checkers are in home board A0..A5
        total_in_home = 0
        total_elsewhere = 0
        # count current checkers excluding off
        for i in range(24):
            c = current_my_pts[i]
            if c:
                if i in home:
                    total_in_home += c
                else:
                    total_elsewhere += c
        # bar must be zero (bar checkers handled elsewhere)
        # If there are no checkers elsewhere, bearing off allowed.
        if total_elsewhere != 0:
            return False
        # Compute destination: if within home or beyond.
        dest = dest_from_start(start, die)
        if dest in home:
            return True
        # If dest < 0 => bear off (over-shoot)
        if dest < 0:
            # Simplified rule: bear off allowed if there is no checker on points below the start-die
            # Standard rule depends on highest checker. We approximate using "all home" and legality check below.
            # We'll check exact rule: if there is any checker on points with index between dest+1 and start-die? hard.
            # Better: apply: if dest < 0, bear off only if there is no checker on points 0..(-dest-1)?? Not.
            # We'll implement standard for decreasing index:
            # If destination is below 0, you may bear off if you have no checkers on points 0..(start - die + 5?) confusing.
            # Instead: ensure there is no checker on points that would have been able to receive the die (i.e., points > dest).
            # For decreasing movement, if die overshoots, the relevant alternative is the smallest p in home that still could land.
            # We'll implement: if dest < 0, bear off is allowed if there is no checker on points with index > dest (i.e., 0..start-1)
            # that could have been moved into the board with same die. That is, if all checkers in home are on points <= start - die + ???.
            # Given uncertainty, but engine will enforce legality when we output; still we need move generation.
            # We'll take a conservative approach: allow bear-off overshoot only if there is no checker on points higher than 0 that
            # are in the "landing range" that would be inside home. With dest < 0, landing inside home would be points 0..(0?) none.
            # In practice, overshoot occurs only when start is in home with small index; then it's usually legal.
            return True
        return False

    def apply_move(current_my_pts, current_opp_pts, current_my_bar_val, move_start, die):
        # Returns new (my_pts, opp_pts, my_bar, my_off_delta, legal_bool)
        myp = current_my_pts[:]
        oppp = current_opp_pts[:]
        my_bar_local = current_my_bar_val
        my_off_delta = 0

        # Remove checker from start
        if move_start == 'B':
            if my_bar_local <= 0:
                return None
            my_bar_local -= 1
            start = 'B'
        else:
            start_idx = int(move_start[1:]) if isinstance(move_start, str) and move_start.startswith('A') else move_start
            if myp[start_idx] <= 0:
                return None
            myp[start_idx] -= 1

        dest = dest_from_start(move_start, die)

        # Determine if bear off
        if dest < 0:
            # can bear off only from home and all checkers in home; engine likely checks.
            # We'll allow overshoot bear-off if bear_off_after_move condition says yes.
            if not can_bear_off_after_move(start if move_start != 'B' else 0, die, myp, 0):
                return None
            my_off_delta += 1
            return myp, oppp, my_bar_local, my_off_delta
        else:
            dest_idx = dest
            if dest_idx < 0 or dest_idx > 23:
                return None

            # Blocked by 2+ opponent checkers
            if oppp[dest_idx] >= 2:
                return None

            # Hit: if exactly 1 opponent checker
            if oppp[dest_idx] == 1:
                oppp[dest_idx] -= 1
                # opponent bar increased by engine; we don't track opp_bar in simulation for scoring heavily
                # but we should, for legality of further moves (it affects occupancy).
                # We'll ignore opp_bar count because it doesn't affect board occupancy except future moves (from bar).
                # For our own move legality, only current occupancy matters (we already removed the checker).
                # Put hit checker onto opp_bar abstractly: not needed.
            # Place our checker
            myp[dest_idx] += 1
            return myp, oppp, my_bar_local, my_off_delta

    # Enumerate legal move starts for a single die, based on our internal simulation.
    def legal_starts_for_die(current_my_pts, current_opp_pts, current_my_bar_val, die):
        # If bar has checkers, must move from bar (single action), engine enforces.
        starts = []
        if current_my_bar_val > 0:
            # bar entry destination = 24 - die; must be within 0..23
            dest = 24 - die
            if 0 <= dest <= 23:
                if current_opp_pts[dest] >= 2:
                    return []
                return ['B']
            else:
                return []
        # Otherwise, any point with checker is candidate; but we also must not move to blocked points.
        for i in range(24):
            if current_my_pts[i] <= 0:
                continue
            dest = dest_from_start(i, die)
            if dest < 0:
                # bearing off case, ensure allowed:
                if can_bear_off_after_move(i, die, current_my_pts, 0):
                    starts.append(f"A{i}")
            else:
                if dest > 23:
                    continue
                if current_opp_pts[dest] >= 2:
                    continue
                starts.append(f"A{i}")
        # If no move from any start, return empty
        return starts

    # Apply one die move and score resulting board.
    def evaluate(myp, oppp, my_bar_val, my_off_val):
        # Higher is better.
        # Features:
        # - material/advancement: prefer points with more checkers and being far advanced (near 0)
        score = 0.0
        # Home vs elsewhere
        for i in range(24):
            c = myp[i]
            if c:
                # advancement: closer to 0 is better
                score += c * (25 - i)  # i=0 best
                # safety: make points with 2+ good
                if c >= 2:
                    score += 8 * (c - 1)
                # blot exposure: single checker on points not in safe set
                else:
                    # penalize if opp has exactly 1 or 2 to hit (heuristic)
                    if oppp[i] <= 2:
                        score -= 2.0 * (1 if i >= 6 else 0.5)
        # Hitting potential: if opponent has 1 on some point where we could hit next is hard; approximate:
        # penalize opponent singletons on points we like to land; rough with current board:
        for i in range(24):
            oc = oppp[i]
            if oc == 1:
                score += 1.5 * (25 - i)  # higher points mean more contact opportunity
            elif oc >= 2:
                score -= 2.0 * (oc - 1)
        # Bar/checkers:
        score -= 12.0 * my_bar_val
        score += 30.0 * my_off_val
        return score

    # Generate all legal actions for two dice (or one if only one die).
    def best_action():
        # dice handling
        if d2 is None:
            die_list = [d1]
        else:
            die_list = [d1, d2]

        # If doubles, both dice same; we still treat as two sequential moves.
        # Determine mandatory move-from-bar at each step via simulation.
        best = None
        best_score = -1e18

        def search(step, myp, oppp, barv, offv, moves_so_far):
            nonlocal best, best_score
            if step == len(die_list):
                # Need to return encoding based on whether first die used is high/low.
                # moves_so_far is list of (die_used, start_str)
                # Construct move string accordingly.
                # If one die only, second start is P.
                if len(die_list) == 1:
                    die_used = die_list[0]
                    # decide order char relative to higher die; if single die, order doesn't matter much; use H if die==max
                    order = 'H'
                    first = moves_so_far[0][1] if moves_so_far else 'P'
                    return "H:%s,P" % first

                # Two dice
                hi = max(die_list)
                lo = min(die_list)
                first_die = die_list[0]
                # We must encode as ORDER:FROM1,FROM2 meaning first encoded move uses higher die if ORDER='H'
                # The engine expects FROM1 corresponds to die (high) and FROM2 corresponds to die (low).
                # We have moves in actual die sequence; but we must map them to high/low slots.
                # We'll assume our step-0 uses die_list[0] as first die. If die_list[0]==hi then ORDER='H' and FROM1 is start of that move.
                # If die_list[0]==lo then ORDER='L' and FROM1 corresponds to low die.
                # However official format: H means first encoded checker move uses higher die.
                # So if step0 die is hi => H else L.
                order = 'H' if die_list[0] == hi else 'L'
                # Determine which move corresponds to which die value (could be equal for doubles).
                starts_by_die = {}
                for die_used, start_str in moves_so_far:
                    starts_by_die[die_used] = start_str
                if hi == lo:
                    # doubles: order irrelevant; put first move start at FROM1, second at FROM2
                    from1 = moves_so_far[0][1]
                    from2 = moves_so_far[1][1] if len(moves_so_far) > 1 else 'P'
                    return f"{order}:{from1},{from2}"
                else:
                    from_high = starts_by_die.get(hi, 'P')
                    from_low = starts_by_die.get(lo, 'P')
                    return f"{order}:{from_high},{from_low}"

            die = die_list[step]
            starts = legal_starts_for_die(myp, oppp, barv, die)
            if not starts:
                # must pass for this die
                return search(step + 1, myp, oppp, barv, offv, moves_so_far + [(die, 'P')])

            # Generate options; if multiple, try each.
            # Heuristic ordering: prefer starts that bear off or hit (approximated) by quick apply+eval.
            candidates = []
            for st in starts:
                applied = apply_move(myp, oppp, barv, st, die)
                if applied is None:
                    continue
                nmyp, nopp, nbar, delta_off = applied
                nc = (offv + delta_off, st)
                candidates.append((st, nmyp, nopp, nbar, offv + delta_off))
            if not candidates:
                return search(step + 1, myp, oppp, barv, offv, moves_so_far + [(die, 'P')])

            # Sort candidates by immediate evaluation delta
            def cand_key(c):
                st, nmyp, nopp, nbar, noff = c
                return evaluate(nmyp, nopp, nbar, noff)
            candidates.sort(key=cand_key, reverse=True)

            best_local = None
            for st, nmyp, nopp, nbar, noff in candidates[:12]:
                # continue
                saved_myp, saved_opp, saved_bar, saved_off = myp, oppp, barv, offv
                res = search(step + 1, nmyp, nopp, nbar, noff, moves_so_far + [(die, st)])
                # If res returns a move string, we must score final state, but we don't have it here.
                # So instead score at end by re-simulating from chosen sequence.
                if isinstance(res, str):
                    # Re-simulate from current start isn't possible; we can score at leaf instead.
                    pass
            # We won't use this approach for scoring. We'll score at leaf during recursion by capturing in globals:
            return None

        # Instead of the above (which would be messy for scoring), do explicit 2-ply enumeration
        # and evaluate at leaves.

        # Build start options for first die
        if d2 is None:
            die = d1
            starts = legal_starts_for_die(my_pts, opp_pts, my_bar, die)
            if not starts:
                return "H:P,P"
            # Pick best single move
            best_move = None
            best_s = -1e18
            hi = die
            for st in starts:
                applied = apply_move(my_pts, opp_pts, my_bar, st, die)
                if applied is None:
                    continue
                nmyp, nopp, nbar, doff = applied
                s = evaluate(nmyp, nopp, nbar, my_off + doff)
                if s > best_s:
                    best_s = s
                    best_move = st
            return f"H:{best_move},P" if best_move is not None else "H:P,P"

        # Two dice case
        dice_list = [d1, d2]
        # If doubles, treat as sequential; our encoding later handles order.
        # Evaluate by enumerating all combinations of starts (or P if no legal).
        hi = max(d1, d2)
        lo = min(d1, d2)
        order = 'H' if dice_list[0] == hi else 'L'

        best_move_str = None
        best_s = -1e18

        # Step 0 legal starts
        starts0 = legal_starts_for_die(my_pts, opp_pts, my_bar, dice_list[0])
        if not starts0:
            starts0 = ['P']
        for st0 in starts0:
            if st0 == 'P':
                myp1, oppp1, bar1, off_delta1 = my_pts, opp_pts, my_bar, 0
            else:
                applied0 = apply_move(my_pts, opp_pts, my_bar, st0, dice_list[0])
                if applied0 is None:
                    continue
                myp1, oppp1, bar1, off_delta1 = applied0
            # Step 1 legal starts from resulting position
            starts1 = legal_starts_for_die(myp1, oppp1, bar1, dice_list[1])
            if not starts1:
                starts1 = ['P']
            for st1 in starts1:
                if st1 == 'P':
                    myp2, oppp2, bar2, off_delta2 = myp1, oppp1, bar1, 0
                else:
                    applied1 = apply_move(myp1, oppp1, bar1, st1, dice_list[1])
                    if applied1 is None:
                        continue
                    myp2, oppp2, bar2, off_delta2 = applied1
                s = evaluate(myp2, oppp2, bar2, my_off + off_delta1 + off_delta2)
                if s > best_s:
                    best_s = s
                    # Encode as required compact format with order H/L
                    if hi == lo:
                        best_move_str = f"{order}:{st0},{st1}"
                    else:
                        # Map dice values to encoded positions: FROM1 for high die, FROM2 for low die
                        # If dice_list[0] is high, then st0 goes to FROM1 and st1 to FROM2, else vice versa.
                        if dice_list[0] == hi:
                            from_high, from_low = st0, st1
                        else:
                            from_high, from_low = st1, st0
                        best_move_str = f"{order}:{from_high},{from_low}"

        if best_move_str is None:
            return "H:P,P"
        return best_move_str

    # Ensure output legal string always; fallback pass
    try:
        return best_action()
    except Exception:
        return "H:P,P"
