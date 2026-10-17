
import copy

def is_bearing_off_allowed(my_pts, my_bar):
    if my_bar > 0:
        return False
    return sum(my_pts[6:]) == 0

def get_single_moves(my_pts, opp_pts, my_bar, die):
    """
    Returns list of legal single move origins from the given board state.
    Origin is either 'B' or an integer 0..23.
    """
    moves = []
    # If bar has checkers, must move from bar
    if my_bar > 0:
        dest = 24 - die
        if 0 <= dest <= 23:
            if opp_pts[dest] < 2:
                moves.append('B')
        return moves

    bearing_off = is_bearing_off_allowed(my_pts, my_bar)

    for pt in range(24):
        if my_pts[pt] > 0:
            dest = pt - die
            if dest >= 0:
                if opp_pts[dest] < 2:
                    moves.append(pt)
            elif bearing_off:
                if dest == -1:
                    moves.append(pt)
                else: # dest < -1: overshoot allowed only if no checkers on higher points
                    if sum(my_pts[pt + 1:6]) == 0:
                        moves.append(pt)
    return moves

def apply_single_move(my_pts, opp_pts, my_bar, opp_bar, my_off, move, die):
    """
    Applies a single move and returns new state:
    (my_pts, opp_pts, my_bar, opp_bar, my_off)
    """
    my_pts = list(my_pts)
    opp_pts = list(opp_pts)
    
    if move == 'B':
        my_bar -= 1
        dest = 24 - die
        if opp_pts[dest] == 1:
            opp_pts[dest] = 0
            opp_bar += 1
        my_pts[dest] += 1
    else:
        pt = move
        my_pts[pt] -= 1
        dest = pt - die
        if dest >= 0:
            if opp_pts[dest] == 1:
                opp_pts[dest] = 0
                opp_bar += 1
            my_pts[dest] += 1
        else:
            my_off += 1

    return my_pts, opp_pts, my_bar, opp_bar, my_off

def evaluate_board(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off):
    """
    Heuristic evaluation of the board from 'my' perspective.
    Higher score is better.
    """
    score = 0.0

    # 1. Bear off progress
    score += my_off * 35.0
    score -= opp_off * 35.0

    # 2. Checkers on bar
    score -= my_bar * 45.0
    score += opp_bar * 50.0

    # 3. Pip count (distance to bear off)
    my_pip = my_bar * 25
    opp_pip = opp_bar * 25
    for i in range(24):
        if my_pts[i] > 0:
            my_pip += my_pts[i] * (i + 1)
        if opp_pts[i] > 0:
            opp_pip += opp_pts[i] * (24 - i)
    score += (opp_pip - my_pip) * 2.0

    # 4. Made points (anchors) and primes
    home_points = 0
    prime_len = 0
    max_prime = 0
    for i in range(24):
        count = my_pts[i]
        if count >= 2:
            score += 8.0
            if i <= 5: # Home board point
                home_points += 1
                score += 10.0 + (5 - i) * 1.5
            prime_len += 1
            if prime_len > max_prime:
                max_prime = prime_len
        else:
            prime_len = 0
    score += max_prime * 12.0
    score += (home_points ** 1.5) * 6.0

    # 5. Blot risk evaluation
    for i in range(24):
        if my_pts[i] == 1:
            # Danger level depends on distance to opposing checkers
            threat_level = 0
            if opp_bar > 0 and (24 - i) <= 6:
                threat_level += 2
            for opp_pt in range(24):
                if opp_pts[opp_pt] > 0 and opp_pt < i and (i - opp_pt) <= 12:
                    dist = i - opp_pt
                    if dist <= 6:
                        threat_level += 2
                    else:
                        threat_level += 1
            if threat_level > 0:
                # Vulnerable blot penalty
                score -= 15.0 + min(threat_level, 4) * 6.0
                if i <= 5: # Blots in home board are very risky
                    score -= 10.0
            else:
                score -= 4.0 # Mild penalty for single checker

    return score

def fmt_token(move):
    if move == 'B':
        return 'B'
    elif move == 'P':
        return 'P'
    else:
        return f"A{move}"

