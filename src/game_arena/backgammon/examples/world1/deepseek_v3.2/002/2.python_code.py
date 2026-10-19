
import itertools

def policy(state):
    # Helper functions
    def is_my_home(point):
        # My home board is points 18-23 (since I move from 23 to 0)
        return 18 <= point <= 23
    
    def is_opp_home(point):
        # Opponent home board is points 0-5
        return 0 <= point <= 5
    
    def point_to_abs(point_str):
        if point_str == 'B':
            return -1
        if point_str.startswith('A'):
            return int(point_str[1:])
        return None
    
    def abs_to_point(abs_idx):
        if abs_idx == -1:
            return 'B'
        return f'A{abs_idx}'
    
    def can_bear_off(state):
        my_checkers_outside = sum(state['my_pts'][i] for i in range(0, 18))
        return my_checkers_outside == 0
    
    def is_blot(state, point_idx):
        return state['my_pts'][point_idx] == 1
    
    def would_be_hit(state, from_idx, die):
        # Determine if moving a checker leaves it exposed to being hit next turn
        # Simplified: if moving creates a blot in opponent's home board or leaves a blot elsewhere
        # We'll use a simple heuristic: avoid leaving single checker in range of opponent's hits
        pass
    
    def generate_all_moves(state, dice):
        # Returns list of tuples: (order, (from1, from2))
        # order: 'H' or 'L'
        # from1, from2: absolute indices (-1 for bar)
        moves = []
        if len(dice) == 0:
            return [('H', ('P', 'P'))]
        if len(dice) == 1:
            die = dice[0]
            # Try moves with this single die
            # Must play higher die if possible, but here only one die
            # Check bar first
            if state['my_bar'] > 0:
                # Must enter from bar
                target = 24 - die
                if state['opp_pts'][target] < 2:
                    moves.append(('H', (-1, 'P')))
            else:
                # Normal moves
                for src in range(24):
                    if state['my_pts'][src] > 0:
                        dst = src - die
                        if dst >= 0:
                            if state['opp_pts'][dst] < 2:
                                moves.append(('H', (src, 'P')))
                # Bearing off
                if can_bear_off(state):
                    for src in range(18, 24):
                        if state['my_pts'][src] > 0:
                            if src - die < 0 or src == die - 1:
                                moves.append(('H', (src, 'P')))
            if not moves:
                moves.append(('H', ('P', 'P')))
            return moves
        
        # Two dice
        high, low = max(dice), min(dice)
        # Generate sequences: H then L, and L then H
        sequences = [('H', (high, low)), ('L', (low, high))]
        for order, (first_die, second_die) in sequences:
            # Generate moves for first die
            first_moves = []
            if state['my_bar'] > 0:
                target = 24 - first_die
                if state['opp_pts'][target] < 2:
                    first_moves.append(-1)
            else:
                for src in range(24):
                    if state['my_pts'][src] > 0:
                        dst = src - first_die
                        if dst >= 0 and state['opp_pts'][dst] < 2:
                            first_moves.append(src)
                if can_bear_off(state):
                    for src in range(18, 24):
                        if state['my_pts'][src] > 0:
                            if src - first_die < 0 or src == first_die - 1:
                                first_moves.append(src)
            if not first_moves:
                first_moves.append('P')
            
            for fm in first_moves:
                # Apply first move temporarily
                temp_state = {k: v[:] if isinstance(v, list) else v for k, v in state.items()}
                if fm != 'P' and fm != -1:
                    src = fm
                    dst = src - first_die
                    if dst >= 0:
                        # Move checker
                        temp_state['my_pts'][src] -= 1
                        if state['opp_pts'][dst] == 1:
                            # Hit
                            temp_state['opp_pts'][dst] = 0
                            temp_state['opp_bar'] += 1
                        else:
                            temp_state['my_pts'][dst] += 1
                    else:
                        # Bear off
                        temp_state['my_pts'][src] -= 1
                        temp_state['my_off'] += 1
                elif fm == -1:
                    # Enter from bar
                    target = 24 - first_die
                    temp_state['my_bar'] -= 1
                    if state['opp_pts'][target] == 1:
                        temp_state['opp_pts'][target] = 0
                        temp_state['opp_bar'] += 1
                    temp_state['my_pts'][target] += 1
                
                # Second die
                second_moves = []
                if temp_state['my_bar'] > 0:
                    target2 = 24 - second_die
                    if temp_state['opp_pts'][target2] < 2:
                        second_moves.append(-1)
                else:
                    for src in range(24):
                        if temp_state['my_pts'][src] > 0:
                            dst = src - second_die
                            if dst >= 0 and temp_state['opp_pts'][dst] < 2:
                                second_moves.append(src)
                    if can_bear_off(temp_state):
                        for src in range(18, 24):
                            if temp_state['my_pts'][src] > 0:
                                if src - second_die < 0 or src == second_die - 1:
                                    second_moves.append(src)
                if not second_moves:
                    second_moves.append('P')
                
                for sm in second_moves:
                    moves.append((order, (fm if fm != 'P' else 'P', sm if sm != 'P' else 'P')))
        
        # Deduplicate
        moves = list(set(moves))
        if not moves:
            moves.append(('H', ('P', 'P')))
        return moves
    
    def score_move(state, move):
        order, (from1, from2) = move
        score = 0
        temp_state = {k: v[:] if isinstance(v, list) else v for k, v in state.items()}
        dice = state['dice']
        if len(dice) < 2:
            die = dice[0] if dice else 0
            seq = [die]
        else:
            high, low = max(dice), min(dice)
            seq = [high, low] if order == 'H' else [low, high]
        
        moves_seq = [(from1, seq[0])]
        if len(seq) > 1:
            moves_seq.append((from2, seq[1]))
        
        for i, (fm, die) in enumerate(moves_seq):
            if fm == 'P':
                continue
            if fm == -1:  # bar
                target = 24 - die
                # Hitting bonus
                if state['opp_pts'][target] == 1:
                    score += 3
                # Entering is good
                score += 1
                # Update temp state
                temp_state['my_bar'] -= 1
                if state['opp_pts'][target] == 1:
                    temp_state['opp_pts'][target] = 0
                    temp_state['opp_bar'] += 1
                temp_state['my_pts'][target] += 1
            else:
                src = fm
                dst = src - die
                if dst >= 0:
                    # Hitting bonus
                    if state['opp_pts'][dst] == 1:
                        score += 3
                    # Making a point in home board
                    if is_my_home(dst) and temp_state['my_pts'][dst] == 0:
                        score += 2
                    # Moving toward home
                    if src < 18:  # outside home
                        score += (18 - src) // 3
                    # Update temp state
                    temp_state['my_pts'][src] -= 1
                    if state['opp_pts'][dst] == 1:
                        temp_state['opp_pts'][dst] = 0
                        temp_state['opp_bar'] += 1
                    temp_state['my_pts'][dst] += 1
                else:
                    # Bearing off
                    score += 4
                    temp_state['my_pts'][src] -= 1
                    temp_state['my_off'] += 1
        return score
    
    # Main logic
    dice = state['dice']
    all_moves = generate_all_moves(state, dice)
    if not all_moves:
        return 'H:P,P'
    
    scored = [(score_move(state, m), m) for m in all_moves]
    scored.sort(key=lambda x: x[0], reverse=True)
    best_move = scored[0][1]
    
    order, (from1, from2) = best_move
    from1_str = abs_to_point(from1) if from1 != 'P' else 'P'
    from2_str = abs_to_point(from2) if from2 != 'P' else 'P'
    return f'{order}:{from1_str},{from2_str}'
