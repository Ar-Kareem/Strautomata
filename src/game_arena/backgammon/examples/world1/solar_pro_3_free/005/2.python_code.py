
import copy
from typing import List, Dict

# Helper: convert token string to index (e.g. "A7" -> 7)
def token_to_pt(tok: str) -> int:
    if tok == "B":
        return None                # special case for bar
    elif tok == "P":
        return None                # no source
    else:
        return int(tok[1:])        # "A<n>" -> n

# Heuristic: pip count for a player (distance to bear off)
def pip_count(pts: List[int], is_self: bool) -> int:
    # For ourselves, distance = point index
    # For the opponent, distance = (23 - point index)
    if is_self:
        return sum(p * cnt for p, cnt in enumerate(pts) if cnt > 0)
    else:
        return sum((23 - p) * cnt for p, cnt in enumerate(pts) if cnt > 0)

# Apply a single move to a state, given order H/L
def apply_move(state: Dict,
               src: str,
               die: int) -> Dict:
    """
    Return a new state after moving one checker according to src and die.
    Raises ValueError if the move is illegal.
    """
    pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']

    # --- FROM BAR -------------------------------------------------
    if src == "B":
        if my_bar == 0:
            raise ValueError("No checker on the bar")
        # Destination must be exactly the die value (must be ≤5)
        dest = die
        if die > 5:
            raise ValueError("Cannot re‑enter beyond home board")
        if opp_pts[dest] >= 2:
            raise ValueError("Point occupied by two opponents")
        # Perform the re‑entry
        new_state = copy.deepcopy(state)
        new_state['my_bar'] -= 1
        if opp_pts[dest] == 0:
            new_state['opp_pts'][dest] += 1
        else:  # exactly one opponent
            new_state['opp_pts'][dest] = 0
            new_state['opp_bar'] += 1
        return new_state

    # --- FROM BOARD -----------------------------------------------
    pt = token_to_pt(src)
    if pt is None:
        raise ValueError("Invalid source token")

    # Need at least one checker on the source point
    if pts[pt] == 0:
        raise ValueError("No checker on source point")

    # Compute destination
    if pt - die >= 0:               # regular move
        dest = pt - die
    else:                          # bearing off (only allowed in home board)
        # Check if we are allowed to bear off now
        if die > 5 or any(cnt > 0 for i, cnt in enumerate(pts) if i > 5):
            raise ValueError("Cannot bear off from current position")
        dest = -pt                    # negative means off the board

    # Destination legality
    if dest >= 0 and opp_pts[dest] >= 2:
        raise ValueError("Cannot land on a point occupied by two opponents")

    # Perform the move
    new_state = copy.deepcopy(state)
    # update home board pips
    if dest >= 0:
        if opp_pts[dest] == 0:
            new_state['opp_pts'][dest] += 1
        else:  # exactly one opponent – a hit!
            new_state['opp_pts'][dest] = 0
            new_state['opp_bar'] += 1
    else:  # bearing off
        new_state['my_off'] += 1
    new_state['my_pts'][pt] -= 1
    return new_state

# Return a list of legal source tokens (including a forced pass if none)
def board_candidates(state: Dict,
                    die: int) -> List[str]:
    pts = state['my_pts']
    opp_pts = state['opp_pts']
    result = []
    # All checkers must be in home board for a bearing‑off move
    all_home = all(cnt == 0 or i <= 5 for i, cnt in enumerate(pts) if cnt > 0)

    for src_pt in range(24):
        cnt = pts[src_pt]
        if cnt == 0:
            continue
        # Compute destination for this die
        if src_pt - die >= 0:
            dest = src_pt - die
        else:
            if not all_home or src_pt > die:
                continue            # illegal bearing off
            dest = -src_pt          # off board
        if dest >= 0 and opp_pts[dest] >= 2:
            continue                # blocked
        # src token is legal
        result.append(f"A{src_pt}")
    # If nothing, pass
    if not result:
        return ["P"]
    return result

