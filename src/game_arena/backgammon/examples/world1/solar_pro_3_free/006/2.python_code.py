
from typing import List, Dict, Tuple

def policy(state: Dict) -> str:
    """
    Return a legal move string for Backgammon.
    
    The move format is: <ORDER>:<FROM1>,<FROM2>
    <ORDER> is 'H' (higher die first) or 'L' (lower die first).
    <FROM1> and <FROM2> are either 'A<point>', 'B' (Bar), or 'P' (Pass).
    """
    # -----------------------------------------------------------------
    # Basic inputs
    # -----------------------------------------------------------------
    dice: Tuple[int, int] = tuple(state['dice'])
    if len(dice) != 2:
        # Unexpected format – just pass both dice (should never happen)
        return "H:P,P"
    high, low = sorted(dice, reverse=True)  # high die, low die

    my_bar = state['my_bar']
    opp_pts = state['opp_pts']
    my_pts = state['my_pts']

    # -----------------------------------------------------------------
    # Helper to generate up‑to‑three best board sources for a die.
    # -----------------------------------------------------------------
    def best_board_sources(d: int) -> List[Tuple[int, int]]:
        """
        Return a list of candidate source points (and their destinations)
        sorted by priority: hit first, then farther source.
        The list never contains more than three candidates.
        """
        candidates = []
        # Search from the farthest point (23) down to the die value.
        for i in range(23, d - 1, -1):
            if my_pts[i] == 0:
                continue
            dest = i - d
            if dest < 0:
                continue
            if opp_pts[dest] > 1:          # cannot land on a blocked point
                continue
            # Hit priority (opp_pts[dest] == 1)
            hit = opp_pts[dest] == 1
            candidates.append((i, dest, hit))
        # Sort: hit first, then larger source point
        candidates.sort(key=lambda x: (-int(x[2]), -x[0]))
        # Return only the point indices (ignore dest for token building)
        return [(p, d) for p, d, _ in candidates[:3]]

    # -----------------------------------------------------------------
    # Phase 1 – Bar moves (must be done before any board move)
    # -----------------------------------------------------------------
    bar_moves: List[int] = []
    if my_bar > 0:
        for die in dice:
            # die is a legal Bar move iff the destination is open (0 or 1 opponent)
            if opp_pts[die] <= 1:
                bar_moves.append(die)

    # Decide which dice use the bar
    bar_used: List[int] = []
    if high in bar_moves:
        bar_used.append(high)
    if low in bar_moves:
        bar_used.append(low)

    # -----------------------------------------------------------------
    # Phase 2 – Determine the FROM tokens (Bar, Board, or Pass)
    # -----------------------------------------------------------------
    from1 = None   # token for the first dice (order token decides which die)
    from2 = None   # token for the second dice
    order = 'H'    # default: higher die first

    if bar_used:
        # There is at least one bar move – the first token must be from the bar.
        if len(bar_used) == 2:
            # Both dice come from the bar
            from1 = from2 = 'B'
        else:
            # Exactly one bar move – it must be the first token
            if high in bar_used:
                # high die from bar, low die from board/pass
                from1 = 'B'
                # Pick the best source for the low die
                board_opts = best_board_sources(low)
                from2 = 'A' + str(board_opts[0][0]) if board_opts else 'P'
                order = 'H'   # high die first, matches our choice
            else:
                # low die from bar, high die from board/pass
                from2 = 'B'
                board_opts = best_board_sources(high)
                from1 = 'A' + str(board_opts[0][0]) if board_opts else 'P'
                order = 'L'   # low die (the bar move) is first
    else:
        # No bar checkers – both dice come from the board (or pass)
        board_opts_high = best_board_sources(high)
        board_opts_low = best_board_sources(low)

        # Resolve possible conflict when both dice have the same value.
        # If the best board source for the high die is the same point as the low die,
        # we must ensure there are at least two checkers on that point.
        src_high = board_opts_high[0][0] if board_opts_high else None
        src_low = board_opts_low[0][0] if board_opts_low else None

        # If dice are equal and we only have one checker on the chosen point,
        # use the second-best option for the low die.
        if high == low and src_low is not None and src_high == src_low:
            # check the availability on that point
            checkers_on = my_pts[src_low]
            if checkers_on == 1:
                # fallback to second option (if any)
                src_low = board_opts_low[1][0] if len(board_opts_low) > 1 else None

        # Build the tokens
        from1 = 'A' + str(src_high) if src_high is not None else 'P'
        from2 = 'A' + str(src_low) if src_low is not None else 'P'
        order = 'H'   # higher die first

    # In all cases, FROM1 and FROM2 are filled (P is allowed when no move)
    return f"{order}:{from1},{from2}"
