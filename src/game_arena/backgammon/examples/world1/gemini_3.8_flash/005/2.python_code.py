
def evaluate_state(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off) -> float:
    # 1. Terminal / Bearing off reward
    if my_off == 15:
        return 100000.0
    score = (my_off - opp_off) * 45.0

    # 2. Checkers on the bar
    score += opp_bar * 35.0
    score -= my_bar * 45.0

    # 3. Pip count calculation
    # Player moves 23 -> 0, point p requires p + 1 pips; bar requires 25 pips.
    # Opponent moves 0 -> 23, point p requires 24 - p pips; bar requires 25 pips.
    my_pips = sum(my_pts[p] * (p + 1) for p in range(24)) + my_bar * 25
    opp_pips = sum(opp_pts[p] * (24 - p) for p in range(24)) + opp_bar * 25
    score += (opp_pips - my_pips) * 1.5

    # 4. Contact vs Race detection
    my_max_p = -1
    for p in range(23, -1, -1):
        if my_pts[p] > 0:
            my_max_p = p
            break
    if my_bar > 0:
        my_max_p = 24

    opp_min_p = 25
    for p in range(24):
        if opp_pts[p] > 0:
            opp_min_p = p
            break
    if opp_bar > 0:
        opp_min_p = -1

    # In a pure race, opponent checkers have all passed player checkers
    is_race = (my_max_p < opp_min_p)

    if is_race:
        score += my_off * 15.0
        # In a race, prioritize clearing back home points
        for p in range(6):
            score -= my_pts[p] * p * 0.4
        return score

    # 5. Contact phase: Blots and risk of getting hit
    # Opponent checkers at q < p move towards 23 and can hit our blot at p.
    opp_positions = [p for p in range(24) if opp_pts[p] > 0]
    for p in range(24):
        if my_pts[p] == 1:
            direct_threat = False
            indirect_threat = False

            # Opponent on bar enters at 0..5 (die p + 1)
            if opp_bar > 0 and 0 <= p <= 5:
                direct_threat = True

            for q in opp_positions:
                if q < p:
                    dist = p - q
                    if 1 <= dist <= 6:
                        direct_threat = True
                        break
                    elif 7 <= dist <= 12:
                        indirect_threat = True

            pip_loss = 24 - p
            if direct_threat:
                score -= (18.0 + pip_loss * 0.6)
            elif indirect_threat:
                score -= (7.0 + pip_loss * 0.25)

    # 6. Home board made points (0..5)
    home_weights = [2.0, 3.0, 5.0, 7.0, 9.0, 10.0]
    for p in range(6):
        if my_pts[p] >= 2:
            score += home_weights[p]

    # 7. Consecutive made points (Primes)
    longest_prime = 0
    curr_prime = 0
    for p in range(24):
        if my_pts[p] >= 2:
            curr_prime += 1
            if curr_prime > longest_prime:
                longest_prime = curr_prime
        else:
            curr_prime = 0
    prime_bonuses = [0, 0, 3.0, 7.0, 14.0, 24.0, 42.0]
    score += prime_bonuses[min(longest_prime, 6)]

    # 8. Anchors in opponent's home board (18..23)
    anchor_weights = {18: 3.0, 19: 8.0, 20: 7.0, 21: 5.0, 22: 4.0, 23: 3.0}
    for p, weight in anchor_weights.items():
        if my_pts[p] >= 2:
            score += weight

    # 9. Overstacking penalty (> 4 checkers on a point)
    for p in range(24):
        if my_pts[p] > 4:
            score -= (my_pts[p] - 4) * 2.0

    # 10. Lone deep back checkers penalty
    for p in range(20, 24):
        if my_pts[p] == 1:
            score -= 4.0

    return score


def get_legal_single_moves(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, die):
    moves = []
    # If checkers are on the bar, must move from the bar first
    if my_bar > 0:
        target = 24 - die
        if opp_pts[target] < 2:
            new_my_bar = my_bar - 1
            new_opp_bar = opp_bar
            new_my_pts = list(my_pts)
            new_opp_pts = list(opp_pts)
            if new_opp_pts[target] == 1:
                new_opp_pts[target] = 0
                new_opp_bar += 1
            new_my_pts[target] += 1
            moves.append(('B', (new_my_pts, new_opp_pts, new_my_bar, new_opp_bar, my_off, opp_off)))
        return moves

    # Check bearing off eligibility
    can_bear_off = (sum(my_pts[6:24]) == 0)

    for p in range(24):
        if my_pts[p] <= 0:
            continue
        target = p - die
        if target >= 0:
            if opp_pts[target] < 2:
                new_my_pts = list(my_pts)
                new_opp_pts = list(opp_pts)
                new_opp_bar = opp_bar
                new_my_pts[p] -= 1
                if new_opp_pts[target] == 1:
                    new_opp_pts[target] = 0
                    new_opp_bar += 1
                new_my_pts[target] += 1
                moves.append((f"A{p}", (new_my_pts, new_opp_pts, 0, new_opp_bar, my_off, opp_off)))
        else:
            # Attempt to bear off
            if can_bear_off:
                # Exact roll or oversize roll with no checkers on higher points
                if target == -1 or sum(my_pts[p + 1:6]) == 0:
                    new_my_pts = list(my_pts)
                    new_my_pts[p] -= 1
                    moves.append((f"A{p}", (new_my_pts, list(opp_pts), 0, opp_bar, my_off + 1, opp_off)))

    return moves


def policy(state: dict) -> str:
    my_pts = state.get('my_pts', [0] * 24)
    opp_pts = state.get('opp_pts', [0] * 24)
    my_bar = state.get('my_bar', 0)
    opp_bar = state.get('opp_bar', 0)
    my_off = state.get('my_off', 0)
    opp_off = state.get('opp_off', 0)
    dice = state.get('dice', [])

    if not dice:
        return "H:P,P"

    if len(dice) == 1:
        d = dice[0]
        moves = get_legal_single_moves(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, d)
        if not moves:
            return "H:P,P"
        best_move = max(moves, key=lambda m: evaluate_state(*m[1]))
        return f"H:{best_move[0]},P"

    # len(dice) == 2
    high_d = max(dice)
    low_d = min(dice)

    two_move_actions = []

    # Explore Order H: higher die first, then lower die
    h_first_moves = get_legal_single_moves(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, high_d)
    for f1, s1 in h_first_moves:
        second_moves = get_legal_single_moves(*s1, low_d)
        for f2, s2 in second_moves:
            two_move_actions.append(("H", f1, f2, s2))

    # Explore Order L: lower die first, then higher die (only if dice differ)
    if high_d != low_d:
        l_first_moves = get_legal_single_moves(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, low_d)
        for f1, s1 in l_first_moves:
            second_moves = get_legal_single_moves(*s1, high_d)
            for f2, s2 in second_moves:
                two_move_actions.append(("L", f1, f2, s2))

    # If both dice can be played, select the best 2-move sequence
    if two_move_actions:
        best_action = max(two_move_actions, key=lambda a: evaluate_state(*a[3]))
        return f"{best_action[0]}:{best_action[1]},{best_action[2]}"

    # If only one die can be played, must play the higher die when possible
    if h_first_moves:
        best_single = max(h_first_moves, key=lambda m: evaluate_state(*m[1]))
        return f"H:{best_single[0]},P"

    # Otherwise, try the lower die
    l_first_moves = get_legal_single_moves(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, low_d)
    if l_first_moves:
        best_single = max(l_first_moves, key=lambda m: evaluate_state(*m[1]))
        return f"L:{best_single[0]},P"

    # Full pass if no legal moves exist
    return "H:P,P"
