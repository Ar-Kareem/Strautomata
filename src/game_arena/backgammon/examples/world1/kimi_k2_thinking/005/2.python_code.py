
import copy

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _copy_state(state):
    """Return a deep copy of the state dict."""
    return {
        'my_pts': state['my_pts'][:],
        'opp_pts': state['opp_pts'][:],
        'my_bar': state['my_bar'],
        'opp_bar': state['opp_bar'],
        'my_off': state['my_off'],
        'opp_off': state['opp_off'],
        'dice': state['dice'][:]  # not used after move generation, but keep for completeness
    }

def _all_in_home_board(state):
    """True iff every own checker is in the home board (points 0‑5)."""
    if state['my_bar']:
        return False
    for i in range(6, 24):
        if state['my_pts'][i]:
            return False
    return True

def _pip_counts(state):
    """Return (my_pip, opp_pip).  Bar checkers count as 25 pips."""
    my_pip = sum((i + 1) * state['my_pts'][i] for i in range(24))
    my_pip += state['my_bar'] * 25
    opp_pip = sum((24 - i) * state['opp_pts'][i] for i in range(24))
    opp_pip += state['opp_bar'] * 25
    return my_pip, opp_pip

def _evaluate(state):
    """Heuristic evaluation: larger is better for the player to move."""
    my_pip, opp_pip = _pip_counts(state)

    my_made = sum(1 for i in range(24) if state['my_pts'][i] >= 2)
    opp_made = sum(1 for i in range(24) if state['opp_pts'][i] >= 2)

    my_blots = sum(1 for i in range(24) if state['my_pts'][i] == 1)
    opp_blots = sum(1 for i in range(24) if state['opp_pts'][i] == 1)

    # Weights (tuned by light experimentation)
    w_pip = 1
    w_off = 50
    w_bar = 20
    w_made = 5
    w_blot = 10

    score = (opp_pip - my_pip) * w_pip
    score += (state['my_off'] - state['opp_off']) * w_off
    score += (state['opp_bar'] - state['my_bar']) * w_bar
    score += (my_made - opp_made) * w_made
    score += (opp_blots - my_blots) * w_blot
    return score

def _token(start):
    """Convert a start descriptor (int or 'B') to the move token string."""
    if start == 'B':
        return 'B'
    return f'A{start}'

def _possible_starts(state, die):
    """
    Return a list of start descriptors (int or 'B') that are legal for the
    given die in the current state.  If the bar is non‑empty, only bar‑entry
    moves are returned (or an empty list when the bar move is illegal).
    """
    # bar rule
    if state['my_bar'] > 0:
        dest = 24 - die          # entry point for the opponent's home board
        if state['opp_pts'][dest] >= 2:
            return []            # blocked – cannot use this die
        return ['B']             # must move a checker from the bar

    # normal moves (including bearing‑off when allowed)
    starts = []
    can_bearoff = _all_in_home_board(state)
    for i in range(24):
        if state['my_pts'][i] == 0:
            continue
        dest = i - die
        if dest >= 0:
            # ordinary forward move
            if state['opp_pts'][dest] <= 1:   # 0 or 1 opponent checker
                starts.append(i)
        else:
            # try to bear off
            if can_bearoff:
                starts.append(i)
    return starts

def _apply_single(state, start, die):
    """
    Apply a single checker move (start -> destination) and return the new state.
    Raises ValueError if the move is illegal.
    """
    state = _copy_state(state)
    if start == 'B':
        # move from the bar onto opponent's home board
        dest = 24 - die
        if state['opp_pts'][dest] >= 2:
            raise ValueError("Bar move blocked")
        if state['my_bar'] == 0:
            raise ValueError("No checker on the bar")
        state['my_bar'] -= 1
        # handle a hit
        if state['opp_pts'][dest] == 1:
            state['opp_bar'] += 1
            state['opp_pts'][dest] = 0
        state['my_pts'][dest] += 1
        return state

    # start is a point index
    i = start
    if state['my_pts'][i] == 0:
        raise ValueError("No own checker on start point")
    dest = i - die
    if dest >= 0:
        # normal move
        if state['opp_pts'][dest] >= 2:
            raise ValueError("Destination blocked")
        state['my_pts'][i] -= 1
        if state['opp_pts'][dest] == 1:
            state['opp_bar'] += 1
            state['opp_pts'][dest] = 0
        state['my_pts'][dest] += 1
        return state
    else:
        # bearing off
        if not _all_in_home_board(state):
            raise ValueError("Bearing off not allowed")
        state['my_pts'][i] -= 1
        state['my_off'] += 1
        return state

