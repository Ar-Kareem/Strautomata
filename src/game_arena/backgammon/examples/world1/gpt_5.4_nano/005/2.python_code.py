
import itertools

def policy(state: dict) -> str:
    my_pts = state["my_pts"]
    opp_pts = state["opp_pts"]
    my_bar = state["my_bar"]
    opp_bar = state["opp_bar"]
    dice = state["dice"][:]  # list of 0-2 ints in 1..6

    # Helpers for move tokens
    def token_from_idx(i):
        if i is None:
            return "P"
        if i == -1:
            return "B"
        return f"A{i}"

    # Map point index to home board indices for bearing off decision
    # With engine convention: our home board is points 0..5.
    HOME = set(range(0, 6))

    def all_in_home():
        # all remaining checkers are within home board (A0..A5) to allow bearing off
        # We treat bar as not in home.
        return my_bar == 0 and all(my_pts[i] == 0 for i in range(6, 24))

    def count_my():
        return my_bar + sum(my_pts)

    # Simple scoring after applying a move sequence.
    # We do not know exact destinations, so we evaluate only using properties
    # available from the start positions and our current configuration.
    # To ensure legality, we still rely on engine by enumerating candidate actions
    # and returning a move that is claimed legal by the engine. However, since we
    # can't query engine legality here, we must still generate only plausible legal moves.
    #
    # Therefore: we simulate legality ourselves in a lightweight way using standard
    # backgammon movement direction (we move from higher index down toward 0).
    #
    # We must also handle bar entry and hitting/blocking/stacking.

    # Determine move direction for us: from point i to i - d (since engine says we move 23->0).
    def destination(src, d):
        if src == "B":
            # Entering point index for our side:
            # Typically entry is from opponent's home: point 24 - d (1-indexed).
            # With absolute 0..23 indices where opponent starts at 0->23,
            # our enter point is d-1? Let's derive:
            # If our home is 0..5, then from bar we enter into points 23..18? No, that's far side.
            # Standard mapping: for player moving from 24 to 1, entry square is 24-d.
            # In 0..23: squares are 0..23 corresponding to 1..24.
            # If our entry is at (24-d) in 1-indexed => (24-d)-1 = 23-d.
            # For d=1 -> 22, d=6 -> 17. This matches typical far-side entry.
            return 23 - d
        else:
            i = int(src[1:])  # A#
            return i - d

    def can_bear_off_from(src_idx, d):
        # Bearing off allowed only when all checkers in home board.
        if not all_in_home():
            return False
        # If exact landing is within home, fine. Otherwise if it overshoots, allowed if
        # there are no checkers on points higher than destination.
        # Here our home indices are 0..5.
        dest = src_idx - d
        if dest >= 0:
            return dest in HOME
        # Overshoot: allow only if no checkers on points > dest? For home, overshoot means dest<0.
        # Condition: if all checkers that can potentially block are not on points higher than 0? Actually:
        # In backgammon, if overshoot, you bear off from the highest occupied point in home.
        # So if src_idx is the highest point (within home) that has checkers, it's legal.
        for higher in range(src_idx+1, 6):
            if my_pts[higher] > 0:
                return False
        return True

    # Simulate applying one die from a given start, including hits and bar entry.
    # Returns updated board or None if illegal.
    def apply_one(board_my_pts, board_opp_pts, board_my_bar, src, d):
        my = board_my_pts[:]
        opp = board_opp_pts[:]
        bar = board_my_bar

        # Determine source type
        if src == "B":
            if bar <= 0:
                return None
            dest = destination("B", d)
            if dest < 0:
                # cannot; entry never overshoots
                return None
            # Destination cannot be occupied by 2+ opponent checkers
            if opp[dest] >= 2:
                return None
            # If occupied by exactly 1 opponent, hit it
            if opp[dest] == 1:
                opp[dest] = 0
                # hit opponent checker to bar: engine would do this; we track only for legality scoring
                # We can ignore opp_bar for legality of subsequent moves? It matters for legality later.
                # We'll track opp_bar in the outer simulation closure.
                # Here, we just return a structure including opp_bar separately.
                pass
            # Move checker
            bar -= 1
            if opp[dest] == 1:
                # actual hit handled by caller via opp_bar delta; we encode in a flag
                pass
            my[dest] += 1
            return my, opp, bar, (1 if opp[dest] == 1 else 0), dest  # hitflag based on before clearing not possible now

        # src is "A#"
        s_idx = int(src[1:])
        if my[s_idx] <= 0:
            return None
        dest = s_idx - d
        # Bearing off?
        if dest < 0:
            if not can_bear_off_from(s_idx, d):
                return None
            # Bear off removes checker from src
            my[s_idx] -= 1
            # return with off increment flag (we'll track in outer)
            return my, opp, bar, 0, "OFF"
        # Regular landing
        if dest >= 24:
            return None
        if dest < 6 and dest >= 0:
            pass
        # Block: cannot land on 2+ opponent
        if opp[dest] >= 2:
            return None
        # Hit if exactly 1
        hit = 1 if opp[dest] == 1 else 0
        if hit:
            opp[dest] = 0
        my[s_idx] -= 1
        my[dest] += 1
        return my, opp, bar, hit, dest

    # We'll build a full legality simulation that tracks both players bar/off.
    def simulate_action(move_tokens, dice_vals):
        # move_tokens: list of two src tokens for die1 and die2 (in order corresponding to dice_vals)
        my = my_pts[:]
        opp = opp_pts[:]
        bar_my = my_bar
        bar_opp = state["opp_bar"]
        off_my = state["my_off"]
        off_opp = state["opp_off"]

        for src, d in zip(move_tokens, dice_vals):
            if src == "P":
                continue
            res = None
            if src == "B":
                # entering requires tracking hit to opp_bar; implement correctly here
                if bar_my <= 0:
                    return None
                dest = destination("B", d)
                if dest < 0 or dest >= 24:
                    return None
                if opp[dest] >= 2:
                    return None
                hit = 1 if opp[dest] == 1 else 0
                if hit:
                    opp[dest] = 0
                    bar_opp += 1
                bar_my -= 1
                my[dest] += 1
            else:
                s_idx = int(src[1:])
                if my[s_idx] <= 0:
                    return None
                dest = s_idx - d
                if dest < 0:
                    if not all_in_home():
                        return None
                    # overshoot bearing off legality
                    # exact dest<0 means bear off allowed only if s_idx is highest occupied in home
                    for higher in range(s_idx+1, 6):
                        if my[higher] > 0:
                            return None
                    # If there are checkers on home points less than s_idx, still ok
                    my[s_idx] -= 1
                    off_my += 1
                else:
                    if dest < 0 or dest >= 24:
                        return None
                    if opp[dest] >= 2:
                        return None
                    hit = 1 if opp[dest] == 1 else 0
                    if hit:
                        opp[dest] = 0
                        bar_opp += 1
                    my[s_idx] -= 1
                    my[dest] += 1
        return {
            "my": my, "opp": opp,
            "bar_my": bar_my, "bar_opp": bar_opp,
            "off_my": off_my, "off_opp": off_opp
        }

    # Generate candidate start tokens for each die, respecting bar rule:
    # If my_bar>0, only "B" is allowed for the first die that is to be played.
    # Also, if playing two dice, second move must use updated board legality,
    # but we'll just enumerate broad candidates and rely on simulate_action to reject.
    def candidate_sources():
        sources = []
        if my_bar > 0:
            return ["B"]
        # else any point with our checker
        for i in range(24):
            if my_pts[i] > 0:
                sources.append(f"A{i}")
        if not sources:
            sources = ["P"]
        return sources

    # Scoring: reward hitting, making blocks/stacks, advancing, bearing off.
    def score(result):
        my = result["my"]
        opp = result["opp"]
        # material
        s = 0.0
        # bearing off
        s += (result["off_my"] - state["my_off"]) * 100.0
        # bar safety: if we put opp on bar (hit happened), it helps
        s += (result["bar_opp"] - state["opp_bar"]) * 6.0

        # stack safety / blot penalty
        for i in range(24):
            if my[i] >= 2:
                s += 1.5 * my[i]
            elif my[i] == 1:
                # blot risk: outside home is more risky
                s -= 0.8 * (1.5 if i >= 6 else 0.5)
        # advancement: weighted toward home
        # Our indices decrease as we advance, so lower index is better.
        for i in range(24):
            if my[i] > 0:
                s += (23 - i) * 0.05 * my[i]  # move toward 0 increases (23-i)? Actually 0 gives 23-0=23 big -> better.
        return s

    # Determine dice play order requirement.
    if len(dice) == 0:
        return "H:P,P"
    if len(dice) == 1:
        d1 = dice[0]
        candidates = candidate_sources()
        best = None
        best_s = -1e18
        for src1 in candidates:
            res = simulate_action([src1, "P"], [d1, d1])  # second ignored; dummy
            if res is None:
                continue
            # Only apply once: above sim applies twice; so handle properly by applying one die.
        # Fix: handle one die separately
        for src1 in candidates:
            # simulate with only one die by not applying second at all (P)
            res = simulate_action([src1, "P"], [d1, 0])  # second die 0 won't be used by P but zip will still include it; safer: always P means skip.
            # Our simulate_action skips when src == "P" so it will ignore die 0.
            if res is None:
                continue
            s = score(res)
            if s > best_s:
                best_s = s
                best = src1
        # Must return legal move string; pick with higher-die convention irrelevant for single die.
        # Engine likely accepts H or L as long as die assignment consistent; for 1 die, either order should be fine.
        if best is None:
            return "H:P,P"
        # Put best in the position corresponding to higher die (same die)
        return f"H:{best},P"

    # Two dice
    d_high = max(dice)
    d_low = min(dice)
    # Order for encoding: H means first die uses high, L means first uses low.
    # We'll try both encodings and pick best legal.
    def best_for_order(first_die, second_die):
        order_char = "H" if first_die == d_high else "L"
        sources_first = candidate_sources()

        best_move = None
        best_s = -1e18

        # Candidate second sources depend on having potentially moved a checker off a point;
        # but simulate_action will validate. We'll still enumerate based on current my_pts plus bar rule in simulate_action.
        sources_second_all = []
        if my_bar > 0:
            sources_second_all = ["B"]
        else:
            for i in range(24):
                if my_pts[i] > 0:
                    sources_second_all.append(f"A{i}")
            if not sources_second_all:
                sources_second_all = ["P"]

        # If only one die can be played, engine enforces higher die; we can't know ahead,
        # but our search over both dice with rejection should still work: if one die is illegal,
        # we might still find a legal action where that die is "P".
        # We'll allow "P" for second move and first move as needed.
        # Total candidates: (src1 in sources_first + ["P"], src2 in sources_second_all + ["P"])
        # while respecting bar rule at that time; simulate_action handles it.
        first_opts = sources_first + ["P"]
        second_opts = sources_second_all + ["P"]

        for src1, src2 in itertools.product(first_opts, second_opts):
            # If bar rule violated, simulate_action returns None.
            res = simulate_action([src1, src2], [first_die, second_die])
            if res is None:
                continue
            s = score(res)
            # tiny tie-break: prefer earlier non-pass
            if best_move is None or s > best_s + 1e-9:
                best_s = s
                best_move = (src1, src2, order_char)
        return best_move

    bestH = best_for_order(d_high, d_low)
    bestL = best_for_order(d_low, d_high)

    chosen = bestH if (bestH is not None and (bestL is None or bestH[2] == "H" and True)) else bestL
    if bestH is None and bestL is None:
        return "H:P,P"

    if bestH is None:
        chosen = bestL
    elif bestL is None:
        chosen = bestH
    else:
        # compare scores by re-simulating for certainty
        def score_of_tuple(tup, first_die, second_die):
            src1, src2, _ = tup
            res = simulate_action([src1, src2], [first_die, second_die])
            return -1e18 if res is None else score(res)
        sH = score_of_tuple(bestH, d_high, d_low)
        sL = score_of_tuple(bestL, d_low, d_high)
        chosen = bestH if sH >= sL else bestL

    src1, src2, order_char = chosen
    if src1 is None:
        src1 = "P"
    if src2 is None:
        src2 = "P"
    return f"{order_char}:{src1},{src2}"
