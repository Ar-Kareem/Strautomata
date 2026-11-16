
def policy(state: dict) -> str:
    """
    Return a legal backgammon move string for the given state.
    The move follows the arena ordering: <ORDER>:<FROM1>,<FROM2>
    where ORDER = H (higher die first) or L (lower die first).
    """
    dice = state.get('dice', [])
    if not dice:
        # No dice – must pass both
        return "H:P,P"

    # Unpack point lists
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    total_my = sum(my_pts)
    my_bar = state['my_bar']

    # Token placeholders for the two dice (higher die first)
    tokens = ['P', 'P']

    # ------------------------------------------------------------------
    # 1️⃣ Bar re‑entry (must be done before any other move)
    # ------------------------------------------------------------------
    # Helper that tries a bar move for a given die value
    def try_bar(die_value: int):
        nonlocal my_bar
        if my_bar > 0:
            target = die_value
            if target < len(opp_pts) and opp_pts[target] <= 1:
                # bar re‑entry succeeds
                my_bar -= 1
                opp_pts[target] -= 1          # remove opponent if it was a hit
                return 'B'
        return None

    # Process the higher die
    token0 = try_bar(dice[0])
    if token0 is not None:
        tokens[0] = token0
    else:
        tokens[0] = 'P'

    # Process the lower die
    token1 = try_bar(dice[1])
    if token1 is not None:
        tokens[1] = token1
    else:
        tokens[1] = 'P'

    # After the bar phase we cannot move other checkers if any bar checker
    # remains that could not be re‑entered (the arena rule forces a pass for
    # those dice). Thus non‑bar moves are allowed only when `my_bar == 0`.

    # ------------------------------------------------------------------
    # Helper to find a non‑bar move for a single die
    # ------------------------------------------------------------------
    def find_non_bar_move(die: int) -> str | None:
        """Return a source token (e.g. 'A12') if a legal move exists, else None."""
        total = sum(my_pts)
        if total == sum(my_pts[:6]):                     # all checkers in home board
            src = die - 1                               # bearing‑off point (A0..A5)
            if 0 <= src < len(my_pts) and my_pts[src] > 0:
                token = f"A{src}"
                my_pts[src] -= 1                        # remove the checker
                return token

        # 2️⃣ Try a hit first (target has exactly one opponent)
        hits = []
        for src in reversed(range(len(my_pts))):
            if my_pts[src] == 0:
                continue
            target = src - die
            if target < 0:
                continue
            if opp_pts[target] == 1:                    # hit possible
                hits.append(src)
        if hits:
            src = max(hits)                            # farthest source possible
            token = f"A{src}"
            my_pts[src] -= 1
            opp_pts[target] -= 1                       # remove opponent
            return token

        # 3️⃣ Any legal move onto an empty or single‑own point
        for src in reversed(range(len(my_pts))):
            if my_pts[src] == 0:
                continue
            target = src - die
            if target < 0:
                continue
            # The engine forbids landing on a point with >=2 of its own checkers
            if opp_pts[target] > 1:
                continue
            if my_pts[target] > 1:
                continue
            # legal move found
            token = f"A{src}"
            my_pts[src] -= 1
            if opp_pts[target] == 1:
                opp_pts[target] -= 1                 # hit (already filtered above)
            return token
        return None

    # ------------------------------------------------------------------
    # 4️⃣ Apply non‑bar moves where allowed (my_bar == 0)
    # ------------------------------------------------------------------
    if my_bar == 0:
        for idx, die_val in enumerate(dice):
            if tokens[idx] == 'P':
                token = find_non_bar_move(die_val)
                if token:
                    tokens[idx] = token

    # ------------------------------------------------------------------
    # 5️⃣ Determine the ORDER character
    # ------------------------------------------------------------------
    if tokens[0] != 'P':
        order = 'H'
    elif tokens[1] != 'P':
        order = 'L'
    else:
        order = 'H'          # both dice are passed

    # ------------------------------------------------------------------
    # 6️⃣ Build the final move string
    # ------------------------------------------------------------------
    return f"{order}:{tokens[0]},{tokens[1]}"
