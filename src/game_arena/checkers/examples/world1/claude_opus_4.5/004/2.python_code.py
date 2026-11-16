
def policy(my_men, my_kings, opp_men, opp_kings, color):
    my_men = set(my_men)
    my_kings = set(my_kings)
    opp_men = set(opp_men)
    opp_kings = set(opp_kings)
    
    direction = -1 if color == 'b' else 1
    promo_row = 0 if color == 'b' else 7
    
    def get_captures(men, kings, o_men, o_kings, is_my_turn):
        captures = []
        d = direction if is_my_turn else -direction
        pr = promo_row if is_my_turn else (7 - promo_row)
        all_opp = o_men | o_kings
        all_pieces = men | kings | o_men | o_kings
        
        for r, c in men:
            for dr, dc in [(d, -1), (d, 1)]:
                mr, mc = r + dr, c + dc
                lr, lc = r + 2*dr, c + 2*dc
                if (mr, mc) in all_opp and 0 <= lr < 8 and 0 <= lc < 8 and (lr, lc) not in all_pieces:
                    captures.append(((r, c), (lr, lc), (mr, mc), lr == pr))
        
        for r, c in kings:
            for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                mr, mc = r + dr, c + dc
                lr, lc = r + 2*dr, c + 2*dc
                if (mr, mc) in all_opp and 0 <= lr < 8 and 0 <= lc < 8 and (lr, lc) not in all_pieces:
                    captures.append(((r, c), (lr, lc), (mr, mc), False))
        return captures
    
    def get_all_capture_sequences(men, kings, o_men, o_kings, is_my_turn):
        seqs = []
        caps = get_captures(men, kings, o_men, o_kings, is_my_turn)
        if not caps:
            return []
        for frm, to, capt, promoted in caps:
            n_men = men - {frm}
            n_kings = kings - {frm}
            if frm in kings or promoted:
                n_kings = n_kings | {to}
            else:
                n_men = n_men | {to}
            n_o_men = o_men - {capt}
            n_o_kings = o_kings - {capt}
            
            further = get_all_capture_sequences(n_men, n_kings, n_o_men, n_o_kings, is_my_turn)
            if further:
                for seq in further:
                    if seq[0][0] == to:
                        seqs.append([(frm, to)] + seq)
            else:
                seqs.append([(frm, to)])
        return seqs
    
    def get_simple_moves(men, kings, o_men, o_kings, is_my_turn):
        moves = []
        d = direction if is_my_turn else -direction
        pr = promo_row if is_my_turn else (7 - promo_row)
        all_pieces = men | kings | o_men | o_kings
        
        for r, c in men:
            for dc in [-1, 1]:
                nr, nc = r + d, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in all_pieces:
                    moves.append(((r, c), (nr, nc)))
        for r, c in kings:
            for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in all_pieces:
                    moves.append(((r, c), (nr, nc)))
        return moves
    
    def get_moves(men, kings, o_men, o_kings, is_my_turn):
        cap_seqs = get_all_capture_sequences(men, kings, o_men, o_kings, is_my_turn)
        if cap_seqs:
            return [(seq[0][0], seq[-1][1], seq) for seq in cap_seqs]
        simple = get_simple_moves(men, kings, o_men, o_kings, is_my_turn)
        return [(frm, to, [(frm, to)]) for frm, to in simple]
    
    def apply_move(men, kings, o_men, o_kings, move_seq, is_my_turn):
        d = direction if is_my_turn else -direction
        pr = promo_row if is_my_turn else (7 - promo_row)
        n_men, n_kings = set(men), set(kings)
        n_o_men, n_o_kings = set(o_men), set(o_kings)
        
        for frm, to in move_seq:
            is_king = frm in n_kings
            if is_king:
                n_kings.discard(frm)
            else:
                n_men.discard(frm)
            
            dr = 1 if to[0] > frm[0] else -1
            dc = 1 if to[1] > frm[1] else -1
            steps = abs(to[0] - frm[0])
            if steps == 2:
                capt = (frm[0] + dr, frm[1] + dc)
                n_o_men.discard(capt)
                n_o_kings.discard(capt)
            
            if is_king or to[0] == pr:
                n_kings.add(to)
            else:
                n_men.add(to)
        return n_men, n_kings, n_o_men, n_o_kings
    
    def evaluate(men, kings, o_men, o_kings):
        if not men and not kings:
            return -10000
        if not o_men and not o_kings:
            return 10000
        
        score = 0
        score += len(men) * 100 + len(kings) * 180
        score -= len(o_men) * 100 + len(o_kings) * 180
        
        for r, c in men:
            adv = (7 - r) if color == 'b' else r
            score += adv * 5
            if 2 <= c <= 5:
                score += 3
        for r, c in o_men:
            adv = r if color == 'b' else (7 - r)
            score -= adv * 5
            if 2 <= c <= 5:
                score -= 3
        return score
    
    def minimax(men, kings, o_men, o_kings, depth, alpha, beta, maximizing):
        if depth == 0:
            return evaluate(men, kings, o_men, o_kings), None
        
        moves = get_moves(men, kings, o_men, o_kings, maximizing)
        if not moves:
            return (-10000 if maximizing else 10000), None
        
        best_move = moves[0]
        if maximizing:
            max_eval = -float('inf')
            for frm, to, seq in moves:
                nm, nk, nom, nok = apply_move(men, kings, o_men, o_kings, seq, True)
                ev, _ = minimax(nm, nk, nom, nok, depth-1, alpha, beta, False)
                if ev > max_eval:
                    max_eval = ev
                    best_move = (frm, to, seq)
                alpha = max(alpha, ev)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for frm, to, seq in moves:
                nm, nk, nom, nok = apply_move(o_men, o_kings, men, kings, seq, True)
                ev, _ = minimax(men, kings, nm, nk, depth-1, alpha, beta, True)
                if ev < min_eval:
                    min_eval = ev
                    best_move = (frm, to, seq)
                beta = min(beta, ev)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    moves = get_moves(my_men, my_kings, opp_men, opp_kings, True)
    if not moves:
        return ((0, 0), (0, 0))
    if len(moves) == 1:
        return (moves[0][0], moves[0][1])
    
    _, best = minimax(my_men, my_kings, opp_men, opp_kings, 5, -float('inf'), float('inf'), True)
    if best:
        return (best[0], best[1])
    return (moves[0][0], moves[0][1])