def evaluate_pair(state: Dict,
                  src_h: str,
                  src_l: str,
                  order: str) -> int:
    """
    Simulate the two‑move sequence and return the total pip reduction
    (our pips + opponent hit bonus). Positive values are good.
    """
    # Apply moves in the order dictated by the flag
    if order == "H":
        seq = [src_h, src_l]
        dice_seq = state['dice']
    else:   # order == "L"
        seq = [src_l, src_h]
        dice_seq = list(reversed(state['dice']))  # low die first

    try:
        # Apply first move
        s1 = apply_move(state, seq[0], dice_seq[0])
        # Apply second move (if source is still valid)
        s2 = apply_move(s1, seq[1], dice_seq[1])
    except ValueError:
        return -1e9                     # illegal, treat as terrible

    # Compute pip differences
    my_initial = pip_count(state['my_pts'], True)
    opp_initial = pip_count(state['opp_pts'], False)
    my_new = pip_count(s2['my_pts'], True)
    opp_new = pip_count(s2['opp_pts'], False)

    # Total reduction
    total = (my_initial - my_new) + (opp_initial - opp_new)
    return total

def policy(state: Dict) -> str:
    dice = sorted(state['dice'])
    high = dice[0]
    low = dice[1]

    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']

    # -------------------------------------------------
    # Determine bar‑entry feasibility
    bar_eligible = []
    for d in dice:
        if d <= 5 and opp_pts[d] <= 1:   # point d is empty or has a single opponent
            bar_eligible.append(d)
    # -------------------------------------------------
    # Case 1: We have checkers on the bar
    if my_bar > 0:
        bar_len = len(bar_eligible)
        if bar_len == 2:                  # both dice can re‑enter
            # Must move both from bar; order H is fine (both first)
            return "H:B,B"
        elif bar_len == 1:                # exactly one bar move required
            eligible_die = bar_eligible[0]
            # The bar move must be the *first* move
            order = "H" if eligible_die == high else "L"
            other_die = low if eligible_die == high else high
            other_srcs = board_candidates(state, other_die)

            # If there are board moves, evaluate them; otherwise force a pass
            best_val = -1e9
            best_src = None
            for src in other_srcs:
                val = evaluate_pair(state, "B", src, order)
                if val > best_val:
                    best_val = val
                    best_src = src
            # If no board move, we must pass the remaining die
            if best_src is None:
                # Second token is forced pass
                return f"{order}:B,P"
            else:
                return f"{order}:B,{best_src}"
        else:                             # bar entry not possible for either die
            # Must pass both dice
            return "H:P,P"

    # -------------------------------------------------
    # No checkers on the bar – normal board moves
    # Build candidate lists for each die (including forced pass)
    cand_high = board_candidates(state, high)
    cand_low  = board_candidates(state, low)

    # Ensure each list has at least one entry (pass if none)
    if not cand_high:
        cand_high = ["P"]
    if not cand_low:
        cand_low = ["P"]

    best_val = -1e9
    best_move = None   # (src_h, src_l, order)

    # Enumerate all legal pairings respecting checker availability
    for src_h in cand_high:
        for src_l in cand_low:
            # Helper to get point index
            def pt(tok):
                return token_to_pt(tok)

            # Check resource constraints
            if src_h != "P" and src_l != "P":
                p_h = pt(src_h)
                p_l = pt(src_l)
                if src_h == src_l and my_pts[p_h] < 2:
                    continue                     # not enough checkers at same point
                if src_h != src_l and (my_pts[p_h] < 1 or my_pts[p_l] < 1):
                    continue                     # insufficient checkers

            # Evaluate both orders
            val_h = evaluate_pair(state, src_h, src_l, "H")
            val_l = evaluate_pair(state, src_l, src_h, "L")
            if val_h > best_val:
                best_val = val_h
                best_move = (src_h, src_l, "H")
            if val_l > best_val:
                best_val = val_l
                best_move = (src_l, src_h, "L")

    # best_move is guaranteed to be set because we added passes
    src1, src2, order = best_move
    return f"{order}:{src1},{src2}"
