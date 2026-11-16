
import copy

def policy(state: dict) -> str:
    moves = _generate_moves(state)
    if not moves:
        return "H:P,P"
    
    best_move = moves[0]
    best_score = -float('inf')
    
    for move in moves:
        score = _evaluate(move[3])
        if score > best_score:
            best_score = score
            best_move = move
    
    return f"{best_move[0]}:{best_move[1]},{best_move[2]}"

def _copy_state(s):
    return {
        'my_pts': s['my_pts'][:],
        'opp_pts': s['opp_pts'][:],
        'my_bar': s['my_bar'],
        'opp_bar': s['opp_bar'],
        'my_off': s['my_off'],
        'opp_off': s['opp_off'],
        'dice': s['dice'][:]
    }

def _all_in_home_board(s):
    if s['my_bar'] > 0:
        return False
    for i in range(6, 24):
        if s['my_pts'][i] > 0:
            return False
    return True

def _apply_single_move(s, src, die):
    """Apply a single die move. Returns new state or None if illegal."""
    if src == 'B':
        if s['my_bar'] <= 0:
            return None
        dest = 24 - die
        if dest < 0 or dest >= 24:
            return None
        if s['opp_pts'][dest] >= 2:
            return None
        ns = _copy_state(s)
        ns['my_bar'] -= 1
        if ns['opp_pts'][dest] == 1:
            ns['opp_pts'][dest] = 0
            ns['opp_bar'] += 1
        ns['my_pts'][dest] += 1
        return ns
    else:
        try:
            idx = int(src[1:])
        except:
            return None
        if idx < 0 or idx >= 24 or s['my_pts'][idx] <= 0:
            return None
        
        dest = idx - die
        ns = _copy_state(s)
        
        if dest >= 0:
            if ns['opp_pts'][dest] >= 2:
                return None
            ns['my_pts'][idx] -= 1
            if ns['opp_pts'][dest] == 1:
                ns['opp_pts'][dest] = 0
                ns['opp_bar'] += 1
            ns['my_pts'][dest] += 1
            return ns
        else:
            if not _all_in_home_board(ns):
                return None
            if die > idx:
                for j in range(idx + 1, 6):
                    if ns['my_pts'][j] > 0:
                        return None
            ns['my_pts'][idx] -= 1
            ns['my_off'] += 1
            return ns

def _generate_moves(state):
    dice = state['dice']
    if not dice:
        return [('H', 'P', 'P', state)]
    
    if len(dice) == 1:
        d = dice[0]
        res = []
        if state['my_bar'] > 0:
            ns = _apply_single_move(state, 'B', d)
            if ns:
                res.append(('H', 'B', 'P', ns))
        else:
            for i in range(24):
                if state['my_pts'][i] > 0:
                    src = f'A{i}'
                    ns = _apply_single_move(state, src, d)
                    if ns:
                        res.append(('H', src, 'P', ns))
        if not res:
            return [('H', 'P', 'P', state)]
        return res
    
    d1, d2 = dice
    high = max(d1, d2)
    low = min(d1, d2)
    moves = []
    
    # Order H: high then low
    first_sources = []
    if state['my_bar'] > 0:
        if _apply_single_move(state, 'B', high):
            first_sources.append('B')
    else:
        for i in range(24):
            if state['my_pts'][i] > 0:
                if _apply_single_move(state, f'A{i}', high):
                    first_sources.append(f'A{i}')
    
    for src1 in first_sources:
        s1 = _apply_single_move(state, src1, high)
        if not s1:
            continue
        second_sources = []
        if s1['my_bar'] > 0:
            if _apply_single_move(s1, 'B', low):
                second_sources.append('B')
        else:
            for i in range(24):
                if s1['my_pts'][i] > 0:
                    if _apply_single_move(s1, f'A{i}', low):
                        second_sources.append(f'A{i}')
        if second_sources:
            for src2 in second_sources:
                s2 = _apply_single_move(s1, src2, low)
                if s2:
                    moves.append(('H', src1, src2, s2))
        else:
            moves.append(('H', src1, 'P', s1))
    
    # Order L: low then high
    first_sources = []
    if state['my_bar'] > 0:
        if _apply_single_move(state, 'B', low):
            first_sources.append('B')
    else:
        for i in range(24):
            if state['my_pts'][i] > 0:
                if _apply_single_move(state, f'A{i}', low):
                    first_sources.append(f'A{i}')
    
    for src1 in first_sources:
        s1 = _apply_single_move(state, src1, low)
        if not s1:
            continue
        second_sources = []
        if s1['my_bar'] > 0:
            if _apply_single_move(s1, 'B', high):
                second_sources.append('B')
        else:
            for i in range(24):
                if s1['my_pts'][i] > 0:
                    if _apply_single_move(s1, f'A{i}', high):
                        second_sources.append(f'A{i}')
        if second_sources:
            for src2 in second_sources:
                s2 = _apply_single_move(s1, src2, high)
                if s2:
                    moves.append(('L', src1, src2, s2))
        else:
            moves.append(('L', src1, 'P', s1))
    
    full_moves = [m for m in moves if m[2] != 'P']
    if full_moves:
        return full_moves
    
    high_only = [m for m in moves if m[0] == 'H' and m[2] == 'P']
    if high_only:
        return high_only
    
    low_only = [m for m in moves if m[0] == 'L' and m[2] == 'P']
    if low_only:
        return low_only
    
    return [('H', 'P', 'P', state)]

def _evaluate(s):
    score = 0.0
    
    # Pip count (lower is better)
    my_pips = 25 * s['my_bar'] + sum((i + 1) * s['my_pts'][i] for i in range(24))
    opp_pips = 25 * s['opp_bar'] + sum((24 - i) * s['opp_pts'][i] for i in range(24))
    score += (opp_pips - my_pips) * 2.0
    
    # Bearing off progress
    score += s['my_off'] * 50.0
    score -= s['opp_off'] * 50.0
    
    # Home board strength (0-5)
    home_points = sum(1 for i in range(6) if s['my_pts'][i] >= 2)
    score += home_points * 5.0
    
    # Prime building in outer board (6-17)
    for i in range(6, 18):
        if s['my_pts'][i] >= 2 and s['my_pts'][i+1] >= 2:
            score += 2.0
    
    # Blots (exposed checkers) - penalty
    for i in range(24):
        if s['my_pts'][i] == 1:
            # Check for direct shots from opponent (they move 0->23)
            shots = 0
            for d in range(1, 7):
                opp_src = i + d
                if opp_src <= 23 and s['opp_pts'][opp_src] > 0:
                    shots += 1
            if shots > 0:
                score -= 3.0
    
    # Opponent on bar is good
    score += s['opp_bar'] * 10.0
    
    # Being on bar is bad
    score -= s['my_bar'] * 10.0
    
    return score
