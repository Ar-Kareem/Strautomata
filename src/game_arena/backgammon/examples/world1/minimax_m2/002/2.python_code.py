
def policy(state: dict) -> str:
    import random
    # Short alias for board vectors
    my = state["my_pts"]
    op = state["opp_pts"]
    my_bar = state["my_bar"]
    opp_bar = state["opp_bar"]
    my_off = state["my_off"]
    opp_off = state["opp_off"]
    dice = state["dice"]
    if not dice:
        return "H:P,P"
    dice = list(sorted(dice, reverse=True))  # [high, low]
    high, low = dice[0], dice[1] if len(dice) == 2 else None

    def home(i):
        return 0 <= i <= 5

    def count_my():
        return my_off + sum(my) + my_bar

    def total_my_checkers():
        return my_off + sum(my) + my_bar

    def my_outstanding():
        return 15 - my_off

    def can_enter_from_bar(die):
        dst = 24 - die
        if not home(dst):
            return False
        if op[dst] >= 2:
            return False
        return True

    # Generate legal move sequences for a single die
    def moves_for_die(die, s_my, s_op, s_my_bar):
        moves = []
        # Must enter from bar first if any
        if s_my_bar > 0:
            dst = 24 - die
            if home(dst) and s_op[dst] <= 1:
                moves.append(("B", dst))
            return moves
        # Bearing off
        if all(home(j) for j in range(24) if s_my[j] > 0):
            # Only consider bearing off when all checkers are home
            # Find the highest occupied point
            highest = -1
            for j in range(23, -1, -1):
                if s_my[j] > 0:
                    highest = j
                    break
            if highest != -1:
                need = highest + 1
                if die >= need:
                    # Bearing off is legal from 'highest'
                    moves.append((highest, None))  # (from, None) => bear off
                    # Additional subtlety: if die > need, you can also bear off from lower point
                    # Engine will compute destination; we only need to return a legal FROM
                    # Additional from-points that also allow bearing off for this die:
                    for j in range(highest - 1, -1, -1):
                        if s_my[j] > 0:
                            needj = j + 1
                            if die > needj:
                                moves.append((j, None))
                # Note: we return all legal FROMs for bearing off
        # Regular point moves (cannot land on a point with 2+ opponent checkers)
        for i in range(24):
            if s_my[i] > 0:
                dst = i - die
                if dst < 0:
                    continue
                if s_op[dst] <= 1:
                    moves.append((i, dst))
        return moves

    # Apply one move to a snapshot state
    def apply_move(move, s_my, s_op, s_my_bar):
        frm, dst = move
        ns_my = list(s_my)
        ns_op = list(s_op)
        ns_my_bar = s_my_bar
        if frm == "B":
            ns_my_bar -= 1
            dst_idx = 24 - (high if len(dice) == 2 and dice[0] == high else dice[0])
            # Actually, this function is used generically; we need the die it was called with.
            # We will wrap apply_move with die later, so avoid this branch complexity.
        # We'll instead pass die explicitly in a wrapper

    # Helper to generate all legal action strings for the current state
    def generate_all_actions():
        actions = []
        # Ensure dice is sorted [high, low]
        dice_sorted = sorted(state["dice"], reverse=True)
        hi, lo = dice_sorted[0], dice_sorted[1] if len(dice_sorted) == 2 else None
        both_playable = False
        # Generate sequences for both orders
        for order in ("H", "L"):
            d1 = hi if order == "H" else lo
            d2 = lo if order == "H" else hi
            # Build list of legal first moves
            first_moves = moves_for_die(d1, my, op, my_bar)
            if not first_moves:
                continue
            # For each first move, apply, then compute legal second moves
            for f_from, f_to in first_moves:
                # Snapshot for first move
                ns_my = list(my)
                ns_op = list(op)
                ns_my_bar = my_bar
                # Execute first move
                # Handle from bar
                if f_from == "B":
                    ns_my_bar -= 1
                    dst1 = 24 - d1
                    if ns_op[dst1] == 1:
                        ns_op[dst1] = 0
                        # Opponent checker goes to bar, but we don't model opponent's bar for scoring
                    ns_my[dst1] += 1
                else:
                    # From a point
                    ns_my[f_from] -= 1
                    if f_to is None:
                        # Bearing off
                        pass
                    else:
                        # Move to f_to
                        if ns_op[f_to] == 1:
                            ns_op[f_to] = 0
                        ns_my[f_to] += 1
                # Determine second moves
                second_moves = []
                # If we can use both dice now, generate second move
                # Note: we assume no double dice here; if doubles, engine still passes two dice and expects two moves (up to 4).
                # For simplicity with doubles, we will still generate up to two moves.
                second_moves = moves_for_die(d2, ns_my, ns_op, ns_my_bar)
                if second_moves:
                    # There is at least one legal second move
                    both_playable = True
                    for s_from, s_to in second_moves:
                        # Choose the first from for the string; second from also needs to be resolved
                        # We only need to output FROMs; order matters only for H/L string.
                        # We will use the chosen s_from as the second FROM.
                        # For bearing-off second move, we include FROM and 'P' is not needed because we have a FROM.
                        # If second move can bear off, s_to is None, which is fine.
                        actions.append((order, f_from, s_from))
                else:
                    # Only one die can be played for this order
                    actions.append((order, f_from, "P"))
        # Deduplicate actions by (order, from1, from2)
        seen = set()
        uniq = []
        for a in actions:
            if a not in seen:
                seen.add(a)
                uniq.append(a)
        return uniq, both_playable

    actions, both_playable = generate_all_actions()

    # If no actions, full pass
    if not actions:
        return "H:P,P"

    # If only one die can be played overall, choose higher die when possible
    if not both_playable:
        # Prefer actions that start with the higher die
        dice_sorted = sorted(state["dice"], reverse=True)
        hi, lo = dice_sorted[0], dice_sorted[1] if len(dice_sorted) == 2 else None
        hi_actions = [a for a in actions if (a[0] == "H")]
        if hi_actions:
            chosen = random.choice(hi_actions)
        else:
            # Fallback to whatever is available
            chosen = random.choice(actions)
        order, f1, f2 = chosen
        return f"{order}:{f1},{f2}"

    # Evaluate and pick best action
    # Precompute some aggregates
    my_total = total_my_checkers()
    my_home_pts = sum(my[i] for i in range(6))
    opp_home_pts = sum(op[i] for i in range(6))
    opp_home_hits = sum(1 for i in range(6) if op[i] == 1)

    # Heuristic scoring for an action (higher is better)
    def action_score(order, from1, from2):
        score = 0.0
        # Use dice according to order
        d1 = (high if order == "H" else low)
        d2 = (low if order == "H" else high)
        # Simulate move to compute derived features
        s_my = list(my)
        s_op = list(op)
        s_my_bar = my_bar
        # First move
        if from1 == "B":
            s_my_bar -= 1
            dst1 = 24 - d1
            if s_op[dst1] == 1:
                # hit opponent blot
                score += 25 + (5 if home(dst1) else 0)
                s_op[dst1] = 0
            s_my[dst1] += 1
        else:
            s_my[from1] -= 1
            dst1 = from1 - d1
            if dst1 < 0:
                # bearing off
                score += 120.0
            else:
                if s_op[dst1] == 1:
                    score += 22 + (5 if home(dst1) else 0)
                    s_op[dst1] = 0
                s_my[dst1] += 1
                # Progress: how far advanced toward home
                if home(dst1):
                    score += 8.0 + (5 if home(dst1) and dst1 <= 2 else 0)
                else:
                    score += 2.0
                # Build a builder if landing on a friendly point
                if s_my[dst1] >= 2:
                    score += 3.0
        # Second move
        if from2 == "P":
            # Could not play second die => heavy penalty
            score -= 40.0
        else:
            if from2 == "B":
                s_my_bar -= 1
                dst2 = 24 - d2
                if s_op[dst2] == 1:
                    score += 25 + (5 if home(dst2) else 0)
                    s_op[dst2] = 0
                s_my[dst2] += 1
            else:
                s_my[from2] -= 1
                dst2 = from2 - d2
                if dst2 < 0:
                    score += 120.0  # bearing off second checker
                else:
                    if s_op[dst2] == 1:
                        score += 22 + (5 if home(dst2) else 0)
                        s_op[dst2] = 0
                    s_my[dst2] += 1
                    if home(dst2):
                        score += 8.0 + (5 if home(dst2) and dst2 <= 2 else 0)
                    else:
                        score += 2.0
                    if s_my[dst2] >= 2:
                        score += 3.0
        # Race progress: checkers in home board
        final_home = sum(s_my[i] for i in range(6)) + s_my_bar
        score += final_home * 1.0
        # Safety: penalize leaving blots in range of opponent's high dice
        if my_total >= 7:
            max_die = max(state["dice"])
            # If you leave a blot on a point that opponent can reach with max_die, penalize
            for i in range(24):
                if s_my[i] == 1:
                    for dst in (i + max_die, i - max_die):
                        if 0 <= dst < 24:
                            if op[dst] >= 2:
                                score -= 6.0
                            elif op[dst] == 1:
                                score -= 3.0
        # Small randomness to break ties
        score += random.random() * 0.01
        return score

    best_score = -1e18
    best_actions = []
    for act in actions:
        s = action_score(*act)
        if s > best_score + 1e-9:
            best_score = s
            best_actions = [act]
        elif abs(s - best_score) <= 1e-9:
            best_actions.append(act)
    chosen = random.choice(best_actions)
    order, f1, f2 = chosen
    return f"{order}:{f1},{f2}"
