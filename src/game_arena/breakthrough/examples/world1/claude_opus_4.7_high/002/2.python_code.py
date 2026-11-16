
import time

def policy(me, opp, color):
    start = time.time()
    TIME_LIMIT = 0.85
    
    my_dir = 1 if color == 'w' else -1
    my_goal = 7 if color == 'w' else 0
    op_goal = 7 - my_goal
    op_dir = -my_dir
    
    INF = 10**8
    
    def gen_moves(pieces, enemy, direction):
        moves = []
        for p in pieces:
            r, c = p
            nr = r + direction
            if nr < 0 or nr > 7:
                continue
            t = (nr, c)
            if t not in pieces and t not in enemy:
                moves.append((p, t, False))
            if c > 0:
                t2 = (nr, c-1)
                if t2 not in pieces:
                    moves.append((p, t2, t2 in enemy))
            if c < 7:
                t2 = (nr, c+1)
                if t2 not in pieces:
                    moves.append((p, t2, t2 in enemy))
        return moves
    
    def evaluate(my_p, op_p):
        mc, oc = len(my_p), len(op_p)
        if oc == 0: return INF - 1
        if mc == 0: return -INF + 1
        score = (mc - oc) * 80
        if my_dir == 1:
            for (r,c) in my_p:
                score += r * r + r * 3
            for (r,c) in op_p:
                adv = 7 - r
                score -= adv * adv + adv * 3
        else:
            for (r,c) in my_p:
                adv = 7 - r
                score += adv * adv + adv * 3
            for (r,c) in op_p:
                score -= r * r + r * 3
        return score
    
    time_up = [False]
    node_count = [0]
    
    def sort_my(moves):
        def k(m):
            tr = m[1][0]; s = 0
            if tr == my_goal: s -= 1000000
            if m[2]: s -= 1000
            adv = tr if my_dir == 1 else (7-tr)
            s -= adv * 10
            return s
        moves.sort(key=k)
    
    def sort_op(moves):
        def k(m):
            tr = m[1][0]; s = 0
            if tr == op_goal: s -= 1000000
            if m[2]: s -= 1000
            adv = tr if op_dir == 1 else (7-tr)
            s -= adv * 10
            return s
        moves.sort(key=k)
    
    def ab(my_p, op_p, turn, depth, alpha, beta):
        node_count[0] += 1
        if (node_count[0] & 2047) == 0:
            if time.time() - start > TIME_LIMIT:
                time_up[0] = True
        if time_up[0]:
            return 0
        if depth == 0:
            return evaluate(my_p, op_p)
        if turn:
            moves = gen_moves(my_p, op_p, my_dir)
            if not moves: return -INF + 2
            sort_my(moves)
            best = -INF
            for f, t, cap in moves:
                my_p.remove(f); my_p.add(t)
                if cap: op_p.remove(t)
                if t[0] == my_goal or (cap and not op_p):
                    val = INF - (10 - depth)
                else:
                    val = ab(my_p, op_p, False, depth-1, alpha, beta)
                my_p.remove(t); my_p.add(f)
                if cap: op_p.add(t)
                if val > best: best = val
                if best > alpha: alpha = best
                if alpha >= beta: break
            return best
        else:
            moves = gen_moves(op_p, my_p, op_dir)
            if not moves: return INF - 2
            sort_op(moves)
            best = INF
            for f, t, cap in moves:
                op_p.remove(f); op_p.add(t)
                if cap: my_p.remove(t)
                if t[0] == op_goal or (cap and not my_p):
                    val = -INF + (10 - depth)
                else:
                    val = ab(my_p, op_p, True, depth-1, alpha, beta)
                op_p.remove(t); op_p.add(f)
                if cap: my_p.add(t)
                if val < best: best = val
                if best < beta: beta = best
                if alpha >= beta: break
            return best
    
    my_set = set(me)
    op_set = set(opp)
    root_moves = gen_moves(my_set, op_set, my_dir)
    if not root_moves:
        if me: return (me[0], me[0])
        return ((0,0),(0,0))
    for f, t, cap in root_moves:
        if t[0] == my_goal:
            return (f, t)
    sort_my(root_moves)
    best_move = (root_moves[0][0], root_moves[0][1])
    
    for depth in range(2, 8):
        if time.time() - start > TIME_LIMIT * 0.4:
            break
        scores = []
        alpha = -INF; beta = INF
        completed = True
        iter_best = None
        iter_best_val = -INF - 1
        for move in root_moves:
            if time_up[0] or time.time() - start > TIME_LIMIT:
                completed = False; break
            f, t, cap = move
            my_set.remove(f); my_set.add(t)
            if cap: op_set.remove(t)
            if t[0] == my_goal or (cap and not op_set):
                val = INF
            else:
                val = ab(my_set, op_set, False, depth-1, alpha, beta)
            my_set.remove(t); my_set.add(f)
            if cap: op_set.add(t)
            if time_up[0]:
                completed = False; break
            scores.append((val, move))
            if val > iter_best_val:
                iter_best_val = val
                iter_best = move
            if iter_best_val > alpha:
                alpha = iter_best_val
        if completed and iter_best is not None:
            best_move = (iter_best[0], iter_best[1])
            scores.sort(key=lambda x: -x[0])
            root_moves = [m for _, m in scores]
            if iter_best_val >= INF - 1000:
                break
        else:
            break
    return best_move
