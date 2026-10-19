
def policy(state: dict) -> str:
    """
    Choose a legal backgammon move for the current player.

    Parameters
    ----------
    state : dict
        The game state with keys:
        - 'my_pts'   : list of 24 integers (checkers on each point 0‑23)
        - 'opp_pts'  : list of 24 integers (opponent checkers)
        - 'my_bar'   : number of my checkers on the bar
        - 'dice'     : list of 0‑2 integers in 1‑6 (current roll)

    Returns
    -------
    str
        A move string in the form <ORDER>:<FROM1>,<FROM2>.
        ORDER is 'H' (higher die first) or 'L' (lower die first).
        FROM tokens are absolute point identifiers:
            'B'      – from the bar,
            'A{i}'   – from absolute point i,
            'P'      – pass.
    """

    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = state.get('dice', [])               # may be empty (both dice passed)

    # --------------------------------------------------------------------
    # Helper: evaluate possible point moves for a given die value.
    # --------------------------------------------------------------------
    def evaluate_point(die):
        """Return (score, source_index) for the best legal move with `die`.
        If no legal move exists, return (None, None)."""
        best_score = None
        best_source = None
        # Scan points from furthest to nearest – higher points are preferred.
        for src in range(23, -1, -1):
            if my_pts[src] == 0:
                continue
            target = src - die
            if target < 0:               # cannot move past the board
                continue
            if opp_pts[target] >= 2:     # blocked by two or more opponent
                continue
            # Compute a simple scoring function
            score = die
            if opp_pts[target] == 1:     # hitting a blot
                score += 5
            if target == 0:              # moving onto the home board
                score += 10
            # Small extra reward for moving from a point that holds many checkers
            score += my_pts[src]
            # Keep the best move, breaking ties by higher source point (already scanned)
            if best_score is None or score > best_score:
                best_score, best_source = score, src
        return best_score, best_source

    # --------------------------------------------------------------------
    # Helper: determine the order token based on which die(s) are actually used.
    # --------------------------------------------------------------------
    def decide_order(tokens):
        """tokens is a list of the two FROM tokens (length 2).
        Returns 'H' or 'L'."""
        # If the first token is a bar move we used the higher die for it → H
        if tokens[0] == 'B':
            return 'H'
        # Otherwise, if the second token is a bar move we used the lower die first → L
        if tokens[1] == 'B':
            return 'L'
        # First token is a point move (or pass) and the higher die was usable → H
        # Otherwise (first token is pass, second is point) the lower die is first → L
        if tokens[0] == 'P':
            return 'L' if tokens[1] != 'P' else 'H'
        return 'H'

    # --------------------------------------------------------------------
    # 1. If we have checkers on the bar, re‑enter them first.
    # --------------------------------------------------------------------
    if my_bar > 0:
        ordered = []               # two slots for this turn
        used = set()               # dice that have already been used for bar
        # Process dice in descending order (higher die first)
        sorted_dice = sorted(dice, reverse=True)   # works for 0,1,2 dice
        for d in sorted_dice:
            if opp_pts[d] < 2 and my_bar > 0:      # legal re‑entry
                ordered.append('B')
                my_bar -= 1
                used.add(d)
            else:
                # cannot re‑enter this die – it will be a pass
                ordered.append('P')
                used.add(d)

        # At this point `ordered` already contains exactly two tokens (B or P)
        order = decide_order(ordered)
        return f"{order}:{ordered[0]},{ordered[1]}"

    # --------------------------------------------------------------------
    # 2. No bar checkers – move from points (or pass) respecting dice order.
    # --------------------------------------------------------------------
    ordered = []

    # Helper to fetch a token for a given die (higher die first)
    def get_move(d):
        """Return source token for die `d`."""
        best_score, src = evaluate_point(d)
        if best_score is None:          # no legal point move
            return 'P'
        # Encode the source point
        return f"A{src}"

    # Process the dice in order (higher die first)
    sorted_dice = sorted(dice, reverse=True)   # works for single‑die case too
    for d in sorted_dice:
        src_token = get_move(d)
        ordered.append(src_token)

    # --------------------------------------------------------------------
    # 3. Build final move string.
    # --------------------------------------------------------------------
    # If the higher die had no move and the lower die did, we must use L.
    order = 'H'
    if ordered[0] == 'P' and ordered[1] != 'P':
        order = 'L'

    return f"{order}:{ordered[0]},{ordered[1]}"
