
def policy(my_men, my_kings, opp_men, opp_kings, color):
    import time
    
    start_time = time.time()
    TIME_LIMIT = 0.85
    
    my_men_set = set(map(tuple, my_men))
    my_kings_set = set(map(tuple, my_kings))
    opp_men_set = set(map(tuple, opp_men))
    opp_kings_set = set(map(tuple, opp_kings))
    
    # State: (my_men_fs, my_kings_fs, opp_men_fs, opp_kings_fs)
    def make_state(mm, mk, om, ok):
        return (frozenset(mm), frozenset(mk), frozenset(om), frozenset(ok))
    
    def get_jumps(pos, is_king, color, my_m, my_k, opp_m, opp_k):
        """Get all multi-jump sequences from pos."""
        r, c = pos
        all_pieces = my_m | my_k | opp_m | opp_k
        opp_pieces = opp_m | opp_k
        
        if is_king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            if color == 'w':
                directions = [(1, -1), (1, 1)]
            else:
                directions = [(-1, -1), (-1, 1)]
        
        sequences = []
        
        def dfs(cr, cc, captured, cur_is_king, cur_opp_m, cur_opp_k):
            if cur_is_king:
                dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            else:
                if color == 'w':
                    dirs = [(1, -1), (1, 1)]
                else:
                    dirs = [(-1, -1), (-1, 1)]
            
            found = False
            cur_all = my_m | my_k | cur_opp_m | cur_opp_k
            # Remove original position from blocking
            cur_all_adj = (cur_all - {pos}) | {(cr, cc)} if (cr, cc) != pos else cur_all
            # Actually let's be more careful
            cur_all_adj = set()
            for p in my_m:
                if p != pos:
                    cur_all_adj.add(p)
            for p in my_k:
                if p != pos:
                    cur_all_adj.add(p)
            for p in cur_opp_m:
                cur_all_adj.add(p)
            for p in cur_opp_k:
                cur_all_adj.add(p)
            cur_all_adj.add((cr, cc))  # current position blocks
            cur_opp = cur_opp_m | cur_opp_k
            
            for dr, dc in dirs:
                mr, mc = cr + dr, cc + dc
                lr, lc = cr + 2*dr, cc + 2*dc
                if 0 <= lr <= 7 and 0 <= lc <= 7:
                    mid = (mr, mc)
                    land = (lr, lc)
                    if mid in cur_opp and mid not in captured and land not in cur_all_adj:
                        found = True
                        new_captured = captured | {mid}
                        new_opp_m = cur_opp_m - {mid}
                        new_opp_k = cur_opp_k - {mid}
                        # Check promotion
                        new_is_king = cur_is_king
                        if not cur_is_king:
                            if (color == 'w' and lr == 7) or (color == 'b' and lr == 0):
                                new_is_king = True
                                # In standard checkers, promotion ends the turn
                                sequences.append(((pos), (lr, lc), new_captured, new_is_king))
                                continue
                        dfs(lr, lc, new_captured, new_is_king, new_opp_m, new_opp_k)
            
            if not found:
                if captured:
                    sequences.append((pos, (cr, cc), captured, cur_is_king))
        
        dfs(r, c, frozenset(), is_king, opp_m, opp_k)
        return sequences
    
    def get_simple_moves(pos, is_king, clr, all_pieces):
        r, c = pos
        moves = []
        if is_king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            if clr == 'w':
                directions = [(1, -1), (1, 1)]
            else:
                directions = [(-1, -1), (-1, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr <= 7 and 0 <= nc <= 7 and (nr, nc) not in all_pieces:
                moves.append((pos, (nr, nc)))
        return moves
    
    def get_all_moves(mm, mk, om, ok, clr):
        """Returns list of (from, to, new_mm, new_mk, new_om, new_ok)"""
        all_jumps = []
        for p in mm:
            seqs = get_jumps(p, False, clr, mm, mk, om, ok)
            for seq in seqs:
                frm, to, captured, became_king = seq
                new_mm = mm - {frm}
                new_mk = mk.copy()
                new_om = om - captured
                new_ok = ok - captured
                if became_king:
                    new_mk = new_mk | {to}
                else:
                    new_mm = new_mm | {to}
                all_jumps.append((frm, to, new_mm, new_mk, new_om, new_ok))
        for p in mk:
            seqs = get_jumps(p, True, clr, mm, mk, om, ok)
            for seq in seqs:
                frm, to, captured, became_king = seq
                new_mk = mk - {frm} | {to}
                new_om = om - captured
                new_ok = ok - captured
                all_jumps.append((frm, to, mm, new_mk, new_om, new_ok))
        
        if all_jumps:
            return all_jumps
        
        all_pieces = mm | mk | om | ok
        simple = []
        for p in mm:
            for frm, to in get_simple_moves(p, False, clr, all_pieces):
                new_mm = mm - {frm}
                new_mk = mk.copy()
                if (clr == 'w' and to[0] == 7) or (clr == 'b' and to[0] == 0):
                    new_mk = new_mk | {to}
                else:
                    new_mm = new_mm | {to}
                simple.append((frm, to, new_mm, new_mk, om, ok))
        for p in mk:
            for frm, to in get_simple_moves(p, True, clr, all_pieces):
                new_mk = mk - {frm} | {to}
                simple.append((frm, to, mm, new_mk, om, ok))
        return simple
    
    opp_color = 'b' if color == 'w' else 'w'
    
    def evaluate(mm, mk, om, ok):
        my_count = len(mm) * 100 + len(mk) * 160
        opp_count = len(om) * 100 + len(ok) * 160
        
        score = my_count - opp_count
        
        for r, c in mm:
            # Advancement
            if color == 'w':
                score += r * 3
            else:
                score += (7 - r) * 3
            # Center control
            if 2 <= c <= 5 and 2 <= r <= 5:
                score += 3
            # Back row
            if color == 'w' and r == 0:
                score += 4
            elif color == 'b' and r == 7:
                score += 4
        
        for r, c in mk:
            if 2 <= c <= 5 and 2 <= r <= 5:
                score += 5
        
        for r, c in om:
            if opp_color == 'w':
                score -= r * 3
            else:
                score -= (7 - r) * 3
            if 2 <= c <= 5 and 2 <= r <= 5:
                score -= 3
        
        for r, c in ok:
            if 2 <= c <= 5 and 2 <= r <= 5:
                score -= 5
        
        return score
    
    def minimax(mm, mk, om, ok, clr, depth, alpha, beta, maximizing):
        if time.time() - start_time > TIME_LIMIT:
            return evaluate(mm, mk, om, ok) if maximizing else evaluate(mm, mk, om, ok)
        
        if depth == 0:
            return evaluate(mm, mk, om, ok)
        
        if maximizing:
            moves = get_all_moves(mm, mk, om, ok, clr)
            if not moves:
                return -10000 - depth
            best = -999999
            for frm, to, nmm, nmk, nom, nok in moves:
                opp_c = 'b' if clr == 'w' else 'w'
                val = minimax(nom, nok, nmm, nmk, opp_c, depth - 1, alpha, beta, False)
                if val > best:
                    best = val
                alpha = max(alpha, best)
                if alpha >= beta:
                    break
            return best
        else:
            # Opponent moves: from their perspective, their pieces are om/ok and ours are mm/mk
            moves = get_all_moves(mm, mk, om, ok, clr)
            if not moves:
                return 10000 + depth
            best = 999999
            for frm, to, nmm, nmk, nom, nok in moves:
                opp_c = 'b' if clr == 'w' else 'w'
                val = minimax(nom, nok, nmm, nmk, opp_c, depth - 1, alpha, beta, True)
                if val < best:
                    best = val
                beta = min(beta, best)
                if alpha >= beta:
                    break
            return best
    
    # Get legal moves
    moves = get_all_moves(my_men_set, my_kings_set, opp_men_set, opp_kings_set, color)
    
    if not moves:
        # Should not happen if we have legal moves, but fallback
        return ((0,0),(0,0))
    
    if len(moves) == 1:
        return (moves[0][0], moves[0][1])
    
    best_move = None
    best_val = -999999
    
    # Iterative deepening
    max_depth = 6
    total_pieces = len(my_men_set) + len(my_kings_set) + len(opp_men_set) + len(opp_kings_set)
    if total_pieces <= 8:
        max_depth = 8
    elif total_pieces <= 12:
        max_depth = 7
    
    for depth in range(1, max_depth + 1):
        if time.time() - start_time > TIME_LIMIT * 0.7:
            break
        current_best = None
        current_val = -999999
        for frm, to, nmm, nmk, nom, nok in moves:
            if time.time() - start_time > TIME_LIMIT * 0.85:
                break
            val = minimax(nom, nok, nmm, nmk, opp_color, depth - 1, -999999, 999999, False)
            if val > current_val:
                current_val = val
                current_best = (frm, to)
        if current_best is not None:
            best_move = current_best
            best_val = current_val
    
    if best_move is None:
        best_move = (moves[0][0], moves[0][1])
    
    return best_move
