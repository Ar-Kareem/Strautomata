
import copy

def policy(state: dict) -> str:
    """
    Return a legal move for the given backgammon state.
    The move is chosen by enumerating all legal moves, simulating them,
    scoring the resulting board with a simple heuristic, and picking the
    highest‑scoring move that obeys the rule “play both dice if possible,
    otherwise play the higher die”.
    """
    # ----------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------
    def all_in_home(my_pts, my_bar):
        """True iff every checker is inside the home board (points 0‑5) and none are on the bar."""
        if my_bar != 0:
            return False
        for i in range(6, 24):
            if my_pts[i] > 0:
                return False
        return True

    def evaluate(st):
        """Simple heuristic: higher is better."""
        score = 0
        # borne off checkers are the ultimate goal
        score += st['my_off'] * 1000
        # checkers in the home board
        for i in range(6):
            score += st['my_pts'][i] * 10
        # made points (≥2 checkers) in home board
        for i in range(6):
            if st['my_pts'][i] >= 2:
                score += 5
        # penalise blots outside the home board
        for i in range(6, 24):
            if st['my_pts'][i] == 1:
                score -= 5
        # opponent on the bar is good for us
        score += st['opp_bar'] * 50
        # opponent checkers in their home board are a threat
        for i in range(18, 24):
            score -= st['opp_pts'][i] * 2
        return score

    def simulate(state, order, start1, start2):
        """
        Apply the move described by (order, start1, start2) to a *copy* of state.
        Returns the new state dict if the move is legal, otherwise None.
        """
        dice = state['dice']
        # Determine which die corresponds to each move
        if len(dice) == 0:
            return None          # should never happen
        elif len(dice) == 1:
            die_val = dice[0]
            if order == 'H':
                first_die, second_die = die_val, None
            else:
                first_die, second_die = None, die_val
        else:
            d_hi = max(dice)
            d_lo = min(dice)
            if order == 'H':
                first_die, second_die = d_hi, d_lo
            else:
                first_die, second_die = d_lo, d_hi

        # Copy state lists – we will work on these mutable copies
        my_pts = list(state['my_pts'])
        opp_pts = list(state['opp_pts'])
        my_bar = state['my_bar']
        opp_bar = state['opp_bar']
        my_off = state['my_off']
        opp_off = state['opp_off']

        # ------------------------------------------------------------------
        # Helper that mutates the board for one part of the move.
        # Returns True on success, False if the move part is illegal.
        # ------------------------------------------------------------------
        def apply_one_die(die, start):
            nonlocal my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off
            # bar‑check: if any of our checkers are on the bar, we must move them first.
            if my_bar > 0 and start != 'B':
                return False
            if my_bar == 0 and start == 'B':
                return False   # cannot move from bar when we have none there

            if start == 'P':
                # passing is always allowed (the engine will reject it later if a die must be played)
                return True

            if start == 'B':
                if my_bar <= 0:
                    return False
                dest = 24 - die          # absolute destination point for a bar entry
                # destination must be inside the board (it always is for 1‑6)
                if dest < 0 or dest > 23:
                    return False
                # cannot land on a point with two or more opponent checkers
                if opp_pts[dest] >= 2:
                    return False
                # hit a blot?
                if opp_pts[dest] == 1:
                    opp_pts[dest] = 0
                    opp_bar += 1
                # move the checker from bar to dest
                my_bar -= 1
                my_pts[dest] += 1
                return True

            # otherwise start must be "A{idx}"
            if not start.startswith('A'):
                return False
            try:
                src = int(start[1:])
            except:
                return False
            if src < 0 or src > 23:
                return False
            if my_pts[src] <= 0:
                return False

            dest = src - die

            # bearing off?
            if dest < 0:
                # allowed only when every checker is already in the home board
                if not all_in_home(my_pts, my_bar):
                    return False
                # also we must own the source point (we already know we have a checker there)
                my_pts[src] -= 1
                my_off += 1
                return True

            # normal move on the board
            if opp_pts[dest] >= 2:
                return False   # blocked point
            # hit a blot?
            if opp_pts[dest] == 1:
                opp_pts[dest] = 0
                opp_bar += 1
            # move our checker
            my_pts[src] -= 1
            my_pts[dest] += 1
            return True

        # Apply the first part of the move (if there is a die for it)
        if first_die is not None:
            if not apply_one_die(first_die, start1):
                return None

        # Apply the second part of the move (if there is a die for it)
        if second_die is not None:
            if not apply_one_die(second_die, start2):
                return None

        # Build the resulting state dict
        return {
            'my_pts': my_pts,
            'opp_pts': opp_pts,
            'my_bar': my_bar,
            'opp_bar': opp_bar,
            'my_off': my_off,
            'opp_off': opp_off,
            'dice': state['dice']   # dice do not change
        }

    # ----------------------------------------------------------------------
    # 1. No dice → pass
    # ----------------------------------------------------------------------
    dice = state['dice']
    if len(dice) == 0:
        return "H:P,P"

    # ----------------------------------------------------------------------
    # 2. Build list of possible start strings (B, P, and each occupied point)
    # ----------------------------------------------------------------------
    possible_starts = ['P']
    if state['my_bar'] > 0:
        possible_starts.append('B')
    for i in range(24):
        if state['my_pts'][i] > 0:
            possible_starts.append(f'A{i}')

    # ----------------------------------------------------------------------
    # 3. Generate all candidate move strings
    # ----------------------------------------------------------------------
    candidates = []
    # helper to add a candidate
    def add_candidate(order, s1, s2):
        candidates.append(f"{order}:{s1},{s2}")

    if len(dice) == 1:
        # Only one die – we must play it (the higher die).
        for s in possible_starts:
            if s == 'P':
                continue
            # order H: first move uses the die, second passes
            add_candidate('H', s, 'P')
            # order L: second move uses the die, first passes
            add_candidate('L', 'P', s)
    else:
        # Two dice – allow any combination (including passes)
        for order in ('H', 'L'):
            for s1 in possible_starts:
                for s2 in possible_starts:
                    add_candidate(order, s1, s2)

    # ----------------------------------------------------------------------
    # 4. Simulate each candidate and keep the legal ones together with a heuristic score
    # ----------------------------------------------------------------------
    legal_moves = []   # list of (move_str, new_state, score)
    for mv in candidates:
        parts = mv.split(':')
        if len(parts) != 2:
            continue
        order, rest = parts
        s1, s2 = rest.split(',', 1)   # split only once (avoids extra commas)
        new_state = simulate(state, order, s1, s2)
        if new_state is None:
            continue
        score = evaluate(new_state)
        legal_moves.append((mv, new_state, score))

    # ----------------------------------------------------------------------
    # 5. If no legal move at all, pass
    # ----------------------------------------------------------------------
    if not legal_moves:
        return "H:P,P"

    # ----------------------------------------------------------------------
    # 6. Enforce the backgammon rule: if any move uses both dice, we must play one of those.
    # ----------------------------------------------------------------------
    both_moves = []
    for mv, ns, sc in legal_moves:
        # a move uses both dice iff neither start is 'P'
        p1, p2 = mv.split(':')[1].split(',')
        if p1 != 'P' and p2 != 'P':
            both_moves.append((mv, ns, sc))

    if both_moves:
        best = max(both_moves, key=lambda x: x[2])
        return best[0]

    # ----------------------------------------------------------------------
    # 7. No two‑dice move is possible – we must play the higher die if we can.
    # ----------------------------------------------------------------------
    higher_die = max(dice)
    # For order 'H' the higher die is the first move, for 'L' it is the second move.
    single_moves = []
    for mv, ns, sc in legal_moves:
        order = mv[0]
        p1, p2 = mv.split(':')[1].split(',')
        if order == 'H' and p1 != 'P':
            single_moves.append((mv, ns, sc))
        elif order == 'L' and p2 != 'P':
            single_moves.append((mv, ns, sc))
    if single_moves:
        best = max(single_moves, key=lambda x: x[2])
        return best[0]

    # ----------------------------------------------------------------------
    # 8. Nothing is playable – pass
    # ----------------------------------------------------------------------
    return "H:P,P"
