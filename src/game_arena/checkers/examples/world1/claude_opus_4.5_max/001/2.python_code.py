
def policy(my_men, my_kings, opp_men, opp_kings, color):
    import time
    
    start_time = time.time()
    time_limit = 0.8
    
    am_white = (color == 'w')
    
    if am_white:
        w_men, w_kings = frozenset(my_men), frozenset(my_kings)
        b_men, b_kings = frozenset(opp_men), frozenset(opp_kings)
    else:
        b_men, b_kings = frozenset(my_men), frozenset(my_kings)
        w_men, w_kings = frozenset(opp_men), frozenset(opp_kings)
    
    def in_bounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8
    
    def get_moves(w_men, w_kings, b_men, b_kings, white_turn):
        if white_turn:
            my_m, my_k = w_men, w_kings
            opp_pieces = b_men | b_kings
            forward = 1
        else:
            my_m, my_k = b_men, b_kings
            opp_pieces = w_men | w_kings
            forward = -1
        
        all_pieces = w_men | w_kings | b_men | b_kings
        captures = []
        
        for r, c in my_m:
            for dc in [-1, 1]:
                mr, mc = r + forward, c + dc
                er, ec = r + 2*forward, c + 2*dc
                if in_bounds(er, ec) and (mr, mc) in opp_pieces and (er, ec) not in all_pieces:
                    captures.append(((r, c), (er, ec)))
        
        for r, c in my_k:
            for dr in [-1, 1]:
                for dc in [-1, 1]:
                    mr, mc = r + dr, c + dc
                    er, ec = r + 2*dr, c + 2*dc
                    if in_bounds(er, ec) and (mr, mc) in opp_pieces and (er, ec) not in all_pieces:
                        captures.append(((r, c), (er, ec)))
        
        if captures:
            opp_k = b_kings if white_turn else w_kings
            captures.sort(key=lambda m: 10 if ((m[0][0]+m[1][0])//2, (m[0][1]+m[1][1])//2) in opp_k else 5, reverse=True)
            return captures, True
        
        moves = []
        for r, c in my_m:
            for dc in [-1, 1]:
                nr, nc = r + forward, c + dc
                if in_bounds(nr, nc) and (nr, nc) not in all_pieces:
                    moves.append(((r, c), (nr, nc)))
        
        for r, c in my_k:
            for dr in [-1, 1]:
                for dc in [-1, 1]:
                    nr, nc = r + dr, c + dc
                    if in_bounds(nr, nc) and (nr, nc) not in all_pieces:
                        moves.append(((r, c), (nr, nc)))
        
        return moves, False
    
    def apply_move(w_men, w_kings, b_men, b_kings, move, white_turn, is_capture):
        w_men_s, w_kings_s = set(w_men), set(w_kings)
        b_men_s, b_kings_s = set(b_men), set(b_kings)
        (fr, fc), (tr, tc) = move
        
        if white_turn:
            if (fr, fc) in w_kings_s:
                w_kings_s.discard((fr, fc)); w_kings_s.add((tr, tc))
            else:
                w_men_s.discard((fr, fc))
                (w_kings_s if tr == 7 else w_men_s).add((tr, tc))
            if is_capture:
                mr, mc = (fr + tr) // 2, (fc + tc) // 2
                b_men_s.discard((mr, mc)); b_kings_s.discard((mr, mc))
        else:
            if (fr, fc) in b_kings_s:
                b_kings_s.discard((fr, fc)); b_kings_s.add((tr, tc))
            else:
                b_men_s.discard((fr, fc))
                (b_kings_s if tr == 0 else b_men_s).add((tr, tc))
            if is_capture:
                mr, mc = (fr + tr) // 2, (fc + tc) // 2
                w_men_s.discard((mr, mc)); w_kings_s.discard((mr, mc))
        
        return frozenset(w_men_s), frozenset(w_kings_s), frozenset(b_men_s), frozenset(b_kings_s)
    
    def evaluate(w_men, w_kings, b_men, b_kings, am_white_player):
        w_score = len(w_men) * 100 + len(w_kings) * 150
        b_score = len(b_men) * 100 + len(b_kings) * 150
        
        for r, c in w_men:
            w_score += r * 5 + (8 if r == 0 else 0) + (2 if 2 <= c <= 5 else 0)
        for r, c in b_men:
            b_score += (7-r) * 5 + (8 if r == 7 else 0) + (2 if 2 <= c <= 5 else 0)
        for r, c in w_kings:
            if 2 <= r <= 5 and 2 <= c <= 5: w_score += 3
        for r, c in b_kings:
            if 2 <= r <= 5 and 2 <= c <= 5: b_score += 3
        
        return (w_score - b_score) if am_white_player else (b_score - w_score)
    
    timeout = [False]
    
    def minimax(w_men, w_kings, b_men, b_kings, white_turn, depth, alpha, beta, am_white):
        if time.time() - start_time > time_limit:
            timeout[0] = True
            return 0, None
        
        moves, is_capture = get_moves(w_men, w_kings, b_men, b_kings, white_turn)
        
        if not moves:
            return (-10000 - depth if white_turn == am_white else 10000 + depth), None
        if depth == 0:
            return evaluate(w_men, w_kings, b_men, b_kings, am_white), None
        
        maximizing = (white_turn == am_white)
        best_move = moves[0]
        best_val = float('-inf') if maximizing else float('inf')
        
        for move in moves:
            if timeout[0]: break
            new_state = apply_move(w_men, w_kings, b_men, b_kings, move, white_turn, is_capture)
            val, _ = minimax(*new_state, not white_turn, depth - 1, alpha, beta, am_white)
            
            if maximizing:
                if val > best_val: best_val, best_move = val, move
                alpha = max(alpha, val)
            else:
                if val < best_val: best_val, best_move = val, move
                beta = min(beta, val)
            if beta <= alpha: break
        
        return best_val, best_move
    
    moves, _ = get_moves(w_men, w_kings, b_men, b_kings, am_white)
    if not moves:
        return ((0, 0), (0, 0))
    
    best_move = moves[0]
    
    for depth in range(1, 20):
        if time.time() - start_time > time_limit: break
        timeout[0] = False
        _, move = minimax(w_men, w_kings, b_men, b_kings, am_white, depth, float('-inf'), float('inf'), am_white)
        if not timeout[0] and move:
            best_move = move
    
    return best_move
