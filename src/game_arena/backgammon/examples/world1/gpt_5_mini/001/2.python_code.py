
import copy

def policy(state: dict) -> str:
    """
    Return a move string "<ORDER>:<FROM1>,<FROM2>" according to the required API.

    Strategy summary:
    - If there are checkers on the bar, attempt bar entries first.
    - Prefer sequences that play both dice when legal. Try both orders (H and L).
    - Prefer sequences that hit opponent checkers. Otherwise choose the sequence
      that advances the most pips.
    - If only one die can be played, play it (prefer the higher die if there's a choice).
    - If no legal moves, return a pass "H:P,P".
    """

    # Helpers and board model
    my_pts = list(state.get('my_pts', [0]*24))
    opp_pts = list(state.get('opp_pts', [0]*24))
    my_bar = int(state.get('my_bar', 0))
    opp_bar = int(state.get('opp_bar', 0))
    my_off = int(state.get('my_off', 0))
    # dice: list of len 0,1,2
    dice = list(state.get('dice', []))

    # formatting helpers
    def fmt_from_token(tok):
        if tok == 'B':
            return 'B'
        if tok == 'P':
            return 'P'
        return f"A{tok}"

    # movement helpers: for a given from (int index 0..23 or 24 for bar) and die, compute dest
    def dest_of(from_idx, die):
        return from_idx - die

    # check whether all of my checkers are in home board (points 0..5)
    def all_in_home(mypts):
        return sum(mypts[6:]) == 0

    # bearing off rule: allow exact or use higher die only if no checkers on higher points
    def can_bear_off_from(mypts, from_idx, die):
        # from_idx must be in 0..5
        if not (0 <= from_idx <= 5):
            return False
        if not all_in_home(mypts):
            return False
        dist = from_idx + 1
        if die == dist:
            return True
        if die > dist:
            # allowed only if no checkers on any point with index > from_idx (i.e., further from bear-off)
            for j in range(from_idx + 1, 6):
                if mypts[j] > 0:
                    return False
            return True
        return False

    # Determine single-die legal starting points for a given die on a given board state
    def legal_single_froms(mypts, opppts, mybar, die):
        res = []
        # if there are checkers on bar, only bar entries allowed (if legal)
        if mybar > 0:
            # bar represented as start index 24
            enter_dest = dest_of(24, die)
            if 0 <= enter_dest <= 23:
                if opppts[enter_dest] < 2:
                    res.append(24)  # bar is represented as 24 internally
            # no other moves allowed if bar present
            return res

        # otherwise check all points that have my checkers
        for i in range(24):
            if mypts[i] <= 0:
                continue
            d = dest_of(i, die)
            if d >= 0:
                # normal move onto board
                if opppts[d] < 2:
                    res.append(i)
            else:
                # bearing off attempt
                if can_bear_off_from(mypts, i, die):
                    res.append(i)
        return res

    # Apply a single move to board copies; return (new_mypts, new_opppts, new_mybar, new_oppbar, new_myoff, hit)
    def apply_move(mypts, opppts, mybar, oppbar, myoff, from_token, die):
        # make shallow copies of lists to mutate
        mypts = list(mypts)
        opppts = list(opppts)
        mybar = int(mybar)
        oppbar = int(oppbar)
        myoff = int(myoff)
        hit = False

        if from_token == 24:  # bar
            if mybar <= 0:
                return None  # illegal
            from_idx = 24
        else:
            from_idx = from_token
            if mypts[from_idx] <= 0:
                return None  # illegal

        d = dest_of(from_idx, die)
        # remove checker from source
        if from_idx == 24:
            mybar -= 1
        else:
            mypts[from_idx] -= 1

        if d >= 0:
            # landing on board point d
            if opppts[d] >= 2:
                return None  # illegal
            if opppts[d] == 1:
                # hit opponent
                opppts[d] = 0
                oppbar += 1
                hit = True
            mypts[d] += 1
        else:
            # bear off
            if not can_bear_off_from(mypts, from_idx, die) and not (from_idx == 24 and False):
                # For safety, we should only have allowed valid bear offs earlier.
                return None
            myoff += 1
        return (mypts, opppts, mybar, oppbar, myoff, hit)

    # If no dice, must pass
    if len(dice) == 0:
        return "H:P,P"

    # Prepare high and low dice
    if len(dice) == 1:
        d_high = dice[0]
        d_low = dice[0]
    else:
        d_high = max(dice[0], dice[1])
        d_low = min(dice[0], dice[1])

    # First check if any two-move sequence exists. Try both orders.
    sequences = []  # list of tuples: (order_char, from1, from2, score, hit_flag)
    # Original board snapshot
    orig_mypts = my_pts
    orig_opppts = opp_pts
    orig_mybar = my_bar
    orig_oppbar = opp_bar
    orig_myoff = my_off

    orders = [('H', d_high, d_low), ('L', d_low, d_high)]
    for order_char, first_die, second_die in orders:
        # first move candidates:
        first_candidates = legal_single_froms(orig_mypts, orig_opppts, orig_mybar, first_die)
        if not first_candidates:
            continue
        for f in first_candidates:
            res1 = apply_move(orig_mypts, orig_opppts, orig_mybar, orig_oppbar, orig_myoff, f, first_die)
            if res1 is None:
                continue
            my1, opp1, mybar1, oppbar1, myoff1, hit1 = res1
            # second candidates from updated state:
            second_candidates = legal_single_froms(my1, opp1, mybar1, second_die)
            if second_candidates:
                # collect possible second moves
                for s in second_candidates:
                    # simulate second move
                    res2 = apply_move(my1, opp1, mybar1, oppbar1, myoff1, s, second_die)
                    if res2 is None:
                        continue
                    my2, opp2, mybar2, oppbar2, myoff2, hit2 = res2
                    # compute score: prefer hitting, then prefer pip advancement
                    hit_flag = hit1 or hit2
                    # pip advancement estimate: original pip sum minus new pip sum
                    # approximate by sum(i*count) where smaller index = closer to being borne off
                    def pip_sum(pts):
                        return sum(i * pts[i] for i in range(24))
                    orig_pip = pip_sum(orig_mypts)
                    new_pip = pip_sum(my2)  # ignores bar/off but gives relative order
                    pip_advance = orig_pip - new_pip
                    score = (1000 if hit_flag else 0) + pip_advance
                    sequences.append((order_char, f, s, score, hit_flag))

    # If any full two-dice sequences exist, pick best
    if sequences:
        # prefer hit sequences first, then highest score
        sequences.sort(key=lambda x: (0 if x[4] else 1, -x[3]))
        best = sequences[0]
        order_char, f, s, _, _ = best
        return f"{order_char}:{fmt_from_token(f)},{fmt_from_token(s)}"

    # No legal two-dice sequences. Must attempt single-die plays.
    # According to rule: if only one die can be played, play the higher die when possible.
    # We'll check which dice have any single legal moves on the original board.
    high_moves = legal_single_froms(orig_mypts, orig_opppts, orig_mybar, d_high)
    low_moves = legal_single_froms(orig_mypts, orig_opppts, orig_mybar, d_low) if (d_low != d_high) else high_moves

    # If both dice individually have moves, then one of them must be playable but the rules about which to prefer when only one die can be played
    # Apply preference: if only one die has any moves, play that die. If both have moves but no two-dice sequence, play the higher die first.
    if high_moves or low_moves:
        # decide which die to play
        if high_moves and not low_moves:
            chosen_die = d_high
            chosen_froms = high_moves
            order_char = 'H'  # first used is higher die
        elif (not high_moves) and low_moves:
            chosen_die = d_low
            chosen_froms = low_moves
            # Here we still mark order as H to indicate first uses higher die: but since only one die exists,
            # if d_low == d_high this is same. If not, higher die is not playable so we play the low; set order to L.
            order_char = 'L'
        else:
            # both have single-die moves available but no two-move sequence; per rule prefer playing the higher die.
            chosen_die = d_high
            chosen_froms = high_moves
            order_char = 'H'

        # choose among chosen_froms the best single move: prefer hits, then pip advance
        best_choice = None
        best_score = None
        for f in chosen_froms:
            res = apply_move(orig_mypts, orig_opppts, orig_mybar, orig_oppbar, orig_myoff, f, chosen_die)
            if res is None:
                continue
            my1, opp1, mybar1, oppbar1, myoff1, hit1 = res
            hit_flag = hit1
            def pip_sum(pts):
                return sum(i * pts[i] for i in range(24))
            orig_pip = sum(i * orig_mypts[i] for i in range(24))
            new_pip = sum(i * my1[i] for i in range(24))
            pip_advance = orig_pip - new_pip
            score = (1000 if hit_flag else 0) + pip_advance
            if best_choice is None or score > best_score:
                best_choice = f
                best_score = score

        if best_choice is not None:
            # second move is a pass
            return f"{order_char}:{fmt_from_token(best_choice)},P"

    # No legal single or double moves found with our rules => must pass.
    # Return pass string. Use H by default.
    return "H:P,P"
