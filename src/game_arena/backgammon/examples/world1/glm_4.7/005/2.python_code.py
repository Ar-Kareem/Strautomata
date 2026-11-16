
import copy

def policy(state: dict) -> str:
    """
    A smart Backgammon policy using 1-ply search and heuristic evaluation.
    """

    def evaluate(s):
        # Calculate Pip Counts
        # My checkers move 23 -> 0. Point i has value (i+1).
        my_pips = sum((i + 1) * c for i, c in enumerate(s['my_pts']))
        
        # Opponent moves 0 -> 23. Point i has value (24 - i).
        opp_pips = sum((24 - i) * c for i, c in enumerate(s['opp_pts']))
        
        # Extract state features
        my_bar = s['my_bar']
        opp_bar = s['opp_bar']
        my_off = s['my_off']
        opp_off = s['opp_off']
        
        # Anchors (checkers in opponent's home board 18-23 for me, 0-5 for opp)
        my_anchors = sum(1 for i in range(18, 24) if s['my_pts'][i] > 0)
        
        # Blots (single checkers)
        my_blots = sum(1 for i in range(24) if s['my_pts'][i] == 1)
        opp_blots = sum(1 for i in range(24) if s['opp_pts'][i] == 1)
        
        # Scoring weights
        score = 0.0
        
        # 1. Race component (Pip difference)
        score += 1.0 * (opp_pips - my_pips)
        
        # 2. Safety and Hitting
        score += 25.0 * (opp_bar - my_bar)
        score -= 1.5 * (my_blots - opp_blots)
        
        # 3. Bearing off
        score += 30.0 * (my_off - opp_off)
        
        # 4. Positional / Strategy
        score += 2.0 * my_anchors
        
        return score

    def get_legal_sources(s, die):
        """Returns a list of legal source points for a given die value."""
        sources = []
        
        # Must move from bar if checkers exist there
        if s['my_bar'] > 0:
            entry_point = 24 - die
            if s['opp_pts'][entry_point] < 2:
                sources.append('B')
            return sources
        
        # Check if bearing off is allowed (all checkers in home board 0-5)
        can_bear_off = (sum(s['my_pts'][6:]) == 0)
        
        for i in range(24):
            if s['my_pts'][i] > 0:
                dest = i - die
                
                if dest >= 0:
                    # Standard move
                    if s['opp_pts'][dest] < 2:
                        sources.append(f"A{i}")
                else:
                    # Bearing off attempt
                    if can_bear_off:
                        # Exact bear off (e.g. from 2 with 6 lands on -4? No)
                        # dist to off is i+1. die == i+1 -> exact.
                        # dest = i - die. dest == -1 -> exact.
                        if dest == -1:
                            sources.append(f"A{i}")
                        # Over-bear off (die > distance)
                        # Only allowed if no checkers on higher points
                        elif die > i + 1:
                            # Check points i+1 to 5
                            if sum(s['my_pts'][i+1:6]) == 0:
                                sources.append(f"A{i}")
        return sources

    def apply_move(s, src, die):
        """Returns a new state dictionary after applying the move."""
        ns = copy.deepcopy(s)
        
        if src == 'B':
            dest = 24 - die
            ns['my_bar'] -= 1
            if ns['opp_pts'][dest] == 1:
                ns['opp_pts'][dest] = 0
                ns['opp_bar'] += 1
            ns['my_pts'][dest] += 1
            
        elif src == 'P':
            pass # No move
            
        else:
            idx = int(src[1:])
            ns['my_pts'][idx] -= 1
            dest = idx - die
            
            if dest >= 0:
                if ns['opp_pts'][dest] == 1:
                    ns['opp_pts'][dest] = 0
                    ns['opp_bar'] += 1
                ns['my_pts'][dest] += 1
            else:
                ns['my_off'] += 1
                
        return ns

    # Main Logic
    dice = state['dice']
    if not dice:
        return "H:P,P"
        
    d1 = dice[0]
    # If only one die is provided, it implies a double or remaining turn, so treat as two same values
    d2 = dice[1] if len(dice) > 1 else d1
    
    high_die = max(d1, d2)
    low_die = min(d1, d2)
    
    # Candidates: (score, move_string, dice_count)
    candidates = []
    
    # --- Try High then Low ---
    srcs_high = get_legal_sources(state, high_die)
    
    if not srcs_high:
        # Cannot play high die. Try low die.
        # Rule: "If only one die can be played, you must play the higher die when possible."
        # Since high is impossible, we play low if possible.
        srcs_low = get_legal_sources(state, low_die)
        if srcs_low:
            for s_low in srcs_low:
                next_state = apply_move(state, s_low, low_die)
                score = evaluate(next_state)
                # Format H:P,Src (High Pass, Low Move) since High was impossible
                candidates.append((score, f"H:P,{s_low}", 1))
        else:
            candidates.append((evaluate(state), "H:P,P", 0))
    else:
        for s_high in srcs_high:
            state_after_high = apply_move(state, s_high, high_die)
            srcs_low = get_legal_sources(state_after_high, low_die)
            
            if not srcs_low:
                # Can only play high die
                score = evaluate(state_after_high)
                candidates.append((score, f"H:{s_high},P", 1))
            else:
                for s_low in srcs_low:
                    # Can play both dice
                    final_state = apply_move(state_after_high, s_low, low_die)
                    score = evaluate(final_state)
                    candidates.append((score, f"H:{s_high},{s_low}", 2))

    # --- Try Low then High (Only if dice are distinct) ---
    # We must check this order because sometimes playing Low first enables High, 
    # whereas playing High first blocks Low.
    if high_die != low_die:
        srcs_low_first = get_legal_sources(state, low_die)
        
        if srcs_low_first:
            for s_low in srcs_low_first:
                state_after_low = apply_move(state, s_low, low_die)
                srcs_high_second = get_legal_sources(state_after_low, high_die)
                
                if not srcs_high_second:
                    # Can only play low die
                    score = evaluate(state_after_low)
                    # Format L:Src,P (Low Move, High Pass)
                    candidates.append((score, f"L:{s_low},P", 1))
                else:
                    # Can play both dice
                    final_state = apply_move(state_after_low, srcs_high_second[0], high_die) # dummy execute for loop
                    # Actually need to loop all srcs_high_second
                    for s_high in srcs_high_second:
                        final_state = apply_move(state_after_low, s_high, high_die)
                        score = evaluate(final_state)
                        candidates.append((score, f"L:{s_low},{s_high}", 2))

    # --- Select Best Move ---
    
    if not candidates:
        return "H:P,P"
        
    # 1. Maximize number of dice used (Legal Requirement)
    max_dice_used = max(c[2] for c in candidates)
    valid_candidates = [c for c in candidates if c[2] == max_dice_used]
    
    # 2. If max_dice_used == 1, enforce "Must play higher die" rule
    if max_dice_used == 1:
        def uses_high_die(move_str):
            prefix, rest = move_str.split(':')
            p1, p2 = rest.split(',')
            if prefix == 'H':
                return p1 != 'P' # H:Src,P uses High
            else: # L
                return p2 != 'P' # L:P,Src uses High
        
        # Check if playing high die is possible among the 1-die candidates
        if any(uses_high_die(c[1]) for c in valid_candidates):
            valid_candidates = [c for c in valid_candidates if uses_high_die(c[1])]
            
    # 3. Pick highest score
    valid_candidates.sort(key=lambda x: x[0], reverse=True)
    
    return valid_candidates[0][1]
