
import copy

def policy(state: dict) -> str:
    # -- Constants & Setup --
    dirs = [1, -1]
    dice = state['dice']
    if not dice:
        return "H:P,P"

    # -- Heuristic Weights --
    W_PIP = -0.5
    W_HIT = 200.0
    W_OFF = 1000.0  # Huge priority to win/bear off
    W_BLOT = -20.0  # Penalize exposure
    W_PRIME = 5.0   # Reward wall building

    # -- Helper: Board Logic --
    
    def is_legal_move(board, bar, opp, off, src, die, direction):
        # Checks if a move is legal and returns (is_legal, dest_index, is_hit)
        # direction 1: Moving 0->23. Bar Entry effectively -1. Off > 23.
        # direction -1: Moving 23->0. Bar Entry effectively 24. Off < 0.
        
        # Source Validation
        if src == 'B':
            if bar <= 0: return False, None, None
            # Entry point index calculation
            # D=1 enters at 0..5 (from "virtual -1"). Dest = -1 + die.
            # D=-1 enters at 18..23 (from "virtual 24"). Dest = 24 - die.
            start_idx = -1 if direction == 1 else 24
        else:
            if board[src] <= 0: return False, None, None
            if bar > 0: return False, None, None # Must move bar first
            start_idx = src

        # Destination Calc
        if direction == 1:
            dest = start_idx + die
        else:
            dest = start_idx - die
        
        # Check Bounds / Bear Off
        bearing_off = False
        
        if direction == 1:
            # 0 -> 23
            if dest > 23:
                # Bear off check: All checkers must be in home (18-23)
                # i.e., indices 0..17 empty and bar empty.
                if bar > 0 or any(board[i] > 0 for i in range(0, 18)):
                    return False, None, None
                
                dist = 24 - start_idx
                if die == dist:
                    bearing_off = True
                elif die > dist:
                    # Allow only if no checkers on lower indices in home board
                    if any(board[i] > 0 for i in range(18, start_idx)):
                        return False, None, None
                    bearing_off = True
                else:
                    return False, None, None
            elif dest < 0:
                return False, None, None
        else:
            # 23 -> 0
            if dest < 0:
                # Bear off check: All checkers in home (0-5)
                # i.e., indices 6..23 empty and bar empty.
                if bar > 0 or any(board[i] > 0 for i in range(6, 24)):
                    return False, None, None
                
                dist = start_idx + 1 # e.g. at 0, dist is 1
                if die == dist:
                    bearing_off = True
                elif die > dist:
                    # Allow only if no checkers on higher indices in home board
                    if any(board[i] > 0 for i in range(start_idx + 1, 6)):
                        return False, None, None
                    bearing_off = True
                else:
                    return False, None, None
            elif dest > 23:
                return False, None, None

        hit = False
        if not bearing_off:
            if opp[dest] >= 2:
                return False, None, None # Blocked
            if opp[dest] == 1:
                hit = True
        
        return True, dest, hit

    def apply_move(board, bar, opp, off, opp_bar, src, dest, hit, direction):
        new_board = board[:]
        new_opp = opp[:]
        new_bar = bar
        new_off = off
        new_opp_bar = opp_bar

        # Remove from source
        if src == 'B':
            new_bar -= 1
        else:
            new_board[src] -= 1

        # Add to dest
        if dest is None or (direction == 1 and dest > 23) or (direction == -1 and dest < 0):
            new_off += 1
        else:
            if hit:
                new_opp[dest] = 0
                new_opp_bar += 1
                new_board[dest] += 1
            else:
                new_board[dest] += 1
        
        return new_board, new_bar, new_opp, new_off, new_opp_bar

    def get_steps(curr_state, die, direction):
        b, bar, o, off, obar = curr_state
        steps = []
        possible_srcs = []
        if bar > 0:
            possible_srcs = ['B']
        else:
            possible_srcs = [i for i, x in enumerate(b) if x > 0]
            
        for src in possible_srcs:
            legal, dest, hit = is_legal_move(b, bar, o, off, src, die, direction)
            if legal:
                next_st = apply_move(b, bar, o, off, obar, src, dest, hit, direction)
                code = "B" if src == 'B' else f"A{src}"
                steps.append((code, next_st))
        return steps

    def solve_depth(curr_state, dice_seq, direction):
        if not dice_seq:
            return [([], curr_state)]
        
        die = dice_seq[0]
        steps = get_steps(curr_state, die, direction)
        
        if not steps:
            # Cannot move this die, sequence ends here
            return [([], curr_state)]
        
        results = []
        for mv_str, next_st in steps:
            tails = solve_depth(next_st, dice_seq[1:], direction)
            for t_mv, t_st in tails:
                results.append(([mv_str] + t_mv, t_st))
        
        return results

    # -- Logic --
    # Setup Orders
    orders = [] 
    if len(dice) == 1:
        orders.append(('H', dice))
    else:
        d1, d2 = dice[0], dice[1]
        # Treat doubles as just one H sequence (since dice are identical)
        # However, engine might require specific output. 
        # Standard doubles is 4 moves, but input is size 2. We play what we have.
        if d1 == d2:
             orders.append(('H', [d1, d2])) 
        else:
             # Try both regular and swapped orders
             if d1 > d2:
                 orders.append(('H', [d1, d2]))
                 orders.append(('L', [d2, d1]))
             else:
                 orders.append(('H', [d2, d1]))
                 orders.append(('L', [d1, d2]))

    candidates = []
    initial_tuple = (state['my_pts'], state['my_bar'], state['opp_pts'], state['my_off'], state['opp_bar'])

    for direct in dirs:
        for code, seq in orders:
            sequences = solve_depth(initial_tuple, seq, direct)
            
            if not sequences: continue
            
            # Filter for max length within this branch
            max_len = max(len(x[0]) for x in sequences)
            if max_len == 0: continue
            
            valid_seqs = [x for x in sequences if len(x[0]) == max_len]

            # Heuristic Scoring
            for moves, f_st in valid_seqs:
                my_p_b, my_p_bar, op_p, my_p_off, op_p_bar = f_st
                
                # Metric: Pips (Distance to finish)
                pips = 0
                if direct == 1: # Moving to 24
                    pips += my_p_bar * 25
                    for i in range(24): pips += my_p_b[i] * (24 - i)
                else: # Moving to -1
                    pips += my_p_bar * 25
                    for i in range(24): pips += my_p_b[i] * (i + 1)
                
                # Metric: Primes
                prime_score = 0
                cons = 0
                for x in my_p_b:
                    if x >= 2: cons += 1
                    else:
                        if cons > 1: prime_score += (cons * cons)
                        cons = 0
                if cons > 1: prime_score += (cons * cons)

                # Metric: Blots
                blots = sum(1 for x in my_p_b if x == 1)
                
                # Metric: Hits
                hits = op_p_bar - state['opp_bar']
                offs = my_p_off - state['my_off']

                score = (pips * W_PIP) + (hits * W_HIT) + (offs * W_OFF) + (blots * W_BLOT) + (prime_score * W_PRIME)
                
                # High Die Usage Flag:
                # If len=1, we must use high die if possible.
                # If code='H', first move corresponds to the max die of the pair.
                # If len=2, we used both, satisfying the rule.
                high_die_used = False
                if len(dice) == 2:
                    if max_len == 2: high_die_used = True
                    elif max_len == 1 and code == 'H': high_die_used = True
                else: 
                    high_die_used = True # Single die provided and used

                candidates.append({
                    'score': score,
                    'order': code,
                    'moves': moves,
                    'len': max_len,
                    'high_die_used': high_die_used
                })

    if not candidates:
        return "H:P,P"

    # Global Rules Filtering
    # 1. Must pick sequence with max moves played (usually 2, or 1 if blocked)
    global_max = max(c['len'] for c in candidates)
    cands = [c for c in candidates if c['len'] == global_max]
    
    # 2. If we handled 2 dice but could only play 1, we MUST play the higher die if possible.
    # Logic: If there is at least one candidate that 'used high die', we disqualify those that didn't.
    if any(c['high_die_used'] for c in cands):
        cands = [c for c in cands if c['high_die_used']]

    # 3. Select Best Score
    best = max(cands, key=lambda x: x['score'])
    
    # Format Output
    m_list = best['moves']
    m1 = m_list[0] if len(m_list) > 0 else "P"
    m2 = m_list[1] if len(m_list) > 1 else "P"
    
    return f"{best['order']}:{m1},{m2}"
