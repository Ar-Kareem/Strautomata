
import time

def policy(me, opp, color):
    me_set = set(me)
    opp_set = set(opp)
    direction = 1 if color == 'w' else -1
    home_row = 7 if color == 'w' else 0  # opponent's home row (our goal)
    
    def get_moves(my_set, their_set, d):
        moves = []
        for r, c in my_set:
            nr = r + d
            if 0 <= nr <= 7:
                # straight forward
                if (nr, c) not in my_set and (nr, c) not in their_set:
                    moves.append(((r, c), (nr, c)))
                # diagonal captures and moves
                for dc in [-1, 1]:
                    nc = c + dc
                    if 0 <= nc <= 7:
                        if (nr, nc) in their_set:
                            moves.append(((r, c), (nr, nc)))
                        elif (nr, nc) not in my_set:
                            moves.append(((r, c), (nr, nc)))
        return moves
    
    def evaluate(my_set, their_set):
        if not their_set:
            return 100000
        if not my_set:
            return -100000
        
        score = 0
        goal = home_row
        opp_goal = 0 if color == 'w' else 7
        
        # Material
        score += (len(my_set) - len(their_set)) * 100
        
        for r, c in my_set:
            # Advancement (exponential)
            if color == 'w':
                adv = r
            else:
                adv = 7 - r
            score += adv * adv * 5
            # Center control
            score += (3.5 - abs(c - 3.5)) * 3
            # Check if next move wins
            if r + direction == goal:
                score += 2000
        
        for r, c in their_set:
            if color == 'w':
                adv = 7 - r
            else:
                adv = r
            score -= adv * adv * 5
            score -= (3.5 - abs(c - 3.5)) * 3
            if r - direction == opp_goal:
                score -= 2000
        
        return score
    
    def order_moves(moves, my_set, their_set):
        scored = []
        for m in moves:
            s = 0
            (fr, fc), (tr, tc) = m
            if (tr, tc) in their_set:
                s += 1000
            if tr == home_row:
                s += 50000
            if color == 'w':
                s += tr * 10
            else:
                s += (7 - tr) * 10
            scored.append((s, m))
        scored.sort(reverse=True)
        return [m for _, m in scored]
    
    def minimax(my_set, their_set, depth, alpha, beta, maximizing, d, deadline):
        if time.time() > deadline:
            return evaluate(my_set, their_set), None
        
        if maximizing:
            moves = get_moves(my_set, their_set, d)
        else:
            moves = get_moves(their_set, my_set, -d)
        
        if not moves:
            return (-100000 if maximizing else 100000), None
        
        if depth == 0:
            return evaluate(my_set, their_set), None
        
        moves = order_moves(moves, my_set if maximizing else their_set, their_set if maximizing else my_set)
        
        best_move = moves[0]
        if maximizing:
            val = -200000
            for m in moves:
                (fr, fc), (tr, tc) = m
                new_my = my_set - {(fr, fc)} | {(tr, tc)}
                new_their = their_set - {(tr, tc)}
                goal = home_row
                if tr == goal or not new_their:
                    return 100000 + depth, m
                v, _ = minimax(new_my, new_their, depth-1, alpha, beta, False, d, deadline)
                if v > val:
                    val = v
                    best_move = m
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return val, best_move
        else:
            val = 200000
            opp_goal = 0 if color == 'w' else 7
            for m in moves:
                (fr, fc), (tr, tc) = m
                new_their = their_set - {(fr, fc)} | {(tr, tc)}
                new_my = my_set - {(tr, tc)}
                if tr == opp_goal or not new_my:
                    return -100000 - depth, m
                v, _ = minimax(new_my, new_their, depth-1, alpha, beta, True, d, deadline)
                if v < val:
                    val = v
                    best_move = m
                beta = min(beta, val)
                if alpha >= beta:
                    break
            return val, best_move
    
    deadline = time.time() + 0.85
    best_move = None
    
    # Iterative deepening
    for depth in range(1, 20):
        if time.time() > deadline - 0.05:
            break
        val, move = minimax(me_set, opp_set, depth, -200000, 200000, True, direction, deadline)
        if move is not None:
            best_move = move
        if abs(val) >= 90000:
            break
    
    if best_move is None:
        moves = get_moves(me_set, opp_set, direction)
        best_move = moves[0]
    
    return best_move
