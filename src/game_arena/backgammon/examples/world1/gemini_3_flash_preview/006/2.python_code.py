
import copy

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = sorted(state['dice'], reverse=True)
    
    if not dice:
        return "H:P,P"

    def get_legal_moves(s_my_pts, s_opp_pts, s_my_bar, die):
        legs = []
        # Must move from bar if checkers are there
        if s_my_bar > 0:
            dest = 24 - die
            if dest >= 0 and s_opp_pts[dest] < 2:
                legs.append('B')
            return legs # Must move from bar
        
        for i in range(24):
            if s_my_pts[i] > 0:
                dest = i - die
                if dest >= 0:
                    if s_opp_pts[dest] < 2:
                        legs.append(f"A{i}")
                else:
                    # Bearing off
                    can_bear_off = True
                    for j in range(6, 24):
                        if s_my_pts[j] > 0:
                            can_bear_off = False
                            break
                    if can_bear_off:
                        # Exact or furthest back rule
                        if i == die - 1:
                            legs.append(f"A{i}")
                        elif i < die - 1:
                            is_furthest = True
                            for j in range(i + 1, 6):
                                if s_my_pts[j] > 0:
                                    is_furthest = False
                                    break
                            if is_furthest:
                                legs.append(f"A{i}")
        return legs

    def simulate_move(pts, opp_p, bar, move_from, die):
        new_pts = list(pts)
        new_opp = list(opp_p)
        new_bar = bar
        if move_from == 'B':
            new_bar -= 1
            dest = 24 - die
        else:
            idx = int(move_from[1:])
            new_pts[idx] -= 1
            dest = idx - die
        
        if dest >= 0:
            if new_opp[dest] == 1:
                new_opp[dest] = 0
            new_pts[dest] += 1
        return new_pts, new_opp, new_bar

    def evaluate(pts, opp, bar, off):
        score = 0
        for i in range(24):
            # Penalize blots
            if pts[i] == 1:
                # Higher penalty if blot is in range of opponent
                score -= 15
            # Reward anchors
            if pts[i] >= 2:
                score += 10
                if i < 6: score += 5 # Home board anchors
        
        # Reward progress
        for i in range(24):
            score += pts[i] * (24 - i) * 0.2
        
        # Penalty for bar
        score -= bar * 50
        return score

    best_move = "H:P,P"
    max_score = -float('inf')

    # Try H (High die first) then L (Low die first)
    configs = [('H', dice), ('L', dice[::-1])] if len(dice) == 2 else [('H', dice)]
    
    for order, d_list in configs:
        # Move 1
        m1_options = get_legal_moves(my_pts, opp_pts, my_bar, d_list[0])
        if not m1_options:
            m1_options = ['P']
            
        for m1 in m1_options:
            s1_pts, s1_opp, s1_bar = (my_pts, opp_pts, my_bar)
            if m1 != 'P':
                s1_pts, s1_opp, s1_bar = simulate_move(my_pts, opp_pts, my_bar, m1, d_list[0])
            
            # Move 2
            if len(d_list) > 1:
                m2_options = get_legal_moves(s1_pts, s1_opp, s1_bar, d_list[1])
                if not m2_options:
                    m2_options = ['P']
                
                for m2 in m2_options:
                    s2_pts, s2_opp, s2_bar = (s1_pts, s1_opp, s1_bar)
                    if m2 != 'P':
                        s2_pts, s2_opp, s2_bar = simulate_move(s1_pts, s1_opp, s1_bar, m2, d_list[1])
                    
                    # Score state
                    cur_score = evaluate(s2_pts, s2_opp, s2_bar, 0)
                    if cur_score > max_score:
                        max_score = cur_score
                        best_move = f"{order}:{m1},{m2}"
            else:
                cur_score = evaluate(s1_pts, s1_opp, s1_bar, 0)
                if cur_score > max_score:
                    max_score = cur_score
                    best_move = f"{order}:{m1},P"

    return best_move