def policy(state: dict) -> str:
    dice = state.get('dice', [])
    if not dice:
        return "H:P,P"

    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']

    if len(dice) == 1:
        die = dice[0]
        moves = get_single_moves(my_pts, opp_pts, my_bar, die)
        if not moves:
            return "H:P,P"
        best_score = -float('inf')
        best_move = moves[0]
        for m in moves:
            m_pts, o_pts, m_bar, o_bar, m_off = apply_single_move(
                my_pts, opp_pts, my_bar, opp_bar, my_off, m, die
            )
            s = evaluate_board(m_pts, o_pts, m_bar, o_bar, m_off, opp_off)
            if s > best_score:
                best_score = s
                best_move = m
        return f"H:{fmt_token(best_move)},P"

    d1, d2 = dice[0], dice[1]
    d_high = max(d1, d2)
    d_low = min(d1, d2)

    # Find all legal 2-ply actions
    # We explore both orders:
    # 'H': d_high then d_low
    # 'L': d_low then d_high
    two_ply_candidates = []
    one_ply_high = []
    one_ply_low = []

    # 1. Order 'H'
    moves1_H = get_single_moves(my_pts, opp_pts, my_bar, d_high)
    for m1 in moves1_H:
        s1_pts, s1_opp_pts, s1_bar, s1_opp_bar, s1_off = apply_single_move(
            my_pts, opp_pts, my_bar, opp_bar, my_off, m1, d_high
        )
        moves2 = get_single_moves(s1_pts, s1_opp_pts, s1_bar, d_low)
        if moves2:
            for m2 in moves2:
                s2_pts, s2_opp_pts, s2_bar, s2_opp_bar, s2_off = apply_single_move(
                    s1_pts, s1_opp_pts, s1_bar, s1_opp_bar, s1_off, m2, d_low
                )
                score = evaluate_board(s2_pts, s2_opp_pts, s2_bar, s2_opp_bar, s2_off, opp_off)
                two_ply_candidates.append(('H', m1, m2, score))
        else:
            score = evaluate_board(s1_pts, s1_opp_pts, s1_bar, s1_opp_bar, s1_off, opp_off)
            one_ply_high.append(('H', m1, 'P', score))

    # 2. Order 'L' (only necessary if d_high != d_low)
    if d_high != d_low:
        moves1_L = get_single_moves(my_pts, opp_pts, my_bar, d_low)
        for m1 in moves1_L:
            s1_pts, s1_opp_pts, s1_bar, s1_opp_bar, s1_off = apply_single_move(
                my_pts, opp_pts, my_bar, opp_bar, my_off, m1, d_low
            )
            moves2 = get_single_moves(s1_pts, s1_opp_pts, s1_bar, d_high)
            if moves2:
                for m2 in moves2:
                    s2_pts, s2_opp_pts, s2_bar, s2_opp_bar, s2_off = apply_single_move(
                        s1_pts, s1_opp_pts, s1_bar, s1_opp_bar, s1_off, m2, d_high
                    )
                    score = evaluate_board(s2_pts, s2_opp_pts, s2_bar, s2_opp_bar, s2_off, opp_off)
                    two_ply_candidates.append(('L', m1, m2, score))
            else:
                score = evaluate_board(s1_pts, s1_opp_pts, s1_bar, s1_opp_bar, s1_off, opp_off)
                one_ply_low.append(('L', m1, 'P', score))

    # Decision logic based on Backgammon rules:
    # 1. If both dice can be played, must play both.
    if two_ply_candidates:
        best_action = max(two_ply_candidates, key=lambda c: c[3])
        return f"{best_action[0]}:{fmt_token(best_action[1])},{fmt_token(best_action[2])}"

    # 2. If only one die can be played, must play higher die if possible.
    if one_ply_high:
        best_action = max(one_ply_high, key=lambda c: c[3])
        return f"{best_action[0]}:{fmt_token(best_action[1])},{fmt_token(best_action[2])}"

    if one_ply_low:
        best_action = max(one_ply_low, key=lambda c: c[3])
        return f"{best_action[0]}:{fmt_token(best_action[1])},{fmt_token(best_action[2])}"

    # 3. No legal moves
    return "H:P,P"
