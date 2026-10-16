
def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = state['dice']

    if my_bar > 0:
        # Handle checkers on the bar
        possible_bar_moves = [d for d in dice if opp_pts[d] < 2]
        if not possible_bar_moves:
            return 'H:P,P'
        # Sort dice in descending order
        sorted_dice = sorted(dice, reverse=True)
        used_dice = []
        for d in sorted_dice:
            if d in possible_bar_moves:
                used_dice.append(d)
                if len(used_dice) == 2:
                    break
        if len(used_dice) == 2:
            return "H:B,B"
        else:
            d_used = used_dice[0]
            # Determine order: higher die if used, else lower
            if d_used == sorted_dice[0]:
                order = 'H'
            else:
                order = 'L'
            return f"{order}:B,P"
    else:
        if len(dice) == 0:
            return "H:P,P"

        def can_bear_off(state):
            for i in range(6, 24):
                if state['my_pts'][i] > 0:
                    return False
            return True

        def get_best_move(state, die):
            best_score = -1
            best_from = -1
            can_b = can_bear_off(state)
            for p in range(23, -1, -1):  # Start from highest to lowest index
                if state['my_pts'][p] == 0:
                    continue
                if can_b:
                    # Check if bearing off is possible
                    if die >= (p + 1):  # If die >= position + 1, can bear off
                        return p
                new_p = p - die
                if new_p < 0:
                    continue  # Already handled by bearing off
                if opp_pts[new_p] >= 2:
                    continue  # Cannot move to occupied point
                # Score calculation
                score = 0
                if opp_pts[new_p] == 1:
                    score += 100  # Hit
                elif my_pts[new_p] > 0:
                    score += 50  # Make a point
                if new_p < p:
                    score += 10  # Move closer to home
                if score > best_score:
                    best_score = score
                    best_from = p
            return best_from if best_score >= 0 else None

        sorted_dice = sorted(dice, reverse=True)
        d1 = sorted_dice[0]
        d2 = sorted_dice[1] if len(dice) > 1 else 0

        # Try to use both dice
        first_move = get_best_move(state, d1)
        if first_move is not None:
            # Simulate state after first move
            new_my_pts = my_pts[:]
            new_my_pts[first_move] -= 1
            new_p = first_move - d1
            if can_bear_off(state) or new_p < 0:
                new_off = state['my_off'] + 1
                new_my_pts[new_off] = 0  # Placeholder, but this is handled during bearing off
            else:
                new_off = state['my_off']
                new_my_pts[new_p] += 1
            simulated_state = {
                'my_pts': new_my_pts,
                'opp_pts': opp_pts,
                'my_off': new_off,
                'dice': [d2]
            }
            second_move = get_best_move(simulated_state, d2)
            if second_move is not None:
                return f"H:A{first_move},A{second_move}"

        # Try higher die
        first_move = get_best_move(state, d1)
        if first_move is not None:
            return f"H:A{first_move},P"
        # Try lower die
        first_move = get_best_move(state, d2)
        if first_move is not None:
            return f"L:A{first_move},P"
        # No legal moves
        return 'H:P,P'
