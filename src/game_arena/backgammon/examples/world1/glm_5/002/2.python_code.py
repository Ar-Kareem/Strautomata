
import copy

def policy(state: dict) -> str:
    """
    Calculates the best move for the given backgammon state.
    Returns a move string in the format <ORDER>:<FROM1>,<FROM2>.
    """
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    # Determine dice values
    if not dice:
        return "H:P,P"
    
    d1, d2 = (dice[0], dice[0]) if len(dice) == 1 else (dice[0], dice[1])
    
    # Sort dice to identify High and Low
    # Note: The prompt says H means first move uses higher die.
    low_d = min(d1, d2)
    high_d = max(d1, d2)
    
    # Helper to check if a point is valid for landing
    def is_valid_dest(pt_idx, opp_pts_arr):
        if pt_idx < 0: # Bearing off
            return True
        # Cannot land on point with 2+ opponent checkers
        return opp_pts_arr[pt_idx] < 2

    # Helper to get valid sources for a specific die value
    def get_sources(die_val, my_pts_arr, my_bar_cnt, opp_pts_arr):
        sources = []
        
        # 1. Must move from Bar if checkers are there
        if my_bar_cnt > 0:
            dest = 24 - die_val # Entering from bar (opponent's home board 18-23)
            if is_valid_dest(dest, opp_pts_arr):
                sources.append('B')
            return sources # If bar is occupied, we must attempt to move from it. If no valid dest, we can't move this die.
        
        # 2. Move from points
        # Check bearing off
        home_board_range = range(6) # 0..5
        all_in_home = True
        for i in range(6, 24):
            if my_pts_arr[i] > 0:
                all_in_home = False
                break
        
        for i in range(23, -1, -1):
            if my_pts_arr[i] == 0:
                continue
            
            dest = i - die_val
            
            if dest >= 0:
                if is_valid_dest(dest, opp_pts_arr):
                    sources.append(f'A{i}')
            elif all_in_home:
                # Bearing off logic
                # Exact roll
                if dest == -1:
                    sources.append(f'A{i}')
                # Higher roll
                else:
                    # Can bear off from i if i is the furthest checker
                    # i is the 'highest' point index occupied.
                    # Check if there are checkers on points > i
                    has_higher = False
                    for j in range(i + 1, 6):
                        if my_pts_arr[j] > 0:
                            has_higher = True
                            break
                    if not has_higher:
                        sources.append(f'A{i}')
                        
        return sources

    # Helper to apply a move to a copied state
    def apply_move(s, src, die_val):
        # s is a tuple: (my_pts, opp_pts, my_bar, opp_bar)
        my_pts_c, opp_pts_c, my_bar_c, opp_bar_c = s
        
        my_pts_n = list(my_pts_c)
        opp_pts_n = list(opp_pts_c)
        my_bar_n = my_bar_c
        opp_bar_n = opp_bar_c
        
        dest = -1
        
        if src == 'B':
            my_bar_n -= 1
            dest = 24 - die_val
        else:
            pt_idx = int(src[1:])
            my_pts_n[pt_idx] -= 1
            dest = pt_idx - die_val
            
        if dest >= 0:
            # Check for hit
            if opp_pts_n[dest] == 1:
                opp_pts_n[dest] = 0
                opp_bar_n += 1
            my_pts_n[dest] += 1
        # else: bearing off, checker removed
        
        return (my_pts_n, opp_pts_n, my_bar_n, opp_bar_n)

    # Evaluation function
    def evaluate(s):
        my_pts_e, opp_pts_e, my_bar_e, opp_bar_e = s
        
        score = 0
        
        # 1. Pip Count (Lower is better for me, Higher is better for opp)
        # My pip count
        my_pips = my_bar_e * 25
        for i, cnt in enumerate(my_pts_e):
            if cnt > 0:
                my_pips += cnt * (i + 1)
        score -= my_pips * 10
        
        # Opponent pip count (we want to maximize this)
        opp_pips = opp_bar_e * 25
        for i, cnt in enumerate(opp_pts_e):
            if cnt > 0:
                opp_pips += cnt * (24 - i)
        score += opp_pips * 10
        
        # 2. Home Board Points (Strong home board is good)
        for i in range(6):
            if my_pts_e[i] >= 2:
                score += 50
        
        # 3. Blots (Vulnerability)
        for i, cnt in enumerate(my_pts_e):
            if cnt == 1:
                # Penalize blots more if in opponent's home board or exposed
                if i >= 18: # Opponent's home board
                    score -= 40
                else:
                    score -= 15
                    
        # 4. Pointing (Making points)
        for i, cnt in enumerate(my_pts_e):
            if cnt >= 2:
                score += 30
                
        return score

    # Generate all valid move sequences
    # Sequence: (move_str, resulting_state, dice_used_count)
    candidates = []
    
    # We handle single die logic manually to ensure correct move generation
    # Try double moves first
    
    # Order: H means High first. L means Low first.
    # Format: Order:From1,From2
    
    # Case 1: Use High die then Low die (Order 'H')
    s1_sources = get_sources(high_d, my_pts, my_bar, opp_pts)
    for s1 in s1_sources:
        # Apply s1 with high_d
        state_after_1 = apply_move((my_pts, opp_pts, my_bar, opp_bar), s1, high_d)
        # Check if we can play second die
        s2_sources = get_sources(low_d, *state_after_1)
        for s2 in s2_sources:
            # We can play both dice
            final_state = apply_move(state_after_1, s2, low_d)
            move_str = f"H:{s1},{s2}"
            candidates.append((move_str, final_state, 2))
            
    # Case 2: Use Low die then High die (Order 'L')
    # Only if dice are different
    if high_d != low_d:
        s1_sources = get_sources(low_d, my_pts, my_bar, opp_pts)
        for s1 in s1_sources:
            state_after_1 = apply_move((my_pts, opp_pts, my_bar, opp_bar), s1, low_d)
            s2_sources = get_sources(high_d, *state_after_1)
            for s2 in s2_sources:
                final_state = apply_move(state_after_1, s2, high_d)
                move_str = f"L:{s1},{s2}"
                candidates.append((move_str, final_state, 2))
    
    # If we found moves using both dice, pick the best one
    # The rules say "If both dice can be played, you must play both."
    # But we should check if *any* combination uses both.
    
    double_moves = [c for c in candidates if c[2] == 2]
    
    if double_moves:
        # Evaluate and pick best
        best_move = max(double_moves, key=lambda x: evaluate(x[1]))
        return best_move[0]
        
    # If no double moves, try single moves
    # Rule: "If only one die can be played, you must play the higher die when possible."
    
    single_candidates = []
    
    # Try High die
    high_sources = get_sources(high_d, my_pts, my_bar, opp_pts)
    for s in high_sources:
        final_state = apply_move((my_pts, opp_pts, my_bar, opp_bar), s, high_d)
        # Format for single move: H:From,P
        move_str = f"H:{s},P"
        single_candidates.append((move_str, final_state, 'H'))
        
    # Try Low die
    low_sources = get_sources(low_d, my_pts, my_bar, opp_pts)
    for s in low_sources:
        final_state = apply_move((my_pts, opp_pts, my_bar, opp_bar), s, low_d)
        # Format: L:From,P
        move_str = f"L:{s},P"
        single_candidates.append((move_str, final_state, 'L'))
        
    if single_candidates:
        # Check rule: play higher if possible
        high_moves = [m for m in single_candidates if m[2] == 'H']
        if high_moves:
            best_move = max(high_moves, key=lambda x: evaluate(x[1]))
            return best_move[0]
        else:
            # If high not possible, play low
            best_move = max(single_candidates, key=lambda x: evaluate(x[1]))
            return best_move[0]
            
    # If absolutely no moves
    return "H:P,P"

