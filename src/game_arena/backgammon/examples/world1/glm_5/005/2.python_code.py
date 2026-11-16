
import copy

def policy(state: dict) -> str:
    """
    Calculates the best move for the current Backgammon state.
    """
    # Extract state variables
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    # Helper to check if a point is valid landing spot
    # Point indices are 0-23.
    # We move 23 -> 0. Home is 0-5.
    # Landing on a point with >= 2 opponent checkers is illegal.
    
    def get_landing_point(start, die):
        if start == 'B':
            # Enter from bar. 
            # Opponent home is 18-23.
            # Die 1 -> 23, Die 6 -> 18.
            return 24 - die
        else:
            return start - die

    def is_valid_landing(idx, opp_pts_local):
        if idx < 0: # Bearing off
            return True
        if idx > 23: # Should not happen for normal moves
            return False
        return opp_pts_local[idx] < 2

    def apply_move(my_pts_local, opp_pts_local, my_bar_local, opp_bar_local, my_off_local, start, die):
        """
        Applies a move to a state copy.
        Returns (new_my_pts, new_opp_pts, new_my_bar, new_opp_bar, new_my_off, valid)
        """
        target = get_landing_point(start, die)
        
        # Check validity
        if target >= 0 and target <= 23:
            if opp_pts_local[target] >= 2:
                return None, None, None, None, None, False
        
        new_my_pts = list(my_pts_local)
        new_opp_pts = list(opp_pts_local)
        new_my_bar = my_bar_local
        new_opp_bar = opp_bar_local
        new_my_off = my_off_local
        
        # Execute move
        if start == 'B':
            new_my_bar -= 1
        else:
            new_my_pts[start] -= 1
            
        if target < 0:
            # Bear off
            new_my_off += 1
        else:
            new_my_pts[target] += 1
            # Check hit
            if new_opp_pts[target] == 1:
                new_opp_pts[target] = 0
                new_opp_bar += 1
                
        return new_my_pts, new_opp_pts, new_my_bar, new_opp_bar, new_my_off, True

    def can_bear_off(my_pts_local, my_bar_local):
        if my_bar_local > 0: return False
        # All checkers must be in home board (0-5)
        # sum of checkers from 6 to 23 must be 0
        return sum(my_pts_local[6:]) == 0

    def get_bear_off_move(my_pts_local, start, die):
        # If exact bear off
        if start == die - 1:
            return True
        # If die is larger than point distance
        if start < die - 1:
            # Check if there are checkers on higher points
            # We are at 'start'. We want to use 'die'.
            # If we are at 2 (distance 3), and die is 5.
            # We can bear off if there are no checkers at 3, 4, 5...
            # Index start+1 to 5.
            if sum(my_pts_local[start+1:6]) == 0:
                return True
        return False

    def get_possible_moves(my_pts_local, opp_pts_local, my_bar_local, die):
        moves = []
        
        # Must move from bar first
        if my_bar_local > 0:
            target = 24 - die
            if is_valid_landing(target, opp_pts_local):
                moves.append('B')
            return moves # Even if list is empty, we can't move others
        
        # Check board moves
        for i in range(23, -1, -1):
            if my_pts_local[i] > 0:
                target = i - die
                # Normal move
                if target >= 0:
                    if is_valid_landing(target, opp_pts_local):
                        moves.append(i)
                # Bear off
                elif can_bear_off(my_pts_local, 0): # my_bar is 0 checked implicitly by loop above usually, but safer to pass it
                    if get_bear_off_move(my_pts_local, i, die):
                        moves.append(i)
        return moves

    def evaluate_state(my_pts_local, opp_pts_local, my_bar_local, my_off_local, opp_bar_local):
        score = 0
        # 1. Pip count (lower is better) -> We maximize negative pip count
        # Points 0-23. Checker at 23 has 23 pips to go? No, to go to off.
        # Pip = index + 1 (approx, ignoring bearing off precision)
        pip_count = my_bar_local * 25 # Bar is roughly 25 pips (enter at 24 + 1)
        for i, count in enumerate(my_pts_local):
            if count > 0:
                pip_count += (i + 1) * count
        
        score -= pip_count * 10
        
        # 2. Borne off checkers (Huge bonus)
        score += my_off_local * 10000
        
        # 3. Opponent on Bar (Tactical advantage)
        score += opp_bar_local * 100
        
        # 4. Board Strength (Made points)
        # Pairs in home board are very good
        for i in range(6):
            if my_pts_local[i] >= 2:
                score += 50 - i * 2 # Closer to edge is slightly better?
                
        # Pairs in outer board are good
        for i in range(6, 24):
            if my_pts_local[i] >= 2:
                score += 20
        
        # 5. Blots (Single checkers) - Penalty
        # Blots in opponent's home board (18-23) or far out are dangerous
        for i in range(6, 24):
            if my_pts_local[i] == 1:
                # Penalty increases with distance
                score -= 30 + i
        
        return score

    # Main logic
    if not dice:
        return "H:P,P"

    # Resolve doubles logic: If dice are equal, H and L are same. 
    # We just iterate through H and L combinations.
    d1, d2 = dice[0], dice[-1] # handles length 1 or 2
    dice_set = sorted(list(set(dice)), reverse=True)
    
    # We need to check if we have 1 or 2 dice provided in the list.
    # State['dice'] can be length 1 or 2.
    
    best_move = None
    best_score = -float('inf')
    
    # We try both orders: H then L, and L then H.
    # d_high, d_low
    d_high = max(dice)
    d_low = min(dice)
    
    # Handle single die case gracefully
    if len(dice) == 1:
        # Only one die, just find best move for that die
        # Order doesn't matter, use H
        possible_starts = get_possible_moves(my_pts, opp_pts, my_bar, d_high)
        for start in possible_starts:
            # Calc score
            next_my_pts, next_opp_pts, next_my_bar, next_opp_bar, next_my_off, valid = \
                apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, start, d_high)
            if valid:
                score = evaluate_state(next_my_pts, next_opp_pts, next_my_bar, next_my_off, next_opp_bar)
                if score > best_score:
                    best_score = score
                    s_str = "B" if start == 'B' else f"A{start}"
                    best_move = f"H:{s_str},P"
        if best_move: return best_move
        return "H:P,P"

    # Two dice logic
    # Try Sequence 1: High then Low
    # Order = H
    starts_high = get_possible_moves(my_pts, opp_pts, my_bar, d_high)
    for s1 in starts_high:
        # Apply first move
        pts1, opp_pts1, bar1, opp_bar1, off1, valid1 = \
            apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, s1, d_high)
        if not valid1: continue
        
        # Get possible second moves
        starts_low = get_possible_moves(pts1, opp_pts1, bar1, d_low)
        if not starts_low:
            # Can only play one die?
            # Evaluate state after one die
            score = evaluate_state(pts1, opp_pts1, bar1, off1, opp_bar1)
            if score > best_score:
                best_score = score
                s1_str = "B" if s1 == 'B' else f"A{s1}"
                best_move = f"H:{s1_str},P" # Played High, Pass Low
        else:
            for s2 in starts_low:
                pts2, opp_pts2, bar2, opp_bar2, off2, valid2 = \
                    apply_move(pts1, opp_pts1, bar1, opp_bar1, off1, s2, d_low)
                if valid2:
                    score = evaluate_state(pts2, opp_pts2, bar2, off2, opp_bar2)
                    if score > best_score:
                        best_score = score
                        s1_str = "B" if s1 == 'B' else f"A{s1}"
                        s2_str = "B" if s2 == 'B' else f"A{s2}"
                        best_move = f"H:{s1_str},{s2_str}"

    # Try Sequence 2: Low then High
    # Order = L
    starts_low_init = get_possible_moves(my_pts, opp_pts, my_bar, d_low)
    for s1 in starts_low_init:
        pts1, opp_pts1, bar1, opp_bar1, off1, valid1 = \
            apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, s1, d_low)
        if not valid1: continue
        
        starts_high_next = get_possible_moves(pts1, opp_pts1, bar1, d_high)
        if not starts_high_next:
            # Can only play one die?
            score = evaluate_state(pts1, opp_pts1, bar1, off1, opp_bar1)
            # Note: Rule says if only one die can be played, must play higher.
            # However, if we CAN play Low but CANNOT play High afterwards, maybe we could have played High alone?
            # The engine enforces "must play higher die when possible".
            # This implies if we can play High (alone) that takes precedence over playing Low (alone).
            # But here we are constructing a move string.
            # If we found a valid H:P move previously, it should be preferred if score is similar?
            # Actually, we rely on the previous loop (H order) to catch "Play High only".
            # This loop catches "Play Low then High" (Full move).
            # If we are here, we played Low.
            # If we can't play High next, we check if this state is good.
            # But strict rule: "If only one die can be played, you must play the higher die when possible."
            # If `starts_high` (from initial state) was not empty, we should have played it.
            # So if we play Low alone, we must ensure High was unplayable initially.
            # BUT `starts_high` might be dependent on playing Low first?
            # No, starts_high is computed on initial state.
            # If `starts_high` was non-empty, we shouldn't output `L:s1,P` unless `starts_low` was empty? No.
            # Logic: If we can play H, we must.
            # If we output `L:...,P` we are playing Low only. This is illegal if High was playable.
            # So we should penalize single-Low moves if High was playable.
            
            # Check if High was playable initially
            high_playable_initially = len(starts_high) > 0
            if high_playable_initially:
                # We cannot play Low only. Skip or penalize heavily.
                continue 
            
            if score > best_score:
                best_score = score
                s1_str = "B" if s1 == 'B' else f"A{s1}"
                best_move = f"L:{s1_str},P"
        else:
            for s2 in starts_high_next:
                pts2, opp_pts2, bar2, opp_bar2, off2, valid2 = \
                    apply_move(pts1, opp_pts1, bar1, opp_bar1, off1, s2, d_high)
                if valid2:
                    score = evaluate_state(pts2, opp_pts2, bar2, off2, opp_bar2)
                    if score > best_score:
                        best_score = score
                        s1_str = "B" if s1 == 'B' else f"A{s1}"
                        s2_str = "B" if s2 == 'B' else f"A{s2}"
                        best_move = f"L:{s1_str},{s2_str}"

    if best_move:
        return best_move
        
    # If absolutely no moves found (should be caught by P,P logic usually, but safety)
    return "H:P,P"

