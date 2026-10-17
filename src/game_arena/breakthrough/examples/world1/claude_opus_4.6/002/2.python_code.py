
import time

def policy(me, opp, color):
    start_time = time.time()
    time_limit = 0.85
    
    direction = 1 if color == 'w' else -1
    goal_row = 7 if color == 'w' else 0
    opp_goal = 0 if color == 'w' else 7
    
    me_set = set(me)
    opp_set = set(opp)
    
    def get_moves(pieces, opponents, d, is_me=True):
        moves = []
        pset = set(pieces)
        oset = set(opponents)
        for r, c in pieces:
            nr = r + d
            if 0 <= nr <= 7:
                # straight forward
                if (nr, c) not in pset and (nr, c) not in oset:
                    moves.append(((r, c), (nr, c)))
                # diagonal left
                if c - 1 >= 0:
                    if (nr, c-1) in oset:
                        moves.append(((r, c), (nr, c-1)))
                    elif (nr, c-1) not in pset:
                        moves.append(((r, c), (nr, c-1)))
                # diagonal right
                if c + 1 <= 7:
                    if (nr, c+1) in oset:
                        moves.append(((r, c), (nr, c+1)))
                    elif (nr, c+1) not in pset:
                        moves.append(((r, c), (nr, c+1)))
        return moves
    
    def evaluate(my_pieces, opp_pieces, d, gr):
        if not opp_pieces:
            return 100000
        if not my_pieces:
            return -100000
        
        score = 0
        my_set_local = set(my_pieces)
        opp_set_local = set(opp_pieces)
        
        score += (len(my_pieces) - len(opp_pieces)) * 150
        
        for r, c in my_pieces:
            adv = r if d == 1 else (7 - r)
            score += adv * adv * 8
            if (r + d) == gr:
                score += 2000
            # center control
            score += (3.5 - abs(c - 3.5)) * 3
            # protection
            br = r - d
            if 0 <= br <= 7:
                if (br, c-1) in my_set_local or (br, c+1) in my_set_local:
                    score += 15
        
        opp_d = -d
        opp_gr = 0 if gr == 7 else 7
        for r, c in opp_pieces:
            adv = r if opp_d == 1 else (7 - r)
            score -= adv * adv * 8
            if (r + opp_d) == opp_gr:
                score -= 2000
            score -= (3.5 - abs(c - 3.5)) * 3
        
        return score
    
    def order_moves(moves, gr, opp_s):
        def key(m):
            s = 0
            if m[1][0] == gr:
                s += 50000
            if m[1] in opp_s:
                s += 10000
            return -s
        moves.sort(key=key)
        return moves
    
    def minimax(my_p, opp_p, depth, alpha, beta, maximizing, my_d, my_gr, opp_d, opp_gr):
        if time.time() - start_time > time_limit:
            return evaluate(my_p, opp_p, my_d, my_gr), None
        
        # Check wins
        for r, c in my_p:
            if r == my_gr:
                return 100000, None
        for r, c in opp_p:
            if r == opp_gr:
                return -100000, None
        if not opp_p:
            return 100000, None
        if not my_p:
            return -100000, None
        
        if depth == 0:
            return evaluate(my_p, opp_p, my_d, my_gr), None
        
        if maximizing:
            moves = get_moves(my_p, opp_p, my_d)
            if not moves:
                return -100000, None
            opp_s = set(opp_p)
            moves = order_moves(moves, my_gr, opp_s)
            best_val = -999999
            best_move = moves[0]
            for frm, to in moves:
                new_my = [p for p in my_p if p != frm] + [to]
                new_opp = [p for p in opp_p if p != to]
                if to[0] == my_gr:
                    return 100000, (frm, to)
                val, _ = minimax(new_opp, new_my, depth - 1, -beta, -alpha, False, opp_d, opp_gr, my_d, my_gr)
                val = -val
                if val > best_val:
                    best_val = val
                    best_move = (frm, to)
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
                if time.time() - start_time > time_limit:
                    break
            return best_val, best_move
        else:
            moves = get_moves(my_p, opp_p, my_d)
            if not moves:
                return 100000, None
            opp_s = set(opp_p)
            moves = order_moves(moves, my_gr, opp_s)
            best_val = -999999
            best_move = moves[0]
            for frm, to in moves:
                new_my = [p for p in my_p if p != frm] + [to]
                new_opp = [p for p in opp_p if p != to]
                if to[0] == my_gr:
                    return -100000, (frm, to)
                val, _ = minimax(new_opp, new_my, depth - 1, -beta, -alpha, True, opp_d, opp_gr, my_d, my_gr)
                val = -val
                if val > best_val:
                    best_val = val
                    best_move = (frm, to)
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
                if time.time() - start_time > time_limit:
                    break
            return best_val, best_move
    
    # Check for immediate winning moves
    all_moves = get_moves(list(me), list(opp), direction)
    if not all_moves:
        return (me[0], (me[0][0] + direction, me[0][1]))  # fallback
    
    for frm, to in all_moves:
        if to[0] == goal_row:
            return (frm, to)
    
    opp_dir = -direction
    best_move = all_moves[0]
    
    # Iterative deepening with negamax
    for depth in range(1, 20):
        if time.time() - start_time > time_limit * 0.7:
            break
        val, move = minimax(list(me), list(opp), depth, -999999, 999999, True, direction, goal_row, opp_dir, opp_goal)
        if move:
            best_move = move
        if abs(val) >= 90000:
            break
    
    return best_move
