
import time

_deadline = [0.0]

class _Timeout(Exception):
    pass


def _find_jumps(pos, is_king, color, my_wo, opp_pieces, captured, origin, results):
    r, c = pos
    if is_king:
        dirs = [(-1,-1),(-1,1),(1,-1),(1,1)]
    elif color == 'b':
        dirs = [(-1,-1),(-1,1)]
    else:
        dirs = [(1,-1),(1,1)]
    promo_row = 0 if color == 'b' else 7
    extended = False
    for dr, dc in dirs:
        over = (r+dr, c+dc)
        land = (r+2*dr, c+2*dc)
        if not (0 <= land[0] < 8 and 0 <= land[1] < 8):
            continue
        if over not in opp_pieces or over in captured:
            continue
        if land in my_wo:
            continue
        if land in opp_pieces and land not in captured:
            continue
        new_cap = captured | {over}
        became_king = (not is_king) and land[0] == promo_row
        new_king = is_king or became_king
        if became_king:
            results.append((origin, land, new_cap, True))
        else:
            sub = _find_jumps(land, new_king, color, my_wo, opp_pieces, new_cap, origin, results)
            if not sub:
                results.append((origin, land, new_cap, new_king))
        extended = True
    return extended


def _gen_moves(my_men, my_kings, opp_men, opp_kings, color):
    my_p = my_men | my_kings
    opp_p = opp_men | opp_kings
    jumps = []
    for p in my_men:
        _find_jumps(p, False, color, my_p - {p}, opp_p, frozenset(), p, jumps)
    for p in my_kings:
        _find_jumps(p, True, color, my_p - {p}, opp_p, frozenset(), p, jumps)
    if jumps:
        return jumps
    all_p = my_p | opp_p
    if color == 'b':
        mdirs = [(-1,-1),(-1,1)]; promo = 0
    else:
        mdirs = [(1,-1),(1,1)]; promo = 7
    kdirs = [(-1,-1),(-1,1),(1,-1),(1,1)]
    regular = []
    for p in my_men:
        r, c = p
        for dr, dc in mdirs:
            nr, nc = r+dr, c+dc
            if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in all_p:
                regular.append((p, (nr, nc), frozenset(), nr == promo))
    for p in my_kings:
        r, c = p
        for dr, dc in kdirs:
            nr, nc = r+dr, c+dc
            if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in all_p:
                regular.append((p, (nr, nc), frozenset(), True))
    return regular


def _apply(move, my_men, my_kings, opp_men, opp_kings):
    fp, ep, cap, king_after = move
    nmm = set(my_men); nmk = set(my_kings)
    nom = opp_men - cap; nok = opp_kings - cap
    if fp in nmk:
        nmk.discard(fp); nmk.add(ep)
    else:
        nmm.discard(fp)
        if king_after:
            nmk.add(ep)
        else:
            nmm.add(ep)
    return (nmm, nmk, nom, nok)


def _evaluate(my_men, my_kings, opp_men, opp_kings, color):
    score = 100 * (len(my_men) - len(opp_men)) + 160 * (len(my_kings) - len(opp_kings))
    if color == 'b':
        for r, c in my_men: score += (7 - r) * 2
        for r, c in opp_men: score -= r * 2
    else:
        for r, c in my_men: score += r * 2
        for r, c in opp_men: score -= (7 - r) * 2
    for r, c in my_men:
        if c == 0 or c == 7: score += 1
    for r, c in opp_men:
        if c == 0 or c == 7: score -= 1
    for r, c in my_kings:
        score += int(5 - (abs(r-3.5) + abs(c-3.5)))
    for r, c in opp_kings:
        score -= int(5 - (abs(r-3.5) + abs(c-3.5)))
    return score


def _negamax(state, color, depth, alpha, beta):
    if time.time() > _deadline[0]:
        raise _Timeout()
    mm, mk, om, ok = state
    moves = _gen_moves(mm, mk, om, ok, color)
    if not moves:
        return -9000 - depth
    if depth == 0:
        return _evaluate(mm, mk, om, ok, color)
    moves.sort(key=lambda m: -len(m[2]))
    best = -100000
    opp_color = 'w' if color == 'b' else 'b'
    for move in moves:
        ns = _apply(move, mm, mk, om, ok)
        sw = (ns[2], ns[3], ns[0], ns[1])
        val = -_negamax(sw, opp_color, depth-1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def policy(my_men, my_kings, opp_men, opp_kings, color):
    mm = set(tuple(s) for s in my_men)
    mk = set(tuple(s) for s in my_kings)
    om = set(tuple(s) for s in opp_men)
    ok = set(tuple(s) for s in opp_kings)
    moves = _gen_moves(mm, mk, om, ok, color)
    if not moves:
        return ((0, 0), (0, 0))
    best_move = moves[0]
    moves.sort(key=lambda m: -len(m[2]))
    start = time.time()
    _deadline[0] = start + 0.75
    state = (mm, mk, om, ok)
    opp_color = 'w' if color == 'b' else 'b'
    for depth in range(1, 14):
        cur_best = None
        cur_val = -200000
        alpha = -100000
        beta = 100000
        try:
            for move in moves:
                ns = _apply(move, *state)
                sw = (ns[2], ns[3], ns[0], ns[1])
                val = -_negamax(sw, opp_color, depth-1, -beta, -alpha)
                if val > cur_val:
                    cur_val = val
                    cur_best = move
                if val > alpha:
                    alpha = val
        except _Timeout:
            break
        if cur_best is not None:
            best_move = cur_best
            moves = [best_move] + [m for m in moves if m != best_move]
        if time.time() - start > 0.5:
            break
        if cur_val > 8000:
            break
    return (tuple(best_move[0]), tuple(best_move[1]))
