
def policy(state):
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    dice = state['dice']
    
    if not dice:
        return "H:P,P"
    
    # Normalize dice
    if len(dice) == 1:
        d1 = dice[0]
        d2 = None
        d_high, d_low = d1, None
    else:
        d1, d2 = dice[0], dice[1]
        d_high = max(d1, d2)
        d_low = min(d1, d2)
    
    # Check if bearing off is allowed (all checkers in home board 0-5 or off)
    can_bear_off = my_bar == 0 and all(my_pts[i] == 0 for i in range(6, 24))
    
    def get_highest_home():
        for i in range(5, -1, -1):
            if my_pts[i] > 0:
                return i
        return -1
    
    def get_sources(pts, bar, die, is_bear_off_allowed):
        """Get valid source points for a given die."""
        sources = []
        if bar > 0:
            # Must enter from bar
            dest = 24 - die
            if 0 <= dest <= 23 and opp_pts[dest] < 2:
                sources.append('B')
        else:
            # Normal moves
            for p in range(24):
                if pts[p] == 0:
                    continue
                dest = p - die
                if dest >= 0:
                    if opp_pts[dest] < 2:
                        sources.append(p)
                else:
                    # Bear off attempt
                    if is_bear_off_allowed and p < die:
                        # Check if p is the highest occupied point
                        h = get_highest_home()
                        if p == h:
                            sources.append(p)
        return sources
    
    def apply_move(pts, bar, opp_pts, opp_bar, src, die):
        """Apply a single checker move. Returns (new_pts, new_bar, new_opp_pts, new_opp_bar, was_hit)."""
        new_pts = list(pts)
        new_opp_pts = list(opp_pts)
        new_bar = bar
        new_opp_bar = opp_bar
        was_hit = False
        
        if src == 'B':
            src_idx = None
            dest = 24 - die
            new_bar -= 1
        else:
            src_idx = src
            dest = src - die
            new_pts[src_idx] -= 1
        
        if dest >= 0:
            if new_opp_pts[dest] == 1:
                # Hit
                new_opp_pts[dest] = 0
                new_opp_bar += 1
                was_hit = True
            new_pts[dest] += 1
        # else: bearing off, dest < 0, no destination point
        
        return new_pts, new_bar, new_opp_pts, new_opp_bar, was_hit
    
    def evaluate(mp, mb, mo, op, ob):
        """Evaluate position from my perspective."""
        score = 0
        
        # Pip count (race)
        my_pips = sum((i+1) * mp[i] for i in range(24)) + mb * 25
        opp_pips = sum((i+1) * op[i] for i in range(24)) + ob * 25
        score += (opp_pips - my_pips) * 1.5
        
        # Home board points (0-5)
        home_points = sum(1 for i in range(6) if mp[i] >= 2)
        score += home_points * 12
        
        # Anchors in opponent home (18-23) - block their entry
        back_points = sum(1 for i in range(18, 24) if mp[i] >= 2)
        score += back_points * 8
        
        # Bar status
        score -= mb * 40
        score += ob * 45
        
        # Blots vulnerability
        for i in range(24):
            if mp[i] == 1:
                vulnerable = False
                # Can opponent hit from their checkers?
                # Opponent moves 0->23, so they hit from lower indices
                for j in range(max(0, i-6), i):
                    if op[j] > 0:
                        vulnerable = True
                        break
                # Can opponent hit from bar?
                if ob > 0 and 18 <= i <= 23:
                    vulnerable = True
                if vulnerable:
                    score -= 20
        
        # Off checkers (endgame)
        score += mo * 15
        
        return score
    
    def gen_move_sequences(first_die, second_die):
        """Generate all valid move sequences for given die order."""
        sequences = []
        
        sources1 = get_sources(my_pts, my_bar, first_die, can_bear_off)
        
        if not sources1:
            # Cannot play first die
            if second_die is not None:
                # Try to play only second die (which is smaller, but we already know first is unplayable)
                sources2 = get_sources(my_pts, my_bar, second_die, can_bear_off)
                for s2 in sources2:
                    new_mp, new_mb, new_op, new_ob, hit = apply_move(my_pts, my_bar, opp_pts, opp_bar, s2, second_die)
                    val = evaluate(new_mp, new_mb, my_off, new_op, new_ob)
                    # This is actually L order if first_die > second_die, but we're in the context where we wanted to play first
                    # For simplicity, we return this as a valid partial move
                    sequences.append((val, 'L' if second_die == d_low else 'H', s2, 'P'))
            return sequences
        
        for s1 in sources1:
            mp1, mb1, op1, ob1, hit1 = apply_move(my_pts, my_bar, opp_pts, opp_bar, s1, first_die)
            
            if second_die is None:
                val = evaluate(mp1, mb1, my_off, op1, ob1)
                seq_order = 'H' if first_die == d_high else 'L'
                sequences.append((val, seq_order, s1, 'P'))
            else:
                # Check if we can play second die
                can_bear_off2 = mb1 == 0 and all(mp1[i] == 0 for i in range(6, 24))
                sources2 = get_sources(mp1, mb1, second_die, can_bear_off2)
                
                if sources2:
                    for s2 in sources2:
                        mp2, mb2, op2, ob2, hit2 = apply_move(mp1, mb1, op1, ob1, s2, second_die)
                        val = evaluate(mp2, mb2, my_off, op2, ob2)
                        seq_order = 'H' if first_die == d_high else 'L'
                        sequences.append((val, seq_order, s1, s2))
                else:
                    # Cannot play second die, but first was playable
                    val = evaluate(mp1, mb1, my_off, op1, ob1)
                    seq_order = 'H' if first_die == d_high else 'L'
                    sequences.append((val, seq_order, s1, 'P'))
        
        return sequences
    
    candidates = []
    
    # Try H order: high die first
    if d_high is not None:
        if d_low is None:
            # Single die
            seqs = gen_move_sequences(d_high, None)
            candidates.extend(seqs)
        else:
            seqs = gen_move_sequences(d_high, d_low)
            for val, ord_char, s1, s2 in seqs:
                if ord_char == 'H':
                    candidates.append((val, 'H', s1, s2))
    
    # Try L order: low die first (only if dice different and both exist)
    if d_low is not None and d_high != d_low:
        seqs = gen_move_sequences(d_low, d_high)
        for val, ord_char, s1, s2 in seqs:
            # In L order, we played low first, so mark as L
            candidates.append((val, 'L', s1, s2))
    
    if not candidates:
        return "H:P,P"
    
    # Sort by value descending
    candidates.sort(key=lambda x: x[0], reverse=True)
    _, order, src1, src2 = candidates[0]
    
    def fmt_src(s):
        if s == 'P':
            return 'P'
        elif s == 'B':
            return 'B'
        else:
            return f'A{s}'
    
    return f"{order}:{fmt_src(src1)},{fmt_src(src2)}"
