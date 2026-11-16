
import time

def _find_jumps_from(piece, is_king, my_men, my_kings, opp_men, opp_kings, my_dir):
    r, c = piece
    all_opp = opp_men | opp_kings
    all_pieces = my_men | my_kings | all_opp
    jumps = []
    dirs = [(-1,-1),(-1,1),(1,-1),(1,1)] if is_king else [(my_dir,-1),(my_dir,1)]
    for dr, dc in dirs:
        mr, mc = r+dr, c+dc
        tr, tc = r+2*dr, c+2*dc
        if 0 <= tr < 8 and 0 <= tc < 8:
            if (mr,mc) in all_opp and (tr,tc) not in all_pieces:
                jumps.append((tr, tc, mr, mc))
    return jumps

def _explore_jumps(piece, is_king, my_men, my_kings, opp_men, opp_kings, my_dir, my_promote):
    jumps = _find_jumps_from(piece, is_king, my_men, my_kings, opp_men, opp_kings, my_dir)
    if not jumps:
        return [(my_men, my_kings, opp_men, opp_kings)]
    outcomes = []
    for tr, tc, mr, mc in jumps:
        new_opp_men = opp_men - {(mr,mc)}
        new_opp_kings = opp_kings - {(mr,mc)}
        if is_king:
            new_my_kings = (my_kings - {piece}) | {(tr,tc)}
            outcomes.extend(_explore_jumps((tr,tc), True, my_men, new_my_kings,
                                           new_opp_men, new_opp_kings, my_dir, my_promote))
        else:
            base = my_men - {piece}
            if tr == my_promote:
                new_my_kings = my_kings | {(tr,tc)}
                outcomes.append((base, new_my_kings, new_opp_men, new_opp_kings))
            else:
                new_my_men = base | {(tr,tc)}
                outcomes.extend(_explore_jumps((tr,tc), False, new_my_men, my_kings,
                                               new_opp_men, new_opp_kings, my_dir, my_promote))
    return outcomes

def _generate_full_moves(my_men, my_kings, opp_men, opp_kings, my_dir, my_promote):
    all_captures = []
    for piece in my_men:
        jumps = _find_jumps_from(piece, False, my_men, my_kings, opp_men, opp_kings, my_dir)
        for tr, tc, mr, mc in jumps:
            new_opp_men = opp_men - {(mr,mc)}
            new_opp_kings = opp_kings - {(mr,mc)}
            base = my_men - {piece}
            if tr == my_promote:
                new_my_kings = my_kings | {(tr,tc)}
                all_captures.append((piece, (tr,tc),
                                     (base, new_my_kings, new_opp_men, new_opp_kings)))
            else:
                new_my_men = base | {(tr,tc)}
                subs = _explore_jumps((tr,tc), False, new_my_men, my_kings,
                                      new_opp_men, new_opp_kings, my_dir, my_promote)
                for s in subs:
                    all_captures.append((piece, (tr,tc), s))
    for piece in my_kings:
        jumps = _find_jumps_from(piece, True, my_men, my_kings, opp_men, opp_kings, my_dir)
        for tr, tc, mr, mc in jumps:
            new_opp_men = opp_men - {(mr,mc)}
            new_opp_kings = opp_kings - {(mr,mc)}
            new_my_kings = (my_kings - {piece}) | {(tr,tc)}
            subs = _explore_jumps((tr,tc), True, my_men, new_my_kings,
                                  new_opp_men, new_opp_kings, my_dir, my_promote)
            for s in subs:
                all_captures.append((piece, (tr,tc), s))
    if all_captures:
        return [((f, t), s) for f, t, s in all_captures]
    moves = []
    all_pieces = my_men | my_kings | opp_men | opp_kings
    for piece in my_men:
        r, c = piece
        for dc in (-1, 1):
            tr, tc = r + my_dir, c + dc
            if 0 <= tr < 8 and 0 <= tc < 8 and (tr, tc) not in all_pieces:
                base = my_men - {piece}
                if tr == my_promote:
                    new_my_kings = my_kings | {(tr,tc)}
                    moves.append(((piece, (tr,tc)),
                                  (base, new_my_kings, opp_men, opp_kings)))
                else:
                    new_my_men = base | {(tr,tc)}
                    moves.append(((piece, (tr,tc)),
                                  (new_my_men, my_kings, opp_men, opp_kings)))
    for piece in my_kings:
        r, c = piece
        for dr in (-1, 1):
            for dc in (-1, 1):
                tr, tc = r + dr, c + dc
                if 0 <= tr < 8 and 0 <= tc < 8 and (tr, tc) not in all_pieces:
                    new_my_kings = (my_kings - {piece}) | {(tr,tc)}
                    moves.append(((piece, (tr,tc)),
                                  (my_men, new_my_kings, opp_men, opp_kings)))
    return moves

