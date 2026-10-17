
import copy
from functools import lru_cache

# Policy: Backgammon move selector (single-agent, player to move).
# Returns a legal move string in the required format.

def policy(state: dict) -> str:
    my_pts = state["my_pts"]
    opp_pts = state["opp_pts"]
    my_bar = state["my_bar"]
    opp_bar = state["opp_bar"]
    my_off = state["my_off"]
    opp_off = state["opp_off"]
    dice = state["dice"]
    assert isinstance(dice, list) and len(dice) in (1, 2)

    # --- Utilities for mapping directions ---
    # We assume engine uses absolute indices 0..23 with you moving from 23 -> 0.
    # That implies: from point i, a die d moves to dest = i - d.
    # Bear-off destinations handled by engine; for legality we need only home-board check.
    def is_my_home_point(p):
        # Home board is A0..A5 => indices 0..5
        return 0 <= p <= 5

    def count_my_remaining():
        return sum(my_pts) + my_bar  # borne off not included

    # --- Generate legal "from" choices for a single die ---
    # We must respect:
    # - If my_bar > 0, must move from Bar.
    # - Can't move onto point with 2+ opponent checkers.
    # - Bear off only allowed when all remaining are in home board.
    #
    # Note: We don't compute destinations for return validity; engine will.
    # But to generate legal FROMs we must ensure destination is not blocked and
    # bear-off is allowed if applicable.

    def apply_one_move(board_my, board_opp, bar_my, die, from_pos):
        """
        Simulate one move to update occupancy.
        Returns (new_my_pts, new_opp_pts, new_bar_my, moved_flag, legal_flag)
        moved_flag indicates whether a checker moved (should always for legal).
        """
        my_pts_l = list(board_my)
        opp_pts_l = list(board_opp)
        if from_pos == "B":
            if bar_my <= 0:
                return None
            dest = 23 - die  # re-entry follows same direction rule: from "virtual 23"? In engines often re-enter to point 23-d
            # With indices moving 23->0, entering point for die d is 23-d
            # If dest < 0, that would mean bear off directly, which shouldn't happen on re-entry.
        else:
            i = int(from_pos[1:]) if from_pos.startswith("A") else int(from_pos)
            if my_pts_l[i] <= 0:
                return None
            dest = i - die

        # Handle blocked destination
        if dest >= 0:
            if opp_pts_l[dest] >= 2:
                return None

            # Move checker
            if from_pos == "B":
                bar_my2 = bar_my - 1
            else:
                bar_my2 = bar_my
                my_pts_l[i] -= 1

            # Hit logic (only if dest has exactly 1 opposing checker)
            if opp_pts_l[dest] == 1:
                opp_pts_l[dest] = 0
                # hit means opponent bar increases; but we don't have opp_bar here.
                # In evaluation we can track hits by encoding into a simplified state.
                # For legality, only occupancy matters; we'll update counts.
                # We'll maintain opp bar separately in caller if needed; here not.
                # So we skip updating opp_bar; treat as legal and set a marker.
                hit = True
            else:
                hit = False

            my_pts_l[dest] += 1
            return my_pts_l, opp_pts_l, bar_my2, hit, dest, False  # False = not borne off

        # dest < 0 => bear off attempt
        # Bear off allowed only if all remaining checkers are in home board (A0..A5)
        remaining = sum(my_pts_l) + bar_my
        # After removing the moving checker, remaining would be remaining-1, but condition is about
        # current remaining checkers all in home board.
        if remaining <= 0:
            return None

        # Check if all checkers are in home board or to bear off with exact roll.
        # Condition: all remaining checkers are in home board.
        # That means: no checkers outside 0..5 and no bar.
        if bar_my != 0:
            return None
        for p in range(6, 24):
            if my_pts_l[p] != 0:
                return None

        # Then bear off is legal.
        # Update checker removal
        if from_pos == "B":
            return None  # normally can't bear off from bar
        else:
            my_pts_l[i] -= 1
        # borne off
        return my_pts_l, opp_pts_l, bar_my, False, None, True

    def legal_froms_for_die(board_my, board_opp, bar_my, die):
        froms = []
        if bar_my > 0:
            # must re-enter from Bar
            # entry point is 23-d
            dest = 23 - die
            if dest < 0:
                return []  # shouldn't happen
            if board_opp[dest] >= 2:
                return []
            return ["B"]
        # Otherwise consider all points with my checkers
        for i in range(24):
            if board_my[i] <= 0:
                continue
            dest = i - die
            if dest >= 0:
                if board_opp[dest] >= 2:
                    continue
                froms.append(f"A{i}")
            else:
                # bear off possible only if all in home board
                remaining = sum(board_my) + bar_my
                if remaining <= 0:
                    continue
                if bar_my != 0:
                    continue
                ok = True
                for p in range(6, 24):
                    if board_my[p] != 0:
                        ok = False
                        break
                if ok:
                    froms.append(f"A{i}")
        return froms

    # --- Generate legal move for one die as FROM token list ---
    # For selection we will simulate both dice orders if two dice.
    def decode_move_string(order, from1, from2):
        return f"{order}:{from1},{from2}"

    # --- Evaluation function ---
    def evaluate(board_my, board_opp, bar_my, hit_count, borne_off_count):
        # Simple heuristic:
        # - Prefer bearing off (progress): reward borne off heavily.
        # - Reward hits (hit_count).
        # - Reward having checkers on home points (0..5) and making stacks.
        # - Penalize making blot (single checker vulnerable) on non-home points.
        # - Penalize giving opponent entry by creating points with 1 checker when opponent has opportunities.
        score = 0
        score += 20 * borne_off_count
        score += 6 * hit_count

        # home progress
        for p in range(6):
            score += 2 * board_my[p]
            if board_my[p] >= 2:
                score += 3  # made point protection

        # distribution
        for p in range(6, 24):
            score += 0.2 * board_my[p]
            if board_my[p] == 1:
                score -= 1.0  # blot

        # opponent pressure (stacked opp is bad for us)
        for p in range(24):
            score -= 0.15 * board_opp[p]
            if p <= 5 and board_opp[p] > 0:
                score -= 0.3 * board_opp[p]  # blocking our home
        # bar penalty
        score -= 1.5 * bar_my
        return score

    # --- Ensure we return a legal move ---
    # We'll enumerate legal from pairs consistent with dice order.
    def best_legal_move():
        if len(dice) == 1:
            die = dice[0]
            froms = legal_froms_for_die(my_pts, opp_pts, my_bar, die)
            if not froms:
                # Need to pass for this die: return format with P
                return "H:P,P" if True else "L:P,P"
            # Choose best single move among candidates; encode other as P
            best = None
            best_score = -10**18
            for f1 in froms:
                sim = apply_one_move(my_pts, opp_pts, my_bar, die, f1)
                if sim is None:
                    continue
                nm, no, nb, hit, dest, borne = sim
                s = evaluate(nm, no, nb, 1 if hit else 0, 1 if borne else 0)
                if s > best_score:
                    best_score = s
                    best = f1
            # If die considered higher/lower doesn't matter with single die; we can use H marker.
            return f"H:{best},P"

        # two dice
        d1, d2 = dice[0], dice[1]
        hi = max(d1, d2)
        lo = min(d1, d2)

        # Must play both dice if possible; we will find legal pair for each order then pick best.
        def enumerate_pairs(order_hi_first=True):
            die_first = hi if order_hi_first else lo
            die_second = lo if order_hi_first else hi

            froms_first = legal_froms_for_die(my_pts, opp_pts, my_bar, die_first)
            if not froms_first:
                return []
            results = []
            for f1 in froms_first:
                sim1 = apply_one_move(my_pts, opp_pts, my_bar, die_first, f1)
                if sim1 is None:
                    continue
                m1, o1, b1, hit1, dest1, borne1 = sim1

                froms_second = legal_froms_for_die(m1, o1, b1, die_second)
                if not froms_second:
                    # cannot play both for this order
                    continue
                for f2 in froms_second:
                    sim2 = apply_one_move(m1, o1, b1, die_second, f2)
                    if sim2 is None:
                        continue
                    m2, o2, b2, hit2, dest2, borne2 = sim2
                    results.append((f1, f2, m2, o2, b2, (1 if hit1 else 0) + (1 if hit2 else 0),
                                    (1 if borne1 else 0) + (1 if borne2 else 0)))
            return results

        pairs_hi_first = enumerate_pairs(True)
        pairs_lo_first = enumerate_pairs(False)

        candidates = []
        if pairs_hi_first:
            for f1, f2, m2, o2, b2, hits, bornes in pairs_hi_first:
                score = evaluate(m2, o2, b2, hits, bornes)
                candidates.append(("H", f1, f2, score))
        if pairs_lo_first:
            for f1, f2, m2, o2, b2, hits, bornes in pairs_lo_first:
                score = evaluate(m2, o2, b2, hits, bornes)
                candidates.append(("L", f1, f2, score))

        # If neither order can play both dice (rare if both dice exist but blocked),
        # we must play the higher die when possible and pass the other.
        if not candidates:
            # Try higher die only
            die = hi
            froms = legal_froms_for_die(my_pts, opp_pts, my_bar, die)
            if froms:
                best = froms[0]
                best_score = -10**18
                for f1 in froms:
                    sim = apply_one_move(my_pts, opp_pts, my_bar, die, f1)
                    if sim is None:
                        continue
                    nm, no, nb, hit, dest, borne = sim
                    s = evaluate(nm, no, nb, 1 if hit else 0, 1 if borne else 0)
                    if s > best_score:
                        best_score = s
                        best = f1
                # Encode as playing higher die first => order 'H' with second pass
                return f"H:{best},P"
            # Else no legal moves at all
            return "H:P,P"

        # Choose best candidate
        candidates.sort(key=lambda x: x[3], reverse=True)
        _, f1, f2, _ = candidates[0]
        return f"{candidates[0][0]}:{f1},{f2}"

    mv = best_legal_move()

    # Final sanity: ensure it's a string in expected format
    if not isinstance(mv, str) or len(mv) < 3 or ":" not in mv:
        return "H:P,P"
    return mv

