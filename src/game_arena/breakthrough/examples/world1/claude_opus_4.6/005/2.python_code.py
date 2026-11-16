
import time

def policy(me, opp, color):
    start_time = time.time()
    time_limit = 0.85  # seconds
    
    me_set = frozenset(me)
    opp_set = frozenset(opp)
    direction = 1 if color == 'w' else -1
    my_goal = 7 if color == 'w' else 0
    opp_goal = 0 if color == 'w' else 7
    opp_dir = -direction
    
    def get_moves(my_pieces, their_pieces, d):
        moves = []
        their_set = their_pieces if isinstance(their_pieces, (set, frozenset)) else set(their_pieces)
        my_set = my_pieces if isinstance(my_pieces, (set, frozenset)) else set(my_pieces)
        all_occupied = my_set | their_set
        for (r, c) in my_pieces:
            nr = r + d
            if 0 <= nr <= 7:
                # Forward
                if (nr, c) not in all_occupied:
                    moves.append(((r, c), (nr, c)))
                # Diagonal left
                if c - 1 >= 0:
                    if (nr, c - 1) in their_set:
                        moves.append(((r, c), (nr, c - 1)))
                    elif (nr, c - 1) not in my_set:
                        moves.append(((r, c), (nr, c - 1)))
                # Diagonal right
                if c + 1 <= 7:
                    if (nr, c + 1) in their_set:
                        moves.append(((r, c), (nr, c + 1)))
                    elif (nr, c + 1) not in my_set:
                        moves.append(((r, c), (nr, c + 1)))
        return moves
    
    def evaluate(my_pieces, their_pieces):
        if not their_pieces:
            return 100000
        if not my_pieces:
            return -100000
        
        score = 0
        # Material
        score += (len(my_pieces) - len(their_pieces)) * 100
        
        their_set = their_pieces if isinstance(their_pieces, (set, frozenset)) else set(their_pieces)
        my_set = my_pieces if isinstance(my_pieces, (set, frozenset)) else set(my_pieces)
        
        for (r, c) in my_pieces:
            # Advancement
            adv = abs(r - (0 if direction == 1 else 7))  # distance from start
            score += adv * adv * 3
            # Promotion proximity
            dist_to_goal = abs(my_goal - r)
            if dist_to_goal == 0:
                return 100000
            if dist_to_goal == 1:
                score += 200
            elif dist_to_goal == 2:
                score += 80
            # Center control
            center_dist = abs(c - 3.5)
            score += (4 - center_dist) * 2
            # Protection: check if supported by friendly piece behind
            br = r - direction
            if 0 <= br <= 7:
                if (br, c-1) in my_set or (br, c+1) in my_set:
                    score += 10
        
        for (r, c) in their_pieces:
            adv = abs(r - (0 if opp_dir == 1 else 7))
            score -= adv * adv * 3
            dist_to_goal = abs(opp_goal - r)
            if dist_to_goal == 0:
                return -100000
            if dist_to_goal == 1:
                score -= 200
            elif dist_to_goal == 2:
                score -= 80
            center_dist = abs(c - 3.5)
            score -= (4 - center_dist) * 2
        
        return score
    
    def order_moves(moves, their_pieces):
        their_set = their_pieces if isinstance(their_pieces, (set, frozenset)) else set(their_pieces)
        captures = []
        advances = []
        others = []
        for m in moves:
            fr, to = m
            if to in their_set:
                captures.append(m)
            elif to[1] == fr[1]:
                advances.append(m)
            else:
                others.append(m)
        return captures + advances + others
    
    def minimax(my_pieces, their_pieces, my_dir, my_goal_r, depth, alpha, beta, is_max):
        if time.time() - start_time > time_limit:
            raise TimeoutError
        
        if not their_pieces:
            return 100000 if is_max else -100000
        if not my_pieces:
            return -100000 if is_max else 100000
        
        # Check for goal reached
        for (r, c) in my_pieces:
            if r == my_goal_r:
                return 100000 if is_max else -100000
        opp_goal_r = 0 if my_goal_r == 7 else 7
        for (r, c) in their_pieces:
            if r == opp_goal_r:
                return -100000 if is_max else 100000
        
        if depth == 0:
            raw = evaluate(my_pieces if is_max else their_pieces, 
                          their_pieces if is_max else my_pieces) if is_max else \
                  evaluate(their_pieces, my_pieces)
            # Actually let's simplify: always evaluate from "me" perspective
            if is_max:
                return evaluate(my_pieces, their_pieces) if my_dir == direction else evaluate(their_pieces, my_pieces)
            else:
                return evaluate(their_pieces, my_pieces) if my_dir != direction else evaluate(my_pieces, their_pieces)
        
        moves = get_moves(my_pieces, their_pieces, my_dir)
        if not moves:
            return -100000 if is_max else 100000
        
        moves = order_moves(moves, their_pieces)
        
        their_set = set(their_pieces)
        
        if is_max:
            max_eval = -200000
            for (fr, to) in moves:
                new_my = (my_pieces - {fr}) | {to}
                new_their = their_set - {to}
                new_their_fs = frozenset(new_their)
                opp_dir = -my_dir
                opp_goal = 0 if my_goal_r == 7 else 7
                val = minimax(new_their_fs, frozenset(new_my), opp_dir, opp_goal, depth - 1, alpha, beta, False)
                if val > max_eval:
                    max_eval = val
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = 200000
            for (fr, to) in moves:
                new_my = (my_pieces - {fr}) | {to}
                new_their = their_set - {to}
                new_their_fs = frozenset(new_their)
                opp_dir = -my_dir
                opp_goal = 0 if my_goal_r == 7 else 7
                val = minimax(new_their_fs, frozenset(new_my), opp_dir, opp_goal, depth - 1, alpha, beta, True)
                if val < min_eval:
                    min_eval = val
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return min_eval
    
    me_fs = frozenset(me)
    opp_fs = frozenset(opp)
    
    moves = get_moves(me_fs, opp_fs, direction)
    if not moves:
        return moves[0]  # shouldn't happen
    
    best_move = moves[0]
    
    # Check instant wins
    for m in moves:
        if m[1][0] == my_goal:
            return m
    
    for max_depth in range(1, 20):
        try:
            best_val = -300000
            ordered = order_moves(moves, opp_fs)
            current_best = ordered[0]
            for (fr, to) in ordered:
                new_me = (me_fs - {fr}) | {to}
                new_opp = opp_fs - {to}
                val = minimax(frozenset(new_opp), frozenset(new_me), opp_dir, opp_goal, max_depth - 1, -300000, 300000, False)
                if val > best_val:
                    best_val = val
                    current_best = (fr, to)
                if time.time() - start_time > time_limit:
                    raise TimeoutError
            best_move = current_best
        except TimeoutError:
            if current_best:
                best_move = current_best
            break
        if best_val >= 90000:
            best_move = current_best
            break
    
    return best_move
