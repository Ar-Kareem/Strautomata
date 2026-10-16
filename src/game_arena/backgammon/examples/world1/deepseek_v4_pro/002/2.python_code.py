
import copy

def policy(state: dict) -> str:
    # Constants
    MY_HOME = set(range(0, 6))
    OPP_HOME = set(range(18, 24))
    
    def copy_state(s):
        return {k: v[:] if isinstance(v, list) else v for k, v in s.items()}
    
    def evaluate(s):
        """Heuristic evaluation from our perspective. Higher is better."""
        score = 0.0
        
        # Pip counts
        my_pips = sum(s['my_pts'][i] * (i + 1) for i in range(24)) + s['my_bar'] * 25
        opp_pips = sum(s['opp_pts'][i] * (24 - i) for i in range(24)) + s['opp_bar'] * 25
        score += opp_pips - my_pips  # we want to be ahead in pips
        
        # Blots
        my_blot_penalty = 0.0
        for p in range(24):
            if s['my_pts'][p] == 1:
                if p in OPP_HOME:
                    my_blot_penalty += 2.0
                elif p >= 12:
                    my_blot_penalty += 1.0
                else:
                    my_blot_penalty += 0.5
        score -= my_blot_penalty
        
        opp_blot_reward = 0.0
        for p in range(24):
            if s['opp_pts'][p] == 1:
                if p in MY_HOME:
                    opp_blot_reward += 2.0
                elif p <= 11:
                    opp_blot_reward += 1.0
                else:
                    opp_blot_reward += 0.5
        score += opp_blot_reward
        
        # Blocks (points with >=2 checkers)
        my_blocks = sum(1 for p in range(24) if s['my_pts'][p] >= 2)
        opp_blocks = sum(1 for p in range(24) if s['opp_pts'][p] >= 2)
        score += (my_blocks - opp_blocks) * 0.2
        
        # Bar
        score -= s['my_bar'] * 3.0
        score += s['opp_bar'] * 3.0
        
        # Borne off
        score += s['my_off'] * 2.0
        score -= s['opp_off'] * 2.0
        
        return score

    def get_legal_moves_for_die(s, D):
        """Return list of (from_str, new_state) for a single die D from state s."""
        moves = []
        # Must re-enter from bar first
        if s['my_bar'] > 0:
            entry = 24 - D  # entry point in opp home (18..23)
            if s['opp_pts'][entry] < 2:
                ns = copy_state(s)
                ns['my_bar'] -= 1
                ns['my_pts'][entry] += 1
                if s['opp_pts'][entry] == 1:
                    ns['opp_pts'][entry] -= 1
                    ns['opp_bar'] += 1
                moves.append(('B', ns))
            # if entry blocked, no moves
            return moves
        
        my_pts = s['my_pts']
        opp_pts = s['opp_pts']
        in_home = all(my_pts[i] == 0 for i in range(6, 24)) and s['my_bar'] == 0
        
        normal_points = []
        bear_candidates = []  # points from which we could bear off (dest < 0)
        
        for p in range(24):
            if my_pts[p] > 0:
                dest = p - D
                if dest >= 0:
                    if opp_pts[dest] < 2:
                        normal_points.append(p)
                else:
                    if in_home:
                        bear_candidates.append(p)
        
        legal_points = set()
        if in_home:
            exact = D - 1
            legal_points.update(normal_points)
            if my_pts[exact] > 0:
                legal_points.add(exact)
            else:
                # exact empty: bear off only if no normal moves exist
                if len(normal_points) == 0:
                    # can bear off from highest occupied point in home
                    highest = -1
                    for p in range(5, -1, -1):
                        if my_pts[p] > 0:
                            highest = p
                            break
                    if highest >= 0:
                        legal_points.add(highest)
        else:
            legal_points.update(normal_points)
        
        # Build new states for valid points
        for p in legal_points:
            bear = (p in bear_candidates)
            ns = copy_state(s)
            ns['my_pts'][p] -= 1
            if bear:
                ns['my_off'] += 1
            else:
                dest = p - D
                ns['my_pts'][dest] += 1
                if opp_pts[dest] == 1:
                    ns['opp_pts'][dest] -= 1
                    ns['opp_bar'] += 1
            moves.append((f'A{p}', ns))
        
        return moves

    # Main logic
    dice = state['dice']
    if not dice:
        return "H:P,P"
    
    # Generate orders to try
    orders = []
    if len(dice) == 1:
        orders = [('H', dice)]
    else:
        d1, d2 = dice
        if d1 > d2:
            orders = [('H', [d1, d2]), ('L', [d2, d1])]
        else:
            orders = [('H', [d2, d1])] if d1 == d2 else [('H', [d2, d1]), ('L', [d1, d2])]
    
    all_sequences = []  # list of tuples (order_flag, seq_str_list, final_state)
    
    for order_flag, die_list in orders:
        def dfs(current_state, die_idx, from_list):
            if die_idx == len(die_list):
                all_sequences.append((order_flag, from_list, current_state))
                return
            D = die_list[die_idx]
            moves = get_legal_moves_for_die(current_state, D)
            if not moves:
                # No move for this die
                # If on bar and cannot enter, forfeit all remaining dice
                if current_state['my_bar'] > 0:
                    # Pass all remaining
                    rem = len(die_list) - die_idx
                    dfs(current_state, len(die_list), from_list + ['P'] * rem)
                else:
                    # Pass this die and try next
                    dfs(current_state, die_idx + 1, from_list + ['P'])
                return
            for from_str, ns in moves:
                dfs(ns, die_idx + 1, from_list + [from_str])
        
        dfs(state, 0, [])
    
    # Filter sequences to respect "must play both if possible, else higher if possible"
    # Determine max dice playable
    max_played = 0
    for _, seq, _ in all_sequences:
        played = sum(1 for m in seq if m != 'P')
        if played > max_played:
            max_played = played
    
    # Collect sequences meeting the rule
    if max_played == 2:
        candidates = [(flag, seq, fstate) for flag, seq, fstate in all_sequences 
                      if sum(1 for m in seq if m != 'P') == 2]
    elif max_played == 1:
        # Higher die playable?
        high_die = max(dice)
        has_high = any(any(m != 'P' and ( (flag=='H' and i==0) or (flag=='L' and i==1) ) 
                         for i, m in enumerate(seq))
                       for flag, seq, _ in all_sequences
                       if sum(1 for m in seq if m != 'P') == 1)
        # Actually need to check if the played die value equals high_die.
        # We know the sequence's flag and which position was played.
        def get_played_die(flag, seq):
            # seq is list of moves; find first non-'P'
            for i, m in enumerate(seq):
                if m != 'P':
                    if flag == 'H':
                        return max(dice) if i == 0 else min(dice)
                    else:
                        return min(dice) if i == 0 else max(dice)
            return None
        
        # Check if any sequence plays the higher die
        high_possible = any(get_played_die(flag, seq) == high_die 
                            for flag, seq, _ in all_sequences 
                            if sum(1 for m in seq if m != 'P') == 1)
        
        if high_possible:
            candidates = [(flag, seq, fstate) for flag, seq, fstate in all_sequences
                          if sum(1 for m in seq if m != 'P') == 1 and get_played_die(flag, seq) == high_die]
        else:
            # Only lower die possible
            candidates = [(flag, seq, fstate) for flag, seq, fstate in all_sequences
                          if sum(1 for m in seq if m != 'P') == 1]
    else:  # max_played == 0
        candidates = [(flag, seq, fstate) for flag, seq, fstate in all_sequences 
                      if sum(1 for m in seq if m != 'P') == 0]
    
    if not candidates:
        # fallback (should not happen)
        return "H:P,P"
    
    # Evaluate candidates and pick best
    best_score = -float('inf')
    best_move_str = None
    for flag, seq, fstate in candidates:
        score = evaluate(fstate)
        if score > best_score:
            best_score = score
            from1 = seq[0] if len(seq) > 0 else 'P'
            from2 = seq[1] if len(seq) > 1 else 'P'
            best_move_str = f"{flag}:{from1},{from2}"
    
    return best_move_str
