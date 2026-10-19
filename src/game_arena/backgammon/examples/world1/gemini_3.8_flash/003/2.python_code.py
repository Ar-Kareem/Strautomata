
def get_single_moves(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, die):
    moves = []
    
    # Checkers on the bar must enter first
    if my_bar > 0:
        dest = 24 - die
        if opp_pts[dest] < 2:
            new_my_pts = list(my_pts)
            new_opp_pts = list(opp_pts)
            new_opp_bar = opp_bar
            if new_opp_pts[dest] == 1:
                new_opp_pts[dest] = 0
                new_opp_bar += 1
            new_my_pts[dest] += 1
            moves.append(('B', (new_my_pts, new_opp_pts, my_bar - 1, new_opp_bar, my_off, opp_off)))
        return moves

    # Board moves
    can_bear_off = (sum(my_pts[6:]) == 0)

    for i in range(24):
        if my_pts[i] == 0:
            continue
        dest = i - die
        if dest >= 0:
            if opp_pts[dest] < 2:
                new_my_pts = list(my_pts)
                new_opp_pts = list(opp_pts)
                new_opp_bar = opp_bar
                if new_opp_pts[dest] == 1:
                    new_opp_pts[dest] = 0
                    new_opp_bar += 1
                new_my_pts[i] -= 1
                new_my_pts[dest] += 1
                moves.append((f"A{i}", (new_my_pts, new_opp_pts, 0, new_opp_bar, my_off, opp_off)))
        else:
            # dest < 0: bearing off
            if can_bear_off:
                if dest == -1:
                    new_my_pts = list(my_pts)
                    new_my_pts[i] -= 1
                    moves.append((f"A{i}", (new_my_pts, list(opp_pts), 0, opp_bar, my_off + 1, opp_off)))
                elif dest < -1:
                    # Overshoot bear off: only legal if no checkers on higher points
                    if sum(my_pts[i + 1:6]) == 0:
                        new_my_pts = list(my_pts)
                        new_my_pts[i] -= 1
                        moves.append((f"A{i}", (new_my_pts, list(opp_pts), 0, opp_bar, my_off + 1, opp_off)))

    return moves


def eval_state(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off):
    score = 0.0

    # 1. Borne off checkers
    score += my_off * 32.0
    score -= opp_off * 32.0

    # 2. Bar checkers
    score += opp_bar * 38.0
    score -= my_bar * 42.0

    # 3. Pip race
    my_pip = my_bar * 25 + sum(my_pts[i] * (i + 1) for i in range(24))
    opp_pip = opp_bar * 25 + sum(opp_pts[i] * (24 - i) for i in range(24))
    score += (opp_pip - my_pip) * 1.6

    # 4. Blots vulnerability
    for i in range(24):
        if my_pts[i] == 1:
            has_direct = False
            has_indirect = False

            if opp_bar > 0 and i <= 5:
                has_direct = True
            else:
                for j in range(max(0, i - 12), i):
                    if opp_pts[j] > 0:
                        dist = i - j
                        if dist <= 6:
                            has_direct = True
                            break
                        else:
                            has_indirect = True

            pips_lost = 24 - i
            if has_direct:
                score -= 16.0 + pips_lost * 0.75
            elif has_indirect:
                score -= 6.0 + pips_lost * 0.25
            else:
                score -= 1.0

    # 5. Made points, anchors, and primes
    run = 0
    max_run = 0
    for i in range(24):
        if my_pts[i] >= 2:
            score += 3.5
            if i <= 5:
                score += 5.5  # Home board point
            elif 18 <= i <= 22:
                score += 4.5  # Advanced anchor in opponent territory

            if my_pts[i] > 3:
                score -= (my_pts[i] - 3) * 1.5  # Avoid over-stacking

            run += 1
            if run > max_run:
                max_run = run
        else:
            run = 0

    if max_run >= 2:
        prime_bonus = {2: 4.0, 3: 10.0, 4: 22.0, 5: 42.0, 6: 70.0}
        score += prime_bonus.get(min(max_run, 6), 70.0)

    # 6. Trapping opponent on bar with closed home points
    home_closed = sum(1 for i in range(6) if my_pts[i] >= 2)
    if opp_bar > 0:
        score += home_closed * opp_bar * 6.0

    return score


def policy(state: dict) -> str:
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state.get('dice', [])

    if not dice:
        return "H:P,P"

    if len(dice) == 1:
        d = dice[0]
        moves = get_single_moves(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, d)
        if not moves:
            return "H:P,P"
        best_move = max(moves, key=lambda m: eval_state(*m[1]))
        return f"H:{best_move[0]},P"

    d_H = max(dice[0], dice[1])
    d_L = min(dice[0], dice[1])

    two_move_candidates = []

    # Order 'H' (High die first, then Low die)
    moves1_H = get_single_moves(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, d_H)
    for from1, s1 in moves1_H:
        moves2 = get_single_moves(s1[0], s1[1], s1[2], s1[3], s1[4], s1[5], d_L)
        for from2, s2 in moves2:
            two_move_candidates.append(('H', from1, from2, s2))

    # Order 'L' (Low die first, then High die)
    moves1_L = []
    if d_H != d_L:
        moves1_L = get_single_moves(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, d_L)
        for from1, s1 in moves1_L:
            moves2 = get_single_moves(s1[0], s1[1], s1[2], s1[3], s1[4], s1[5], d_H)
            for from2, s2 in moves2:
                two_move_candidates.append(('L', from1, from2, s2))

    # If both dice can be played, choose the optimal 2-move action
    if two_move_candidates:
        best = max(two_move_candidates, key=lambda c: eval_state(*c[3]))
        return f"{best[0]}:{best[1]},{best[2]}"

    # If only one die can be played, higher die must be played if possible
    if moves1_H:
        best = max(moves1_H, key=lambda m: eval_state(*m[1]))
        return f"H:{best[0]},P"

    # Otherwise, check if lower die can be played
    if not moves1_L and d_H == d_L:
        moves1_L = moves1_H
    elif not moves1_L:
        moves1_L = get_single_moves(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, d_L)

    if moves1_L:
        best = max(moves1_L, key=lambda m: eval_state(*m[1]))
        return f"L:{best[0]},P"

    # No legal moves possible
    return "H:P,P"