def _apply_move(state, move_str):
    """
    Apply a full move string (e.g. "H:A0,A18") to a state and return the resulting state.
    """
    parts = move_str.split(':')
    order = parts[0]
    tokens = parts[1].split(',')
    if len(tokens) != 2:
        raise ValueError("Invalid move format")
    tok1, tok2 = tokens

    dice = state['dice']
    if len(dice) == 0:
        # no dice – nothing changes
        return state
    if len(dice) == 1:
        d0 = dice[0]
        d_low, d_high = d0, d0
    else:
        d_low, d_high = sorted(dice)

    # determine which die corresponds to which token
    if order == 'H':
        first_die, second_die = d_high, d_low
    elif order == 'L':
        first_die, second_die = d_low, d_high
    else:
        raise ValueError("Invalid order token")

    # helper to parse a token into start descriptor
    def _parse(tok):
        if tok == 'P':
            return None          # pass
        if tok == 'B':
            return 'B'
        if tok.startswith('A'):
            return int(tok[1:])
        raise ValueError("Invalid start token")

    # apply first move
    s1 = _parse(tok1)
    state1 = _apply_single(state, s1, first_die) if s1 is not None else _copy_state(state)

    # apply second move
    s2 = _parse(tok2)
    state2 = _apply_single(state1, s2, second_die) if s2 is not None else _copy_state(state1)

    return state2

def _generate_all_moves(state):
    """
    Return a list of all legal move strings for the given state.
    """
    moves = []
    dice = state['dice']
    if len(dice) == 0:
        moves.append("H:P,P")
        return moves

    if len(dice) == 1:
        d = dice[0]
        # possible start points for this single die
        starts = _possible_starts(state, d)
        if not starts:
            moves.append("H:P,P")
        else:
            for s in starts:
                moves.append(f"H:{_token(s)},P")
        return moves

    # len(dice) == 2
    d_low, d_high = sorted(dice)
    # try both orderings
    for order, first_die, second_die in [('H', d_high, d_low), ('L', d_low, d_high)]:
        # iterate over all possible first starts
        first_starts = _possible_starts(state, first_die)
        found_two_die_move = False
        for s1 in first_starts:
            try:
                state1 = _apply_single(state, s1, first_die)
            except ValueError:
                continue
            # possible second starts in the intermediate state
            second_starts = _possible_starts(state1, second_die)
            for s2 in second_starts:
                try:
                    _ = _apply_single(state1, s2, second_die)
                except ValueError:
                    continue
                # legal two‑move sequence
                moves.append(f"{order}:{_token(s1)},{_token(s2)}")
                found_two_die_move = True
        # if we found at least one two‑die move for this ordering we must not consider
        # one‑die moves for this ordering (the rules force us to play both dice).
        # If none were found, we may have to play a single die (the higher one).
        if not found_two_die_move:
            # try to play only the higher die
            higher_starts = _possible_starts(state, d_high)
            if higher_starts:
                for s in higher_starts:
                    moves.append(f"H:{_token(s)},P")
            else:
                # cannot play any die – pass
                moves.append("H:P,P")
    # It is possible that both orderings produced the same move; the caller
    # will handle duplicates implicitly when picking the best score.
    return moves

def policy(state):
    """
    Return a legal move for the given Backgammon state.
    """
    candidates = _generate_all_moves(state)
    best_move = None
    best_score = -float('inf')
    for mv in candidates:
        try:
            after = _apply_move(state, mv)
            score = _evaluate(after)
        except Exception:
            # Should never happen for a legal move, but ignore just in case
            continue
        if score > best_score:
            best_score = score
            best_move = mv
    if best_move is None:
        # emergency fallback – a guaranteed legal pass
        return "H:P,P"
    return best_move
