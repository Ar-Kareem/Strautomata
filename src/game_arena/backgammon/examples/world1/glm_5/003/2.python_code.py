
def policy(state: dict) -> str:
    """
    Backgammon policy using position evaluation for move selection.
    Evaluates moves based on pip count, point making, safety, and hitting.
    """
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = list(state['dice'])
    
    def get_bar_dest(die):
        """Get destination when entering from bar."""
        return 24 - die
    
    def can_bear_off_state(pts, bar):
        """Check if all checkers are in home board (points 0-5)."""
        if bar > 0:
            return False
        return all(pts[i] == 0 for i in range(6, 24))
    
    def get_sources_for_die(pts, opp, bar, die):
        """Get all valid source points for a move with given die."""
        sources = []
        if bar > 0:
            dest = get_bar_dest(die)
            if 0 <= dest < 24 and opp[dest] < 2:
                sources.append("B")
        else:
            bear_off = can_bear_off_state(pts, bar)
            for i in range(24):
                if pts[i] > 0:
                    dest = i - die
                    if dest >= 0:
                        if opp[dest] < 2:
                            sources.append(f"A{i}")
                    elif bear_off:
                        exact_point = die - 1
                        if i == exact_point:
                            sources.append(f"A{i}")
                        elif i < exact_point:
                            if all(pts[j] == 0 for j in range(i + 1, min(exact_point + 1, 6))):
                                sources.append(f"A{i}")
        return sources
    
    def simulate_move(pts, opp, bar, source, die):
        """Simulate move and return new board state."""
        new_pts = pts.copy()
        new_opp = opp.copy()
        new_bar = bar
        
        if source == "B":
            new_bar -= 1
            dest = get_bar_dest(die)
            if new_opp[dest] == 1:
                new_opp[dest] = 0
            new_pts[dest] += 1
        else:
            pt = int(source[1:])
            new_pts[pt] -= 1
            dest = pt - die
            if dest >= 0:
                if new_opp[dest] == 1:
                    new_opp[dest] = 0
                new_pts[dest] += 1
        return new_pts, new_opp, new_bar
    
    def evaluate_state(pts, opp, bar, off, opp_orig, init_opp_bar):
        """Evaluate board position."""
        score = 0.0
        
        # Pip count
        my_pip = sum(pts[i] * (i + 1) for i in range(24)) + bar * 25
        opp_pip = sum(opp_orig[i] * (24 - i) for i in range(24)) + init_opp_bar * 25
        score -= my_pip * 0.1
        score += opp_pip * 0.05
        
        # Points made
        for i in range(24):
            if pts[i] >= 2:
                if i < 6:
                    score += 14
                elif i >= 18:
                    score += 18
                else:
                    score += 10
        
        # Prime detection
        prime_len = 0
        for i in range(24):
            if pts[i] >= 2:
                prime_len += 1
            else:
                if prime_len >= 3:
                    score += prime_len ** 2 * 3
                prime_len = 0
        if prime_len >= 3:
            score += prime_len ** 2 * 3
        
        # Blots
        for i in range(24):
            if pts[i] == 1:
                if i >= 18:
                    score -= 20
                elif i >= 12:
                    score -= 14
                elif i >= 6:
                    score -= 9
                else:
                    score -= 4
        
        # Hits
        hits = sum(1 for i in range(24) if opp_orig[i] == 1 and opp[i] == 0)
        score += hits * 16
        
        # Opponent on bar
        total_opp_bar = init_opp_bar + hits
        score += total_opp_bar * 6
        
        # Borne off
        score += off * 24
        
        # My bar penalty
        score -= bar * 24
        
        return score
    
    def select_best(moves):
        if not moves:
            return "H:P,P"
        best_move = moves[0][0]
        best_score = float('-inf')
        for move_str, d1, d2, s1, s2 in moves:
            pts, opp, bar = my_pts.copy(), opp_pts.copy(), my_bar
            if s1:
                pts, opp, bar = simulate_move(pts, opp, bar, s1, d1)
            if s2:
                pts, opp, bar = simulate_move(pts, opp, bar, s2, d2)
            score = evaluate_state(pts, opp, bar, my_off, opp_pts, opp_bar)
            if score > best_score:
                best_score = score
                best_move = move_str
        return best_move
    
    if len(dice) == 0:
        return "H:P,P"
    
    if len(dice) == 1:
        d = dice[0]
        sources = get_sources_for_die(my_pts, opp_pts, my_bar, d)
        if sources:
            moves = [(f"H:{s},P", d, None, s, None) for s in sources]
            return select_best(moves)
        return "H:P,P"
    
    d1, d2 = dice[0], dice[1]
    high, low = max(d1, d2), min(d1, d2)
    
    both_moves = []
    
    for s1 in get_sources_for_die(my_pts, opp_pts, my_bar, high):
        new_pts, new_opp, new_bar = simulate_move(my_pts, opp_pts, my_bar, s1, high)
        for s2 in get_sources_for_die(new_pts, new_opp, new_bar, low):
            both_moves.append((f"H:{s1},{s2}", high, low, s1, s2))
    
    if high != low:
        for s1 in get_sources_for_die(my_pts, opp_pts, my_bar, low):
            new_pts, new_opp, new_bar = simulate_move(my_pts, opp_pts, my_bar, s1, low)
            for s2 in get_sources_for_die(new_pts, new_opp, new_bar, high):
                both_moves.append((f"L:{s1},{s2}", low, high, s1, s2))
    
    if both_moves:
        return select_best(both_moves)
    
    high_sources = get_sources_for_die(my_pts, opp_pts, my_bar, high)
    if high_sources:
        moves = [(f"H:{s},P", high, None, s, None) for s in high_sources]
        return select_best(moves)
    
    low_sources = get_sources_for_die(my_pts, opp_pts, my_bar, low)
    if low_sources:
        moves = [(f"L:{s},P", low, None, s, None) for s in low_sources]
        return select_best(moves)
    
    return "H:P,P"
