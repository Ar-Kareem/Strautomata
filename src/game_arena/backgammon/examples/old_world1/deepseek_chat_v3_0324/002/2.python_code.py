
import numpy as np

def policy(state: dict) -> str:
    my_pts = np.array(state['my_pts'])
    opp_pts = np.array(state['opp_pts'])
    dice = sorted(state['dice'], reverse=True)
    if len(dice) == 0:
        return "H:P,P"
    
    def is_blocked(point):
        return opp_pts[point] >= 2
    
    def is_blot(point):
        return opp_pts[point] == 1
    
    def can_hit(from_point, steps):
        to_point = from_point - steps
        if 0 <= to_point < 24:
            return is_blot(to_point)
        return False
    
    def is_legal_move(from_point, die):
        if from_point == 'B':
            if state['my_bar'] == 0:
                return False
            to_point = 24 - die
            return not is_blocked(to_point)
        else:
            to_point = from_point - die
            if to_point < 0:  # Bearing off
                return all(my_pts[i] == 0 for i in range(18))
            return not is_blocked(to_point)
    
    def evaluate_move(move):
        score = 0
        order, from1, from2 = move
        
        # Check bar re-entry first
        if state['my_bar'] > 0:
            if from1 == 'B':
                score += 100
            if from2 == 'B':
                score += 100
        
        # Evaluate first move
        if from1 != 'P':
            die = dice[0] if order == 'H' else dice[1]
            if from1 == 'B':
                entry_point = 24 - die
                score += entry_point  # Prefer higher entry points
            else:
                to_point = from1 - die
                if to_point >= 0:
                    if is_blot(to_point):
                        score += 50  # Hitting bonus
                    if from1 - to_point > 1:
                        score += 10  # Running bonus
                else:
                    score += 30  # Bearing off bonus
        
        # Evaluate second move
        if from2 != 'P':
            die = dice[1] if order == 'H' else dice[0]
            if from2 == 'B':
                entry_point = 24 - die
                score += entry_point
            else:
                to_point = from2 - die
                if to_point >= 0:
                    if is_blot(to_point):
                        score += 50
                    if from2 - to_point > 1:
                        score += 10
                else:
                    score += 30
        
        return score
    
    # Generate all possible legal moves
    possible_moves = []
    
    # Handle bar re-entry first if needed
    if state['my_bar'] > 0:
        for die in dice:
            if is_legal_move('B', die):
                if len(dice) == 1:
                    possible_moves.append(('H', 'B', 'P'))
                else:
                    other_die = dice[0] if die == dice[1] else dice[1]
                    if is_legal_move('B', other_die):
                        possible_moves.append(('H', 'B', 'B'))
                    else:
                        possible_moves.append(('H', 'B', 'P'))
                    possible_moves.append(('L', 'B', 'P'))
        if not possible_moves:
            return "H:P,P"
    else:
        # Generate regular moves
        for order in ['H', 'L']:
            if len(dice) == 1:
                die = dice[0]
                for from1 in range(24):
                    if my_pts[from1] > 0 and is_legal_move(from1, die):
                        possible_moves.append((order, from1, 'P'))
            else:
                die1 = dice[0] if order == 'H' else dice[1]
                die2 = dice[1] if order == 'H' else dice[0]
                
                # Try all combinations of two moves
                for from1 in range(24):
                    if my_pts[from1] > 0 and is_legal_move(from1, die1):
                        for from2 in range(24):
                            if (from1 == from2 and my_pts[from1] > 1) or (from1 != from2 and my_pts[from2] > 0):
                                if is_legal_move(from2, die2):
                                    possible_moves.append((order, from1, from2))
                        # Also consider single moves when two aren't possible
                        possible_moves.append((order, from1, 'P'))
                
                # Also consider reverse order if no two moves found
                if not any(m[1] != 'P' and m[2] != 'P' for m in possible_moves):
                    for from2 in range(24):
                        if my_pts[from2] > 0 and is_legal_move(from2, die2):
                            possible_moves.append((order, 'P', from2))
    
    if not possible_moves:
        return "H:P,P"
    
    # Select the best move based on evaluation
    best_move = max(possible_moves, key=evaluate_move)
    order, from1, from2 = best_move
    
    def format_point(p):
        if p == 'P':
            return 'P'
        elif p == 'B':
            return 'B'
        else:
            return f'A{p}'
    
    from1_str = format_point(from1)
    from2_str = format_point(from2)
    
    return f"{order}:{from1_str},{from2_str}"
