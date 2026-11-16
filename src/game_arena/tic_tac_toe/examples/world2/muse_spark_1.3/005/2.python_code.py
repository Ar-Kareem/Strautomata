
import time

WIN_LINES = [
    (0,1,2,3),(4,5,6,7),(8,9,10,11),(12,13,14,15),
    (0,4,8,12),(1,5,9,13),(2,6,10,14),(3,7,11,15),
    (0,5,10,15),(3,6,9,12)
]

# positional weights: centre 4, corners 2, edges 1
W = [
    2,1,1,2,
    1,4,4,1,
    1,4,4,1,
    2,1,1,2
]

# static priority: centre first, corners, edges
ORDER = [5,6,9,10,0,3,12,15,1,2,4,7,8,11,13,14]

INF = 1000000

class _Timeout(Exception):
    pass

def _winner(b):
    # b is flat list len 16 with 1,-1,0
    for a,c,d,e in WIN_LINES:
        s = b[a]+b[c]+b[d]+b[e]
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0

def _evaluate(b):
    s = 0
    for a,c,d,e in WIN_LINES:
        v0 = b[a]; v1 = b[c]; v2 = b[d]; v3 = b[e]
        c1 = (v0==1)+(v1==1)+(v2==1)+(v3==1)
        if c1:
            if v0==-1 or v1==-1 or v2==-1 or v3==-1:
                continue
            if c1 == 4:
                return 100000
            elif c1 == 3:
                s += 1000
            elif c1 == 2:
                s += 20
            else:
                s += 1
        else:
            co = (v0==-1)+(v1==-1)+(v2==-1)+(v3==-1)
            if co == 0:
                continue
            if co == 4:
                return -100000
            elif co == 3:
                s -= 1200
            elif co == 2:
                s -= 25
            else:
                s -= 2
    # positional bonus
    # sum b[i]*W[i]
    for i in range(16):
        bi = b[i]
        if bi != 0:
            s += bi * W[i]
    return s

def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        start = time.perf_counter()
        deadline = start + 0.90

        # flatten
        flat = [0]*16
        for r in range(4):
            row = board[r]
            for c in range(4):
                flat[r*4+c] = row[c]

        legal = [i for i,v in enumerate(flat) if v == 0]
        if not legal:
            return (0,0)
        if len(legal) == 1:
            i = legal[0]
            return (i//4, i%4)

        # immediate win
        for i in legal:
            flat[i] = 1
            if _winner(flat) == 1:
                flat[i] = 0
                return (i//4, i%4)
            flat[i] = 0

        # immediate block
        opp_wins = []
        for i in legal:
            flat[i] = -1
            if _winner(flat) == -1:
                opp_wins.append(i)
            flat[i] = 0
        if len(opp_wins) == 1:
            i = opp_wins[0]
            return (i//4, i%4)

        # empty board opening
        if len(legal) == 16:
            return (1,1)

        # order root moves by static ORDER
        order_set = set(legal)
        root_moves = [i for i in ORDER if i in order_set]

        best_idx = root_moves[0]
        # if multiple opp wins we cannot block all, continue to search

        max_depth = len(legal)
        # cap max depth for early game to avoid huge branching wasting time
        # iterative deepening will stop on timeout anyway
        tt = {}
        nodes = [0]

        # closure for negamax
        def negamax(b, depth, alpha, beta, color):
            nodes[0] += 1
            if (nodes[0] & 1023) == 0 and time.perf_counter() > deadline:
                raise _Timeout()
            w = _winner(b)
            if w != 0:
                if w == color:
                    return 100000 + depth
                else:
                    return -100000 - depth
            # draw?
            # check empty existence quickly
            has_empty = False
            for v in b:
                if v == 0:
                    has_empty = True
                    break
            if not has_empty:
                return 0
            if depth == 0:
                e = _evaluate(b)
                return e if color == 1 else -e

            # TT lookup
            key = (tuple(b), color)
            tt_entry = tt.get(key)
            tt_best = -1
            if tt_entry is not None:
                s_depth, s_val, s_flag, s_best = tt_entry
                if s_depth >= depth:
                    if s_flag == 0:
                        return s_val
                    elif s_flag == 1:
                        if s_val >= beta:
                            return s_val
                        if s_val > alpha:
                            alpha = s_val
                    else:
                        if s_val <= alpha:
                            return s_val
                        if s_val < beta:
                            beta = s_val
                tt_best = s_best

            # generate moves in ORDER, tt best first
            # build list
            moves = []
            for idx in ORDER:
                if b[idx] == 0:
                    moves.append(idx)
            if tt_best != -1 and tt_best in moves:
                moves.remove(tt_best)
                moves.insert(0, tt_best)

            best = -INF
            best_mv = moves[0]
            orig_alpha = alpha
            for mv in moves:
                b[mv] = color
                try:
                    sc = -negamax(b, depth-1, -beta, -alpha, -color)
                finally:
                    b[mv] = 0
                if sc > best:
                    best = sc
                    best_mv = mv
                if sc > alpha:
                    alpha = sc
                if alpha >= beta:
                    break
            # store TT
            if best <= orig_alpha:
                flag = 2  # upper
            elif best >= beta:
                flag = 1  # lower
            else:
                flag = 0
            tt[key] = (depth, best, flag, best_mv)
            return best

        # iterative deepening
        # start depth 1
        # if few empties, go deep immediately
        start_depth = 1
        for depth in range(start_depth, max_depth+1):
            if time.perf_counter() > deadline - 0.05:
                break
            try:
                alpha = -INF
                beta = INF
                cur_best = root_moves[0]
                cur_best_score = -INF
                scores = {}
                for mv in root_moves:
                    flat[mv] = 1
                    sc = -negamax(flat, depth-1, -beta, -alpha, -1)
                    flat[mv] = 0
                    scores[mv] = sc
                    if sc > cur_best_score:
                        cur_best_score = sc
                        cur_best = mv
                    if sc > alpha:
                        alpha = sc
                # update best
                best_idx = cur_best
                # reorder for next iteration by scores descending
                root_moves = sorted(root_moves, key=lambda x: scores.get(x, -INF), reverse=True)
                # winning line found
                if cur_best_score >= 100000 - 50:
                    break
                # if depth == max_depth solved
                if depth == max_depth:
                    break
            except _Timeout:
                # restore board (ensure empties)
                for i in legal:
                    if flat[i] != 0 and i not in [j for j,v in enumerate(flat) if v!=0 and j not in legal]:
                        pass
                # ensure flat clean: any root move left placed?
                for i in legal:
                    # if we timed out inside, board may have leftover stones from recursion?
                    # recursion always unmakes via finally, except root mv may remain
                    pass
                # clean root placement if needed
                for i in legal:
                    # flat should be 0 on all legal squares at this point except possibly current mv
                    # reset any non-zero that should be zero? legal squares must be 0
                    # but deeper stones are also on legal squares! Actually flat has stones on non-legal + search stones.
                    # Search stones are unmade, only root mv might remain. So reset all legal to 0.
                    flat[i] = 0
                break
        return (best_idx//4, best_idx%4)
    except Exception:
        try:
            for r in range(4):
                for c in range(4):
                    if board[r][c] == 0:
                        return (r,c)
        except Exception:
            pass
        return (0,0)
