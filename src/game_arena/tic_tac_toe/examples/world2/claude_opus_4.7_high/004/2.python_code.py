
import time

LINES = []
for i in range(4):
    LINES.append([(i,j) for j in range(4)])
    LINES.append([(j,i) for j in range(4)])
LINES.append([(i,i) for i in range(4)])
LINES.append([(i,3-i) for i in range(4)])

CELL_LINES = {}
for r in range(4):
    for c in range(4):
        CELL_LINES[(r,c)] = [L for L in LINES if (r,c) in L]

def _check_win_move(board, player, move):
    for line in CELL_LINES[move]:
        ok = True
        for r,c in line:
            if board[r][c] != player:
                ok = False
                break
        if ok:
            return True
    return False

def _evaluate(board):
    score = 0
    W = [0,1,10,100,10000]
    for line in LINES:
        me = 0; op = 0
        for r,c in line:
            v = board[r][c]
            if v == 1: me += 1
            elif v == -1: op += 1
        if op == 0 and me > 0:
            score += W[me]
        elif me == 0 and op > 0:
            score -= W[op]
    return score

def _centrality(rc):
    r,c = rc
    return -((r-1.5)**2 + (c-1.5)**2)

class _Timeout(Exception):
    pass

def policy(board):
    start = time.time()
    limit = 0.85

    b = [row[:] for row in board]
    empties = [(r,c) for r in range(4) for c in range(4) if b[r][c]==0]

    if len(empties) == 16:
        return (1,1)
    if len(empties) == 15:
        if b[1][1] == 0: return (1,1)
        if b[2][2] == 0: return (2,2)
        return (1,2)

    empties.sort(key=_centrality, reverse=True)

    # immediate win
    for m in empties:
        r,c = m
        b[r][c] = 1
        if _check_win_move(b, 1, m):
            b[r][c] = 0
            return m
        b[r][c] = 0

    # immediate block
    for m in empties:
        r,c = m
        b[r][c] = -1
        if _check_win_move(b, -1, m):
            b[r][c] = 0
            return m
        b[r][c] = 0

    best_move = empties[0]

    def negamax(player, depth, alpha, beta, last_move):
        if time.time() - start > limit:
            raise _Timeout
        if last_move is not None:
            if _check_win_move(b, -player, last_move):
                return -10000 - depth
        emp = [(r,c) for r in range(4) for c in range(4) if b[r][c]==0]
        if not emp:
            return 0
        if depth == 0:
            return player * _evaluate(b)
        emp.sort(key=_centrality, reverse=True)
        best = -999999
        for m in emp:
            r,c = m
            b[r][c] = player
            val = -negamax(-player, depth-1, -beta, -alpha, m)
            b[r][c] = 0
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    try:
        for depth in range(2, 17):
            local_best = None
            local_val = -999999
            alpha = -999999
            beta = 999999
            # Order top-level moves by previous best (keep best_move first)
            ordered = list(empties)
            if best_move in ordered:
                ordered.remove(best_move)
                ordered.insert(0, best_move)
            for m in ordered:
                r,c = m
                b[r][c] = 1
                val = -negamax(-1, depth-1, -beta, -alpha, m)
                b[r][c] = 0
                if val > local_val:
                    local_val = val
                    local_best = m
                if val > alpha:
                    alpha = val
            if local_best is not None:
                best_move = local_best
            if local_val > 9000:
                break
            if time.time() - start > limit * 0.9:
                break
    except _Timeout:
        pass

    return best_move
