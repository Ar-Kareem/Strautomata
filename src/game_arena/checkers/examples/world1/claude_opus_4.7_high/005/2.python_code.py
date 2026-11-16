
import time

def get_captures(pos, is_king, color, my_pieces_except, opp_men, opp_kings, captured):
    if is_king:
        dirs = [(-1,-1),(-1,1),(1,-1),(1,1)]
    elif color == 'b':
        dirs = [(-1,-1),(-1,1)]
    else:
        dirs = [(1,-1),(1,1)]
    r, c = pos
    results = []
    for dr, dc in dirs:
        mr, mc = r+dr, c+dc
        er, ec = r+2*dr, c+2*dc
        if er < 0 or er > 7 or ec < 0 or ec > 7:
            continue
        mid = (mr, mc); end = (er, ec)
        if mid in captured:
            continue
        if mid not in opp_men and mid not in opp_kings:
            continue
        if end in my_pieces_except or end in opp_men or end in opp_kings:
            continue
        new_captured = captured | {mid}
        becomes_king = False
        if not is_king:
            if color == 'b' and er == 0: becomes_king = True
            elif color == 'w' and er == 7: becomes_king = True
        sub = []
        if not becomes_king:
            sub = get_captures(end, is_king, color, my_pieces_except, opp_men, opp_kings, new_captured)
        if sub:
            for path, caps in sub:
                results.append(([pos] + path, caps))
        else:
            results.append(([pos, end], new_captured))
    return results

def get_all_moves(my_men, my_kings, opp_men, opp_kings, color):
    my_pieces = my_men | my_kings
    captures = []
    for pos in my_pieces:
        is_king = pos in my_kings
        mp_except = my_pieces - {pos}
        caps = get_captures(pos, is_king, color, mp_except, opp_men, opp_kings, frozenset())
        captures.extend(caps)
    if captures:
        captures.sort(key=lambda m: -len(m[1]))
        return captures
    moves = []
    all_pieces = my_pieces | opp_men | opp_kings
    for pos in my_pieces:
        is_king = pos in my_kings
        if is_king:
            dirs = [(-1,-1),(-1,1),(1,-1),(1,1)]
        elif color == 'b':
            dirs = [(-1,-1),(-1,1)]
        else:
            dirs = [(1,-1),(1,1)]
        r, c = pos
        for dr, dc in dirs:
            nr, nc = r+dr, c+dc
            if 0<=nr<8 and 0<=nc<8 and (nr,nc) not in all_pieces:
                moves.append(([pos, (nr,nc)], frozenset()))
    return moves

def apply_move(my_men, my_kings, opp_men, opp_kings, color, path, captured):
    my_men = set(my_men); my_kings = set(my_kings)
    opp_men = set(opp_men); opp_kings = set(opp_kings)
    start = path[0]; end = path[-1]
    is_king = start in my_kings
    if is_king:
        my_kings.discard(start); my_kings.add(end)
    else:
        my_men.discard(start)
        if (color == 'b' and end[0] == 0) or (color == 'w' and end[0] == 7):
            my_kings.add(end)
        else:
            my_men.add(end)
    for cap in captured:
        opp_men.discard(cap); opp_kings.discard(cap)
    return my_men, my_kings, opp_men, opp_kings

def evaluate(my_men, my_kings, opp_men, opp_kings, color):
    score = 0
    score += 100 * len(my_men) + 160 * len(my_kings)
    score -= 100 * len(opp_men) + 160 * len(opp_kings)
    for r, c in my_men:
        score += ((7-r) if color == 'b' else r) * 3
    opp_color = 'w' if color == 'b' else 'b'
    for r, c in opp_men:
        score -= ((7-r) if opp_color == 'b' else r) * 3
    back_row = 7 if color == 'b' else 0
    for r, c in my_men:
        if r == back_row: score += 5
    opp_back = 7 if opp_color == 'b' else 0
    for r, c in opp_men:
        if r == opp_back: score -= 5
    for r, c in my_kings:
        score += int(6 - abs(3.5-r) - abs(3.5-c))
    for r, c in opp_kings:
        score -= int(6 - abs(3.5-r) - abs(3.5-c))
    return score

class Timeout(Exception): pass

def search(state, depth, alpha, beta, deadline):
    if time.time() > deadline:
        raise Timeout
    my_men, my_kings, opp_men, opp_kings, color = state
    moves = get_all_moves(my_men, my_kings, opp_men, opp_kings, color)
    if not moves:
        return -99999 - depth
    if depth == 0:
        return evaluate(my_men, my_kings, opp_men, opp_kings, color)
    opp_color = 'w' if color == 'b' else 'b'
    best = -10**9
    for path, captured in moves:
        nm, nk, om, ok = apply_move(my_men, my_kings, opp_men, opp_kings, color, path, captured)
        new_state = (om, ok, nm, nk, opp_color)
        score = -search(new_state, depth-1, -beta, -alpha, deadline)
        if score > best: best = score
        if best > alpha: alpha = best
        if alpha >= beta: break
    return best

def policy(my_men, my_kings, opp_men, opp_kings, color):
    my_men_s = set(tuple(p) for p in my_men)
    my_kings_s = set(tuple(p) for p in my_kings)
    opp_men_s = set(tuple(p) for p in opp_men)
    opp_kings_s = set(tuple(p) for p in opp_kings)
    moves = get_all_moves(my_men_s, my_kings_s, opp_men_s, opp_kings_s, color)
    if not moves:
        return ((0,0),(0,0))
    opp_color = 'w' if color == 'b' else 'b'
    start = time.time()
    deadline = start + 0.75
    best_move = moves[0]
    try:
        for depth in range(1, 20):
            if time.time() - start > 0.35:
                break
            best_score = -10**9
            current_best = moves[0]
            alpha = -10**9; beta = 10**9
            ordered = [best_move] + [m for m in moves if m is not best_move]
            for path, captured in ordered:
                nm, nk, om, ok = apply_move(my_men_s, my_kings_s, opp_men_s, opp_kings_s, color, path, captured)
                new_state = (om, ok, nm, nk, opp_color)
                score = -search(new_state, depth-1, -beta, -alpha, deadline)
                if score > best_score:
                    best_score = score
                    current_best = (path, captured)
                if score > alpha: alpha = score
            best_move = current_best
    except Timeout:
        pass
    path, _ = best_move
    return (path[0], path[-1])
