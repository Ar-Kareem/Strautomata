
import math

def policy(state: dict) -> str:
    my_pts = state["my_pts"]
    opp_pts = state["opp_pts"]
    my_bar = state["my_bar"]
    opp_bar = state["opp_bar"]
    my_off = state["my_off"]
    opp_off = state["opp_off"]
    dice = state["dice"]
    dice = list(dice)

    # Board orientation note:
    # We are always the player to move, engine handles destination computation.
    # Indices 0..23 are absolute; we always move from 23 downwards.
    # "Home board" for bearing off is points A0..A5 (indices 0..5).
    HOME = set(range(0, 6))

    # Helper: determine if we have all checkers in home for bear-off eligibility heuristic
    def in_home_only(my_pts, my_bar):
        if my_bar > 0:
            return False
        return all((i in HOME) or (c == 0) for i, c in enumerate(my_pts))

    # We need to enumerate legal moves. Because the prompt says the engine enforces legality
    # but we don't have a direct move generator, we approximate by generating candidate
    # FROM choices based on bar/must-move rules and using a lightweight internal legality
    # check by simulating destinations.
    #
    # We will implement a local legality check with standard backgammon rules assuming:
    # - We move "down" from 23 to 0.
    # - Die steps: dest = src - die, except when bearing off.
    # - Entry from bar (B): bar checkers re-enter at A? For the moving player orientation:
    #   common convention: if you move from 23->0, then entering point is 24-die? Actually
    #   typical orientation: player enters at point 24-die (index 23 down to ...).
    #   We'll derive: starting from 23 moving down by 1 reaches 22. So src index corresponds
    #   to "distance from your home". For re-entry, standard is index = 24 - die.
    #   With indices 0..23, that gives entry = 24 - die -> for die=6 entry=18, die=1 entry=23.
    def reentry_point(d):
        return 24 - d  # returns 18..23

    # Mapping points: index i has distance i from 0. Moving down decreases index.
    def bearing_off_dest_possible(src, d):
        # If dest < 0, it's bearing off. But only allowed when all remaining are in home.
        # We'll handle outside with in_home_only.
        return src - d < 0

    # Destination computation given src and die.
    def compute_dest(src, d):
        dest = src - d
        if dest < 0:
            return "OFF"  # bear off
        return dest

    # Check if a move from src with die is legal w.r.t occupancy (ignoring turn/ordering constraints)
    def is_legal_single(src, die, my_pts, opp_pts, my_bar, my_off):
        # must-move-from-bar rule
        if my_bar > 0:
            if src != "B":
                return False

        # determine src index
        if src == "B":
            sidx = reentry_point(die)
            # if reentry point has 2+ opponent checkers -> illegal
            if opp_pts[sidx] >= 2:
                return False
            return True
        else:
            sidx = int(src[1:]) if isinstance(src, str) and src.startswith("A") else int(src)
            if my_pts[sidx] <= 0:
                return False
            # dest
            dest = compute_dest(sidx, die)
            if dest == "OFF":
                # bearing off allowed only if all remaining checkers are in home board.
                if not in_home_only(my_pts, my_bar):
                    return False
                return True
            # normal dest
            if opp_pts[dest] >= 2:
                return False
            return True

    # Apply a single move to update board counts (local simulation)
    def apply_single(src, die, my_pts, opp_pts, my_bar, opp_bar, my_off_local):
        # returns updated (my_pts2, opp_pts2, my_bar2, opp_bar2, my_off2)
        my_pts2 = my_pts[:]
        opp_pts2 = opp_pts[:]
        my_bar2 = my_bar
        opp_bar2 = opp_bar
        my_off2 = my_off_local

        if src == "B":
            sidx = reentry_point(die)
            # remove from bar
            my_bar2 -= 1
        else:
            sidx = int(src[1:]) if isinstance(src, str) and src.startswith("A") else int(src)
        # move checker out of source
        if src != "B":
            my_pts2[sidx] -= 1

        dest = compute_dest(sidx, die) if src != "B" else compute_dest(reentry_point(die), die)  # not used for reentry
        # For reentry, we should NOT subtract again; actually reentry lands on reentry_point.
        if src == "B":
            landed = reentry_point(die)
        else:
            landed = dest

        if landed == "OFF":
            my_off2 += 1
        else:
            # hit?
            if opp_pts2[landed] == 1:
                opp_pts2[landed] = 0
                opp_bar2 += 1
            opp_pts2_landing_before = opp_pts2[landed]
            # place checker
            my_pts2[landed] += 1

        return my_pts2, opp_pts2, my_bar2, opp_bar2, my_off2

    # Generate candidate FROM locations based on must-move-from-bar and available checkers
    def candidate_sources(my_pts, my_bar):
        if my_bar > 0:
            return ["B"]
        # any point with at least one checker
        return [f"A{i}" for i, c in enumerate(my_pts) if c > 0]

    # Enumerate legal move strings for dice.
    # Order constraints:
    # - If two dice exist, we must play both (unless order forces one die illegal? In backgammon rules,
    #   typically you play both dice if possible; if only one die is legal you play it. The prompt says:
    #   If both dice can be played, you must play both. If only one can be played, play higher when possible.
    # We'll implement by enumerating possible first/second moves accordingly.
    #
    # We'll return the best among the legal strings we can construct under these constraints.
    def list_legal_moves_for_order(d1, d2):
        # Returns list of move strings H/L given specific die order: first uses d1 then d2.
        # First-move sources from candidates; second-move sources similarly after applying first.
        legal = []
        first_sources = candidate_sources(my_pts, my_bar)
        # Determine if any first move exists at all with die d1
        any_first = False
        for src1 in first_sources:
            if not is_legal_single(src1, d1, my_pts, opp_pts, my_bar, my_off):
                continue
            any_first = True
            # simulate after first
            m1, o1, mb1, ob1, off1 = apply_single(src1, d1, my_pts, opp_pts, my_bar, opp_bar, my_off)
            # second
            second_sources = ["B"] if mb1 > 0 else [f"A{i}" for i, c in enumerate(m1) if c > 0]
            moved_second = False
            for src2 in second_sources:
                if is_legal_single(src2, d2, m1, o1, mb1, off1):
                    moved_second = True
                    # construct token from src2
                    s1 = src1 if src1 == "B" else src1
                    s2 = src2 if src2 == "B" else src2
                    legal.append((s1, s2))
            if not moved_second:
                # if second die cannot be played, then this overall two-dice sequence might be illegal.
                # We'll allow it only when a two-dice play is impossible globally, handled later.
                pass
        return legal, any_first

    # Since we do not have true full legality generation from engine, we ensure compliance with the
    # prompt rule set by:
    # 1) If two dice: check all plays that use both dice (any legal moves with both).
    #    If none exist, then check legal plays using only one die: prefer higher die.
    # 2) If one die: choose any legal move with that die; engine will require higher if two.
    all_legal_moves = []

    def score_position(my_pts_s, opp_pts_s, my_bar_s, opp_bar_s, my_off_s, opp_off_s):
        # Heuristic:
        # - Strongly reward bearing off
        # - Reward having 2+ checkers on points (safe)
        # - Reward occupying home points (indices 0..5) and advancing progress
        # - Reward capturing (opponent checkers sent to bar) via opp_bar change captured during simulation
        # - Penalize blots: single checker on a point that can be hit by opponent (rough proxy)
        # - Penalize opponent having blots on our potential landing squares? (light)

        s = 0.0
        # bearing off / progress
        s += (my_off_s - my_off) * 50.0
        # home points occupancy
        for i in range(6):
            c = my_pts_s[i]
            if c > 0:
                s += c * 6.0 + (c >= 2) * 10.0
        # made points elsewhere
        for i in range(6, 24):
            c = my_pts_s[i]
            if c >= 2:
                s += 2.0 + (c - 2) * 1.0

        # pip-like approximation: farther points have worse
        # For our mover direction, points 23..0 decreasing: distance to home roughly i.
        for i in range(24):
            c = my_pts_s[i]
            if c > 0:
                s -= c * (i / 24.0) * 2.0  # prefer lower i (towards home)

        # blot penalty and safety proxy
        for i in range(24):
            c = my_pts_s[i]
            if c == 1:
                # danger: if opponent has potential landing onto i.
                # Proxy using opponent stacks: if opponent has checkers that could hit with small die,
                # approximate by checking opp points for a checker that is within 1..6 steps above i.
                danger = 0
                # if opponent has any checker on points j where j - d = i (our landing), opponent could hit us after moving.
                # That requires opponent die d = j - i in 1..6. Opponent moves opposite direction (0->23),
                # so exact geometry is complicated; we use a coarse proxy:
                for d in range(1, 7):
                    j = i + d
                    if 0 <= j < 24 and opp_pts_s[j] > 0:
                        danger += 1
                if danger > 0:
                    s -= 3.0 * danger / 6.0

        # bar checkers penalty (bad to have on bar)
        s -= my_bar_s * 5.0
        # opponent bar reward
        s += opp_bar_s * 3.5

        # avoid helping opponent bear off (small)
        s += (opp_off_s - opp_off_s) * 0.0

        return s

    best_move = "H:P,P"
    best_score = -1e18

    if len(dice) == 0:
        return "H:P,P"

    if len(dice) == 1:
        d1 = dice[0]
        sources = candidate_sources(my_pts, my_bar)
        any_moves = False
        for src1 in sources:
            if is_legal_single(src1, d1, my_pts, opp_pts, my_bar, my_off):
                any_moves = True
                m2, o2, mb2, ob2, off2 = apply_single(src1, d1, my_pts, opp_pts, my_bar, opp_bar, my_off)
                sc = score_position(m2, o2, mb2, ob2, off2, state["opp_off"])
                # encode as using both slots with P for second
                move = f"H:{src1 if src1!='B' else 'B'},P"
                if sc > best_score:
                    best_score = sc
                    best_move = move
        if not any_moves:
            return "H:P,P"
        # Ensure correct order letter: with one die, engine will interpret? We'll provide H and P.
        return best_move

    # two dice
    dA, dB = dice[0], dice[1]
    hi, lo = (dA, dB) if dA >= dB else (dB, dA)

    # Check plays using both dice for either order
    def evaluate_order(first_die, second_die, order_letter):
        nonlocal best_score, best_move
        moved_any = False
        for src1 in candidate_sources(my_pts, my_bar):
            if not is_legal_single(src1, first_die, my_pts, opp_pts, my_bar, my_off):
                continue
            m1, o1, mb1, ob1, off1 = apply_single(src1, first_die, my_pts, opp_pts, my_bar, opp_bar, my_off)
            # second must be legal
            second_sources = ["B"] if mb1 > 0 else [f"A{i}" for i, c in enumerate(m1) if c > 0]
            for src2 in second_sources:
                if is_legal_single(src2, second_die, m1, o1, mb1, off1):
                    moved_any = True
                    m2, o2, mb2, ob2, off2 = apply_single(src2, second_die, m1, o1, mb1, ob1, off1)
                    sc = score_position(m2, o2, mb2, ob2, off2, state["opp_off"])
                    move = f"{order_letter}:{src1 if src1!='B' else 'B'},{src2 if src2!='B' else 'B'}"
                    if sc > best_score:
                        best_score = sc
                        best_move = move
        return moved_any

    any_both = False
    any_both |= evaluate_order(hi, lo, "H")
    any_both |= evaluate_order(lo, hi, "L")  # L means first uses lower die

    if any_both:
        return best_move

    # If cannot play both dice, play only one die.
    # Prefer higher die when possible.
    def evaluate_single_die(d, order_letter_for_first_die):
        nonlocal best_score, best_move
        moved = False
        for src1 in candidate_sources(my_pts, my_bar):
            if is_legal_single(src1, d, my_pts, opp_pts, my_bar, my_off):
                moved = True
                m2, o2, mb2, ob2, off2 = apply_single(src1, d, my_pts, opp_pts, my_bar, opp_bar, my_off)
                sc = score_position(m2, o2, mb2, ob2, off2, state["opp_off"])
                move = f"{order_letter_for_first_die}:{src1 if src1!='B' else 'B'},P"
                if sc > best_score:
                    best_score = sc
                    best_move = move
        return moved

    if evaluate_single_die(hi, "H"):
        return best_move
    if evaluate_single_die(lo, "L"):
        return best_move
    return "H:P,P"
