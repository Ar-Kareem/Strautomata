
import itertools

def policy(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']
    
    # helper: is point index in my home board? (points 0-5 for me)
    def in_my_home(pt):
        return 0 <= pt <= 5
    
    # helper: is point index in opponent's home board? (points 18-23 for opponent)
    def in_opp_home(pt):
        return 18 <= pt <= 23
    
    # generate all legal moves given dice and state
    # returns list of (order, from1, from2) where order is 'H' or 'L'
    def legal_moves():
        moves = []
        if not dice:
            return [('H', 'P', 'P')]
        if len(dice) == 1:
            die = dice[0]
            # must play higher die if possible, but here only one die
            # try all possible from points
            candidates = []
            if my_bar > 0:
                from_pt = 'B'
                dest = die - 1  # bar entry to point die-1 (0‑based)
                if opp_pts[dest] < 2:
                    candidates.append(('H', 'B', 'P'))
            else:
                for pt in range(24):
                    if my_pts[pt] == 0:
                        continue
                    dest = pt - die
                    if dest < 0:
                        # bearing off possible only if all in home
                        if all(my_pts[i] == 0 for i in range(6, 24)):
                            candidates.append(('H', f'A{pt}', 'P'))
                    else:
                        if opp_pts[dest] < 2:
                            candidates.append(('H', f'A{pt}', 'P'))
            if candidates:
                # must play if possible
                return candidates
            else:
                return [('H', 'P', 'P')]
        else:  # two dice
            d1, d2 = dice
            high, low = (d1, d2) if d1 >= d2 else (d2, d1)
            # generate all permutations of dice usage
            perms = [(high, low), (low, high)]
            # we must try both orders H and L
            for order_idx, (first_die, second_die) in enumerate(perms):
                order = 'H' if order_idx == 0 else 'L'
                # we need to try all possible first moves, then second moves
                # but exhaustive search is fine here (max 24*24 combos)
                # first, if bar > 0, must move from bar first
                if my_bar > 0:
                    # first move from bar
                    dest1 = first_die - 1
                    if opp_pts[dest1] >= 2:
                        continue  # cannot play this die from bar
                    # simulate after first move
                    temp_my_bar = my_bar - 1
                    temp_my_pts = my_pts[:]
                    temp_my_pts[dest1] += 1
                    # second move: if still bar left, must move from bar again
                    if temp_my_bar > 0:
                        dest2 = second_die - 1
                        if opp_pts[dest2] >= 2:
                            continue
                        moves.append((order, 'B', 'B'))
                    else:
                        # second move from points
                        found = False
                        for pt in range(24):
                            if temp_my_pts[pt] == 0:
                                continue
                            dest = pt - second_die
                            if dest < 0:
                                if all(temp_my_pts[i] == 0 for i in range(6, 24)):
                                    moves.append((order, 'B', f'A{pt}'))
                                    found = True
                            else:
                                if opp_pts[dest] < 2:
                                    moves.append((order, 'B', f'A{pt}'))
                                    found = True
                        if not found:
                            # can't play second die, but must play if possible? rule: if both dice can be played, must play both.
                            # here second die cannot be played, so this permutation invalid.
                            pass
                else:
                    # no bar: try all pairs of from points
                    for pt1 in range(24):
                        if my_pts[pt1] == 0:
                            continue
                        dest1 = pt1 - first_die
                        if dest1 < 0:
                            # bearing off first die
                            if not all(my_pts[i] == 0 for i in range(6, 24)):
                                continue
                        else:
                            if opp_pts[dest1] >= 2:
                                continue
                        # simulate after first move
                        temp_my_pts = my_pts[:]
                        temp_my_pts[pt1] -= 1
                        if dest1 >= 0:
                            temp_my_pts[dest1] += 1
                        # second move
                        found_second = False
                        for pt2 in range(24):
                            if temp_my_pts[pt2] == 0:
                                continue
                            dest2 = pt2 - second_die
                            if dest2 < 0:
                                if all(temp_my_pts[i] == 0 for i in range(6, 24)):
                                    moves.append((order, f'A{pt1}', f'A{pt2}'))
                                    found_second = True
                            else:
                                if opp_pts[dest2] < 2:
                                    moves.append((order, f'A{pt1}', f'A{pt2}'))
                                    found_second = True
                        # also allow second move from same point if still has checkers
                        # (already covered in loop)
                        if not found_second:
                            # check if second die can be played by moving the same checker again? not allowed in backgammon (two different checkers unless same point has multiple)
                            # but if pt1 has multiple, we can move another from same point
                            # our loop already considered pt2 = pt1 if count >=2
                            pass
        # deduplicate moves (order matters, so keep as is)
        # filter duplicates
        unique = []
        seen = set()
        for order, f1, f2 in moves:
            key = (order, f1, f2)
            if key not in seen:
                seen.add(key)
                unique.append((order, f1, f2))
        if not unique:
            return [('H', 'P', 'P')]
        return unique
    
    # evaluate a board position after a move
    def evaluate(pos_my_pts, pos_opp_pts, pos_my_bar, pos_opp_bar, pos_my_off, pos_opp_off):
        score = 0
        # race: total pip count
        my_pips = sum((i+1) * pos_my_pts[i] for i in range(24)) + 25 * pos_my_bar
        opp_pips = sum((24-i) * pos_opp_pts[i] for i in range(24)) + 25 * pos_opp_bar
        score += (opp_pips - my_pips) * 0.1  # lower pips better
        
        # blot penalty: single checker vulnerable
        for i in range(24):
            if pos_my_pts[i] == 1 and not in_my_home(i):
                # vulnerability: opponent can hit from points ahead
                for opp_i in range(i+1, min(i+7, 24)):
                    if pos_opp_pts[opp_i] > 0 and (opp_i - i) in [1,2,3,4,5,6]:
                        score -= 2.0
                # extra penalty if in opponent's home
                if in_opp_home(i):
                    score -= 1.0
        
        # blockade bonus: points with >=2 checkers
        for i in range(24):
            if pos_my_pts[i] >= 2:
                score += 0.5
                # bonus if in opponent's home
                if 18 <= i <= 23:
                    score += 1.0
        
        # opponent blot bonus: we like hitting
        for i in range(24):
            if pos_opp_pts[i] == 1:
                # we can hit if we have checker behind?
                score += 0.3
        
        # bearing off progress
        score += pos_my_off * 0.2
        score -= pos_opp_off * 0.2
        
        # control of home board
        my_home_count = sum(pos_my_pts[i] for i in range(6))
        opp_home_count = sum(pos_opp_pts[i] for i in range(18,24))
        score += my_home_count * 0.1
        score -= opp_home_count * 0.1
        
        return score
    
    # get legal moves
    moves = legal_moves()
    if len(moves) == 1:
        order, f1, f2 = moves[0]
        return f"{order}:{f1},{f2}"
    
    # evaluate each move
    best_score = -1e9
    best_move = moves[0]
    for order, f1, f2 in moves:
        # simulate board after move
        sim_my_pts = my_pts[:]
        sim_opp_pts = opp_pts[:]
        sim_my_bar = my_bar
        sim_opp_bar = opp_bar
        sim_my_off = my_off
        sim_opp_off = opp_off
        
        # decode first move
        def apply_move(from_token, die):
            nonlocal sim_my_pts, sim_my_bar, sim_my_off, sim_opp_pts, sim_opp_bar
            if from_token == 'P':
                return
            if from_token == 'B':
                dest = die - 1
                sim_my_bar -= 1
                # hit?
                if sim_opp_pts[dest] == 1:
                    sim_opp_pts[dest] = 0
                    sim_opp_bar += 1
                sim_my_pts[dest] += 1
            else:  # A{pt}
                pt = int(from_token[1:])
                dest = pt - die
                sim_my_pts[pt] -= 1
                if dest < 0:
                    sim_my_off += 1
                else:
                    # hit?
                    if sim_opp_pts[dest] == 1:
                        sim_opp_pts[dest] = 0
                        sim_opp_bar += 1
                    sim_my_pts[dest] += 1
        
        # determine dice used
        if order == 'H':
            first_die = max(dice)
            second_die = min(dice)
        else:
            first_die = min(dice)
            second_die = max(dice)
        
        apply_move(f1, first_die)
        apply_move(f2, second_die)
        
        scr = evaluate(sim_my_pts, sim_opp_pts, sim_my_bar, sim_opp_bar, sim_my_off, sim_opp_off)
        if scr > best_score:
            best_score = scr
            best_move = (order, f1, f2)
    
    order, f1, f2 = best_move
    return f"{order}:{f1},{f2}"
