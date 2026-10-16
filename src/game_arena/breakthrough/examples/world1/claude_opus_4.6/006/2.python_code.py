
import time

def policy(me, opp, color):
    me_set = set(me)
    opp_set = set(opp)
    direction = 1 if color == 'w' else -1
    my_home = 7 if color == 'w' else 0
    opp_home = 7 if color == 'w' else 0
    # opp_home for me is the row I want to reach
    target_row = 7 if color == 'w' else 0
    opp_target_row = 0 if color == 'w' else 7

    def get_moves(pieces, opponents, d):
        moves = []
        oset = set(opponents)
        pset = set(pieces)
        for r, c in pieces:
            nr = r + d
            if 0 <= nr <= 7:
                # straight forward
                if (nr, c) not in pset and (nr, c) not in oset:
                    moves.append(((r, c), (nr, c)))
                # diagonal captures and moves
                for dc in (-1, 1):
                    nc = c + dc
                    if 0 <= nc <= 7:
                        if (nr, nc) in oset:
                            moves.append(((r, c), (nr, nc)))
                        elif (nr, nc) not in pset:
                            moves.append(((r, c), (nr, nc)))
        return moves

    def evaluate(my_pieces, opp_pieces, my_dir):
        tr = target_row
        otr = opp_target_row
        opp_dir = -my_dir

        if not opp_pieces:
            return 100000
        if not my_pieces:
            return -100000

        for r, c in my_pieces:
            if r == tr:
                return 100000
        for r, c in opp_pieces:
            if r == otr:
                return -100000

        score = (len(my_pieces) - len(opp_pieces)) * 200

        for r, c in my_pieces:
            adv = r if my_dir == 1 else (7 - r)
            score += adv * adv * 5
            if adv == 6:
                score += 150
            # center bonus
            score += (3.5 - abs(c - 3.5)) * 3

        for r, c in opp_pieces:
            adv = r if opp_dir == 1 else (7 - r)
            score -= adv * adv * 5
            if adv == 6:
                score -= 150
            score -= (3.5 - abs(c - 3.5)) * 3

        return score

    def order_moves(moves, my_pieces_set, opp_pieces_set, d, tr):
        scored = []
        for frm, to in moves:
            s = 0
            if to in opp_pieces_set:
                s += 1000
            if to[0] == tr:
                s += 5000
            adv_to = to[0] if d == 1 else (7 - to[0])
            s += adv_to * 10
            scored.append((s, (frm, to)))
        scored.sort(key=lambda x: -x[0])
        return [m for _, m in scored]

    def minimax(my_p, opp_p, my_dir, depth, alpha, beta, maximizing, deadline):
        if time.time() > deadline:
            return evaluate(my_p, opp_p, direction), None

        tr = target_row if maximizing else opp_target_row
        d = my_dir if maximizing else -my_dir
        pieces = list(my_p) if maximizing else list(opp_p)
        opponents = opp_p if maximizing else my_p

        if not opponents:
            return (100000 if maximizing else -100000), None
        for r, c in pieces:
            if r == tr:
                return (100000 if maximizing else -100000), None

        if depth == 0:
            return evaluate(my_p, opp_p, direction), None

        moves = get_moves(pieces, opponents, d)
        if not moves:
            return (-100000 if maximizing else 100000), None

        pset = set(pieces)
        oset = set(opponents)
        moves = order_moves(moves, pset, oset, d, tr)

        best_move = moves[0]
        if maximizing:
            max_eval = -999999
            for frm, to in moves:
                if time.time() > deadline:
                    break
                new_my = set(my_p)
                new_opp = set(opp_p)
                new_my.discard(frm)
                new_my.add(to)
                if to in new_opp:
                    new_opp.discard(to)
                val, _ = minimax(frozenset(new_my), frozenset(new_opp), my_dir, depth - 1, alpha, beta, False, deadline)
                if val > max_eval:
                    max_eval = val
                    best_move = (frm, to)
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = 999999
            for frm, to in moves:
                if time.time() > deadline:
                    break
                new_opp = set(opp_p)
                new_my = set(my_p)
                new_opp.discard(frm)
                new_opp.add(to)
                if to in new_my:
                    new_my.discard(to)
                val, _ = minimax(frozenset(new_my), frozenset(new_opp), my_dir, depth - 1, alpha, beta, True, deadline)
                if val < min_eval:
                    min_eval = val
                    best_move = (frm, to)
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return min_eval, best_move

    deadline = time.time() + 0.85
    my_fs = frozenset(me_set)
    opp_fs = frozenset(opp_set)

    best_move = None
    # Get a legal move as fallback
    fallback_moves = get_moves(list(me_set), list(opp_set), direction)
    if fallback_moves:
        best_move = fallback_moves[0]

    for depth in range(1, 20):
        if time.time() > deadline:
            break
        val, move = minimax(my_fs, opp_fs, direction, depth, -999999, 999999, True, deadline)
        if move is not None:
            best_move = move
        if abs(val) >= 90000:
            break

    return best_move
