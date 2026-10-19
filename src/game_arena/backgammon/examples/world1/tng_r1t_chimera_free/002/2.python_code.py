
def policy(state):
    # Implement a strategy that prefers hitting, blocking, and bearing off
    
    def can_bear_off():
        # Check if all checkers are in home board (0-5)
        return not any(count > 0 for count in state['my_pts'][6:]) and state['my_bar'] == 0
    
    def generate_bar_moves():
        dice = state['dice']
        valid = []
        for d in dice:
            entry_point = d - 1  # opponent's home board points 0-5
            if 0 <= entry_point < 24 and state['opp_pts'][entry_point] < 2:
                valid.append((d, entry_point))
        if not valid:
            return []
        # Prioritize hitting blots and higher points
        valid.sort(key=lambda x: (-(state['opp_pts'][x[1]] == 1), -x[1]))
        best_die, best_point = valid[0]
        other_dice = [d for d in dice if d != best_die]
        # Generate move strings
        if not other_dice or len(valid) == 1:
            order = 'H' if best_die == max(dice) else 'L'
            return [f"{order}:B,P"]
        else:
            return [f"H:B,B"] if best_die > other_dice[0] else [f"L:B,B"]
    
    def generate_bear_off_moves():
        dice = state['dice']
        moves = []
        for d in sorted(dice, reverse=True):
            s = min(d-1, 23)
            while s >= 0:
                if state['my_pts'][s] > 0:
                    moves.append(s)
                    break
                s -= 1
        if not moves:
            return []
        # Create move strings
        if len(moves) == 1:
            order = 'H' if dice[0] > dice[-1] else 'L'
            return [f"{order}:A{moves[0]},P"]
        return [f"H:A{moves[0]},A{moves[1]}"] if len(moves) >=2 else []
    
    def generate_normal_moves():
        my_pts = state['my_pts']
        opp_pts = state['opp_pts']
        candidates = []
        for s in range(23, -1, -1):
            if my_pts[s] == 0:
                continue
            for d in state['dice']:
                dest = s - d
                if dest >= 0 and opp_pts[dest] < 2:
                    score = (100 if opp_pts[dest] == 1 else 0) + \
                            (50 if dest >=0 and my_pts[dest] > 0 else 0) + \
                            (23 - s)*2 - \
                            (30 if my_pts[s] == 1 else 0)
                    candidates.append((-d, score, s))  # Negative die for reverse sorting
        
        candidates.sort(key=lambda x: (x[1], x[0]), reverse=True)
        used_dice = set()
        selected = []
        for d, _, s in candidates:
            die = -d
            if die not in used_dice:
                selected.append((die, s))
                used_dice.add(die)
                if len(selected) == 2:
                    break
        # Form move string
        if not selected:
            return []
        if len(selected) == 1:
            die, s = selected[0]
            order = 'H' if die == max(state['dice']) else 'L'
            return [f"{order}:A{s},P"]
        d1, s1 = selected[0]
        d2, s2 = selected[1]
        return [f"H:A{s1},A{s2}"] if d1 >= d2 else [f"L:A{s2},A{s1}"]
    
    # Main decision logic
    if state['my_bar'] > 0:
        bar_moves = generate_bar_moves()
        return bar_moves[0] if bar_moves else "H:P,P"
    elif can_bear_off():
        bear_moves = generate_bear_off_moves()
        return bear_moves[0] if bear_moves else "H:P,P"
    else:
        norm_moves = generate_normal_moves()
        return norm_moves[0] if norm_moves else "H:P,P"
