
import time

def policy(me, opp, color):
    start = time.time()
    TIME_LIMIT = 0.85

    board = bytearray(64)
    pieces = [set(), set(), set()]
    for r, c in me:
        idx = r*8+c
        board[idx] = 1
        pieces[1].add(idx)
    for r, c in opp:
        idx = r*8+c
        board[idx] = 2
        pieces[2].add(idx)

    my_dir = 1 if color == 'w' else -1
    dirs = [0, my_dir, -my_dir]
    goals = [0, 7 if color == 'w' else 0, 0 if color == 'w' else 7]

    def gen_moves(player):
        moves = []
        off = dirs[player] * 8
        for idx in pieces[player]:
            nidx = idx + off
            c = idx & 7
            if 0 <= nidx < 64:
                if board[nidx] == 0:
                    moves.append((idx, nidx))
                if c > 0 and board[nidx-1] != player:
                    moves.append((idx, nidx-1))
                if c < 7 and board[nidx+1] != player:
                    moves.append((idx, nidx+1))
        return moves

    def evaluate(player):
        opp_p = 3 - player
        mg = goals[player]; og = goals[opp_p]
        ma = 0; oa = 0
        for idx in pieces[player]:
            r = idx >> 3
            adv = 7 - abs(mg - r)
            ma += adv*adv
        for idx in pieces[opp_p]:
            r = idx >> 3
            adv = 7 - abs(og - r)
            oa += adv*adv
        return (len(pieces[player]) - len(pieces[opp_p])) * 100 + (ma - oa) * 2

    def search(player, depth, alpha, beta):
        if not pieces[player]:
            return -100000 - depth
        if time.time() - start > TIME_LIMIT:
            return evaluate(player)
        moves = gen_moves(player)
        if not moves:
            return -100000 - depth
        my_goal = goals[player]
        opp_p = 3 - player
        for m in moves:
            if (m[1] >> 3) == my_goal:
                return 100000 + depth
        if depth == 0:
            return evaluate(player)
        def mscore(m):
            t = m[1]; s = 0
            if board[t] == opp_p: s += 100
            s += 7 - abs(my_goal - (t >> 3))
            return -s
        moves.sort(key=mscore)
        best = -10**9
        for m in moves:
            f, t = m
            cap = board[t]
            board[f] = 0; board[t] = player
            pieces[player].discard(f); pieces[player].add(t)
            if cap == opp_p: pieces[opp_p].discard(t)
            val = -search(opp_p, depth-1, -beta, -alpha)
            board[t] = cap; board[f] = player
            pieces[player].discard(t); pieces[player].add(f)
            if cap == opp_p: pieces[opp_p].add(t)
            if val > best: best = val
            if best > alpha: alpha = best
            if alpha >= beta: break
        return best

    my_goal = goals[1]
    moves = gen_moves(1)
    for m in moves:
        if (m[1] >> 3) == my_goal:
            f, t = m
            return ((f >> 3, f & 7), (t >> 3, t & 7))

    def mscore_root(m):
        t = m[1]; s = 0
        if board[t] == 2: s += 100
        s += 7 - abs(my_goal - (t >> 3))
        return -s
    moves.sort(key=mscore_root)
    best_move = moves[0]

    for depth in range(1, 10):
        if time.time() - start > TIME_LIMIT * 0.4:
            break
        alpha = -10**9; beta = 10**9
        best_val = -10**9; current_best = None; completed = True
        ordered = [best_move] + [m for m in moves if m != best_move]
        for m in ordered:
            if time.time() - start > TIME_LIMIT:
                completed = False
                break
            f, t = m
            cap = board[t]
            board[f] = 0; board[t] = 1
            pieces[1].discard(f); pieces[1].add(t)
            if cap == 2: pieces[2].discard(t)
            val = -search(2, depth-1, -beta, -alpha)
            board[t] = cap; board[f] = 1
            pieces[1].discard(t); pieces[1].add(f)
            if cap == 2: pieces[2].add(t)
            if val > best_val:
                best_val = val
                current_best = m
            if best_val > alpha: alpha = best_val
        if completed and current_best is not None:
            best_move = current_best

    f, t = best_move
    return ((f >> 3, f & 7), (t >> 3, t & 7))
