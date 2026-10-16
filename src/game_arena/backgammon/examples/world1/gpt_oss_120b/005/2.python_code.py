
def policy(state: dict) -> str:
    """
    Return a legal Backgammon move string for the given state.
    The move respects all mandatory‑move rules and prefers hits,
    bearing off and advancing the furthest checker.
    """

    my_pts = state["my_pts"]
    opp_pts = state["opp_pts"]
    my_bar = state["my_bar"]
    dice = state["dice"]

    # No dice -> pass
    if not dice:
        return "H:P,P"

    # Sort dice: high first, low last
    dice_sorted = sorted(dice, reverse=True)
    high = dice_sorted[0]
    low = dice_sorted[-1] if len(dice_sorted) > 1 else dice_sorted[0]

    # Are we allowed to bear off?
    home_ready = sum(my_pts[6:]) == 0

    # ------------------------------------------------------------------
    # Helper: destination index for a start point and a die
    # ------------------------------------------------------------------
    def dest_from(start: str, die: int) -> int:
        if start == "B":                 # from the bar
            return 24 - die
        else:                            # absolute point A<i>
            i = int(start[1:])
            return i - die

    # ------------------------------------------------------------------
    # Gather all legal starts for a given die
    # ------------------------------------------------------------------
    def possible_starts(die: int):
        starts = []

        # Bar must be cleared first
        if my_bar > 0:
            dest = 24 - die
            if opp_pts[dest] < 2:          # entry point not blocked
                starts.append("B")
            return starts                  # no other moves allowed while on the bar

        # Normal board moves
        for i, cnt in enumerate(my_pts):
            if cnt == 0:
                continue
            dest = i - die
            if dest >= 0:
                if opp_pts[dest] < 2:      # not blocked
                    starts.append(f"A{i}")
            else:                           # bearing off attempt
                if home_ready and i <= 5:  # exact bear‑off allowed
                    starts.append(f"A{i}")
        return starts

    # ------------------------------------------------------------------
    # Scoring function – higher is better
    #   hit   : +2
    #   bear‑off : +1
    #   advance furthest : tiny bonus based on point index
    # ------------------------------------------------------------------
    def score_start(start: str, die: int) -> float:
        dest = dest_from(start, die)
        s = 0.0
        if dest >= 0:
            if opp_pts[dest] == 1:          # hit a blot
                s += 2.0
        else:
            s += 1.0                         # bear‑off
        if start != "B":                     # prefer higher points (closer to home)
            idx = int(start[1:])
            s += (23 - idx) / 1000.0
        return s

    # ------------------------------------------------------------------
    # Choose the best start from a list according to the scoring function
    # ------------------------------------------------------------------
    def best_start(candidates, die):
        if not candidates:
            return None
        best = max(candidates, key=lambda st: score_start(st, die))
        return best

    # ------------------------------------------------------------------
    # BAR handling (must move from bar before anything else)
    # ------------------------------------------------------------------
    if my_bar > 0:
        high_st = possible_starts(high)
        low_st = possible_starts(low) if low != high else high_st

        # Both dice can be played from the bar
        if high_st and low_st:
            hs = best_start(high_st, high)
            ls = best_start(low_st, low)
            return f"H:{hs},{ls}"

        # Only one die can be played from the bar
        if high_st:
            return f"H:{best_start(high_st, high)},P"
        if low_st:
            return f"L:{best_start(low_st, low)},P"

        # No legal entry -> pass
        return "H:P,P"

    # ------------------------------------------------------------------
    # Normal board (no checkers on the bar)
    # ------------------------------------------------------------------
    high_st = possible_starts(high)
    low_st = possible_starts(low) if low != high else high_st

    # Both dice usable
    if high_st and low_st:
        hs = best_start(high_st, high)
        ls = best_start(low_st, low)
        return f"H:{hs},{ls}"

    # Only one die usable – must use the higher die if possible
    if high_st:
        return f"H:{best_start(high_st, high)},P"
    if low_st:
        return f"L:{best_start(low_st, low)},P"

    # No move possible at all
    return "H:P,P"
