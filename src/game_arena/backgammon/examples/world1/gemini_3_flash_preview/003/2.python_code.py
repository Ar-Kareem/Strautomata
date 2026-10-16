
import collections

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = sorted(state['dice'], reverse=True)
    
    if not dice:
        return "H:P,P"

    def get_destination(start_idx, die):
        if start_idx == 'B':
            target = 24 - die
        else:
            target = start_idx - die
        return target

    def is_legal_dest(target, opp_pts):
        if target < 0: # Bearing off logic
            return True
        if target > 23:
            return False
        return opp_pts[target] < 2

    def get_legal_moves_for_die(current_my_pts, current_my_bar, die):
        legals = []
        if current_my_bar > 0:
            target = 24 - die
            if is_legal_dest(target, opp_pts):
                legals.append('B')
            return legals # Must move from bar if possible
        
        # Check if bearing off is allowed
        farthest_checker = -1
        for i in range(23, -1, -1):
            if current_my_pts[i] > 0:
                farthest_checker = i
                break
        
        can_bear_off = farthest_checker < 6 and current_my_bar == 0
        
        for i in range(24):
            if current_my_pts[i] > 0:
                target = i - die
                if target >= 0:
                    if is_legal_dest(target, opp_pts):
                        legals.append(f"A{i}")
                elif can_bear_off:
                    # Exact roll or higher roll from farthest point
                    if target == -1 or i == farthest_checker:
                        legals.append(f"A{i}")
        return legals

    def evaluate_board(pts, bar, off):
        score = off * 100
        for i in range(24):
            if pts[i] > 1:
                score += (24 - i) * 0.5 # Bonus for making points
            if pts[i] == 1:
                score -= (24 - i) * 1.5 # Penalty for blots
            if pts[i] > 0:
                score += (24 - i) * 0.1 # Progression
        return score

    best_move = "H:P,P"
    max_score = -float('inf')

    # Try H (High die first) then L (Low die first)
    for order in ['H', 'L']:
        d1, d2 = (dice[0], dice[1]) if order == 'H' else (dice[1], dice[0])
        
        m1_candidates = get_legal_moves_for_die(my_pts, my_bar, d1)
        if not m1_candidates:
            # Try just the second die
            m2_candidates = get_legal_moves_for_die(my_pts, my_bar, d2)
            for m2 in m2_candidates:
                if max_score < -500: # Any move is better than none
                    max_score = -500
                    best_move = f"{order}:P,{m2}"
            continue

        for m1 in m1_candidates:
            # Simulate first move
            tmp_pts = list(my_pts)
            tmp_bar = my_bar
            if m1 == 'B':
                tmp_bar -= 1
                dest = 24 - d1
            else:
                idx = int(m1[1:])
                tmp_pts[idx] -= 1
                dest = idx - d1
            
            hit = False
            if dest >= 0 and opp_pts[dest] == 1:
                hit = True
            
            if dest >= 0:
                tmp_pts[dest] += 1
            
            m2_candidates = get_legal_moves_for_die(tmp_pts, tmp_bar, d2)
            if not m2_candidates:
                score = evaluate_board(tmp_pts, tmp_bar, state['my_off']) + (20 if hit else 0)
                if score > max_score:
                    max_score = score
                    best_move = f"{order}:{m1},P"
            else:
                for m2 in m2_candidates:
                    tmp_pts2 = list(tmp_pts)
                    tmp_bar2 = tmp_bar
                    if m2 == 'B':
                        tmp_bar2 -= 1
                        dest2 = 24 - d2
                    else:
                        idx2 = int(m2[1:])
                        tmp_pts2[idx2] -= 1
                        dest2 = idx2 - d2
                    
                    hit2 = False
                    if dest2 >= 0 and opp_pts[dest2] == 1:
                        hit2 = True
                    
                    if dest2 >= 0:
                        tmp_pts2[dest2] += 1
                    
                    score = evaluate_board(tmp_pts2, tmp_bar2, state['my_off']) + (20 if hit else 0) + (20 if hit2 else 0)
                    if score > max_score:
                        max_score = score
                        best_move = f"{order}:{m1},{m2}"

    return best_move
