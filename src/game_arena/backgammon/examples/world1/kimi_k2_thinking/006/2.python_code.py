
import copy

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _copy_state(state):
    """Return a deep copy of the state dict (lists are copied)."""
    return {
        'my_pts': list(state['my_pts']),
        'opp_pts': list(state['opp_pts']),
        'my_bar': state['my_bar'],
        'opp_bar': state['opp_bar'],
        'my_off': state['my_off'],
        'opp_off': state['opp_off'],
        'dice': state['dice']          # never modified, no need to copy
    }

def _possible_starts(state, die):
    """
    Return a list of legal start tokens for the given die.
    Tokens are 'B' (bar) or 'A0'..'A23' (point indices).
    Respects:
        – bar‑first rule,
        – no moving onto a point with ≥2 opponent checkers,
        – bearing‑off rules (only when all checkers are in the home board,
          and then only the highest point < die may be used if no forward move exists).
    """
    # bar has priority
    if state['my_bar'] > 0:
        dest = 24 - die               # entry point for a bar checker
        if 0 <= dest <= 23 and state['opp_pts'][dest] < 2:
            return ['B']
        return []                     # bar move is illegal

    # No checkers on the bar – consider normal points
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']

    # bearing off allowed only when every remaining checker is in the home board
    bearing_off_allowed = (state['my_bar'] == 0 and sum(my_pts[6:]) == 0)

    # collect forward moves (i - die >= 0 and destination not blocked)
    forward_starts = []
    for i in range(24):
        if my_pts[i] > 0:
            dest = i - die
            if dest >= 0 and opp_pts[dest] < 2:
                forward_starts.append('A{}'.format(i))

    if forward_starts:
        return forward_starts           # must play a forward move if any exist

    # No forward move – maybe we can bear off
    if bearing_off_allowed:
        # highest occupied point that is < die
        for i in range(die - 1, -1, -1):
            if my_pts[i] > 0:
                return ['A{}'.format(i)]
    # nothing legal for this die
    return []

def _apply_move(state, start, die):
    """
    Simulate moving a checker from *start* using *die*.
    Returns the new state (a copy).  Assumes the move is legal.
    """
    st = _copy_state(state)

    if start == 'B':                     # moving from the bar
        dest = 24 - die
        st['my_bar'] -= 1
        if st['opp_pts'][dest] == 1:     # hit a blot
            st['opp_pts'][dest] = 0
            st['opp_bar'] += 1
            st['my_pts'][dest] += 1
        else:                            # empty or own checker(s)
            st['my_pts'][dest] += 1

    elif start.startswith('A'):          # moving from a board point
        i = int(start[1:])
        # we are guaranteed my_pts[i] > 0
        st['my_pts'][i] -= 1
        dest = i - die
        if dest >= 0:                    # still on the board
            if st['opp_pts'][dest] == 1: # hit
                st['opp_pts'][dest] = 0
                st['opp_bar'] += 1
                st['my_pts'][dest] += 1
            else:                         # empty or own checkers
                st['my_pts'][dest] += 1
        else:                            # bearing off
            st['my_off'] += 1
            # the checker was already removed from my_pts[i]
    else:
        # start == 'P' – should never be passed to this function
        pass
    return st

def _evaluate(state):
    """
    Heuristic evaluation of *state* from the player’s perspective.
    Higher values are better.
    """
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']

    # pip counts
    my_pip = sum((i + 1) * my_pts[i] for i in range(24)) + state['my_bar'] * 24
    opp_pip = sum((24 - i) * opp_pts[i] for i in range(24)) + state['opp_bar'] * 24

    # home board occupancy
    my_home = sum(my_pts[0:6])
    opp_home = sum(opp_pts[18:24])

    # blots – single checkers outside the home board (more vulnerable)
    my_blot = sum(1 for i in range(6, 24) if my_pts[i] == 1)
    opp_blot = sum(1 for i in range(24) if opp_pts[i] == 1)

    # weights (tuned by quick experimentation)
    w_pip = 1.0
    w_off = 10.0
    w_bar = 5.0
    w_home = 2.0
    w_blot = 1.0

    score = (opp_pip - my_pip) * w_pip + \
            (state['my_off'] - state['opp_off']) * w_off + \
            (state['opp_bar'] - state['my_bar']) * w_bar + \
            (my_home - opp_home) * w_home + \
            (opp_blot - my_blot) * w_blot

    return score

# ----------------------------------------------------------------------
# Public API required by the engine
# ----------------------------------------------------------------------
def policy(state):
    """
    Return a legal move string for the given backgammon state.
    """
    dice = state['dice']
    n_dice = len(dice)

    # ------------------------------------------------------------------
    # 0 dice – nothing to do
    # ------------------------------------------------------------------
    if n_dice == 0:
        return "H:P,P"

    # ------------------------------------------------------------------
    # 1 die – play it if possible, otherwise pass
    # ------------------------------------------------------------------
    if n_dice == 1:
        die = dice[0]
        starts = _possible_starts(state, die)
        if not starts:
            return "H:P,P"
        best = max(starts, key=lambda s: _evaluate(_apply_move(state, s, die)))
        return "H:{},P".format(best)

    # ------------------------------------------------------------------
    # 2 dice – try to use both, otherwise higher die only, otherwise lower,
    # otherwise pass
    # ------------------------------------------------------------------
    d_high = max(dice)
    d_low  = min(dice)

    candidates = []   # (order, start1, start2, final_state)

    # try both orders
    for order in ("H", "L"):
        first_die  = d_high if order == "H" else d_low
        second_die = d_low  if order == "H" else d_high

        first_starts = _possible_starts(state, first_die)
        for s1 in first_starts:
            mid_state = _apply_move(state, s1, first_die)
            second_starts = _possible_starts(mid_state, second_die)
            for s2 in second_starts:
                final_state = _apply_move(mid_state, s2, second_die)
                candidates.append((order, s1, s2, final_state))

    # If we found any way to play both dice we must use one of them
    if candidates:
        best = max(candidates, key=lambda tpl: _evaluate(tpl[3]))
        order, s1, s2, _ = best
        return "{}:{},{}".format(order, s1, s2)

    # Could not play both – try the higher die alone
    high_starts = _possible_starts(state, d_high)
    if high_starts:
        best = max(high_starts, key=lambda s: _evaluate(_apply_move(state, s, d_high)))
        return "H:{},P".format(best)

    # Higher die not possible – try the lower die alone
    low_starts = _possible_starts(state, d_low)
    if low_starts:
        best = max(low_starts, key=lambda s: _evaluate(_apply_move(state, s, d_low)))
        return "L:{},P".format(best)

    # Nothing is playable
    return "H:P,P"
