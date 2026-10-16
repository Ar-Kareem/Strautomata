
import copy

def policy(state: dict) -> str:
    """
    Returns a legal move string for the current backgammon state.
    Strategy:
      - Generate all legal moves for the two dice (considering both orders).
      - Prefer sequences that hit opponent checkers, bear off, and reduce pip count.
      - If both dice can be played, play both; if only one can be played, play the higher die when possible.
      - Always produce a legal move string. If no move is possible, return H:P,P.
    """
    # Helpers and copies
    my_pts = list(state.get('my_pts', [0]*24))
    opp_pts = list(state.get('opp_pts', [0]*24))
    my_bar = int(state.get('my_bar', 0))
    opp_bar = int(state.get('opp_bar', 0))
    my_off = int(state.get('my_off', 0))
    opp_off = int(state.get('opp_off', 0))
    dice = list(state.get('dice', []))  # length 0..2
    
    # Utility to format a from token
    def fmt_from(x):
        if x == 'B':
            return 'B'
        if x == 'P':
            return 'P'
        return f"A{x}"
    
    # If no dice rolled or none available
    if not dice:
        return "H:P,P"
    
    # Determine higher and lower die values
    if len(dice) == 1:
        high = dice[0]
        low = None
    else:
        d0, d1 = dice[0], dice[1]
        if d0 >= d1:
            high, low = d0, d1
        else:
            high, low = d1, d0
    
    # Compute pip count helper
    def pip_count(pts):
        return sum(i * pts[i] for i in range(24))
    
    init_pip = pip_count(my_pts)
    
    # Check if all checkers are in home board (points 0..5)
    def all_in_home(pts, bar):
        if bar > 0:
            return False
        return sum(pts[6:24]) == 0
    
    # Find highest occupied point in home (0..5), or -1 if none
    def highest_in_home(pts):
        for i in range(5, -1, -1):
            if pts[i] > 0:
                return i
        return -1
    
    # Determine if a single move from 'from_idx' using 'die' is legal in given (mutable) state
    def can_move_from(from_token, die, s_my_pts, s_opp_pts, s_my_bar, s_opp_bar, s_my_off):
        # from_token either integer index 0..23 or 'B'
        if from_token == 'B':
            if s_my_bar <= 0:
                return False
            dest = 24 - die  # bar entry mapping
            if dest < 0 or dest > 23:
                return False
            # destination blocked if opponent has 2 or more there
            if s_opp_pts[dest] >= 2:
                return False
            return True
        else:
            p = from_token
            if p < 0 or p > 23:
                return False
            if s_my_pts[p] <= 0:
                return False
            dest = p - die
            if dest >= 0:
                # normal move, ensure destination not blocked
                if s_opp_pts[dest] >= 2:
                    return False
                return True
            else:
                # potential bearing off; check rules
                if not all_in_home(s_my_pts, s_my_bar):
                    return False
                # if there's any checker on points index >= die and <=5, you cannot bear off from lower points
                # indices range die..5 (die may be 1..6)
                if die <= 6:
                    for k in range(die, 6):
                        if s_my_pts[k] > 0:
                            # there is checker on a higher point than allowed for using this die to bear off
                            return False
                # allowed only if this checker is the highest occupied point (or exact die)
                highest = highest_in_home(s_my_pts)
                if highest == -1:
                    return False
                if p == highest:
                    return True
                # Also if p - die < 0 and p < die and there are no checkers on any points >= die (checked above),
                # only highest can bear off. So disallow if not highest.
                return False
    
    # Apply a move to clones of the state; returns (success, newstate_tuple, hit_flag, off_gain)
    def apply_move(from_token, die, s_my_pts, s_opp_pts, s_my_bar, s_opp_bar, s_my_off):
        # Work on copies provided by caller
        if from_token == 'P':
            # pass: nothing changes
            return True, (s_my_pts, s_opp_pts, s_my_bar, s_opp_bar, s_my_off), 0, 0
        if from_token == 'B':
            if s_my_bar <= 0:
                return False, None, 0, 0
            dest = 24 - die
            if dest < 0 or dest > 23:
                return False, None, 0, 0
            if s_opp_pts[dest] >= 2:
                return False, None, 0, 0
            # perform move
            s_my_bar -= 1
            # hitting?
            hit = 0
            if s_opp_pts[dest] == 1:
                s_opp_pts[dest] = 0
                s_opp_bar += 1
                hit = 1
            s_my_pts[dest] += 1
            return True, (s_my_pts, s_opp_pts, s_my_bar, s_opp_bar, s_my_off), hit, 0
        else:
            p = from_token
            if p < 0 or p > 23:
                return False, None, 0, 0
            if s_my_pts[p] <= 0:
                return False, None, 0, 0
            dest = p - die
            s_my_pts[p] -= 1
            if dest >= 0:
                if s_opp_pts[dest] >= 2:
                    return False, None, 0, 0
                hit = 0
                if s_opp_pts[dest] == 1:
                    s_opp_pts[dest] = 0
                    s_opp_bar += 1
                    hit = 1
                s_my_pts[dest] += 1
                return True, (s_my_pts, s_opp_pts, s_my_bar, s_opp_bar, s_my_off), hit, 0
            else:
                # bearing off
                if not all_in_home(s_my_pts, s_my_bar):
                    return False, None, 0, 0
                # check highest rule:
                # if any checkers on points >= die, cannot bear off lower ones
                if die <= 6:
                    for k in range(die, 6):
                        if s_my_pts[k] > 0:
                            return False, None, 0, 0
                highest = highest_in_home(s_my_pts)
                if highest != p:
                    return False, None, 0, 0
                # bear off
                s_my_off += 1
                return True, (s_my_pts, s_opp_pts, s_my_bar, s_opp_bar, s_my_off), 0, 1
    
    # Generate list of candidate from_tokens for a given die in current state
    def generate_first_moves_for_die(die, s_my_pts, s_opp_pts, s_my_bar, s_opp_bar, s_my_off):
        candidates = []
        # if any checkers on bar, only 'B' allowed
        if s_my_bar > 0:
            if can_move_from('B', die, s_my_pts, s_opp_pts, s_my_bar, s_opp_bar, s_my_off):
                candidates.append('B')
            return candidates
        # otherwise consider each point with our checkers
        for i in range(24):
            if s_my_pts[i] <= 0:
                continue
            if can_move_from(i, die, s_my_pts, s_opp_pts, s_my_bar, s_opp_bar, s_my_off):
                candidates.append(i)
        return candidates
    
    # For single-die scenario (len(dice)==1)
    if len(dice) == 1:
        d = high
        # collect possible moves
        first_moves = generate_first_moves_for_die(d, my_pts[:], opp_pts[:], my_bar, opp_bar, my_off)
        if not first_moves:
            return "H:P,P"
        # choose best single move by heuristic
        best = None
        best_score = None
        for f in first_moves:
            # clone state and apply
            smy = my_pts[:]
            sopp = opp_pts[:]
            smb = my_bar
            sob = opp_bar
            smoff = my_off
            ok, newt, hit, off_gain = apply_move(f, d, smy, sopp, smb, sob, smoff)
            if not ok:
                continue
            s_my_pts2, s_opp_pts2, s_my_bar2, s_opp_bar2, s_my_off2 = newt
            pip_after = pip_count(s_my_pts2)
            score = 1000 * hit + 500 * off_gain + (init_pip - pip_after)
            if best is None or score > best_score:
                best = f
                best_score = score
        if best is None:
            return "H:P,P"
        return f"H:{fmt_from(best)},P"
    
    # For two-dice scenario
    # Candidate sequences: try both orders H-first (higher die first) and L-first
    sequences = []  # tuples (order_char, from1, from2, score, details)
    # Utility to attempt building sequences for given order
    def try_order(first_die, second_die, order_char):
        nonlocal sequences
        # generate legal first-froms in original state
        first_moves = generate_first_moves_for_die(first_die, my_pts[:], opp_pts[:], my_bar, opp_bar, my_off)
        for f in first_moves:
            # simulate applying first move
            smy = my_pts[:]
            sopp = opp_pts[:]
            smb = my_bar
            sob = opp_bar
            smoff = my_off
            ok, newt, hit1, off1 = apply_move(f, first_die, smy, sopp, smb, sob, smoff)
            if not ok:
                continue
            s_my_pts2, s_opp_pts2, s_my_bar2, s_opp_bar2, s_my_off2 = newt
            # generate legal second moves given updated state
            second_moves = generate_first_moves_for_die(second_die, s_my_pts2, s_opp_pts2, s_my_bar2, s_opp_bar2, s_my_off2)
            if second_moves:
                for f2 in second_moves:
                    # simulate second
                    smy2 = s_my_pts2[:]
                    sopp2 = s_opp_pts2[:]
                    smb2 = s_my_bar2
                    sob2 = s_opp_bar2
                    smoff2 = s_my_off2
                    ok2, newt2, hit2, off2 = apply_move(f2, second_die, smy2, sopp2, smb2, sob2, smoff2)
                    if not ok2:
                        continue
                    s_my_pts3, s_opp_pts3, s_my_bar3, s_opp_bar3, s_my_off3 = newt2
                    pip_after = pip_count(s_my_pts3)
                    score = 1000 * (hit1 + hit2) + 500 * (off1 + off2) + (init_pip - pip_after)
                    sequences.append((order_char, f, f2, score, (hit1 + hit2, off1 + off2, init_pip - pip_after)))
            else:
                # no second move possible after this first move
                # record single-move possibility as fallback (we may prefer full two-move sequences)
                pip_after = pip_count(s_my_pts2)
                score = 1000 * hit1 + 500 * off1 + (init_pip - pip_after)
                sequences.append((order_char, f, 'P', score, (hit1, off1, init_pip - pip_after)))
    
    # Try both orders. Determine which die is higher/ lower as values
    # If dice equal, treat first order as H.
    if high is None:
        return "H:P,P"
    if low is None:
        # already handled len==1 earlier
        return "H:P,P"
    
    # If dice equal values, we'll do H-first (arbitrary)
    if high == low:
        try_order(high, low, 'H')
    else:
        try_order(high, low, 'H')
        try_order(low, high, 'L')
    
    # Now choose best complete two-move sequence if any that contains two actual moves (not 'P')
    full_two_moves = [s for s in sequences if s[2] != 'P']
    if full_two_moves:
        # choose best by score, tie-breaker fewest blots etc (not computed): choose max score
        best_seq = max(full_two_moves, key=lambda x: x[3])
        order_char, f1, f2, score, detail = best_seq
        return f"{order_char}:{fmt_from(f1)},{fmt_from(f2)}"
    
    # No full two-move sequences. According to rules, if only one die can be played, must play higher if possible.
    # Check if any single move using higher die is possible in initial position.
    high_first_moves = generate_first_moves_for_die(high, my_pts[:], opp_pts[:], my_bar, opp_bar, my_off)
    low_first_moves = generate_first_moves_for_die(low, my_pts[:], opp_pts[:], my_bar, opp_bar, my_off)
    
    # If any sequence in 'sequences' includes single move with first die equal to higher die prefer those
    # But engine requires: if only one die playable, play higher. We interpret: if high has any single moves, play best among them.
    # If high cannot but low can, play best low single.
    if high_first_moves:
        # choose best single move for high
        best = None
        best_score = None
        for s in sequences:
            order_char, f1, f2, score, detail = s
            # We only consider sequences where only one move was possible (second 'P') and the first die was high
            if order_char == 'H' and f2 == 'P':
                if best is None or score > best_score:
                    best = (order_char, f1)
                    best_score = score
            # Also consider sequences where order_char == 'L' but the first die equals high (only possible when dice equal)
            if order_char == 'L' and f2 == 'P' and high == low:
                if best is None or score > best_score:
                    best = (order_char, f1)
                    best_score = score
        if best:
            order_char, f1 = best
            # ensure we return with correct order char: must indicate which die applied first.
            return f"{order_char}:{fmt_from(f1)},P"
        # fallback: pick some legal high move
        f = high_first_moves[0]
        return f"H:{fmt_from(f)},P"
    elif low_first_moves:
        # No high moves playable; play best low single
        best = None
        best_score = None
        for s in sequences:
            order_char, f1, f2, score, detail = s
            if f2 == 'P':
                # ensure this corresponds to using low die first (order_char 'L') or equal dice
                if order_char == 'L' or (high == low and order_char == 'H'):
                    if best is None or score > best_score:
                        best = (order_char, f1)
                        best_score = score
        if best:
            order_char, f1 = best
            return f"{order_char}:{fmt_from(f1)},P"
        f = low_first_moves[0]
        # if order char should be L since low played first
        # But if dice equal, use H
        oc = 'L' if high != low else 'H'
        return f"{oc}:{fmt_from(f)},P"
    
    # If nothing playable at all:
    return "H:P,P"
