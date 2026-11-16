
import time

WIN_MASKS = []
for r in range(4):
    WIN_MASKS.append(sum(1 << (r*4+c) for c in range(4)))
for c in range(4):
    WIN_MASKS.append(sum(1 << (r*4+c) for r in range(4)))
WIN_MASKS.append(sum(1 << (i*4+i) for i in range(4)))
WIN_MASKS.append(sum(1 << (i*4+(3-i)) for i in range(4)))

def policy(board):
    my_bb = 0
    op_bb = 0
    for r in range(4):
        for c in range(4):
            v = board[r][c]
            idx = r*4+c
            if v == 1:
                my_bb |= 1 << idx
            elif v == -1:
                op_bb |= 1 << idx

    occ = my_bb | op_bb
    legal = [i for i in range(16) if not (occ >> i) & 1]

    if not legal:
        return (0, 0)
    if len(legal) == 16:
        return (1, 1)

    start = time.time()
    TIME_LIMIT = 0.85

    def has_win(bb):
        for m in WIN_MASKS:
            if (bb & m) == m:
                return True
        return False

    def evaluate(me, op):
        score = 0
        for m in WIN_MASKS:
            mm = me & m
            om = op & m
            if mm and om:
                continue
            if mm:
                cnt = bin(mm).count('1')
                score += (1, 10, 100, 10000)[cnt-1]
            elif om:
                cnt = bin(om).count('1')
                score -= (1, 10, 100, 10000)[cnt-1]
        return score

    INF = 10**9
    WIN_SCORE = 100000

    center_order = [5, 6, 9, 10, 0, 3, 12, 15, 1, 2, 4, 7, 8, 11, 13, 14]
    ord_map = {v: i for i, v in enumerate(center_order)}

    class TO(Exception):
        pass

    def negamax(me, op, depth, alpha, beta):
        if has_win(op):
            return -WIN_SCORE - depth
        occ_l = me | op
        if occ_l == 0xFFFF:
            return 0
        if depth == 0:
            return evaluate(me, op)
        if time.time() - start > TIME_LIMIT:
            raise TO()
        moves = [i for i in range(16) if not (occ_l >> i) & 1]
        moves.sort(key=lambda x: ord_map[x])
        best = -INF
        for i in moves:
            val = -negamax(op, me | (1 << i), depth-1, -beta, -alpha)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    # Immediate win
    for i in legal:
        if has_win(my_bb | (1 << i)):
            return (i // 4, i % 4)

    # Must-block
    block_moves = [i for i in legal if has_win(op_bb | (1 << i))]
    if len(block_moves) >= 1:
        # If only one threat, block it. If multiple, we're losing — block any.
        if len(block_moves) == 1:
            i = block_moves[0]
            return (i // 4, i % 4)

    best_move_idx = legal[0]
    legal_sorted = sorted(legal, key=lambda x: ord_map[x])

    for depth in range(2, 17):
        try:
            alpha, beta = -INF, INF
            cur_best = None
            cur_val = -INF
            for i in legal_sorted:
                new_me = my_bb | (1 << i)
                if has_win(new_me):
                    return (i // 4, i % 4)
                val = -negamax(op_bb, new_me, depth-1, -beta, -alpha)
                if val > cur_val:
                    cur_val = val
                    cur_best = i
                    if val > alpha:
                        alpha = val
            if cur_best is not None:
                best_move_idx = cur_best
                legal_sorted.remove(cur_best)
                legal_sorted.insert(0, cur_best)
            if cur_val > WIN_SCORE - 1000:
                break
            if time.time() - start > TIME_LIMIT * 0.6:
                break
        except TO:
            break

    return (best_move_idx // 4, best_move_idx % 4)
