
import copy
from itertools import permutations

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'], reverse=True)
    
    # If no dice, pass
    if not dice:
        return "H:P,P"
    
    # Determine if all my checkers are in home board (for bearing off)
    in_home_board = all(my_pts[i] == 0 for i in range(18))  # points 0-17 are outer, 18-23 home for player 0 (assumed)
    
    # Generate legal moves
    def is_legal_start(src, die):
        if src == 'B':
            if my_bar == 0:
                return False
            dest = die - 1  # assuming from bar, die 1 moves to point 0
        else:
            pt = int(src[1:])
            if my_pts[pt] == 0:
                return False
            dest = pt + die
        if dest >= 24:  # bearing off
            if in_home_board:
                return True  # allowed
            else:
                # must bear off from highest point or use exact die
                max_pt = max([i for i, c in enumerate(my_pts) if c > 0], default=-1)
                if pt == max_pt and dest >= 24:
                    return True
                if dest > 23:
                    return False
        if dest < 24 and opp_pts[dest] >= 2:
            return False
        return True

    def apply_move(state_copy, src, die):
        # Applies a move and returns success and new state
        my_pts = state_copy['my_pts']
        opp_pts = state_copy['opp_pts']
        my_bar = state_copy['my_bar']
        my_off = state_copy['my_off']
        in_home_board = all(my_pts[i] == 0 for i in range(18))
        
        if src == 'B':
            if my_bar == 0:
                return False, state_copy
            dest = die - 1
            state_copy['my_bar'] -= 1
        else:
            pt = int(src[1:])
            if my_pts[pt] == 0:
                return False, state_copy
            dest = pt + die
            state_copy['my_pts'][pt] -= 1
        
        if dest >= 24:  # bear off
            if in_home_board or (pt == max(i for i, c in enumerate(my_pts) if c > 0) and dest > 23):
                state_copy['my_off'] += 1
                return True, state_copy
            else:
                return False, state_copy
        
        if opp_pts[dest] == 1:  # hit
            state_copy['opp_pts'][dest] = 0
            state_copy['opp_bar'] += 1
        
        state_copy['my_pts'][dest] += 1
        return True, state_copy

    def get_legal_moves(dice_list, state_copy):
        # Returns list of possible (<ORDER>, <FROM1>, <FROM2>) moves
        moves = []
        dice_sorted = sorted(dice_list, reverse=True)
        h_die, l_die = dice_sorted[0], dice_sorted[-1]
        
        # Determine sources
        sources = ['B'] if state_copy['my_bar'] > 0 else [f'A{i}' for i in range(24) if state_copy['my_pts'][i] > 0]
        
        for order in ['H', 'L']:
            d1, d2 = (h_die, l_die) if order == 'H' else (l_die, h_die)
            for src1 in sources:
                if not is_legal_start(src1, d1):
                    continue
                # Try one move
                state1 = copy.deepcopy(state_copy)
                success, state1 = apply_move(state1, src1, d1)
                if not success:
                    continue
                # After first move, update sources
                sources2 = ['B'] if state1['my_bar'] > 0 else [f'A{i}' for i in range(24) if state1['my_pts'][i] > 0]
                found_second = False
                for src2 in sources2:
                    if is_legal_start(src2, d2):
                        moves.append((order, src1, src2))
                        found_second = True
                if not found_second:
                    moves.append((order, src1, 'P'))
            
            # Also consider only second move if first not possible
            for src2 in sources:
                if is_legal_start(src2, d2):
                    state1 = copy.deepcopy(state_copy)
                    success, state1 = apply_move(state1, src2, d2)
                    if not success:
                        continue
                    sources2 = ['B'] if state1['my_bar'] > 0 else [f'A{i}' for i in range(24) if state1['my_pts'][i] > 0]
                    found_second = False
                    for src1 in sources2:
                        if is_legal_start(src1, d1):
                            moves.append((order, src1, src2))
                            found_second = True
                    if not found_second:
                        moves.append((order, 'P', src2))
        
        # Add pass if no moves
        if not moves:
            moves.append(('H', 'P', 'P'))
        return moves

    # Get all legal moves
    legal_moves = get_legal_moves(dice, state)
    
    # If only pass, return it
    if len(legal_moves) == 1 and legal_moves[0][1] == 'P' and legal_moves[0][2] == 'P':
        return "H:P,P"
    
    # Score each move
    best_score = -1e9
    best_move = legal_moves[0]
    
    for move in legal_moves:
        order, src1, src2 = move
        if src1 == 'P' and src2 == 'P':
            score = -1000
        else:
            # Simulate the move to evaluate pip count, safety, hits, etc.
            state_sim = copy.deepcopy(state)
            d1, d2 = (dice[0], dice[1]) if order == 'H' else (dice[1], dice[0])
            score = 0
            
            # Apply first move
            if src1 != 'P':
                success, state_sim = apply_move(state_sim, src1, d1)
                if not success:
                    continue
                # Reward pip gain: more if from back
                if src1 == 'B':
                    score += d1
                else:
                    pt1 = int(src1[1:])
                    dest1 = pt1 + d1
                    if dest1 < 24:
                        score += d1
                    else:
                        score += (18 - pt1) * 0.5  # extra for bearing off
                # Bonus for hitting
                if dest1 < 24 and state['opp_pts'][dest1] == 1:
                    score += 5
                
            # Apply second move
            if src2 != 'P':
                success, state_sim = apply_move(state_sim, src2, d2)
                if not success:
                    continue
                if src2 == 'B':
                    score += d2
                else:
                    pt2 = int(src2[1:])
                    dest2 = pt2 + d2
                    if dest2 < 24:
                        score += d2
                    else:
                        score += (18 - pt2) * 0.5
                if dest2 < 24 and state['opp_pts'][dest2] == 1:
                    score += 5
            
            # Avoid leaving blots
            # Check if any point now has exactly one checker and opponent can hit
            for i, c in enumerate(state_sim['my_pts']):
                if c == 1:
                    for d in dice:
                        if i - d >= 0 and state_sim['opp_pts'][i - d] > 0 and i - d < 24:
                            score -= 3  # risk of being hit
            
            # Bonus for bearing off
            new_off = state_sim['my_off']
            score += (new_off - my_off) * 10
            
            # Prefer using both dice
            if src1 != 'P' and src2 != 'P':
                score += 1
                
        if score > best_score:
            best_score = score
            best_move = move
    
    order, src1, src2 = best_move
    return f"{order}:{src1},{src2}"