def _evaluate(my_men, my_kings, opp_men, opp_kings, my_promote, opp_promote):
    score = 100*len(my_men) + 160*len(my_kings) - 100*len(opp_men) - 160*len(opp_kings)
    for (r, c) in my_men:
        score += (7 - abs(my_promote - r)) * 3
        if c == 0 or c == 7:
            score -= 2
    for (r, c) in opp_men:
        score -= (7 - abs(opp_promote - r)) * 3
        if c == 0 or c == 7:
            score += 2
    for (r, c) in my_kings:
        score -= int(abs(r*2 - 7) + abs(c*2 - 7))
    for (r, c) in opp_kings:
        score += int(abs(r*2 - 7) + abs(c*2 - 7))
    return score

def _negamax(state, my_dir, my_promote, opp_dir, opp_promote, depth, alpha, beta, deadline):
    if time.time() > deadline:
        raise TimeoutError()
    my_men, my_kings, opp_men, opp_kings = state
    if not my_men and not my_kings:
        return -100000 - depth
    if not opp_men and not opp_kings:
        return 100000 + depth
    if depth == 0:
        return _evaluate(my_men, my_kings, opp_men, opp_kings, my_promote, opp_promote)
    full_moves = _generate_full_moves(my_men, my_kings, opp_men, opp_kings, my_dir, my_promote)
    if not full_moves:
        return -100000 - depth
    best = -10**9
    for first_step, fs in full_moves:
        new_state = (fs[2], fs[3], fs[0], fs[1])
        val = -_negamax(new_state, opp_dir, opp_promote, my_dir, my_promote,
                        depth-1, -beta, -alpha, deadline)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(my_men, my_kings, opp_men, opp_kings, color):
    my_men = frozenset(tuple(s) for s in my_men)
    my_kings = frozenset(tuple(s) for s in my_kings)
    opp_men = frozenset(tuple(s) for s in opp_men)
    opp_kings = frozenset(tuple(s) for s in opp_kings)
    if color == 'b':
        my_dir, my_promote = -1, 0
        opp_dir, opp_promote = 1, 7
    else:
        my_dir, my_promote = 1, 7
        opp_dir, opp_promote = -1, 0
    start = time.time()
    deadline = start + 0.85
    full_moves = _generate_full_moves(my_men, my_kings, opp_men, opp_kings, my_dir, my_promote)
    if not full_moves:
        if my_men:
            p = next(iter(my_men))
            return (p, (p[0]+my_dir if 0<=p[0]+my_dir<8 else p[0], p[1]))
        if my_kings:
            p = next(iter(my_kings))
            return (p, (p[0], p[1]))
        return ((0,0),(0,0))
    best_move = full_moves[0][0]
    for depth in range(1, 12):
        if time.time() - start > 0.4:
            break
        try:
            current_best = best_move
            current_val = -10**9
            alpha = -10**9
            beta = 10**9
            # Move best_move first
            ordered = list(full_moves)
            for i, (fs, _) in enumerate(ordered):
                if fs == best_move:
                    if i > 0:
                        ordered = [ordered[i]] + ordered[:i] + ordered[i+1:]
                    break
            for first_step, fs in ordered:
                new_state = (fs[2], fs[3], fs[0], fs[1])
                val = -_negamax(new_state, opp_dir, opp_promote, my_dir, my_promote,
                                depth-1, -beta, -alpha, deadline)
                if val > current_val:
                    current_val = val
                    current_best = first_step
                if current_val > alpha:
                    alpha = current_val
            best_move = current_best
        except TimeoutError:
            break
    return best_move
