
import time

def policy(my_men, my_kings, opp_men, opp_kings, color):
    my_men = set(map(tuple, my_men))
    my_kings = set(map(tuple, my_kings))
    opp_men = set(map(tuple, opp_men))
    opp_kings = set(map(tuple, opp_kings))
    
    start_time = time.time()
    
    # State: (my_men, my_kings, opp_men, opp_kings, is_my_turn, color)
    # We always think from "my" perspective
    
    def get_moves(men, kings, o_men, o_kings, clr):
        """Get all legal moves for the player with color clr whose pieces are men/kings."""
        captures = []
        simple = []
        forward_dirs = [(-1, -1), (-1, 1)] if clr == 'b' else [(1, -1), (1, 1)]
        all_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        occupied_mine = men | kings
        occupied_opp = o_men | o_kings
        occupied = occupied_mine | occupied_opp
        
        def in_bounds(r, c):
            return 0 <= r <= 7 and 0 <= c <= 7
        
        # Find captures (multi-jump)
        def find_captures(r, c, dirs, is_king, visited_caps, men_s, kings_s, o_men_s, o_kings_s):
            """Find all capture sequences from (r,c). Returns list of (final_pos, list_of_jumped_pieces)"""
            results = []
            any_cap = False
            for dr, dc in dirs:
                mr, mc = r + dr, c + dc
                lr, lc = r + 2*dr, c + 2*dc
                if in_bounds(lr, lc) and (mr, mc) in (o_men_s | o_kings_s) and (mr, mc) not in visited_caps and (lr, lc) not in (men_s | kings_s | (o_men_s - visited_caps) | {(r,c)}):
                    # Check landing is empty (not occupied by anything except possibly removed pieces)
                    if (lr, lc) not in occupied or (lr, lc) == (r, c) or all(
                        (lr, lc) not in s for s in [men_s, kings_s, o_men_s - visited_caps - {(mr,mc)}, o_kings_s - visited_caps - {(mr,mc)}]
                    ):
                        # Simpler: landing must be empty
                        all_occ = men_s | kings_s | (o_men_s - visited_caps - {(mr,mc)}) | (o_kings_s - visited_caps - {(mr,mc)})
                        all_occ.discard((r,c))
                        if (lr, lc) not in all_occ:
                            new_visited = visited_caps | {(mr, mc)}
                            # Check promotion
                            promoted = False
                            new_dirs = dirs
                            if not is_king:
                                promo_row = 0 if clr == 'b' else 7
                                if lr == promo_row:
                                    promoted = True
                                    new_dirs = all_dirs  # but in standard checkers, turn ends on promotion during jump
                            
                            if promoted:
                                # Turn ends on promotion
                                results.append(((lr, lc), new_visited))
                                any_cap = True
                            else:
                                sub = find_captures(lr, lc, new_dirs, is_king, new_visited, men_s, kings_s, o_men_s, o_kings_s)
                                if sub:
                                    results.extend(sub)
                                    any_cap = True
                                else:
                                    results.append(((lr, lc), new_visited))
                                    any_cap = True
            return results
        
        for r, c in men:
            caps = find_captures(r, c, forward_dirs, False, set(), men, kings, o_men, o_kings)
            for (dest, jumped) in caps:
                captures.append(((r, c), dest, jumped))
        
        for r, c in kings:
            caps = find_captures(r, c, all_dirs, True, set(), men, kings, o_men, o_kings)
            for (dest, jumped) in caps:
                captures.append(((r, c), dest, jumped))
        
        if captures:
            # Pick longest captures (most jumped)
            max_len = max(len(j) for _, _, j in captures)
            captures = [(f, t, j) for f, t, j in captures if len(j) == max_len]
            return captures, True
        
        # Simple moves
        for r, c in men:
            for dr, dc in forward_dirs:
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and (nr, nc) not in occupied:
                    simple.append(((r, c), (nr, nc), set()))
        
        for r, c in kings:
            for dr, dc in all_dirs:
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and (nr, nc) not in occupied:
                    simple.append(((r, c), (nr, nc), set()))
        
        return simple, False
    
    def apply_move(men, kings, o_men, o_kings, clr, move):
        frm, to, jumped = move
        men = set(men)
        kings = set(kings)
        o_men = set(o_men)
        o_kings = set(o_kings)
        
        is_king = frm in kings
        if is_king:
            kings.discard(frm)
            kings.add(to)
        else:
            men.discard(frm)
            promo_row = 0 if clr == 'b' else 7
            if to[0] == promo_row:
                kings.add(to)
            else:
                men.add(to)
        
        o_men -= jumped
        o_kings -= jumped
        
        return frozenset(men), frozenset(kings), frozenset(o_men), frozenset(o_kings)
    
    def evaluate(men, kings, o_men, o_kings, clr):
        """Evaluate from perspective of the player with clr."""
        my_val = len(men) * 100 + len(kings) * 170
        opp_val = len(o_men) * 100 + len(o_kings) * 170
        
        score = my_val - opp_val
        
        # Positional bonuses
        for r, c in men:
            # Advancement
            if clr == 'b':
                score += (7 - r) * 3  # closer to row 0
            else:
                score += r * 3
            # Center control
            if 2 <= c <= 5 and 2 <= r <= 5:
                score += 5
            # Back row defense
            if clr == 'b' and r == 7:
                score += 4
            elif clr == 'w' and r == 0:
                score += 4
        
        for r, c in kings:
            if 2 <= c <= 5 and 2 <= r <= 5:
                score += 8
        
        for r, c in o_men:
            if clr == 'b':
                score -= r * 3
            else:
                score -= (7 - r) * 3
            if 2 <= c <= 5 and 2 <= r <= 5:
                score -= 5
        
        for r, c in o_kings:
            if 2 <= c <= 5 and 2 <= r <= 5:
                score -= 8
        
        return score
    
    opp_color = 'w' if color == 'b' else 'b'
    
    def minimax(men, kings, o_men, o_kings, clr, depth, alpha, beta, maximizing):
        if time.time() - start_time > 0.7:
            return evaluate(my_men_g, my_kings_g, opp_men_g, opp_kings_g, color) if maximizing else -evaluate(my_men_g, my_kings_g, opp_men_g, opp_kings_g, color)
        
        moves, is_cap = get_moves(set(men), set(kings), set(o_men), set(o_kings), clr)
        
        if not moves:
            return -9999 if maximizing else 9999
        
        if depth == 0:
            if maximizing:
                return evaluate(men, kings, o_men, o_kings, clr)
            else:
                return evaluate(o_men, o_kings, men, kings, color)
        
        next_clr = opp_color if clr == color else color
        
        if maximizing:
            val = -99999
            for move in moves:
                nm, nk, no_m, no_k = apply_move(men, kings, o_men, o_kings, clr, move)
                v = minimax(no_m, no_k, nm, nk, next_clr, depth - 1, alpha, beta, False)
                val = max(val, v)
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return val
        else:
            val = 99999
            for move in moves:
                nm, nk, no_m, no_k = apply_move(men, kings, o_men, o_kings, clr, move)
                v = minimax(no_m, no_k, nm, nk, next_clr, depth - 1, alpha, beta, True)
                val = min(val, v)
                beta = min(beta, val)
                if alpha >= beta:
                    break
            return val
    
    my_men_g = frozenset(my_men)
    my_kings_g = frozenset(my_kings)
    opp_men_g = frozenset(opp_men)
    opp_kings_g = frozenset(opp_kings)
    
    moves, is_cap = get_moves(my_men, my_kings, opp_men, opp_kings, color)
    
    if not moves:
        # Should not happen if we have legal moves, return something
        return ((0,0),(0,0))
    
    if len(moves) == 1:
        m = moves[0]
        return (m[0], m[1])
    
    best_move = moves[0]
    best_val = -999999
    
    for depth in range(1, 20):
        if time.time() - start_time > 0.6:
            break
        current_best = moves[0]
        current_val = -999999
        for move in moves:
            if time.time() - start_time > 0.65:
                break
            nm, nk, no_m, no_k = apply_move(my_men, my_kings, opp_men, opp_kings, color, move)
            v = minimax(no_m, no_k, nm, nk, opp_color, depth - 1, -999999, 999999, False)
            if v > current_val:
                current_val = v
                current_best = move
        if time.time() - start_time <= 0.7:
            best_move = current_best
            best_val = current_val
    
    return (best_move[0], best_move[1])
