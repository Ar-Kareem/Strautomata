
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    me_set = set(me)
    opp_set = set(opp)
    direction = 1 if color == 'w' else -1
    goal_row = 7 if color == 'w' else 0
    opp_goal = 0 if color == 'w' else 7
    
    def get_moves(pieces, opponents, d):
        moves = []
        pieces_set = set(pieces)
        opp_set = set(opponents)
        for r, c in pieces:
            nr = r + d
            if 0 <= nr <= 7:
                # Forward move
                if (nr, c) not in pieces_set and (nr, c) not in opp_set:
                    moves.append(((r, c), (nr, c)))
                # Diagonal moves
                for dc in [-1, 1]:
                    nc = c + dc
                    if 0 <= nc <= 7:
                        if (nr, nc) not in pieces_set:
                            if (nr, nc) in opp_set or (nr, nc) not in opp_set:
                                if (nr, nc) not in pieces_set:
                                    moves.append(((r, c), (nr, nc)))
        return moves
    
    def evaluate(my_pieces, opp_pieces, my_dir, my_goal, opp_goal_row):
        if not opp_pieces:
            return 100000
        if not my_pieces:
            return -100000
        for r, c in my_pieces:
            if r == my_goal:
                return 100000
        for r, c in opp_pieces:
            if r == opp_goal_row:
                return -100000
        
        score = 0
        score += (len(my_pieces) - len(opp_pieces)) * 100
        
        for r, c in my_pieces:
            adv = r if my_dir == 1 else (7 - r)
            score += adv * adv * 3
            score += (3.5 - abs(c - 3.5)) * 2
        
        for r, c in opp_pieces:
            adv = (7 - r) if my_dir == 1 else r
            score -= adv * adv * 3
            score -= (3.5 - abs(c - 3.5)) * 2
        
        return score
    
    def order_moves(moves, pieces, opponents, d, goal):
        opp_s = set(opponents)
        scored = []
        for (fr, fc), (tr, tc) in moves:
            s = 0
            if (tr, tc) in opp_s:
                s += 1000
            if tr == goal:
                s += 10000
            adv = tr if d == 1 else (7 - tr)
            s += adv * 10
            scored.append((s, ((fr, fc), (tr, tc))))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [m for _, m in scored]
    
    def minimax(my_p, opp_p, my_d, my_g, opp_g, depth, alpha, beta, maximizing):
        if depth == 0:
            return evaluate(my_p, opp_p, my_d, my_g, opp_g), None
        
        if maximizing:
            moves = get_moves(my_p, opp_p, my_d)
            if not moves:
                return -50000, None
            moves = order_moves(moves, my_p, opp_p, my_d, my_g)
            best_val = -float('inf')
            best_move = moves[0]
            for (fr, fc), (tr, tc) in moves:
                new_my = [p for p in my_p if p != (fr, fc)] + [(tr, tc)]
                new_opp = [p for p in opp_p if p != (tr, tc)]
                if tr == my_g:
                    return 100000, ((fr, fc), (tr, tc))
                val, _ = minimax(new_opp, new_my, -my_d, opp_g, my_g, depth - 1, -beta, -alpha, False)
                val = -val
                if val > best_val:
                    best_val = val
                    best_move = ((fr, fc), (tr, tc))
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return best_val, best_move
        else:
            moves = get_moves(my_p, opp_p, my_d)
            if not moves:
                return 50000, None
            moves = order_moves(moves, my_p, opp_p, my_d, my_g)
            best_val = -float('inf')
            best_move = moves[0] if moves else None
            for (fr, fc), (tr, tc) in moves:
                new_my = [p for p in my_p if p != (fr, fc)] + [(tr, tc)]
                new_opp = [p for p in opp_p if p != (tr, tc)]
                if tr == my_g:
                    return -100000, ((fr, fc), (tr, tc))
                val, _ = minimax(new_opp, new_my, -my_d, opp_g, my_g, depth - 1, -beta, -alpha, True)
                val = -val
                if val > best_val:
                    best_val = val
                    best_move = ((fr, fc), (tr, tc))
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return best_val, best_move
    
    legal_moves = get_moves(list(me_set), list(opp_set), direction)
    if not legal_moves:
        return (me[0], me[0])
    
    # Check for immediate wins
    for (fr, fc), (tr, tc) in legal_moves:
        if tr == goal_row:
            return ((fr, fc), (tr, tc))
    
    _, best_move = minimax(list(me_set), list(opp_set), direction, goal_row, opp_goal, 4, -float('inf'), float('inf'), True)
    
    if best_move and best_move in legal_moves:
        return best_move
    
    return legal_moves[0]
