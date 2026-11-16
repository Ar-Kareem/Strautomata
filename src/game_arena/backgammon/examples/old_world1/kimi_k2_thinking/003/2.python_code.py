
def policy(state: dict) -> str:
    """
    Return a legal move for the given backgammon state.
    The move is chosen by a one‑ply search using a simple heuristic.
    """
    # ----------------------------------------------------------------------
    # Helper functions
    # ----------------------------------------------------------------------
    def is_legal_move(st, from_loc, die):
        """Return True if moving from from_loc by die is legal."""
        if from_loc == 'B':
            if st['my_bar'] == 0:
                return False
            entry = 24 - die
            return st['opp_pts'][entry] < 2
        else:
            if st['my_pts'][from_loc] == 0:
                return False
            dest = from_loc - die
            if dest >= 0:
                return st['opp_pts'][dest] < 2
            else:
                # bearing off – allowed only if all checkers are in the home board
                return all_checkers_in_home_board(st)

    def all_checkers_in_home_board(st):
        """Return True iff all of our checkers are in points 0..5 and none are on the bar."""
        if st['my_bar'] > 0:
            return False
        for i in range(6, 24):
            if st['my_pts'][i] > 0:
                return False
        return True

    def generate_moves_for_die(st, die, must_move):
        """
        Return a list of possible moves for the given die.
        Each move is a tuple (from_loc, is_pass) where from_loc is 'B', an int 0..23,
        or None if the move is a pass.
        """
        moves = []
        if st['my_bar'] > 0:
            # must move from the bar if possible
            if is_legal_move(st, 'B', die):
                moves.append(('B', False))
            elif not must_move:
                moves.append((None, True))
            return moves
        # no checkers on the bar – can move any of our checkers
        for i in range(24):
            if st['my_pts'][i] > 0 and is_legal_move(st, i, die):
                moves.append((i, False))
        if not moves and not must_move:
            moves.append((None, True))
        return moves

    def apply_move(st, move, die):
        """Return a new state after applying a single move."""
        from_loc, is_pass = move
        if is_pass:
            return st
        # deep copy the state
        ns = {
            'my_pts': st['my_pts'][:],
            'opp_pts': st['opp_pts'][:],
            'my_bar': st['my_bar'],
            'opp_bar': st['opp_bar'],
            'my_off': st['my_off'],
            'opp_off': st['opp_off'],
            'dice': st['dice'][:],
        }
        if from_loc == 'B':
            ns['my_bar'] -= 1
            entry = 24 - die
            if ns['opp_pts'][entry] == 1:
                ns['opp_pts'][entry] = 0
                ns['opp_bar'] += 1
            else:
                ns['my_pts'][entry] += 1
        else:
            ns['my_pts'][from_loc] -= 1
            dest = from_loc - die
            if dest >= 0:
                if ns['opp_pts'][dest] == 1:
                    ns['opp_pts'][dest] = 0
                    ns['opp_bar'] += 1
                else:
                    ns['my_pts'][dest] += 1
            else:
                # bearing off
                ns['my_off'] += 1
        return ns

    def apply_moves(st, move):
        """Apply a full turn (possibly two moves) and return the resulting state."""
        order, first_move, second_move = move
        dice = st['dice']
        ns = {
            'my_pts': st['my_pts'][:],
            'opp_pts': st['opp_pts'][:],
            'my_bar': st['my_bar'],
            'opp_bar': st['opp_bar'],
            'my_off': st['my_off'],
            'opp_off': st['opp_off'],
            'dice': st['dice'][:],
        }
        if len(dice) >= 1:
            if len(dice) == 2:
                high = max(dice)
                low = min(dice)
                first_die = high if order == 'H' else low
            else:
                first_die = dice[0]
            if not first_move[1]:
                ns = apply_move(ns, first_move, first_die)
        if len(dice) == 2:
            high = max(dice)
            low = min(dice)
            second_die = low if order == 'H' else high
            if not second_move[1]:
                ns = apply_move(ns, second_move, second_die)
        return ns

    def evaluate_state(st):
        """Heuristic evaluation: higher is better for us."""
        # pip counts
        my_pip = sum((i + 1) * st['my_pts'][i] for i in range(24)) + 24 * st['my_bar']
        opp_pip = sum((24 - i) * st['opp_pts'][i] for i in range(24)) + 24 * st['opp_bar']
        # other features
        my_bar = st['my_bar']
        opp_bar = st['opp_bar']
        my_off = st['my_off']
        opp_off = st['opp_off']
        blocked_my = sum(1 for i in range(24) if st['my_pts'][i] >= 2)
        blocked_opp = sum(1 for i in range(24) if st['opp_pts'][i] >= 2)
        blots_my = sum(1 for i in range(24) if st['my_pts'][i] == 1)
        blots_opp = sum(1 for i in range(24) if st['opp_pts'][i] == 1)
        # combine
        score = -my_pip + opp_pip - 10 * my_bar + 10 * opp_bar + 100 * (my_off - opp_off)
        score += 5 * blocked_my - 5 * blocked_opp - 2 * blots_my + 2 * blots_opp
        return score

    def format_from(move):
        from_loc, is_pass = move
        if is_pass:
            return 'P'
        if from_loc == 'B':
            return 'B'
        return f'A{from_loc}'

    def generate_all_move_objects(st):
        dice = st['dice']
        # no dice -> pass
        if len(dice) == 0:
            return [('H', (None, True), (None, True))]
        # single die
        if len(dice) == 1:
            die = dice[0]
            moves = generate_moves_for_die(st, die, must_move=True)
            if not moves:
                return [('H', (None, True), (None, True))]
            return [('H', mv, (None, True)) for mv in moves]
        # two dice
        high = max(dice)
        low = min(dice)
        higher_playable = len(generate_moves_for_die(st, high, must_move=True)) > 0
        lower_playable = len(generate_moves_for_die(st, low, must_move=True)) > 0
        move_objs = []

        # try to play both dice (both orders)
        for order in ('H', 'L'):
            first_die = high if order == 'H' else low
            second_die = low if order == 'H' else high
            first_moves = generate_moves_for_die(st, first_die, must_move=True)
            if not first_moves:
                continue
            for first_move in first_moves:
                new_state = apply_move(st, first_move, first_die)
                second_moves = generate_moves_for_die(new_state, second_die, must_move=False)
                if not second_moves:
                    continue
                for second_move in second_moves:
                    move_objs.append((order, first_move, second_move))

        # if no two‑dice move exists, play a single die (prefer higher)
        if not move_objs:
            if higher_playable:
                for mv in generate_moves_for_die(st, high, must_move=True):
                    move_objs.append(('H', mv, (None, True)))
            elif lower_playable:
                for mv in generate_moves_for_die(st, low, must_move=True):
                    move_objs.append(('L', mv, (None, True)))
            else:
                # cannot move at all
                move_objs.append(('H', (None, True), (None, True)))
        return move_objs

    # ----------------------------------------------------------------------
    # Main logic: pick the best move
    # ----------------------------------------------------------------------
    move_objects = generate_all_move_objects(state)
    best_move = None
    best_val = -float('inf')
    for mv in move_objects:
        ns = apply_moves(state, mv)
        val = evaluate_state(ns)
        if val > best_val:
            best_val = val
            best_move = mv
    order, first_move, second_move = best_move
    return f"{order}:{format_from(first_move)},{format_from(second_move)}"
