
import numpy as np

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = sorted(state['dice'], reverse=True)
    
    # Determine movement direction by checking which side checkers move toward
    # In this environment, we analyze the distribution to infer direction.
    # Usually, one player moves 0->23, the other 23->0.
    # We'll detect direction based on 'bearing off' logic or starting positions.
    direction = 1
    home_indices = range(18, 24)
    if sum(my_pts[0:6]) > sum(my_pts[18:24]) and state['my_off'] < 5:
        direction = -1
        home_indices = range(0, 6)

    def is_legal(start_idx, die, current_my, current_opp, current_bar):
        if start_idx == 'B':
            if current_bar == 0: return False
            target = (die - 1) if direction == 1 else (24 - die)
        else:
            target = start_idx + (die * direction)
        
        # Bearing off
        if target < 0 or target > 23:
            # Check if all checkers are in home board
            on_board_count = sum(current_my)
            home_count = sum(current_my[i] for i in home_indices)
            if current_bar > 0 or on_board_count != home_count:
                return False
            return True
        
        # Point occupied by opponent
        if current_opp[target] >= 2:
            return False
        return True

    def get_all_moves():
        moves = []
        d1, d2 = (dice[0], dice[1]) if len(dice) == 2 else (dice[0], 0)
        
        # Try both H (High first) and L (Low first)
        for order in ['H', 'L']:
            curr_d1 = d1 if order == 'H' else d2
            curr_d2 = d2 if order == 'H' else d1
            
            # Step 1
            valid_starts1 = ['B'] if my_bar > 0 else [i for i, count in enumerate(my_pts) if count > 0]
            for s1 in valid_starts1:
                if curr_d1 > 0 and is_legal(s1, curr_d1, my_pts, opp_pts, my_bar):
                    # Simulate step 1
                    m_pts1 = list(my_pts)
                    m_bar1 = my_bar
                    if s1 == 'B': m_bar1 -= 1
                    else: m_pts1[s1] -= 1
                    
                    t1 = (curr_d1 - 1) if direction == 1 else (24 - curr_d1) if s1 == 'B' else s1 + (curr_d1 * direction)
                    if 0 <= t1 <= 23: m_pts1[t1] += 1
                    
                    # Step 2
                    if curr_d2 > 0:
                        valid_starts2 = ['B'] if m_bar1 > 0 else [i for i, count in enumerate(m_pts1) if count > 0]
                        found_s2 = False
                        for s2 in valid_starts2:
                            if is_legal(s2, curr_d2, m_pts1, opp_pts, m_bar1):
                                moves.append(f"{order}:{s1 if s1 == 'B' else 'A'+str(s1)},{s2 if s2 == 'B' else 'A'+str(s2)}")
                                found_s2 = True
                        if not found_s2:
                            moves.append(f"{order}:{s1 if s1 == 'B' else 'A'+str(s1)},P")
                    else:
                        moves.append(f"{order}:{s1 if s1 == 'B' else 'A'+str(s1)},P")
        
        return list(set(moves)) if moves else ["H:P,P"]

    def evaluate(move_str):
        # Simple heuristic: prioritize hitting, making points, and moving forward
        score = 0
        if move_str == "H:P,P": return -10000
        
        # Extract starting points
        try:
            parts = move_str[2:].split(',')
            for i, p in enumerate(parts):
                if p == 'P': continue
                die = dice[0] if (i == 0 and move_str[0] == 'H') or (i == 1 and move_str[0] == 'L') else dice[1]
                if p == 'B':
                    target = (die - 1) if direction == 1 else (24 - die)
                else:
                    idx = int(p[1:])
                    target = idx + (die * direction)
                
                # Reward hitting
                if 0 <= target <= 23 and opp_pts[target] == 1:
                    score += 15
                # Reward bearing off
                if target < 0 or target > 23:
                    score += 10
                # Reward making points
                if 0 <= target <= 23 and my_pts[target] == 1:
                    score += 5
                # Progress score
                score += 1
        except:
            pass
        return score

    all_legal = get_all_moves()
    best_move = max(all_legal, key=evaluate)
    return best_move

