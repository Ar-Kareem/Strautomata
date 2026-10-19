
import time

def _in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def _gen_jumps_from(pos, is_king, color, my_pieces, opp_pieces, captured, start):
    r, c = pos
    if is_king:
        dirs = [(1,1),(1,-1),(-1,1),(-1,-1)]
    else:
        fd = -1 if color == 'b' else 1
        dirs = [(fd,1),(fd,-1)]
    jumps = []
    for dr, dc in dirs:
        mr, mc = r+dr, c+dc
        lr, lc = r+2*dr, c+2*dc
        if not _in_bounds(lr, lc): 
            continue
        if (mr, mc) not in opp_pieces: 
            continue
        if (mr, mc) in captured: 
            continue
        if (lr, lc) in opp_pieces: 
            continue
        if (lr, lc) in my_pieces and (lr, lc) != start: 
            continue
        jumps.append(((lr, lc), (mr, mc)))
    return jumps

def _gen_all_moves(my_men, my_kings, opp_men, opp_kings, color):
    my_men_s = set(my_men)
    my_kings_s = set(my_kings)
    my_pieces = my_men_s | my_kings_s
    opp_pieces = set(opp_men) | set(opp_kings)
    king_row = 0 if color == 'b' else 7
    
    def dfs(start, pos, is_king, captured):
        next_jumps = _gen_jumps_from(pos, is_king, color, my_pieces, opp_pieces, captured, start)
        if not next_jumps:
            return [[]]
        sequences = []
        for (land, cap) in next_jumps:
            if (not is_king) and land[0] == king_row:
                sequences.append([(land, cap)])
            else:
                subs = dfs(start, land, is_king, captured | {cap})
                any_cont = False
                for sub in subs:
                    if sub:
                        any_cont = True
                        sequences.append([(land, cap)] + sub)
                if not any_cont:
                    sequences.append([(land, cap)])
        return sequences
    
    captures = []
    for piece in my_pieces:
        is_king = piece in my_kings_s
        seqs = dfs(piece, piece, is_king, set())
        for seq in seqs:
            if seq:
                captures.append((piece, seq))
    
    if captures:
        return ('capture', captures)
    
    moves = []
    for piece in my_pieces:
        r, c = piece
        is_king = piece in my_kings_s
        if is_king:
            dirs = [(1,1),(1,-1),(-1,1),(-1,-1)]
        else:
            fd = -1 if color == 'b' else 1
            dirs = [(fd,1),(fd,-1)]
        for dr, dc in dirs:
            nr, nc = r+dr, c+dc
            if _in_bounds(nr, nc) and (nr, nc) not in my_pieces and (nr, nc) not in opp_pieces:
                moves.append((piece, (nr, nc)))
    
    return ('move', moves)

def _apply_move(my_men, my_kings, opp_men, opp_kings, color, move_type, move):
    mm = set(my_men); mk = set(my_kings)
    om = set(opp_men); ok = set(opp_kings)
    king_row = 0 if color == 'b' else 7
    
    if move_type == 'move':
        start, end = move
        if start in mm:
            mm.remove(start)
            if end[0] == king_row:
                mk.add(end)
            else:
                mm.add(end)
        else:
            mk.remove(start)
            mk.add(end)
    else:
        start, sequence = move
        is_king = start in mk
        if is_king:
            mk.remove(start)
        else:
            mm.remove(start)
        for (land, cap) in sequence:
            if cap in om:
                om.remove(cap)
            elif cap in ok:
                ok.remove(cap)
            if (not is_king) and land[0] == king_row:
                is_king = True
        final_pos = sequence[-1][0]
        if is_king:
            mk.add(final_pos)
        else:
            mm.add(final_pos)
    
    return list(mm), list(mk), list(om), list(ok)

def _evaluate(my_men, my_kings, opp_men, opp_kings, color):
    score = 0
    score += len(my_men) * 100
    score += len(my_kings) * 175
    score -= len(opp_men) * 100
    score -= len(opp_kings) * 175
    
    for (r, c) in my_men:
        if color == 'b':
            score += (7 - r) * 3
        else:
            score += r * 3
        if c == 0 or c == 7:
            score += 1
    
    opp_color = 'w' if color == 'b' else 'b'
    for (r, c) in opp_men:
        if opp_color == 'b':
            score -= (7 - r) * 3
        else:
            score -= r * 3
        if c == 0 or c == 7:
            score -= 1
    
    for (r, c) in my_kings:
        if 2 <= r <= 5 and 2 <= c <= 5:
            score += 6
    for (r, c) in opp_kings:
        if 2 <= r <= 5 and 2 <= c <= 5:
            score -= 6
    
    return score

def _negamax(my_men, my_kings, opp_men, opp_kings, color, depth, alpha, beta, deadline):
    if time.time() > deadline:
        return _evaluate(my_men, my_kings, opp_men, opp_kings, color)
    
    if not my_men and not my_kings:
        return -100000
    if not opp_men and not opp_kings:
        return 100000
    
    move_type, moves = _gen_all_moves(my_men, my_kings, opp_men, opp_kings, color)
    if not moves:
        return -100000
    
    if depth <= 0:
        if move_type == 'capture':
            if depth > -3:
                pass
            else:
                return _evaluate(my_men, my_kings, opp_men, opp_kings, color)
        else:
            return _evaluate(my_men, my_kings, opp_men, opp_kings, color)
    
    if move_type == 'capture':
        moves.sort(key=lambda m: -len(m[1]))
    
    opp_color = 'w' if color == 'b' else 'b'
    best = -1000000
    for m in moves:
        nm, nk, om, ok = _apply_move(my_men, my_kings, opp_men, opp_kings, color, move_type, m)
        score = -_negamax(om, ok, nm, nk, opp_color, depth-1, -beta, -alpha, deadline)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(my_men, my_kings, opp_men, opp_kings, color):
    start_time = time.time()
    deadline = start_time + 0.85
    
    my_men = [tuple(p) for p in my_men]
    my_kings = [tuple(p) for p in my_kings]
    opp_men = [tuple(p) for p in opp_men]
    opp_kings = [tuple(p) for p in opp_kings]
    
    move_type, moves = _gen_all_moves(my_men, my_kings, opp_men, opp_kings, color)
    if not moves:
        if my_men:
            p = my_men[0]
            r, c = p
            for dr, dc in [(1,1),(1,-1),(-1,1),(-1,-1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    return (p, (nr, nc))
            return (p, p)
        if my_kings:
            p = my_kings[0]
            return (p, p)
        return ((0,0), (0,0))
    
    if move_type == 'capture':
        moves.sort(key=lambda m: -len(m[1]))
    
    opp_color = 'w' if color == 'b' else 'b'
    
    best_move = moves[0]
    best_score_overall = -float('inf')
    
    for depth in range(2, 10):
        if time.time() > deadline:
            break
        current_best_score = -float('inf')
        current_best_move = moves[0]
        completed = True
        for m in moves:
            if time.time() > deadline:
                completed = False
                break
            nm, nk, om, ok = _apply_move(my_men, my_kings, opp_men, opp_kings, color, move_type, m)
            score = -_negamax(om, ok, nm, nk, opp_color, depth-1, -float('inf'), float('inf'), deadline)
            if score > current_best_score:
                current_best_score = score
                current_best_move = m
        if completed:
            best_move = current_best_move
            best_score_overall = current_best_score
            if best_score_overall > 50000:
                break
    
    if move_type == 'move':
        return best_move
    else:
        start, sequence = best_move
        return (start, sequence[0][0])
