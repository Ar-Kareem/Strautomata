
import random

def policy(state: dict) -> str:
    """
    Backgammon policy that generates legal moves, enforces forced-move rules,
    and selects the best action based on a heuristic evaluation.
    """
    
    # --- 1. Helper Functions ---

    def get_state_copy(s):
        """Creates a deep copy of the state for simulation."""
        return {
            'my_pts': list(s['my_pts']),
            'opp_pts': list(s['opp_pts']),
            'my_bar': s['my_bar'],
            'opp_bar': s['opp_bar'],
            'my_off': s['my_off'],
            'opp_off': s['opp_off']
        }

    def can_bear_off(s):
        """Check if bearing off is permitted (all checkers in home board 0-5)."""
        if s['my_bar'] > 0:
            return False
        # Check indices 6 to 23
        for i in range(6, 24):
            if s['my_pts'][i] > 0:
                return False
        return True

    def try_move(s, src_type, src_idx, die):
        """
        Simulates a single move.
        Returns the new state dict if legal, or None if illegal.
        src_type: 'B' (Bar) or 'P' (Point)
        src_idx: 0..23 (ignored if src_type is 'B')
        die: integer (1..6)
        """
        ns = get_state_copy(s)
        
        # -- Source Validation --
        if src_type == 'B':
            if ns['my_bar'] <= 0:
                return None
            # Move from Bar: entry point is 24 - die.
            # Indices: 24-1=23, ..., 24-6=18.
            dest = 24 - die
        else:
            if ns['my_bar'] > 0:
                return None # Must move from Bar first
            if ns['my_pts'][src_idx] <= 0:
                return None # No checker here
            dest = src_idx - die
            
        # -- Destination Validation --
        if dest < 0:
            # Attempting to bear off
            if not can_bear_off(ns):
                return None
            
            # Exact bear-off check
            if dest == -1:
                pass # Exact roll, allowed
            else:
                # Overkill roll (dest < -1). Allowed ONLY if no checkers on higher points.
                # "Higher" means indices > src_idx (further from 0).
                # Since can_bear_off passed, range 6..23 is empty. Check src_idx+1 .. 5.
                for k in range(src_idx + 1, 6):
                    if ns['my_pts'][k] > 0:
                        return None
        else:
            # Moving to a point on board
            if ns['opp_pts'][dest] >= 2:
                return None # Blocked by opponent prime
        
        # -- Apply Move --
        # Remove from source
        if src_type == 'B':
            ns['my_bar'] -= 1
        else:
            ns['my_pts'][src_idx] -= 1
        
        # Add to dest
        if dest < 0:
            ns['my_off'] += 1
        else:
            # Check for hit
            if ns['opp_pts'][dest] == 1:
                ns['opp_pts'][dest] = 0
                ns['opp_bar'] += 1
            ns['my_pts'][dest] += 1
            
        return ns

    def get_moves_for_die(s, die):
        """
        Finds all legal single steps for a specific die.
        Returns list of tuples: (move_string_component, resulting_state)
        e.g., [('B', State), ('A5', State)]
        """
        moves = []
        
        # If checkers on Bar, MUST move from Bar
        if s['my_bar'] > 0:
            res = try_move(s, 'B', 0, die)
            if res:
                moves.append(('B', res))
            return moves
        
        # Otherwise, check all points with checkers
        for i in range(24):
            if s['my_pts'][i] > 0:
                res = try_move(s, 'P', i, die)
                if res:
                    moves.append((f'A{i}', res))
        return moves

    def evaluate(s):
        """
        Heuristic evaluation. Higher score is better.
        Factors: Pips, Hitting, Safety, Structure.
        """
        # 1. Pip Count (Lower pips = better race).
        # We start at 23, move to 0. Distance to off is index + 1.
        my_pips = sum(c * (i + 1) for i, c in enumerate(s['my_pts'])) + s['my_bar'] * 25
        # Opponent moves 0->23. Distance is 24 - index.
        opp_pips = sum(c * (24 - i) for i, c in enumerate(s['opp_pts'])) + s['opp_bar'] * 25
        
        # Base score is pip difference
        score = (opp_pips - my_pips)
        
        # 2. Hitting Bonus (Significant reward)
        # Compare current opp_bar to original to detect hits
        score += (s['opp_bar'] - state['opp_bar']) * 60
        
        # 3. Winning (Bearing off)
        if s['my_off'] == 15:
            return 100000 # Instant win
        score += s['my_off'] * 20
        
        # 4. Safety (Penalize blots)
        blots = 0
        for i in range(24):
            if s['my_pts'][i] == 1:
                blots += 1
                # Extra penalty if blot is effectively behind opponent (vulnerable)
                # Or specifically in home board if being re-entered on
                if i < 6 and s['opp_bar'] > 0:
                    score -= 50
        score -= blots * 15
        
        # 5. Structure (Anchors / Primes)
        for i in range(24):
            if s['my_pts'][i] >= 2:
                score += 8
                # Bonus for adjacent points (Prime building)
                if i > 0 and s['my_pts'][i-1] >= 2:
                    score += 4
                    
        return score

    # --- 2. Main Logic ---

    dice = state['dice']
    if not dice:
        return "H:P,P"

    candidates = [] # List of (move_string, final_state)

    if len(dice) == 1:
        # Case: Single die (e.g. end of game or weird state)
        d = dice[0]
        moves = get_moves_for_die(state, d)
        if not moves:
            return "H:P,P"
        for m_str, ns in moves:
            candidates.append((f"H:{m_str},P", ns))
            
    elif len(dice) == 2:
        d1, d2 = dice[0], dice[1]
        high, low = max(d1, d2), min(d1, d2)
        
        # Generate H sequences (High then Low)
        h_seqs = []
        # high first
        moves1 = get_moves_for_die(state, high)
        if not moves1:
            # High cannot start, so H sequence is empty or invalid
            pass
        else:
            for m1, s1 in moves1:
                # then low
                moves2 = get_moves_for_die(s1, low)
                if moves2:
                    for m2, s2 in moves2:
                        h_seqs.append((f"H:{m1},{m2}", s2))
                else:
                    # Partial: High works, Low fails
                    h_seqs.append((f"H:{m1},P", s1))
        
        # Generate L sequences (Low then High)
        l_seqs = []
        # low first
        moves1 = get_moves_for_die(state, low)
        if not moves1:
            pass
        else:
            for m1, s1 in moves1:
                # then high
                moves2 = get_moves_for_die(s1, high)
                if moves2:
                    for m2, s2 in moves2:
                        l_seqs.append((f"L:{m1},{m2}", s2))
                else:
                    # Partial: Low works, High fails
                    l_seqs.append((f"L:{m1},P", s1))

        # --- Filter Rule: "If both dice can be played, you must play both" ---
        full_h = [x for x in h_seqs if not x[0].endswith('P')]
        full_l = [x for x in l_seqs if not x[0].endswith('P')]
        
        if full_h or full_l:
            candidates = full_h + full_l
        else:
            # No full moves.
            # --- Filter Rule: "If only one die can be played, must play higher" ---
            
            # Check if High could be played as a single move.
            # This consists of partials where High was played first.
            partials_using_high = [x for x in h_seqs if x[0].endswith('P')]
            
            # What if High can be played ONLY as a second move?
            # e.g. Low -> High is a full move (handled above).
            # e.g. Low -> High blocked? Then High wasn't played.
            # e.g. High blocked -> Low OK? This is a Low-only move.
            
            if partials_using_high:
                candidates = partials_using_high
            else:
                # High couldn't be played. Are there Low moves?
                partials_using_low = [x for x in l_seqs if x[0].endswith('P')]
                if partials_using_low:
                    candidates = partials_using_low
                else:
                    return "H:P,P"

    if not candidates:
        return "H:P,P"

    # --- 3. Selection ---
    best_move = "H:P,P"
    best_score = -float('inf')
    
    # Shuffle to avoid directional bias in ties
    random.shuffle(candidates)
    
    for cmd, ns in candidates:
        sc = evaluate(ns)
        if sc > best_score:
            best_score = sc
            best_move = cmd
            
    return best_move
