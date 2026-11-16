
import math
import random
from typing import List, Tuple, Dict, Optional

def policy(state: dict) -> str:
    # Extract state
    my_pts: List[int] = state['my_pts']
    opp_pts: List[int] = state['opp_pts']
    my_bar: int = state['my_bar']
    opp_bar: int = state['opp_bar']
    my_off: int = state['my_off']
    opp_off: int = state['opp_off']
    dice: List[int] = state['dice']

    # Utility: list of dice values
    dice_vals = list(dice)
    dice_vals.sort(reverse=True)  # [high, low]
    hi = dice_vals[0]
    lo = dice_vals[1] if len(dice_vals) > 1 else 0

    # Helpers
    total_checkers = sum(my_pts) + my_bar + my_off
    # Whether bearing off is allowed: all remaining checkers must be in home board 0..5
    def can_bear_off() -> bool:
        # If any on bar, cannot bear off
        if my_bar > 0:
            return False
        # Check all points >5 are empty
        for i in range(6, 24):
            if my_pts[i] > 0:
                return False
        return True

    # Opponent blot risk around the board
    def opponent_presence_on(dest: int) -> int:
        return opp_pts[dest]

    # Probability opponent can hit a blot at dest (rough, used for safety weighting)
    # Only consider direct single-die hits (not doubles). Approximate combinatorics.
    def hit_probability_for_blot(dest: int) -> float:
        # If dest has >=2 opponent checkers, it's already unplayable; but we won't hit there.
        cnt = opponent_presence_on(dest)
        if cnt <= 0:
            return 0.0
        # For a blot (cnt==1), they can hit if they roll the exact die to land on dest.
        # They move from 0..23 toward 23..0, but from our perspective:
        # - If dest is 0..5 (our home), they hit with a die equal to (dest+1)
        # - If dest is 6..23 (their home from our perspective), they hit with a die equal to (24 - dest)
        need = (dest + 1) if dest <= 5 else (24 - dest)
        if need < 1 or need > 6:
            return 0.0
        p_single = 1.0 / 6.0
        # If they have dice left, chance at least one equals need. Approx: 1 - ((5/6)^n)
        p_any = 1.0 - math.pow(5.0 / 6.0, len(dice_vals))
        return min(1.0, p_any * (1.0 if cnt == 1 else 0.0))

    # Compute number of opponent checkers that can immediately enter if we have checkers on bar
    # For a given die d, destination index is d-1 (0-based). Entry allowed if dest has <=1 opponent checker.
    def opponent_entry_count_for_die(d: int) -> int:
        if d <= 0 or d > 6:
            return 0
        dest = d - 1
        cnt = 0
        if 0 <= dest < 24:
            cnt += opp_pts[dest]
        return cnt

    # Safety: penalty if moving to a point that would leave a blot (own count == 1) and opponent has presence.
    def blot_risk_penalty(dest: int, moving_count: int) -> float:
        if moving_count <= 1:
            prob = hit_probability_for_blot(dest)
            if prob <= 0:
                return 0.0
            # Scale penalty with entry power of opponent
            entry = opponent_entry_count_for_die(1)
            if entry >= 2:
                return 0.8 * prob
            elif entry == 1:
                return 0.5 * prob
            else:
                return 0.15 * prob
        return 0.0

    # Evaluate a single-die move (from point index or Bar)
    # Returns (score, info_dict) where info helps score a two-die sequence.
    def evaluate_move(from_pos: str, die: int) -> Tuple[float, Dict]:
        # from_pos is "B" or "A{i}"
        info = {
            'from': from_pos,
            'die': die,
            'is_hit': False,
            'is_point_made': False,
            'is_blocking_point': False,
            'dest': -1,
            'leave_blot': False,
            'safety': 0.0,
            'enter_rolls': 0,   # if from bar, how many die faces allow entry
            'hitting_rolls': 0, # if from bar, how many die faces hit directly
            'home_progress_delta': 0.0, # change in home distribution measure
        }
        score = 0.0

        if from_pos == "B":
            # From bar: destination index is (die - 1)
            if die < 1 or die > 6:
                return (-1e9, info)
            dest = die - 1
            info['dest'] = dest
            # Entry blocked?
            opp_cnt = opp_pts[dest]
            if opp_cnt >= 2:
                # Illegal move; should not be suggested, but guard
                return (-1e9, info)
            # Evaluate hits
            if opp_cnt == 1:
                info['is_hit'] = True
                score += 6.0  # strong positive for hitting from bar
            # Evaluate leaving blot (not applicable since you move 1 checker to dest)
            # Evaluate safety at dest (if you land on a blot you own)
            # If opponent has no checker there, you may land on empty or your own point/stack.
            # Blot risk if you end with exactly 1 checker after move: possible only if landing on empty when moving 1.
            # Since we moved from bar with 1 checker, dest count will be 1.
            if opp_cnt == 0:
                info['leave_blot'] = True
                info['safety'] = -blot_risk_penalty(dest, moving_count=1)
                score += info['safety']
            # Entry success estimate
            # Count faces that allow entry (dest occupied by <=1 opponent)
            enter_faces = 0
            hit_faces = 0
            for d in range(1, 7):
                dst = d - 1
                oc = opp_pts[dst] if 0 <= dst < 24 else 0
                if oc <= 1:
                    enter_faces += 1
                if oc == 1:
                    hit_faces += 1
            info['enter_rolls'] = enter_faces
            info['hitting_rolls'] = hit_faces
            # Heuristic for bar: favor high entry success and direct hitting faces
            score += 0.7 * (enter_faces / 6.0)
            if hit_faces > 0:
                score += 1.2 * (hit_faces / 6.0)
            return (score, info)

        # From board point: parse
        if not from_pos.startswith("A"):
            return (-1e9, info)
        src = int(from_pos[1:])
        if src < 0 or src > 23:
            return (-1e9, info)
        # If we have any checkers on bar, cannot move from board
        if my_bar > 0:
            return (-1e9, info)
        if my_pts[src] <= 0:
            return (-1e9, info)

        # Destination index
        dest = src - die
        info['dest'] = dest

        # Check block/hit legality for dest
        if dest < 0:
            # bearing off allowed only if can_bear_off()
            if not can_bear_off():
                return (-1e9, info)
            # Compute progress toward bearing off: favor bearing off from higher indices more
            info['home_progress_delta'] = 0.2 + 0.05 * max(0, src - 0)  # small boost; exact value not critical
            score += 0.4 + info['home_progress_delta']
            return (score, info)
        else:
            # Normal move within board
            opp_cnt = opp_pts[dest]
            # Cannot land on a point with >=2 opponent checkers
            if opp_cnt >= 2:
                return (-1e9, info)

            # Evaluate hit/block
            if opp_cnt == 1:
                info['is_hit'] = True
                score += 4.5
            else:
                # If moving onto your own point (>=1), maybe making a stronger point
                own_cnt = my_pts[dest]
                if own_cnt > 0:
                    info['is_point_made'] = (own_cnt + 1 >= 2)  # will have >=2 after move
                    score += 1.0 + 0.6 * min(3, own_cnt)  # modest value for reinforcement
                else:
                    # Moving to an empty point: consider its strategic value (closer to home)
                    # Favor points 0..5 more (home board)
                    if 0 <= dest <= 5:
                        score += 0.8
                    elif 6 <= dest <= 11:
                        score += 0.5
                    elif 12 <= dest <= 17:
                        score += 0.25
                    else:
                        score += 0.05

            # Blot risk at src after moving one checker away
            if my_pts[src] == 1:
                # src becomes empty -> no blot risk at src
                pass
            # Blot risk at dest if dest becomes a blot
            if opp_cnt == 0 and my_pts[dest] == 0:
                # after moving, dest will have 1 checker (a blot)
                info['leave_blot'] = True
                info['safety'] = -blot_risk_penalty(dest, moving_count=1)
                score += info['safety']

            # Blocking evaluation: if we occupy dest (own_cnt > 0), we may be blocking opponent entry
            own_cnt = my_pts[dest]
            if own_cnt > 0:
                # points we own in our home board are more valuable to block
                if 0 <= dest <= 5:
                    score += 0.5
                    info['is_blocking_point'] = True
                else:
                    score += 0.25

            return (score, info)

    # Generate all legal single-die moves
    single_moves = []  # elements: (from_token, die, score, info)

    # Moves from Bar
    if my_bar > 0:
        for d in [hi, lo]:
            if d == 0:
                continue
            dest = d - 1
            if 0 <= dest < 24 and opp_pts[dest] <= 1:
                sc, info = evaluate_move("B", d)
                if sc > -1e8:
                    single_moves.append(("B", d, sc, info))

    # Moves from points
    if my_bar == 0:
        # Enumerate src points that have checkers
        src_indices = [i for i, c in enumerate(my_pts) if c > 0]
        # Consider both dice
        for d in [hi, lo]:
            if d == 0:
                continue
            for src in src_indices:
                sc, info = evaluate_move(f"A{src}", d)
                if sc > -1e8:
                    single_moves.append((f"A{src}", d, sc, info))

    # If no single moves, must pass
    if not single_moves:
        # If any dice exist but no move -> Pass
        return "H:P,P" if hi != 0 else "H:P,P"

    # Helper: map from (from_token, die) to (score, info)
    move_map = {(mv[0], mv[1]): (mv[2], mv[3]) for mv in single_moves}

    # Helper: check whether two moves are compatible in a single turn
    def compatible(m1_from: str, m1_die: int, m2_from: str, m2_die: int) -> bool:
        # If Bar present at start, first move must be from Bar
        if my_bar > 0:
            if m1_from != "B":
                return False
        # No move may exceed remaining checkers availability
        # This is a simple check: the same source point cannot be used twice if it had only 1 checker.
        # More precisely, we simulate counts.
        my_src_counts = {f"A{i}": my_pts[i] for i in range(24)}
        if my_bar > 0:
            my_src_counts["B"] = my_bar
        else:
            my_src_counts["B"] = 0

        # Apply first move
        def apply_move(from_t: str, die: int, src_counts: dict, pts: List[int], bar: int, off: int):
            # clone-like operation on local dict
            if from_t == "B":
                # consume from bar
                src_counts["B"] -= 1
                dest = die - 1
                # Apply destination effect: hit or land
                if 0 <= dest < 24:
                    # handle opponent hit or landing
                    # We don't modify opp_pts here; just track your occupancy
                    if pts[dest] == 0 and opp_pts[dest] == 0:
                        # empty
                        pts[dest] = 1
                    elif pts[dest] >= 1 and opp_pts[dest] == 0:
                        # own stack
                        pts[dest] += 1
                    elif opp_pts[dest] == 1:
                        # hit
                        # remove opponent from dest (we don't track opp_pts here) and place your checker there
                        pts[dest] = 1
                    else:
                        # shouldn't happen
                        pass
            else:
                src = int(from_t[1:])
                src_counts[from_t] -= 1
                dest = src - die
                if dest < 0:
                    # bearing off
                    off += 1
                else:
                    # landing
                    if pts[dest] == 0 and opp_pts[dest] == 0:
                        pts[dest] = 1
                    elif pts[dest] >= 1 and opp_pts[dest] == 0:
                        pts[dest] += 1
                    elif opp_pts[dest] == 1:
                        pts[dest] = 1
                    else:
                        # blocked; shouldn't happen because legality already checked
                        pass
            return src_counts, pts, bar, off

        # Local copies (lightweight simulation)
        local_src_counts = dict(my_src_counts)
        local_my_pts = list(my_pts)
        local_my_off = my_off
        # Apply move 1
        local_src_counts, local_my_pts, _, local_my_off = apply_move(m1_from, m1_die, local_src_counts, local_my_pts, my_bar, local_my_off)
        # Apply move 2
        local_src_counts, local_my_pts, _, local_my_off = apply_move(m2_from, m2_die, local_src_counts, local_my_pts, my_bar, local_my_off)
        # Check no negative counts
        for k, v in local_src_counts.items():
            if v < 0:
                return False
        return True

    # Build candidates (order: H or L, first-from, second-from)
    candidates = []

    # Helper to add a candidate and store the used dice
    def add_candidate(order: str, from1: str, from2: str, d1: int, d2: int):
        candidates.append({
            'order': order,
            'from1': from1,
            'from2': from2,
            'd1': d1,
            'd2': d2,
            'score': 0.0,
            'used': [(from1, d1), (from2, d2)]
        })

    # If only one die present, pick best single move, higher die if tie on value.
    if lo == 0:
        best = None
        for mv in single_moves:
            _, d, sc, _ = mv
            if best is None:
                best = mv
            else:
                if sc > best[2] + 1e-9:
                    best = mv
                elif abs(sc - best[2]) <= 1e-9:
                    if d > best[1]:
                        best = mv
        if best is None:
            return "H:P,P"
        from_tok, d_used, sc, inf = best
        # Order doesn't matter with one die; choose H by default
        return f"H:{from_tok},P"

    # We have two dice; generate sequences
    # Enumerate first move candidates
    first_moves = []
    if my_bar > 0:
        # Must start with Bar; order is determined by which die we apply first.
        # We'll generate both H and L sequences explicitly below.
        # We'll fill first_moves only for "B"
        for d in [hi, lo]:
            # only consider legal bar moves
            dest = d - 1
            if 0 <= dest < 24 and opp_pts[dest] <= 1:
                sc, info = evaluate_move("B", d)
                if sc > -1e8:
                    first_moves.append(("B", d, sc, info))
    else:
        # From board
        for mv in single_moves:
            from_t, d, sc, info = mv
            if from_t != "B":
                first_moves.append((from_t, d, sc, info))

    # Build both orders: H first then L first, ensure legality
    for order_label, first_die, second_die in [("H", hi, lo), ("L", lo, hi)]:
        # Build list of compatible first moves for this order
        compatible_first = []
        for fmv in first_moves:
            f_from, f_d, f_sc, f_info = fmv
            if f_d != first_die:
                continue
            # Ensure first move legal (already guaranteed), add
            compatible_first.append(fmv)

        for fmv in compatible_first:
            f_from, f_d, f_sc, f_info = fmv
            # Find second move candidates with remaining die
            # Evaluate all single moves with die == second_die; filter compatibility with first move
            for smv in single_moves:
                s_from, s_d, s_sc, s_info = smv
                if s_d != second_die:
                    continue
                # Check Bar-first constraint: if my_bar>0 at start, second move can be from board; if no bar, both from board.
                # Already satisfied by single_moves generation.
                # Compatibility of using same source point twice:
                if not compatible(f_from, f_d, s_from, s_d):
                    continue
                # Candidate score: sum of individual scores, plus synergy bonus for hits in both
                base = f_sc + s_sc
                synergy = 0.0
                if f_info.get('is_hit') and s_info.get('is_hit'):
                    synergy += 2.0
                # Bonus if first move is a hit and second is a point made
                if f_info.get('is_hit') and s_info.get('is_point_made'):
                    synergy += 0.8
                # Bonus if both moves are blocking points in home board
                if f_info.get('is_blocking_point') and s_info.get('is_blocking_point'):
                    synergy += 0.6
                # Small randomness to break ties deterministically
                noise = random.random() * 1e-6
                total = base + synergy + noise
                add_candidate(order_label, f_from, s_from, f_d, s_d)
                candidates[-1]['score'] = total

    # If no two-dice sequences found, try to play the higher die only
    if not candidates:
        # Choose best single move (prefer higher die if tie)
        best_single = None
        for mv in single_moves:
            _, d, sc, _ = mv
            if best_single is None:
                best_single = mv
            else:
                if sc > best_single[2] + 1e-9:
                    best_single = mv
                elif abs(sc - best_single[2]) <= 1e-9:
                    if d > best_single[1]:
                        best_single = mv
        if best_single is None:
            return "H:P,P"
        from_tok, d_used, _, _ = best_single
        # Play higher die only
        return f"H:{from_tok},P"

    # Choose best candidate by score, tie-break with higher first die order then small randomness
    # Compute effective first die by order
    def effective_first_die(cand):
        return cand['d1'] if cand['order'] == 'H' else cand['d2']
    # Sort by score desc, then by effective first die desc, then random slight jitter
    random.shuffle(candidates)
    best = sorted(candidates, key=lambda c: (c['score'], effective_first_die(c)), reverse=True)[0]

    # Build return string
    # If second move is Pass (we didn't generate pass in candidates), ensure format has P
    from1 = best['from1']
    from2 = best['from2']
    order = best['order']
    return f"{order}:{from1},{from2}"
