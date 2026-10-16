
import itertools

def policy(state: dict) -> str:
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = list(state['dice'])
    
    if len(dice) == 0:
        return "H:P,P"
    
    # Generate all possible moves and evaluate them
    best_score = -1e18
    best_move = "H:P,P"
    
    def can_move_from(pt, die, m_pts, m_bar, m_off, o_pts):
        # Returns (new_m_pts, new_m_bar, new_m_off, new_o_pts, new_o_bar_delta, valid)
        dest = pt - die
        if dest < 0:
            # Bearing off - check all checkers in home board (0-5)
            total = sum(m_pts[i] for i in range(6)) + (1 if pt < 6 else 0)
            remaining = 15 - m_off - m_bar
            if total < remaining:
                return None
            if dest < 0 and pt != die - 1:
                # Check if there's a higher point with checkers
                if dest < -1 or any(m_pts[i] > 0 for i in range(pt+1, 6)):
                    if dest != -1 and pt != max(i for i in range(6) if m_pts[i] > 0):
                        return None
            nm = list(m_pts); no = list(o_pts)
            nm[pt] -= 1
            return (nm, m_bar, m_off + 1, no, 0, True)
        if o_pts[23 - dest] >= 2:
            return None
        nm = list(m_pts); no = list(o_pts)
        nm[pt] -= 1
        nm[dest] += 1
        hit = 0
        if no[23 - dest] == 1:
            no[23 - dest] = 0
            hit = 1
        return (nm, m_bar, m_off, no, hit, True)
    
    def bar_move(die, m_pts, m_bar, m_off, o_pts):
        dest = 23 - (die - 1)  # entering from bar: die 1->pt23, die 6->pt18
        if o_pts[23 - dest] >= 2:
            return None
        nm = list(m_pts); no = list(o_pts)
        nm[dest] += 1
        hit = 0
        if no[23 - dest] == 1:
            no[23 - dest] = 0
            hit = 1
        return (nm, m_bar - 1, m_off, no, hit, True)

    def evaluate(m_pts, m_bar, m_off, o_pts, o_bar, o_off):
        score = 0.0
        score += m_off * 100
        score -= m_bar * 80
        score += o_bar * 60
        pip = sum((i+1) * m_pts[i] for i in range(24)) + m_bar * 25
        score -= pip * 0.5
        for i in range(6):
            if m_pts[i] >= 2: score += 15
        for i in range(6, 24):
            if m_pts[i] >= 2: score += 8
        for i in range(24):
            if m_pts[i] == 1:
                score -= (3 + (23-i)*0.3)
        # Primes
        consec = 0
        for i in range(24):
            if m_pts[i] >= 2: consec += 1
            else: consec = 0
            if consec >= 3: score += 10 * consec
        return score

    def get_sources(m_pts, m_bar, die):
        srcs = []
        if m_bar > 0:
            srcs.append('B')
            return srcs
        for i in range(24):
            if m_pts[i] > 0 and i - die >= -1:
                srcs.append(i)
            elif m_pts[i] > 0 and i < 6:
                # bearing off with higher die
                if all(m_pts[j] == 0 for j in range(i+1, 6)):
                    remaining = 15 - m_off - m_bar
                    home = sum(m_pts[j] for j in range(6))
                    if home >= remaining:
                        srcs.append(i)
        return srcs

    def try_move(src, die, m_pts, m_bar, m_off, o_pts, o_bar):
        if src == 'B':
            res = bar_move(die, m_pts, m_bar, m_off, o_pts)
            if res is None: return None
            nm, nb, noff, no, hit, _ = res
            return (nm, nb, noff, no, o_bar + hit)
        else:
            if m_pts[src] <= 0: return None
            res = can_move_from(src, die, m_pts, m_bar, m_off, o_pts)
            if res is None: return None
            nm, nb, noff, no, hit, _ = res
            return (nm, nb, noff, no, o_bar + hit)

    if len(dice) == 1:
        die = dice[0]
        srcs = get_sources(my_pts, my_bar, die)
        for s in srcs:
            res = try_move(s, die, my_pts, my_bar, my_off, opp_pts, opp_bar)
            if res is None: continue
            nm, nb, noff, no, nob = res
            sc = evaluate(nm, nb, noff, no, nob, opp_off)
            if sc > best_score:
                best_score = sc
                src_str = 'B' if s == 'B' else f'A{s}'
                best_move = f"H:{src_str},P"
        return best_move

    d0, d1 = dice[0], dice[1]
    orders = [('H', max(d0,d1), min(d0,d1)), ('L', min(d0,d1), max(d0,d1))]
    
    for order_char, first_die, second_die in orders:
        srcs1 = get_sources(my_pts, my_bar, first_die)
        for s1 in srcs1:
            r1 = try_move(s1, first_die, my_pts, my_bar, my_off, opp_pts, opp_bar)
            if r1 is None: continue
            nm1, nb1, noff1, no1, nob1 = r1
            srcs2 = get_sources(nm1, nb1, second_die)
            moved_two = False
            for s2 in srcs2:
                r2 = try_move(s2, second_die, nm1, nb1, noff1, no1, nob1)
                if r2 is None: continue
                nm2, nb2, noff2, no2, nob2 = r2
                sc = evaluate(nm2, nb2, noff2, no2, nob2, opp_off)
                if sc > best_score:
                    best_score = sc
                    s1s = 'B' if s1 == 'B' else f'A{s1}'
                    s2s = 'B' if s2 == 'B' else f'A{s2}'
                    best_move = f"{order_char}:{s1s},{s2s}"
                moved_two = True
            if not moved_two:
                sc = evaluate(nm1, nb1, noff1, no1, nob1, opp_off)
                if sc > best_score - 50:
                    s1s = 'B' if s1 == 'B' else f'A{s1}'
                    cand = f"{order_char}:{s1s},P"
                    if sc > best_score:
                        best_score = sc
                        best_move = cand

    return best_move
