
def policy(state: dict) -> str:
    # Helper function to check if a bar move is legal
    def can_enter_bar(die, state_dict):
        dest = 24 - die
        if dest < 0 or dest >= 24:
            return False
        return state_dict['opp_pts'][dest] <= 1

    # Helper function to find the best non-bar move for a given die
    def best_nonbar_move(state_dict, die):
        best_move = None
        best_score = -999
        # Check for bearing off in the home board
        home_points = [i for i in range(6) if state_dict['my_pts'][i] > 0]
        if home_points:
            H = max(home_points)
            if H - die < 0:
                score = 100
                if score > best_score:
                    best_score = score
                    best_move = H
        # Iterate over all points for other moves
        for i in range(24):
            if state_dict['my_pts'][i] == 0:
                continue
            if i == H:
                pass
            j = i - die
            if j < 0:
                continue
            if j < 0 or j >= 24:
                continue
            if state_dict['opp_pts'][j] >= 2:
                continue
            score = 0
            if state_dict['opp_pts'][j] == 1:
                score += 50
            if state_dict['my_pts'][j] >= 1:
                score += 40
            else:
                score += 10
            if j in range(0,6):
                score += 10
            elif j in range(18,24):
                score -= 10
            if state_dict['my_pts'][i] == 2:
                score -= 20
            if score > best_score:
                best_score = score
                best_move = i
        return best_move

    # Helper function to apply a single move
    def apply_move(state_dict, move, die):
        state2 = {
            'my_pts': state_dict['my_pts'][:],
            'opp_pts': state_dict['opp_pts'][:],
            'my_bar': state_dict['my_bar'],
            'opp_bar': state_dict['opp_bar'],
            'my_off': state_dict['my_off'],
            'opp_off': state_dict['opp_off'],
            'dice': state_dict['dice'][:]
        }
        if move == 'B':
            state2['my_bar'] -= 1
            dest = 24 - die
            state2['my_pts'][dest] += 1
            if state_dict['opp_pts'][dest] == 1:
                state2['opp_bar'] += 1
                state2['opp_pts'][dest] = 0
        else:
            i = move
            j = i - die
            state2['my_pts'][i] -= 1
            if j < 0:
                state2['my_off'] += 1
            else:
                if state_dict['opp_pts'][j] == 1:
                    state2['opp_bar'] += 1
                    state2['opp_pts'][j] = 0
                state2['my_pts'][j] += 1
        return state2

    # Helper function to simulate the entire candidate move
    def simulate_move(state_dict, candidate):
        order = candidate[0]
        from1 = candidate[1]
        from2 = candidate[2]
        state2 = {
            'my_pts': state_dict['my_pts'][:],
            'opp_pts': state_dict['opp_pts'][:],
            'my_bar': state_dict['my_bar'],
            'opp_bar': state_dict['opp_bar'],
            'my_off': state_dict['my_off'],
            'opp_off': state_dict['opp_off'],
            'dice': state_dict['dice'][:]
        }
        dice_sorted = sorted(state_dict['dice'], reverse=True)
        if order == 'H':
            die1 = dice_sorted[0]
            die2 = dice_sorted[1]
        else:
            die1 = dice_sorted[1]
            die2 = dice_sorted[0]
        state2 = apply_move(state2, from1, die1)
        if from2 != 'P':
            state2 = apply_move(state2, from2, die2)
        return state2

    # Helper function to evaluate the board state
    def evaluate_board(state_dict):
        score = 0
        for i in range(24):
            if state_dict['my_pts'][i] > 0:
                if i in range(0,6):
                    score += state_dict['my_pts'][i] * 10
                elif i in range(18,24):
                    score -= state_dict['my_pts'][i] * 5
                else:
                    score += state_dict['my_pts'][i] * 2
        for i in range(24):
            if state_dict['my_pts'][i] >= 2:
                score += state_dict['my_pts'][i] * 5
        for i in range(24):
            if state_dict['my_pts'][i] == 1:
                score -= 10
        score -= state_dict['my_bar'] * 20
        score += state_dict['my_off'] * 100
        score += state_dict['opp_bar'] * 20
        for i in range(24):
            if state_dict['opp_pts'][i] >= 2:
                score -= state_dict['opp_pts'][i] * 10
            elif state_dict['opp_pts'][i] == 1:
                score -= 5
        score -= state_dict['opp_off'] * 100
        return score

    my_bar = state['my_bar']
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']
    dice_sorted = sorted(dice, reverse=True)

    candidate_moves = []

    if my_bar > 0:
        if len(dice) == 2:
            d_high = dice_sorted[0]
            d_low = dice_sorted[1]
            # Try higher die first
            if can_enter_bar(d_high, state):
                state2 = {
                    'my_pts': my_pts[:],
                    'opp_pts': opp_pts[:],
                    'my_bar': my_bar - 1,
                    'opp_bar': state['opp_bar'],
                    'my_off': my_off,
                    'opp_off': opp_off,
                    'dice': dice[:]
                }
                dest = 24 - d_high
                state2['my_pts'][dest] += 1
                if opp_pts[dest] == 1:
                    state2['opp_bar'] += 1
                    state2['opp_pts'][dest] = 0
                if my_bar >= 2:
                    if can_enter_bar(d_low, state2):
                        candidate_moves.append(('H', 'B', 'B'))
                    else:
                        candidate_moves.append(('H', 'B', 'P'))
                else:
                    move2 = best_nonbar_move(state2, d_low)
                    if move2 is not None:
                        candidate_moves.append(('H', 'B', move2))
                    else:
                        candidate_moves.append(('H', 'B', 'P'))
            # Try lower die first
            if can_enter_bar(d_low, state):
                state2 = {
                    'my_pts': my_pts[:],
                    'opp_pts': opp_pts[:],
                    'my_bar': my_bar - 1,
                    'opp_bar': state['opp_bar'],
                    'my_off': my_off,
                    'opp_off': opp_off,
                    'dice': dice[:]
                }
                dest = 24 - d_low
                state2['my_pts'][dest] += 1
                if opp_pts[dest] == 1:
                    state2['opp_bar'] += 1
                    state2['opp_pts'][dest] = 0
                if my_bar >= 2:
                    if can_enter_bar(d_high, state2):
                        candidate_moves.append(('L', 'B', 'B'))
                    else:
                        candidate_moves.append(('L', 'B', 'P'))
                else:
                    move2 = best_nonbar_move(state2, d_high)
                    if move2 is not None:
                        candidate_moves.append(('L', 'B', move2))
                    else:
                        candidate_moves.append(('L', 'B', 'P'))
        else:
            d = dice_sorted[0]
            if can_enter_bar(d, state):
                state2 = {
                    'my_pts': my_pts[:],
                    'opp_pts': opp_pts[:],
                    'my_bar': my_bar - 1,
                    'opp_bar': state['opp_bar'],
                    'my_off': my_off,
                    'opp_off': opp_off,
                    'dice': dice[:]
                }
                dest = 24 - d
                state2['my_pts'][dest] += 1
                if opp_pts[dest] == 1:
                    state2['opp_bar'] += 1
                    state2['opp_pts'][dest] = 0
                candidate_moves.append(('H', 'B', 'P'))
    else:
        if len(dice) == 2:
            d_high = dice_sorted[0]
            d_low = dice_sorted[1]
            # Try higher die first, then lower
            move1 = best_nonbar_move(state, d_high)
            if move1 is not None:
                state2 = apply_move(state, move1, d_high)
                move2 = best_nonbar_move(state2, d_low)
                if move2 is not None:
                    candidate_moves.append(('H', move1, move2))
                else:
                    candidate_moves.append(('H', move1, 'P'))
            # Try lower die first, then higher
            move1 = best_nonbar_move(state, d_low)
            if move1 is not None:
                state2 = apply_move(state, move1, d_low)
                move2 = best_nonbar_move(state2, d_high)
                if move2 is not None:
                    candidate_moves.append(('L', move1, move2))
                else:
                    candidate_moves.append(('L', move1, 'P'))
            # If no moves found, try lower die alone if higher didn't work
            if not candidate_moves:
                move1 = best_nonbar_move(state, d_low)
                if move1 is not None:
                    candidate_moves.append(('L', move1, 'P'))
        else:
            d = dice_sorted[0]
            move1 = best_nonbar_move(state, d)
            if move1 is not None:
                candidate_moves.append(('H', move1, 'P'))

    if not candidate_moves:
        candidate_moves.append(('H', 'P', 'P'))

    best_move = None
    best_score = -999999
    for candidate in candidate_moves:
        new_state = simulate_move(state, candidate)
        score = evaluate_board(new_state)
        if score > best_score:
            best_score = score
            best_move = candidate

    order = best_move[0]
    from1 = best_move[1]
    from2 = best_move[2]

    if from1 == 'B':
        s1 = 'B'
    elif from1 == 'P':
        s1 = 'P'
    else:
        s1 = f'A{from1}'

    if from2 == 'B':
        s2 = 'B'
    elif from2 == 'P':
        s2 = 'P'
    else:
        s2 = f'A{from2}'

    return f"{order}:{s1},{s2}"
