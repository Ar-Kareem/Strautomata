
import math
from functools import lru_cache

def policy(state: dict) -> str:
    my_pts = list(state["my_pts"])
    opp_pts = list(state["opp_pts"])
    my_bar = state["my_bar"]
    opp_bar = state["opp_bar"]
    my_off = state["my_off"]
    dice = list(state["dice"])
    # If engine somehow gives invalid/empty dice, pass
    if not dice:
        return "H:P,P"

    # Helpers: indices for home board (for bearing off). For our direction, home is A0..A5
    # Engine uses absolute indices 0..23; we move from 23 -> 0.
    HOME = set(range(0, 6))

    def legal_destinations_from(board_my, board_opp, bar_count, from_idx, die):
        """
        Return list of possible destinations with legality given only occupancy constraints.
        We don't need exact destination for scoring/hitting markers, but we must compute to validate.
        Direction: moving from higher index to lower index by die.
        - from_idx can be 'B' or 0..23.
        - If bearing off is possible, include destination 'OFF'.
        """
        # Determine start index and whether from bar
        if from_idx == "B":
            src = None
        else:
            src = from_idx

        # Compute destination
        if from_idx == "B":
            # Re-entry point corresponds to our index after moving in by die.
            # With direction 23 -> 0, entering from bar uses indices starting at 23 downwards:
            # Typically entry is at point (24 - die) in 1-based. With 0-based index:
            # index = 24 - die - 1 = 23 - die
            dest = 23 - die
            # If dest is outside 0..23, bearing off is not relevant for re-entry.
            if dest < 0 or dest > 23:
                return []
            # Landing legality: cannot land on opp stack >=2
            if board_opp[dest] >= 2:
                return []
            return [dest]

        # normal move
        dest = src - die
        if dest >= 0:
            if board_opp[dest] >= 2:
                return []
            return [dest]
        # bearing off: only if all remaining checkers are in home board
        # Condition: all of our checkers are in points 0..5 (and bar is 0)
        # Our remaining checkers exclude those already off.
        total_remaining = sum(board_my) + bar_count  # board_my sums only on board (0..23)
        # If any checker outside home board, bearing off illegal
        if total_remaining <= 0:
            return []
        for i in range(6, 24):
            if board_my[i] > 0:
                return []
        # Bearing off allowed: any move that goes beyond 0 counts as bearing off
        return ["OFF"]

    def apply_move(board_my, board_opp, bar_count, from_idx, die):
        """
        Apply move and return new (my, opp, bar, off_added, hit_flag)
        """
        my = list(board_my)
        opp = list(board_opp)
        my_bar_new = bar_count
        hit = False
        off_added = 0

        if from_idx == "B":
            # move from bar into board
            # destination computed
            dests = legal_destinations_from(my, opp, my_bar_new, "B", die)
            if not dests:
                return None
            dest = dests[0]
            my_bar_new -= 1
            # If landing on a blot, hit
            if dest != "OFF" and opp[dest] == 1:
                opp[dest] -= 1
                # hit means opponent goes to bar; we don't track opp_bar here but can infer hit
                hit = True
            # If opp has 0, fine; if opp has 1 and hit, replaced
            if dest != "OFF":
                if opp[dest] >= 1:
                    # after hit, opp[dest] should be 0
                    if opp[dest] != 0:
                        return None
                my[dest] += 1
            else:
                return None
        else:
            src = from_idx
            dests = legal_destinations_from(my, opp, my_bar_new, src, die)
            if not dests:
                return None
            dest = dests[0]
            my[src] -= 1
            if dest == "OFF":
                off_added += 1
            else:
                if opp[dest] == 1:
                    hit = True
                    opp[dest] -= 1
                if opp[dest] >= 1:
                    # if opp[dest] was >=1 but not 1 (>=2) it was illegal; if 1 we hit and it becomes 0
                    if opp[dest] != 0:
                        return None
                my[dest] += 1

        return my, opp, my_bar_new, off_added, hit

    # Scoring heuristic
    def score_position(my, opp, my_bar_now, my_off_now, opp_off_now, hit_events):
        """
        Higher is better.
        hit_events: number of hits executed in the last move sequence.
        """
        score = 0

        # Big rewards for hits
        score += 50 * hit_events

        # Reward having checkers on higher probability safe/anchor points (home approach points)
        # home points 0..5: being advanced
        for i in range(0, 6):
            score += 3 * my[i]

        # Slight reward for being far advanced even if not in home
        for i in range(6, 24):
            # closer to home means smaller index
            score += 0.3 * (23 - i) * my[i]

        # Penalize blots: points where we have exactly 1 checker AND opponent can potentially hit (approx).
        # Approx: if opponent has at least one checker, assume vulnerability if opponent could land there.
        # We'll use a simple proxy: penalize our blots a bit when adjacent index in opponent direction has pieces.
        for i in range(0, 24):
            if my[i] == 1:
                score -= 6
                # if opponent stacks exist in a region that could hit: small extra penalty
                if any(opp[j] > 0 for j in range(max(0, i-6), min(24, i+7))):
                    score -= 1

        # Reward made points (stacks of 2+)
        for i in range(0, 24):
            if my[i] >= 2:
                score += 2 * (my[i] - 1)

        # Penalize having pieces on bar (to encourage re-entry and to avoid future bar)
        score -= 10 * my_bar_now

        # Encourage bearing off: each off checker counts positively
        score += 20 * my_off_now
        return score

    # Generate candidate starting moves for a given die, respecting bar rule
    def candidate_starts_for_die(my, my_bar_now, die):
        starts = []
        if my_bar_now > 0:
            # must move from bar
            starts.append("B")
            return starts
        # otherwise any point with a checker can be used if it has a legal destination
        for i in range(24):
            if my[i] > 0:
                if legal_destinations_from(my, opp_pts, my_bar_now, i, die):
                    starts.append(i)
        return starts

    # Simulation across dice with exact order choice (H/L)
    def evaluate_order(first_die_is_high):
        # Determine die order and which dice might be playable
        if len(dice) == 1:
            d1 = d2 = dice[0]
            # Only one die effectively; we will treat the second as pass.
            order = [d1]
        else:
            low = min(dice)
            high = max(dice)
            order = [high, low] if first_die_is_high else [low, high]

        best = None  # (score, move_string)

        if len(dice) == 1:
            die = dice[0]
            starts = candidate_starts_for_die(my_pts, my_bar, die)
            if not starts:
                # must pass
                return -1e9, "H:P,P"
            for s1 in starts:
                res = apply_move(my_pts, opp_pts, my_bar, s1, die)
                if res is None:
                    continue
                my1, opp1, mybar1, off1, hit1 = res
                my_off_now = my_off + off1
                sc = score_position(my1, opp1, mybar1, my_off_now, state["opp_off"], hit1)
                mv = ("H" if (die == max(dice)) else "L")  # arbitrary since only one die; but policy string needs H/L
                # For one die, engine expects higher die when possible; with one die equal.
                move_string = f"{mv}:{_pt_token(s1) if s1!='B' else 'B'},P"
                # But format requires two FROM tokens always. We'll put from1=move, from2=Pass.
                # Choose H or L doesn't affect legality if second is P.
                move_string = f"{mv}:{_pt_token(s1)},{'P' }"
                if best is None or sc > best[0]:
                    best = (sc, move_string)
            return best if best is not None else (-1e9, "H:P,P")

        # Two dice: try all combinations respecting bar constraint at each step
        dieA, dieB = order[0], order[1]
        startsA = candidate_starts_for_die(my_pts, my_bar, dieA)
        if not startsA:
            # if can't play first die, in principle engine might still require playing second die only with rule.
            # We'll handle by using pass for first and try second from resulting state (no state change).
            # But the engine rule: if both dice can be played, must play both. Here if startsA empty, assume only dieB is playable.
            startsB = candidate_starts_for_die(my_pts, my_bar, dieB)
            if not startsB:
                return -1e9, "H:P,P"
            for sB in startsB:
                resB = apply_move(my_pts, opp_pts, my_bar, sB, dieB)
                if resB is None:
                    continue
                my1, opp1, mybar1, off1, hit1 = resB
                sc = score_position(my1, opp1, mybar1, my_off + off1, state["opp_off"], hit1)
                # Encode as first uses Pass, second uses dieB; order letter indicates which die first in encoding.
                # If first_die_is_high True => letter 'H', else 'L'.
                letter = "H" if first_die_is_high else "L"
                move_string = f"{letter}:P,{_pt_token(sB)}" if sB != "B" else f"{letter}:P,B"
                if best is None or sc > best[0]:
                    best = (sc, move_string)
            return best

        letter = "H" if first_die_is_high else "L"
        best = (-1e18, "H:P,P")
        for sA in startsA:
            resA = apply_move(my_pts, opp_pts, my_bar, sA, dieA)
            if resA is None:
                continue
            myA, oppA, mybarA, offA, hitA = resA
            startsB = candidate_starts_for_die(myA, mybarA, dieB)
            if not startsB:
                # cannot play second die; choose pass only if allowed (i.e., second die not playable)
                sc = score_position(myA, oppA, mybarA, my_off + offA, state["opp_off"], hitA)
                mv = f"{letter}:{_pt_token(sA) if sA!='B' else 'B'},P"
                if sc > best[0]:
                    best = (sc, mv)
            else:
                for sB in startsB:
                    resB = apply_move(myA, oppA, mybarA, sB, dieB)
                    if resB is None:
                        continue
                    myB, oppB, mybarB, offB, hitB = resB
                    total_hits = (1 if hitA else 0) + (1 if hitB else 0)
                    sc = score_position(myB, oppB, mybarB, my_off + offA + offB, state["opp_off"], total_hits)
                    mv = f"{letter}:{_pt_token(sA) if sA!='B' else 'B'},{_pt_token(sB) if sB!='B' else 'B'}"
                    if sc > best[0]:
                        best = (sc, mv)
        return best

    def _pt_token(x):
        # x is int 0..23
        return f"A{x}"

    # Evaluate both orderings and pick best legal-scoring one.
    scH, mvH = evaluate_order(True)
    scL, mvL = evaluate_order(False)

    # If only one die, mvH/mvL differ only in letter; keep the better score.
    if scH >= scL:
        return mvH
    return mvL
