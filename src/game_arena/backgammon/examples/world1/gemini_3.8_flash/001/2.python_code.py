
import copy

def _apply_single_move(state: dict, from_pos, die: int):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']

    if from_pos == 'B':
        if my_bar <= 0:
            return None
        dest = 24 - die
        if opp_pts[dest] >= 2:
            return None
        
        new_my_pts = list(my_pts)
        new_opp_pts = list(opp_pts)
        new_opp_bar = opp_bar

        if new_opp_pts[dest] == 1:
            new_opp_pts[dest] = 0
            new_opp_bar += 1
        new_my_pts[dest] += 1

        return {
            'my_pts': new_my_pts,
            'opp_pts': new_opp_pts,
            'my_bar': my_bar - 1,
            'opp_bar': new_opp_bar,
            'my_off': my_off,
            'opp_off': opp_off
        }
    else:
        p = from_pos
        if my_bar > 0 or my_pts[p] <= 0:
            return None
        dest = p - die
        if dest >= 0:
            if opp_pts[dest] >= 2:
                return None
            new_my_pts = list(my_pts)
            new_opp_pts = list(opp_pts)
            new_opp_bar = opp_bar

            new_my_pts[p] -= 1
            if new_opp_pts[dest] == 1:
                new_opp_pts[dest] = 0
                new_opp_bar += 1
            new_my_pts[dest] += 1

            return {
                'my_pts': new_my_pts,
                'opp_pts': new_opp_pts,
                'my_bar': my_bar,
                'opp_bar': new_opp_bar,
                'my_off': my_off,
                'opp_off': opp_off
            }
        else:
            # Bearing off check: no checkers outside home board (0..5)
            for i in range(6, 24):
                if my_pts[i] > 0:
                    return None
            if dest == -1:
                new_my_pts = list(my_pts)
                new_my_pts[p] -= 1
                return {
                    'my_pts': new_my_pts,
                    'opp_pts': list(opp_pts),
                    'my_bar': my_bar,
                    'opp_bar': opp_bar,
                    'my_off': my_off + 1,
                    'opp_off': opp_off
                }
            else:
                # Overshoot: only legal if all higher points in home board are empty
                for i in range(p + 1, 6):
                    if my_pts[i] > 0:
                        return None
                new_my_pts = list(my_pts)
                new_my_pts[p] -= 1
                return {
                    'my_pts': new_my_pts,
                    'opp_pts': list(opp_pts),
                    'my_bar': my_bar,
                    'opp_bar': opp_bar,
                    'my_off': my_off + 1,
                    'opp_off': opp_off
                }


def _evaluate(state: dict) -> float:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']

    score = 0.0

    # 1. Borne off checkers
    score += my_off * 30.0
    score -= opp_off * 30.0

    # 2. Bar checkers
    score -= my_bar * 40.0
    score += opp_bar * 40.0

    # 3. Pip counts (lower is better for us)
    my_pips = my_bar * 25
    for p in range(24):
        if my_pts[p] > 0:
            my_pips += my_pts[p] * (p + 1)

    opp_pips = opp_bar * 25
    for p in range(24):
        if opp_pts[p] > 0:
            opp_pips += opp_pts[p] * (24 - p)

    score += (opp_pips - my_pips) * 1.5

    # 4. Blots vulnerability
    opp_has_bar = (opp_bar > 0)
    for p in range(24):
        if my_pts[p] == 1:
            penalty = 12.0
            in_direct_shot = False
            if opp_has_bar and p <= 5:
                in_direct_shot = True
            else:
                for d in range(1, 7):
                    q = p - d
                    if q >= 0 and opp_pts[q] > 0:
                        in_direct_shot = True
                        break
            if in_direct_shot:
                penalty += 15.0 + (6 - p if p < 6 else 0) * 1.5
            score -= penalty

    # 5. Made points and consecutive primes
    prime_len = 0
    max_prime = 0
    for p in range(24):
        if my_pts[p] >= 2:
            prime_len += 1
            if prime_len > max_prime:
                max_prime = prime_len
            if p <= 5:
                score += 15.0
            elif p <= 7:
                score += 8.0
            else:
                score += 4.0
        else:
            prime_len = 0

    if max_prime >= 6:
        score += 60.0
    elif max_prime == 5:
        score += 35.0
    elif max_prime == 4:
        score += 20.0
    elif max_prime == 3:
        score += 10.0
    elif max_prime == 2:
        score += 4.0

    # 6. Penalty for back checkers stuck far behind
    for p in range(18, 24):
        if my_pts[p] > 0:
            score -= my_pts[p] * 2.0

    return score


def _get_start_positions(st: dict):
    if st['my_bar'] > 0:
        return ['B']
    return [p for p in range(24) if st['my_pts'][p] > 0]


def _format_token(pos):
    return 'B' if pos == 'B' else f'A{pos}'


def policy(state: dict) -> str:
    dice = state.get('dice', [])
    if not dice:
        return "H:P,P"

    if len(dice) == 1:
        d = dice[0]
        best_score = -float('inf')
        best_move = "H:P,P"
        for p in _get_start_positions(state):
            s1 = _apply_single_move(state, p, d)
            if s1 is not None:
                sc = _evaluate(s1)
                if sc > best_score:
                    best_score = sc
                    best_move = f"H:{_format_token(p)},P"
        return best_move

    d1, d2 = dice[0], dice[1]
    high_die = max(d1, d2)
    low_die = min(d1, d2)

    orders = [('H', high_die, low_die)]
    if high_die != low_die:
        orders.append(('L', low_die, high_die))

    # 1. Search for 2-die moves
    two_move_candidates = []
    for order_name, first_die, second_die in orders:
        for p1 in _get_start_positions(state):
            s1 = _apply_single_move(state, p1, first_die)
            if s1 is None:
                continue
            for p2 in _get_start_positions(s1):
                s2 = _apply_single_move(s1, p2, second_die)
                if s2 is not None:
                    sc = _evaluate(s2)
                    move_str = f"{order_name}:{_format_token(p1)},{_format_token(p2)}"
                    two_move_candidates.append((sc, move_str))

    if two_move_candidates:
        return max(two_move_candidates, key=lambda x: x[0])[1]

    # 2. If both cannot be played, higher die must be played if possible
    high_candidates = []
    for p in _get_start_positions(state):
        s1 = _apply_single_move(state, p, high_die)
        if s1 is not None:
            high_candidates.append((_evaluate(s1), f"H:{_format_token(p)},P"))

    if high_candidates:
        return max(high_candidates, key=lambda x: x[0])[1]

    # 3. Otherwise try playing the lower die
    if high_die != low_die:
        low_candidates = []
        for p in _get_start_positions(state):
            s1 = _apply_single_move(state, p, low_die)
            if s1 is not None:
                low_candidates.append((_evaluate(s1), f"L:{_format_token(p)},P"))
        if low_candidates:
            return max(low_candidates, key=lambda x: x[0])[1]

    # 4. No legal moves
    return "H:P,P"
