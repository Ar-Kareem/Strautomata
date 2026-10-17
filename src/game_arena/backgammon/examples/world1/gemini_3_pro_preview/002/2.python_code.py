
import copy

def policy(state: dict) -> str:
    """
    Backgammon policy that performs a generic 1-ply search (full turn simulation)
    to find the best legal move based on a heuristic evaluation.
    """
    
    # --- Constants & Setup ---
    BOARD_SIZE = 24
    BAR_IDX = 24  # Logical index for 'my_bar' entering to 23..0
    
    # Unpack State
    # my_pts: My checkers on points 0..23 (I move 23 -> 0)
    # opp_pts: Opp checkers on points 0..23 (Opp moves 0 -> 23)
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    
    # Prepare Dice
    # Input is list of 0, 1, or 2 ints. 
    # Doubles might come as [X, X].
    raw_dice = state['dice']
    if not raw_dice:
        return "H:P,P"
        
    # Sort dice descending for standard processing (High, Low)
    # We will explicitly try permutations if needed.
    dice_desc = sorted(raw_dice, reverse=True)
    
    # --- Helper Functions ---

    def get_dest(start_idx, die):
        """Calculates destination index from my perspective (23 -> 0)."""
        if start_idx == BAR_IDX:
            # Entering from bar: '24' -> 24 - die
            return 24 - die
        return start_idx - die

    def is_legal(c_my_pts, c_opp_pts, c_my_bar, start, die):
        """Checks if a single checker move is legal."""
        dest = get_dest(start, die)
        
        # 1. Source Validation
        if start == BAR_IDX:
            if c_my_bar <= 0: return False
        else:
            if c_my_bar > 0: return False # Must move from bar first
            if c_my_pts[start] <= 0: return False

        # 2. Destination Validation
        if dest < 0:
            # Bearing Off
            # Rule: All checkers must be in home board (0-5)
            # Check for checkers > 5
            if c_my_bar > 0: return False
            # Check indices 6 to 23
            for i in range(6, 24):
                if c_my_pts[i] > 0: return False
                
            # Exact bear off or override
            if dest == -1: 
                return True # Exact fit
            
            # If dest < -1 (e.g. roll 6 from point 2), allowable ONLY if 
            # no checkers are on points greater than start in the home board.
            # "Greater" in my home board 0..5 means indices > start.
            for i in range(start + 1, 6):
                if c_my_pts[i] > 0: return False
            return True
        else:
            # Standard Move
            # Rule: Destination not blocked by 2+ opponents
            if c_opp_pts[dest] >= 2:
                return False
            return True

    def apply(c_state, start, die):
        """Applies a single move and returns new state (tuple)."""
        mp, op, mb, ob, mo = c_state
        # Clone lists
        mp = list(mp)
        op = list(op)
        
        dest = get_dest(start, die)
        
        # Move Source
        if start == BAR_IDX:
            mb -= 1
        else:
            mp[start] -= 1
            
        # Move Dest
        if dest < 0:
            mo += 1
        else:
            # Check Hit
            if op[dest] == 1:
                op[dest] = 0
                ob += 1
            mp[dest] += 1
            
        return (mp, op, mb, ob, mo)

    def evaluate(mp, op, mb, ob, mo):
        """Heuristic scoring of a board state from my perspective."""
        score = 0.0
        
        # 1. Pip Count (Race) - Lower is better for me
        # My Pips: index i counts as i+1 distance. Bar is 25.
        my_pips = sum(count * (i + 1) for i, count in enumerate(mp)) + (mb * 25)
        
        # Opponent Pips: Opp moves 0->23. 
        # Index 0 is their '24' point. Index 23 is their '1' point.
        opp_pips = sum(count * (24 - i) for i, count in enumerate(op)) + (ob * 25)
        
        # Pip difference metric
        score -= (my_pips * 0.6)
        
        # 2. Hitting (Very valuable)
        score += (ob * 80)
        
        # 3. Bearing Off (Goal)
        score += (mo * 60)
        
        # 4. Blots (Risk)
        # Blot = single checker on a point
        blots = sum(1 for c in mp if c == 1)
        score -= (blots * 15)
        
        # 5. Asset Building
        # Points (Primes): >=2 checkers
        my_points = sum(1 for c in mp if c >= 2)
        score += (my_points * 12)
        
        # Anchors: Points held in opponent home board (indices 18-23 for me)
        anchors = sum(1 for i in range(18, 24) if mp[i] >= 2)
        score += (anchors * 20)
        
        return score

    # --- Move Generation ---
    
    # Store all valid paths: (score, steps_count, order_char, move1_str, move2_str)
    candidate_paths = []
    
    # Define permutations to try.
    # If 2 dice: Try [D1, D2] (High-Low) and [D2, D1] (Low-High).
    # If distinct, these are diff paths. If doubles, same path logic.
    sequences = []
    if len(dice_desc) == 2:
        # High First
        sequences.append( ('H', [dice_desc[0], dice_desc[1]]) )
        # Low First (only if different)
        if dice_desc[0] != dice_desc[1]:
            sequences.append( ('L', [dice_desc[1], dice_desc[0]]) )
    else:
        # Single die
        sequences.append( ('H', [dice_desc[0]]) )

    base_state = (my_pts, opp_pts, my_bar, opp_bar, my_off)

    for order_char, d_seq in sequences:
        d1 = d_seq[0]
        
        # Identify sources for Move 1
        sources1 = []
        if my_bar > 0:
            sources1 = [BAR_IDX]
        else:
            sources1 = [i for i, c in enumerate(my_pts) if c > 0]
            
        legal_move_found = False
        
        for s1 in sources1:
            if is_legal(my_pts, opp_pts, my_bar, s1, d1):
                legal_move_found = True
                state_after_1 = apply(base_state, s1, d1)
                
                m1_str = "B" if s1 == BAR_IDX else f"A{s1}"
                
                # If only 1 die to play
                if len(d_seq) == 1:
                    sc = evaluate(*state_after_1)
                    candidate_paths.append((sc, 1, 'H', m1_str, 'P'))
                    continue
                
                # Check Move 2
                d2 = d_seq[1]
                mp2, op2, mb2, ob2, mo2 = state_after_1
                
                sources2 = []
                if mb2 > 0:
                    sources2 = [BAR_IDX]
                else:
                    sources2 = [i for i, c in enumerate(mp2) if c > 0]
                
                second_move_found = False
                for s2 in sources2:
                    if is_legal(mp2, op2, mb2, s2, d2):
                        second_move_found = True
                        state_after_2 = apply(state_after_1, s2, d2)
                        m2_str = "B" if s2 == BAR_IDX else f"A{s2}"
                        
                        # Calculate final score
                        sc = evaluate(*state_after_2)
                        
                        # Determine order logic for 2 dice
                        # If we played High then Low, order is H.
                        # If we played Low then High, order is L.
                        # For doubles, default H.
                        path_order = 'H'
                        if len(raw_dice) == 2 and raw_dice[0] != raw_dice[1]:
                            # Map actual played dice back to H or L
                            if d1 < d2: path_order = 'L'
                        
                        candidate_paths.append((sc, 2, path_order, m1_str, m2_str))
                
                # If no second move possible, record partial
                if not second_move_found:
                    sc = evaluate(*state_after_1)
                    
                    # Logic: partial move uses d1.
                    # Was d1 high or low?
                    path_order = 'H'
                    if len(raw_dice) == 2 and raw_dice[0] != raw_dice[1]:
                        if d1 < max(raw_dice): path_order = 'L'
                    
                    candidate_paths.append((sc, 1, path_order, m1_str, 'P'))
        
        if not legal_move_found:
            # Path blocked completely
            candidate_paths.append((-float('inf'), 0, 'H', 'P', 'P'))

    # --- Selection Logic ---
    
    if not candidate_paths:
        return "H:P,P"

    # 1. Prune by Step Count (Play Both rule)
    max_steps = max(p[1] for p in candidate_paths)
    best_paths = [p for p in candidate_paths if p[1] == max_steps]
    
    # 2. Prune by Die Value (Play Higher rule)
    # If we could only play 1 die, but we had 2 dice, we must play the higher one.
    if len(raw_dice) == 2 and max_steps == 1 and raw_dice[0] != raw_dice[1]:
        # 'H' indicates we used the higher die (or started with it)
        # However, our path generation logic labeled them correctly.
        # If order was L and resulted in 1 step, it means we used Lower die.
        # If order was H and resulted in 1 step, we used Higher die.
        # Filter for H only.
        high_paths = [p for p in best_paths if p[2] == 'H']
        if high_paths:
            best_paths = high_paths
            
    # 3. Pick Max Score
    best_paths.sort(key=lambda x: x[0], reverse=True)
    best_move = best_paths[0]
    
    return f"{best_move[2]}:{best_move[3]},{best_move[4]}"
