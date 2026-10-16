
import copy

def policy(state: dict) -> str:
    # --- Heuristic Weights ---
    W_OFF = 100000     # Priority 1: Bear off
    W_HIT = 10000      # Priority 2: Hit opponent
    W_BAR = -5000      # Avoid being hit / staying on bar
    W_BLOT = -1000     # Avoid leaving blots
    W_POINT = 500      # Form points
    W_PIP = -10        # Minimize pip count (race advantage)

    # --- Helper: Clone State ---
    def clone(s):
        return {
            'my_pts': s['my_pts'][:],
            'opp_pts': s['opp_pts'][:],
            'my_bar': s['my_bar'],
            'opp_bar': s['opp_bar'],
            'my_off': s['my_off'],
            'opp_off': s['opp_off'],
            'dice': s['dice'][:]
        }

    # --- Helper: Evaluate State ---
    def evaluate(s):
        score = 0
        score += s['my_off'] * W_OFF
        score += s['opp_bar'] * W_HIT
        score += s['my_bar'] * W_BAR
        
        my_pips = 0
        blots = 0
        points = 0
        
        for i in range(24):
            count = s['my_pts'][i]
            if count == 1:
                # Penalty for exposing a checker (blot)
                blots += 1
            elif count > 1:
                # Reward for making a point (prime building block)
                points += 1
            
            # Pip count: distance from 0 (index 0 is 1 step from 0-point/off)
            # Actually indices are 0..23. Distance to bear off is index + 1
            my_pips += count * (i + 1)
            
        score += blots * W_BLOT
        score += points * W_POINT
        score += my_pips * W_PIP
        return score

    # --- Helper: Check Eligibility to Bear Off ---
    def can_bear_off(s):
        if s['my_bar'] > 0: return False
        # Check if any checkers are outside home board (indices 6..23)
        for i in range(6, 24):
            if s['my_pts'][i] > 0: return False
        return True

    # --- Helper: Generate Single Step Actions ---
    def get_moves(s, die):
        moves = [] # List of (move_string_token, resulting_state)
        
        # 1. Must move from Bar if checkers exist there
        if s['my_bar'] > 0:
            # Enter at 24 - die. Map to indices 0..23.
            # Die 1 -> 23, Die 6 -> 18.
            target = 24 - die
            if 0 <= target <= 23:
                # Check occupancy: blocked if opponent has 2+
                if s['opp_pts'][target] < 2:
                    ns = clone(s)
                    ns['my_bar'] -= 1
                    # Hit Logic
                    if ns['opp_pts'][target] == 1:
                        ns['opp_pts'][target] = 0
                        ns['opp_bar'] += 1
                    ns['my_pts'][target] += 1
                    moves.append(('B', ns))
            # If on bar, you cannot move checkers on board. Return found bar moves (or empty if blocked).
            return moves
        
        # 2. Move checkers on board
        bear_allowed = can_bear_off(s)
        
        # Identify source points
        srcs = [i for i, c in enumerate(s['my_pts']) if c > 0]
        for i in srcs:
            target = i - die
            valid = False
            is_off = False
            
            if target >= 0:
                # Normal move
                if s['opp_pts'][target] < 2:
                    valid = True
            else:
                # Bear off attempt
                if bear_allowed:
                    if target == -1: # Exact bear off (e.g. from 2 with die 3 is target -1)
                        # Wait, from 0 with die 1 -> -1. From 2 with die 3 -> -1. Correct.
                        valid = True; is_off = True
                    else:
                        # Over-bear off (e.g. from 2 with die 5 -> -3)
                        # Allowed only if no checkers on points higher than current 'i'
                        # Higher points in home board are i+1 .. 5
                        is_clear = True
                        for k in range(i + 1, 6):
                            if s['my_pts'][k] > 0:
                                is_clear = False
                                break
                        if is_clear:
                            valid = True; is_off = True
            
            if valid:
                ns = clone(s)
                ns['my_pts'][i] -= 1
                if is_off:
                    ns['my_off'] += 1
                else:
                    if ns['opp_pts'][target] == 1:
                        ns['opp_pts'][target] = 0
                        ns['opp_bar'] += 1
                    ns['my_pts'][target] += 1
                moves.append((f"A{i}", ns))
        return moves

    # --- Main Logic ---
    dice = state['dice']
    if not dice: return "H:P,P"
    
    # Sort dice descending: H is 0, L is 1 (if exists)
    sorted_dice = sorted(dice, reverse=True)
    H = sorted_dice[0]
    L = sorted_dice[1] if len(sorted_dice) > 1 else None
    
    # Store all legal final outcomes
    # Item: (sequence_length, uses_high_first_or_only, move_string, final_state)
    candidates = [] 
    
    if L is None:
        # One die case
        steps = get_moves(state, H)
        for m, s in steps:
            candidates.append((1, True, f"H:{m},P", s))
    else:
        # Two dice case
        
        # Path A: Try High die first, then Low die
        h_moves = get_moves(state, H)
        if not h_moves:
            # H blocked immediately
            pass 
        else:
            for m1, s1 in h_moves:
                l_moves = get_moves(s1, L)
                if l_moves:
                    for m2, s2 in l_moves:
                        candidates.append((2, True, f"H:{m1},{m2}", s2))
                else:
                    # L blocked after H
                    candidates.append((1, True, f"H:{m1},P", s1))
        
        # Path B: Try Low die first, then High die
        l_moves = get_moves(state, L)
        for m1, s1 in l_moves:
            h_moves = get_moves(s1, H)
            if h_moves:
                for m2, s2 in h_moves:
                    candidates.append((2, False, f"L:{m1},{m2}", s2))
            else:
                # H blocked after L
                candidates.append((1, False, f"L:{m1},P", s1))

    # If no moves possible
    if not candidates:
        return "H:P,P"
        
    # --- Enforce Rules ---
    
    # Rule 1: Must play both dice if possible
    max_len = max(c[0] for c in candidates)
    best_candidates = [c for c in candidates if c[0] == max_len]
    
    # Rule 2: If only one die can be played, must play higher die
    if max_len == 1 and len(dice) > 1:
        # Check if any candidate used the High die (flag True)
        # Note: In single die case, we set it to True, so this logic is safe
        has_H = any(c[1] for c in best_candidates)
        if has_H:
            best_candidates = [c for c in best_candidates if c[1]]
            
    # --- Find Best Move ---
    best_move_str = "H:P,P"
    best_score = -float('inf')
    
    for _, _, m_str, s in best_candidates:
        sc = evaluate(s)
        if sc > best_score:
            best_score = sc
            best_move_str = m_str
            
    return best_move_str
