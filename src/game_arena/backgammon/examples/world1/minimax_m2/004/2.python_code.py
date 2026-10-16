
def policy(state: dict) -> str:
    dice = state['dice']
    if len(dice) == 0:
        return "H:P,P"
    
    # Sort dice to identify higher and lower dies
    sorted_dice = sorted(dice, reverse=True)
    d1 = sorted_dice[0]  # Higher die
    d2 = sorted_dice[1] if len(sorted_dice) > 1 else None
    
    # Helper function to compute priority of a move
    def compute_priority(start, dest, die, state):
        priority = 0
        # Bar entry
        if start == 'B':
            priority += 100
            # Check if hitting an opponent checker
            if state['opp_pts'][dest] == 1:
                priority += 80
        # Bearing off
        elif dest is None:
            priority += 90
            # Higher points in home board are prioritized
            i = int(start[1:])
            priority += i  # Prioritize bearing off from higher points
        # Regular move
        else:
            # Hitting opponent
            if state['opp_pts'][dest] == 1:
                priority += 80
            # Point building
            elif state['my_pts'][dest] > 0:
                priority += 70
            else:
                # Prioritize moving higher-numbered checkers
                i = int(start[1:])
                priority += 60 + i
        return priority
    
    # Check if a move from start point is legal
    def is_legal_move(start, die, state):
        if start == 'B':
            if state['my_bar'] == 0:
                return False
            dest = 24 - die
            if 0 <= dest <= 23 and state['opp_pts'][dest] < 2:
                return True
            return False
        else:
            if state['my_bar'] > 0:
                return False
            i = int(start[1:])
            if i < 0 or i > 23 or state['my_pts'][i] == 0:
                return False
            dest = i - die
            if dest < 0:
                # Bearing off check
                if state['my_bar'] != 0:
                    return False
                if any(state['my_pts'][j] for j in range(6, 24)):
                    return False
                if die >= i + 1:
                    return True
                elif die == i + 1:
                    return not any(state['my_pts'][j] for j in range(0, i))
                else:
                    return False
            else:
                if dest < 0 or dest > 23:
                    return False
                if state['opp_pts'][dest] >= 2:
                    return False
                return True
    
    # Find best move for a die in current state
    def choose_move(die, state):
        moves = []
        # Check bar entry
        if state['my_bar'] > 0:
            dest = 24 - die
            if 0 <= dest <= 23 and state['opp_pts'][dest] < 2:
                moves.append(('B', dest))
        else:
            for i in range(24):
                if state['my_pts'][i] > 0:
                    dest = i - die
                    if dest < 0:
                        # Bearing off
                        if state['my_bar'] != 0:
                            continue
                        if any(state['my_pts'][j] for j in range(6, 24)):
                            continue
                        if die >= i + 1:
                            moves.append((f'A{i}', None))
                        elif die == i + 1:
                            if not any(state['my_pts'][j] for j in range(0, i)):
                                moves.append((f'A{i}', None))
                    else:
                        if dest < 0 or dest > 23:
                            continue
                        if state['opp_pts'][dest] < 2:
                            moves.append((f'A{i}', dest))
        if not moves:
            return None
        # Compute priorities and select best move
        best_move = None
        best_priority = -1
        for start, dest in moves:
            priority = compute_priority(start, dest, die, state)
            if priority > best_priority:
                best_priority = priority
                best_move = (start, dest)
        return best_move
    
    # Update state after a move
    def apply_move(state, move, die):
        new_state = {
            'my_pts': state['my_pts'][:],
            'opp_pts': state['opp_pts'][:],
            'my_bar': state['my_bar'],
            'opp_bar': state['opp_bar'],
            'my_off': state['my_off'],
            'opp_off': state['opp_off']
        }
        start, dest = move
        if start == 'B':
            new_state['my_bar'] -= 1
            new_state['opp_pts'][dest] -= 1
            if new_state['opp_pts'][dest] == 0:
                new_state['opp_pts'][dest] = 0
                new_state['opp_bar'] += 1
            new_state['my_pts'][dest] += 1
        else:
            i = int(start[1:])
            new_state['my_pts'][i] -= 1
            if dest is None:  # Bearing off
                new_state['my_off'] += 1
            else:
                new_state['my_pts'][dest] += 1
                if state['opp_pts'][dest] == 1:
                    new_state['opp_pts'][dest] = 0
                    new_state['opp_bar'] += 1
        return new_state
    
    # Handle single die
    if len(dice) == 1:
        move = choose_move(d1, state)
        if move:
            return f"H:{move[0]},P"
        else:
            return "H:P,P"
    
    # Handle double dice: try both orders
    scenarios = []
    for order, first_die, second_die in [('H', d1, d2), ('L', d2, d1)]:
        move1 = choose_move(first_die, state)
        if not move1:
            continue
        new_state = apply_move(state, move1, first_die)
        move2 = choose_move(second_die, new_state)
        if move2:
            scenarios.append((order, move1[0], move2[0], len(dice)))
        else:
            scenarios.append((order, move1[0], 'P', 1))
    
    if scenarios:
        # Select scenario with highest score (both dice played > single die, then higher priority moves)
        scenarios.sort(key=lambda x: (x[3], 
                                    compute_priority(x[1], None if x[3]==1 else None, 
                                                    first_die, state), 
                                    compute_priority(x[2], None, second_die, new_state) if x[3]==2 else 0), 
                      reverse=True)
        return f"{scenarios[0][0]}:{scenarios[0][1]},{scenarios[0][2]}"
    else:
        return "H:P,P"
