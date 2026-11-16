
import time

def policy(me, opp, color):
    start = time.time()
    TIME_LIMIT = 0.85

    me_set = set(me)
    opp_set = set(opp)

    if color == 'w':
        me_dir = 1
        me_target = 7
        opp_target = 0
    else:
        me_dir = -1
        me_target = 0
        opp_target = 7

    ADV = [0, 2, 4, 9, 18, 35, 90, 500]

    def evaluate(mine, theirs, my_tgt, opp_tgt):
        s = (len(mine) - len(theirs)) * 45
        for (r, c) in mine:
            adv = 7 - abs(my_tgt - r)
            s += ADV[adv]
            if 2 <= c <= 5:
                s += 1
        for (r, c) in theirs:
            adv = 7 - abs(opp_tgt - r)
            s -= ADV[adv]
            if 2 <= c <= 5:
                s -= 1
        return s

    def gen_moves(mine, theirs, d):
        moves = []
        for (r, c) in mine:
            nr = r + d
            if nr < 0 or nr > 7:
                continue
            if (nr, c) not in mine and (nr, c) not in theirs:
                moves.append(((r, c), (nr, c)))
            if c > 0 and (nr, c - 1) not in mine:
                moves.append(((r, c), (nr, c - 1)))
            if c < 7 and (nr, c + 1) not in mine:
                moves.append(((r, c), (nr, c + 1)))
        return moves

    class Timeout(Exception):
        pass

    def search(mine, theirs, d, my_tgt, opp_tgt, depth, alpha, beta):
        if not theirs:
            return 9000 + depth
        for (r, c) in theirs:
            if r == opp_tgt:
                return -9000 - depth
        if depth == 0:
            return evaluate(mine, theirs, my_tgt, opp_tgt)
        if time.time() - start > TIME_LIMIT:
            raise Timeout()
        moves = gen_moves(mine, theirs, d)
        if not moves:
            return -9000 - depth
        for m in moves:
            if m[1][0] == my_tgt:
                return 9000 + depth

        def mkey(m):
            tr, tc = m[1]
            cap = 1 if (tr, tc) in theirs else 0
            adv = 7 - abs(my_tgt - tr)
            return -(cap * 1000 + adv * 10)
        moves.sort(key=mkey)

        best = -99999
        for m in moves:
            (fr, fc), (tr, tc) = m
            captured = (tr, tc) in theirs
            mine.discard((fr, fc))
            mine.add((tr, tc))
            if captured:
                theirs.discard((tr, tc))
            try:
                score = -search(theirs, mine, -d, opp_tgt, my_tgt, depth - 1, -beta, -alpha)
            finally:
                mine.discard((tr, tc))
                mine.add((fr, fc))
                if captured:
                    theirs.add((tr, tc))
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    moves = gen_moves(me_set, opp_set, me_dir)
    if not moves:
        return (me[0], me[0])
    for m in moves:
        if m[1][0] == me_target:
            return m

    def top_key(m):
        tr, tc = m[1]
        cap = 1 if (tr, tc) in opp_set else 0
        adv = 7 - abs(me_target - tr)
        return -(cap * 1000 + adv * 10)
    moves.sort(key=top_key)

    best_move = moves[0]
    move_scores = {m: 0 for m in moves}

    for depth in range(1, 8):
        if time.time() - start > TIME_LIMIT * 0.5:
            break
        try:
            alpha = -99999
            beta = 99999
            cur_best = -99999
            cur_best_move = None
            moves.sort(key=lambda m: -move_scores[m])
            for m in moves:
                (fr, fc), (tr, tc) = m
                captured = (tr, tc) in opp_set
                me_set.discard((fr, fc))
                me_set.add((tr, tc))
                if captured:
                    opp_set.discard((tr, tc))
                try:
                    score = -search(opp_set, me_set, -me_dir, opp_target, me_target, depth - 1, -beta, -alpha)
                finally:
                    me_set.discard((tr, tc))
                    me_set.add((fr, fc))
                    if captured:
                        opp_set.add((tr, tc))
                move_scores[m] = score
                if score > cur_best:
                    cur_best = score
                    cur_best_move = m
                if cur_best > alpha:
                    alpha = cur_best
            if cur_best_move is not None:
                best_move = cur_best_move
            if cur_best >= 9000:
                break
        except Timeout:
            break

    return best_move
