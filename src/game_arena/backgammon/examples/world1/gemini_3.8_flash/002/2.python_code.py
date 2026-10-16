
def to_token(pos):
    if pos == 'B':
        return 'B'
    elif pos == 'P':
        return 'P'
    return f"A{pos}"


def apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, pos, die):
    """
    Applies a single checker move with given die.
    Returns (True, (new_my_pts, new_opp_pts, new_my_bar, new_opp_bar, new_my_off, new_opp_off))
    if legal, else (False, None).
    """
    if pos == 'B':
        if my_bar <= 0:
            return False, None
        target = 24 - die
        if opp_pts[target] >= 2:
            return False, None

        n_my_pts = list(my_pts)
        n_opp_pts = list(opp_pts)
        n_my_bar = my_bar - 1
        n_opp_bar = opp_bar
        n_my_off = my_off
        n_opp_off = opp_off

        if n_opp_pts[target] == 1:
            n_opp_pts[target] = 0
            n_opp_bar += 1
        n_my_pts[target] += 1
        return True, (n_my_pts, n_opp_pts, n_my_bar, n_opp_bar, n_my_off, n_opp_off)

    elif isinstance(pos, int) and 0 <= pos <= 23:
        if my_bar > 0 or my_pts[pos] <= 0:
            return False, None

        target = pos - die
        if target >= 0:
            if opp_pts[target] >= 2:
                return False, None

            n_my_pts = list(my_pts)
            n_opp_pts = list(opp_pts)
            n_my_pts[pos] -= 1
            n_opp_bar = opp_bar

            if n_opp_pts[target] == 1:
                n_opp_pts[target] = 0
                n_opp_bar += 1
            n_my_pts[target] += 1
            return True, (n_my_pts, n_opp_pts, my_bar, n_opp_bar, my_off, opp_off)
        else:
            # Bearing off: only allowed if all remaining checkers are in home board (0..5)
            if any(my_pts[i] > 0 for i in range(6, 24)):
                return False, None

            if target == -1:
                # Exact bear-off
                pass
            else:
                # Overshoot: only legal if no checkers exist on higher home board points
                if any(my_pts[i] > 0 for i in range(pos + 1, 6)):
                    return False, None

            n_my_pts = list(my_pts)
            n_my_pts[pos] -= 1
            return True, (n_my_pts, list(opp_pts), my_bar, opp_bar, my_off + 1, opp_off)

    return False, None


def evaluate_state(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off):
    """
    Expert heuristic evaluation of the board position from our perspective.
    """
    score = 0.0

    # 1. Borne off checkers (huge score)
    score += my_off * 35.0
    score -= opp_off * 35.0

    # 2. Checkers on Bar
    score -= my_bar * 25.0
    score += opp_bar * 22.0

    # 3. Pip count calculation (lower is better for us)
    my_pip = my_bar * 25
    for p in range(24):
        if my_pts[p] > 0:
            my_pip += my_pts[p] * (p + 1)

    opp_pip = opp_bar * 25
    for p in range(24):
        if opp_pts[p] > 0:
            opp_pip += opp_pts[p] * (24 - p)

    score += (opp_pip - my_pip) * 1.3

    # 4. Point-making and Priming
    consecutive_points = 0
    max_prime = 0

    for p in range(24):
        cnt = my_pts[p]
        if cnt >= 2:
            consecutive_points += 1
            if consecutive_points > max_prime:
                max_prime = consecutive_points

            # Points in our home board (0..5)
            if p <= 5:
                if p in (3, 4):
                    score += 7.5
                elif p in (2, 5):
                    score += 5.5
                else:
                    score += 4.0
            elif p in (6, 7):
                score += 5.0
            elif p in (19, 20):  # Golden anchor in opponent home board
                score += 6.5
            elif p in (18, 21, 22):
                score += 4.5
            else:
                score += 3.0

            # Penalty for over-stacking (> 3 checkers on one point)
            if cnt > 3:
                score -= (cnt - 3) * 1.5
        else:
            consecutive_points = 0

    # Prime bonuses
    if max_prime == 2:
        score += 2.0
    elif max_prime == 3:
        score += 5.5
    elif max_prime == 4:
        score += 11.0
    elif max_prime == 5:
        score += 19.0
    elif max_prime >= 6:
        score += 32.0

    # 5. Blots and Direct Threat Exposure
    for p in range(24):
        if my_pts[p] == 1:
            blot_penalty = 7.0
            hit_threat = False

            # Opponent on bar entering in our home board (0..5)
            if opp_bar > 0 and p <= 5:
                hit_threat = True

            # Opponent on board within direct roll range (1..6)
            for d in range(1, 7):
                q = p - d
                if q >= 0 and opp_pts[q] > 0:
                    hit_threat = True
                    break

            if hit_threat:
                blot_penalty += 8.0
                if p <= 5:
                    blot_penalty += 6.0

            score -= blot_penalty

    # 6. Escaping back checkers
    back_checkers = sum(my_pts[18:24])
    score -= back_checkers * 1.5

    return score


