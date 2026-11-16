
import time

def policy(my_men, my_kings, opp_men, opp_kings, color):
    start_time = time.time()
    
    my_men_set = frozenset(my_men)
    my_kings_set = frozenset(my_kings)
    opp_men_set = frozenset(opp_men)
    opp_kings_set = frozenset(opp_kings)
    
    state = (my_men_set, my_kings_set, opp_men_set, opp_kings_set)
    
    # Direction: black moves down (decreasing row), white moves up (increasing row)
    my_dir = -1 if color == 'b' else 1
    opp_dir = -my_dir
    my_promote = 0 if color == 'b' else 7
    opp_promote = 7 if color == 'b' else 0
    
    def get_captures(mm, mk, om, ok, is_my_turn):
        """Get all capture moves. Returns list of (from_sq, to_sq, new_state) for the top-level move."""
        pieces_men = mm if is_my_turn else om
        pieces_kings = mk if is_my_turn else ok
        opp_m = om if is_my_turn else mm
        opp_k = ok if is_my_turn else mk
        direction = my_dir if is_my_turn else opp_dir
        promote_row = my_promote if is_my_turn else opp_promote
        all_occupied = mm | mk | om | ok
        
        moves = []
        
        def explore_captures_man(pos, cur_mm, cur_mk, cur_om, cur_ok, path, became_king):
            r, c = pos
            found = False
            if became_king:
                dirs = [(-1,-1),(-1,1),(1,-1),(1,1)]
            else:
                dirs = [(direction,-1),(direction,1)]
            
            cur_occupied = cur_mm | cur_mk | cur_om | cur_ok
            enemy = cur_om | cur_ok if is_my_turn else cur_mm | cur_mk
            
            for dr, dc in dirs:
                mr, mc = r+dr, c+dc
                lr, lc = r+2*dr, c+2*dc
                if 0 <= lr <= 7 and 0 <= lc <= 7:
                    mid = (mr, mc)
                    land = (lr, lc)
                    if mid in enemy and land not in cur_occupied:
                        found = True
                        new_om = cur_om - {mid} if is_my_turn else cur_om
                        new_ok = cur_ok - {mid} if is_my_turn else cur_ok
                        new_mm = cur_mm if is_my_turn else cur_mm - {mid}
                        new_mk = cur_mk if is_my_turn else cur_mk - {mid}
                        
                        new_became_king = became_king
                        if lr == promote_row and not became_king:
                            new_became_king = True
                            # promote and stop
                            if is_my_turn:
                                new_mk2 = new_mk | {land}
                            else:
                                new_ok2 = new_ok | {land}
                                new_mk2 = new_mk
                            if is_my_turn:
                                moves.append((path[0], land, (new_mm, new_mk2, new_om, new_ok)))
                            else:
                                moves.append((path[0], land, (new_mm, new_mk, new_om, new_ok2)))
                            continue
                        
                        explore_captures_man(land, new_mm, new_mk, new_om, new_ok, path + [land], new_became_king)
            
            if not found and len(path) > 1:
                # finalize
                if is_my_turn:
                    final_mm = cur_mm
                    final_mk = cur_mk
                else:
                    final_mm = cur_mm
                    final_mk = cur_mk
                moves.append((path[0], pos, (cur_mm, cur_mk, cur_om, cur_ok)))
        
        def explore_captures_king(pos, cur_mm, cur_mk, cur_om, cur_ok, path):
            r, c = pos
            found = False
            dirs = [(-1,-1),(-1,1),(1,-1),(1,1)]
            cur_occupied = cur_mm | cur_mk | cur_om | cur_ok
            enemy = cur_om | cur_ok if is_my_turn else cur_mm | cur_mk
            
            for dr, dc in dirs:
                mr, mc = r+dr, c+dc
                lr, lc = r+2*dr, c+2*dc
                if 0 <= lr <= 7 and 0 <= lc <= 7:
                    mid = (mr, mc)
                    land = (lr, lc)
                    if mid in enemy and land not in cur_occupied:
                        found = True
                        new_om = cur_om - {mid} if is_my_turn else cur_om
                        new_ok = cur_ok - {mid} if is_my_turn else cur_ok
                        new_mm = cur_mm if is_my_turn else cur_mm - {mid}
                        new_mk = cur_mk if is_my_turn else cur_mk - {mid}
                        
                        explore_captures_king(land, new_mm, new_mk, new_om, new_ok, path + [land])
            
            if not found and len(path) > 1:
                moves.append((path[0], pos, (cur_mm, cur_mk, cur_om, cur_ok)))
        
        # For each man
        for p in pieces_men:
            # temporarily remove piece from board
            if is_my_turn:
                tmp_mm = mm - {p}
                explore_captures_man(p, tmp_mm, mk, om, ok, [p], False)
            else:
                tmp_om = om - {p}
                explore_captures_man(p, mm, mk, tmp_om, ok, [p], False)
        
        # For each king
        for p in pieces_kings:
            if is_my_turn:
                tmp_mk = mk - {p}
                explore_captures_king(p, mm, tmp_mk, om, ok, [p])
            else:
                tmp_ok = ok - {p}
                explore_captures_king(p, mm, mk, om, tmp_ok, [p])
        
        # Rebuild states properly: place the piece at destination
        result = []
        for (frm, to, (s_mm, s_mk, s_om, s_ok)) in moves:
            if is_my_turn:
                if frm in pieces_kings:
                    final_mk = s_mk | {to}
                    result.append((frm, to, (s_mm, final_mk, s_om, s_ok)))
                else:
                    if to[0] == promote_row:
                        final_mk = s_mk | {to}
                        result.append((frm, to, (s_mm, final_mk, s_om, s_ok)))
                    else:
                        final_mm = s_mm | {to}
                        result.append((frm, to, (final_mm, s_mk, s_om, s_ok)))
            else:
                if frm in pieces_kings:
                    final_ok = s_ok | {to}
                    result.append((frm, to, (s_mm, s_mk, s_om, final_ok)))
                else:
                    if to[0] == opp_promote:
                        final_ok = s_ok | {to}
                        result.append((frm, to, (s_mm, s_mk, s_om, final_ok)))
                    else:
                        final_om = s_om | {to}
                        result.append((frm, to, (s_mm, s_mk, final_om, s_ok)))
        
        return result
    
    def get_simple_moves(mm, mk, om, ok, is_my_turn):
        pieces_men = mm if is_my_turn else om
        pieces_kings = mk if is_my_turn else ok
        direction = my_dir if is_my_turn else opp_dir
        promote_row = my_promote if is_my_turn else opp_promote
        all_occupied = mm | mk | om | ok
        
        moves = []
        for p in pieces_men:
            r, c = p
            for dc in [-1, 1]:
                nr, nc = r + direction, c + dc
                if 0 <= nr <= 7 and 0 <= nc <= 7 and (nr, nc) not in all_occupied:
                    if is_my_turn:
                        new_mm = mm - {p}
                        if nr == promote_row:
                            new_mk = mk | {(nr, nc)}
                            moves.append((p, (nr, nc), (new_mm, new_mk, om, ok)))
                        else:
                            new_mm = new_mm | {(nr, nc)}
                            moves.append((p, (nr, nc), (new_mm, mk, om, ok)))
                    else:
                        new_om = om - {p}
                        if nr == opp_promote:
                            new_ok = ok | {(nr, nc)}
                            moves.append((p, (nr, nc), (mm, mk, new_om, new_ok)))
                        else:
                            new_om = new_om | {(nr, nc)}
                            moves.append((p, (nr, nc), (mm, mk, new_om, ok)))
        
        for p in pieces_kings:
            r, c = p
            for dr in [-1, 1]:
                for dc in [-1, 1]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr <= 7 and 0 <= nc <= 7 and (nr, nc) not in all_occupied:
                        if is_my_turn:
                            new_mk = (mk - {p}) | {(nr, nc)}
                            moves.append((p, (nr, nc), (mm, new_mk, om, ok)))
                        else:
                            new_ok = (ok - {p}) | {(nr, nc)}
                            moves.append((p, (nr, nc), (mm, mk, om, new_ok)))
        
        return moves
    
    def get_all_moves(mm, mk, om, ok, is_my_turn):
        caps = get_captures(mm, mk, om, ok, is_my_turn)
        if caps:
            return caps
        return get_simple_moves(mm, mk, om, ok, is_my_turn)
    
    def evaluate(mm, mk, om, ok):
        my_men_count = len(mm)
        my_kings_count = len(mk)
        opp_men_count = len(om)
        opp_kings_count = len(ok)
        
        my_total = my_men_count + my_kings_count
        opp_total = opp_men_count + opp_kings_count
        
        if my_total == 0:
            return -1000
        if opp_total == 0:
            return 1000
        
        # Material
        score = (my_men_count - opp_men_count) * 100 + (my_kings_count - opp_kings_count) * 150
        
        # Positional: advancement
        for r, c in mm:
            if my_dir == 1:  # white moves up
                score += r * 5
            else:  # black moves down
                score += (7 - r) * 5
            # center control
            if 2 <= c <= 5 and 2 <= r <= 5:
                score += 3
        
        for r, c in om:
            if opp_dir == 1:
                score -= r * 5
            else:
                score -= (7 - r) * 5
            if 2 <= c <= 5 and 2 <= r <= 5:
                score -= 3
        
        # King center bonus
        for r, c in mk:
            if 2 <= c <= 5 and 2 <= r <= 5:
                score += 5
        for r, c in ok:
            if 2 <= c <= 5 and 2 <= r <= 5:
                score -= 5
        
        # Back row defense
        back_row = 7 if color == 'b' else 0
        for r, c in mm:
            if r == back_row:
                score += 4
        
        return score
    
    def alphabeta(mm, mk, om, ok, depth, alpha, beta, is_my_turn):
        if depth == 0:
            return evaluate(mm, mk, om, ok), None
        
        moves = get_all_moves(mm, mk, om, ok, is_my_turn)
        if not moves:
            if is_my_turn:
                return -1000, None
            else:
                return 1000, None
        
        best_move = None
        if is_my_turn:
            max_val = -10000
            for frm, to, (nmm, nmk, nom, nok) in moves:
                if time.time() - start_time > 0.85:
                    if best_move is None:
                        best_move = (frm, to)
                    break
                val, _ = alphabeta(nmm, nmk, nom, nok, depth - 1, alpha, beta, False)
                if val > max_val:
                    max_val = val
                    best_move = (frm, to)
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return max_val, best_move
        else:
            min_val = 10000
            for frm, to, (nmm, nmk, nom, nok) in moves:
                if time.time() - start_time > 0.85:
                    break
                val, _ = alphabeta(nmm, nmk, nom, nok, depth - 1, alpha, beta, True)
                if val < min_val:
                    min_val = val
                    best_move = (frm, to)
                beta = min(beta, val)
                if alpha >= beta:
                    break
            return min_val, best_move
    
    # Iterative deepening
    best_move = None
    moves = get_all_moves(my_men_set, my_kings_set, opp_men_set, opp_kings_set, True)
    if not moves:
        # shouldn't happen but fallback
        return ((0,0),(0,0))
    if len(moves) == 1:
        return (moves[0][0], moves[0][1])
    
    best_move = (moves[0][0], moves[0][1])
    
    for depth in range(1, 20):
        if time.time() - start_time > 0.7:
            break
        val, move = alphabeta(my_men_set, my_kings_set, opp_men_set, opp_kings_set, depth, -10000, 10000, True)
        if move is not None:
            best_move = move
        if abs(val) >= 999:
            break
    
    return best_move