def policy(state: dict) -> str:
    my_pts = list(state.get('my_pts', [0] * 24))
    opp_pts = list(state.get('opp_pts', [0] * 24))
    my_bar = state.get('my_bar', 0)
    opp_bar = state.get('opp_bar', 0)
    my_off = state.get('my_off', 0)
    opp_off = state.get('opp_off', 0)
    dice = list(state.get('dice', []))

    if not dice:
        return "H:P,P"

    if len(dice) == 1:
        d = dice[0]
        legal_starts = ['B'] if my_bar > 0 else [p for p in range(24) if my_pts[p] > 0]
        best_str = "H:P,P"
        best_eval = -float('inf')

        for pos in legal_starts:
            ok, next_st = apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, pos, d)
            if ok:
                ev = evaluate_state(*next_st)
                if ev > best_eval:
                    best_eval = ev
                    best_str = f"H:{to_token(pos)},P"
        return best_str

    # Exactly 2 dice: evaluate high and low
    d1, d2 = dice[0], dice[1]
    d_high = max(d1, d2)
    d_low = min(d1, d2)

    # 1. Search for legal two-move combinations
    two_moves = []  # List of tuples: (order, pos1, pos2, resulting_state)

    # Order 'H': d_high first, then d_low
    starts_1 = ['B'] if my_bar > 0 else [p for p in range(24) if my_pts[p] > 0]
    for p1 in starts_1:
        ok1, s1 = apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, p1, d_high)
        if ok1:
            m_pts1, o_pts1, m_bar1, o_bar1, m_off1, o_off1 = s1
            starts_2 = ['B'] if m_bar1 > 0 else [p for p in range(24) if m_pts1[p] > 0]
            for p2 in starts_2:
                ok2, s2 = apply_move(m_pts1, o_pts1, m_bar1, o_bar1, m_off1, o_off1, p2, d_low)
                if ok2:
                    two_moves.append(('H', p1, p2, s2))

    # Order 'L': d_low first, then d_high (only needed if dice differ)
    if d_high != d_low:
        starts_1 = ['B'] if my_bar > 0 else [p for p in range(24) if my_pts[p] > 0]
        for p1 in starts_1:
            ok1, s1 = apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, p1, d_low)
            if ok1:
                m_pts1, o_pts1, m_bar1, o_bar1, m_off1, o_off1 = s1
                starts_2 = ['B'] if m_bar1 > 0 else [p for p in range(24) if m_pts1[p] > 0]
                for p2 in starts_2:
                    ok2, s2 = apply_move(m_pts1, o_pts1, m_bar1, o_bar1, m_off1, o_off1, p2, d_high)
                    if ok2:
                        two_moves.append(('L', p1, p2, s2))

    # If both dice can be played, we must play both
    if two_moves:
        best_str = None
        best_eval = -float('inf')
        for order, p1, p2, st in two_moves:
            ev = evaluate_state(*st)
            if ev > best_eval:
                best_eval = ev
                best_str = f"{order}:{to_token(p1)},{to_token(p2)}"
        return best_str

    # 2. If both dice cannot be played, must play higher die if possible
    legal_starts = ['B'] if my_bar > 0 else [p for p in range(24) if my_pts[p] > 0]
    high_moves = []
    for p1 in legal_starts:
        ok, st = apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, p1, d_high)
        if ok:
            high_moves.append((p1, st))

    if high_moves:
        best_p1 = None
        best_eval = -float('inf')
        for p1, st in high_moves:
            ev = evaluate_state(*st)
            if ev > best_eval:
                best_eval = ev
                best_p1 = p1
        return f"H:{to_token(best_p1)},P"

    # 3. If higher die cannot be played, play lower die if possible
    low_moves = []
    for p1 in legal_starts:
        ok, st = apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, p1, d_low)
        if ok:
            low_moves.append((p1, st))

    if low_moves:
        best_p1 = None
        best_eval = -float('inf')
        for p1, st in low_moves:
            ev = evaluate_state(*st)
            if ev > best_eval:
                best_eval = ev
                best_p1 = p1
        return f"L:{to_token(best_p1)},P"

    # 4. No legal moves
    return "H:P,P"
