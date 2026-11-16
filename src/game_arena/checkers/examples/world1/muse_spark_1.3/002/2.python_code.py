
import time
import random

INF = 1000000
WIN = 20000

# piece codes flat board 64: 0 empty, 1 b_man, 2 b_king, 3 w_man, 4 w_king
def _build_board(my_men, my_kings, opp_men, opp_kings, color):
    b = [0]*64
    if color == 'w':
        for r,c in my_men:
            if 0 <= r < 8 and 0 <= c < 8:
                b[r*8+c] = 3
        for r,c in my_kings:
            if 0 <= r < 8 and 0 <= c < 8:
                b[r*8+c] = 4
        # opponent is black: need to know which opp list is men/kings?
        # opp_men, opp_kings as passed correspond to opponent
        for r,c in opp_men:
            if 0 <= r < 8 and 0 <= c < 8:
                b[r*8+c] = 1
        for r,c in opp_kings:
            if 0 <= r < 8 and 0 <= c < 8:
                b[r*8+c] = 2
    else:
        for r,c in my_men:
            if 0 <= r < 8 and 0 <= c < 8:
                b[r*8+c] = 1
        for r,c in my_kings:
            if 0 <= r < 8 and 0 <= c < 8:
                b[r*8+c] = 2
        for r,c in opp_men:
            if 0 <= r < 8 and 0 <= c < 8:
                b[r*8+c] = 3
        for r,c in opp_kings:
            if 0 <= r < 8 and 0 <= c < 8:
                b[r*8+c] = 4
    return b

def _gen_moves(board, side):
    # returns (captures, quiets), each move = (fr,fc,tr,tc,cap_idx,promote,cap_val,move_val)
    caps = []
    quiets = []
    if side == 'w':
        own_man, own_king = 3, 4
        opp_man, opp_king = 1, 2
        promo = 7
        fwd = [(1,1),(1,-1)]
        alld = [(1,1),(1,-1),(-1,1),(-1,-1)]
    else:
        own_man, own_king = 1, 2
        opp_man, opp_king = 3, 4
        promo = 0
        fwd = [(-1,1),(-1,-1)]
        alld = [(1,1),(1,-1),(-1,1),(-1,-1)]
    for r in range(8):
        for c in range(8):
            idx = r*8+c
            p = board[idx]
            if side == 'w':
                is_own = (p == 3 or p == 4)
                is_man = (p == 3)
            else:
                is_own = (p == 1 or p == 2)
                is_man = (p == 1)
            if not is_own:
                continue
            if is_man:
                # quiets forward only
                for dr,dc in fwd:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        nidx = nr*8+nc
                        if board[nidx] == 0:
                            prom = (nr == promo)
                            # ordering score: promotion big, advancement, centre
                            adv = nr if side=='w' else (7-nr)
                            centre = 3 - (abs(nr-3.5)+abs(nc-3.5))/2.0
                            s = (50 if prom else 0) + adv*2 + centre*2
                            quiets.append((r,c,nr,nc,-1,prom,0,s))
                # captures all directions (to be safe vs lenient validators)
                for dr,dc in alld:
                    mr, mc = r+dr, c+dc
                    tr, tc = r+2*dr, c+2*dc
                    if 0 <= tr < 8 and 0 <= tc < 8 and 0 <= mr < 8 and 0 <= mc < 8:
                        midx = mr*8+mc
                        tidx = tr*8+tc
                        mp = board[midx]
                        is_opp = (mp == opp_man or mp == opp_king)
                        if is_opp and board[tidx] == 0:
                            prom = (tr == promo)
                            capv = 140 if mp == opp_king else 100
                            s = capv + (50 if prom else 0) + tr*2 if side=='w' else capv + (50 if prom else 0) + (7-tr)*2
                            caps.append((r,c,tr,tc,midx,prom,capv,s))
            else:
                # king
                for dr,dc in alld:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        nidx = nr*8+nc
                        if board[nidx] == 0:
                            centre = 3 - (abs(nr-3.5)+abs(nc-3.5))/2.0
                            s = centre*3
                            quiets.append((r,c,nr,nc,-1,False,0,s))
                for dr,dc in alld:
                    mr, mc = r+dr, c+dc
                    tr, tc = r+2*dr, c+2*dc
                    if 0 <= tr < 8 and 0 <= tc < 8 and 0 <= mr < 8 and 0 <= mc < 8:
                        midx = mr*8+mc
                        tidx = tr*8+tc
                        mp = board[midx]
                        is_opp = (mp == opp_man or mp == opp_king)
                        if is_opp and board[tidx] == 0:
                            capv = 140 if mp == opp_king else 100
                            centre = 3 - (abs(tr-3.5)+abs(tc-3.5))/2.0
                            s = capv + centre*3
                            caps.append((r,c,tr,tc,midx,False,capv,s))
    return caps, quiets

def _apply(board, move, side):
    fr,fc,tr,tc,cap_idx,prom,capv,sv = move
    nb = board[:]  # copy 64
    fidx = fr*8+fc
    tidx = tr*8+tc
    p = nb[fidx]
    nb[fidx] = 0
    if cap_idx != -1:
        nb[cap_idx] = 0
    if prom:
        nb[tidx] = 4 if side == 'w' else 2
    else:
        nb[tidx] = p
    return nb

def _eval_white(board):
    # white perspective
    s = 0
    for r in range(8):
        for c in range(8):
            p = board[r*8+c]
            if p == 0:
                continue
            dist = abs(r-3.5)+abs(c-3.5)
            centre = (7.0-dist)*1.5
            if p == 3:  # w man
                s += 100 + r*6 + centre*1.0
                if r == 0 or r == 1:
                    s += 8  # back rank
                if c == 0 or c == 7:
                    s += 3
                if 2 <= r <= 5 and 2 <= c <= 5:
                    s += 4
            elif p == 4:  # w king
                s += 140 + centre*2.0
            elif p == 1:  # b man
                s -= 100 + (7-r)*6 + centre*1.0
                if r == 7 or r == 6:
                    s -= 8
                if c == 0 or c == 7:
                    s -= 3
                if 2 <= r <= 5 and 2 <= c <= 5:
                    s -= 4
            elif p == 2:  # b king
                s -= 140 + centre*2.0
    return int(s)

class _TO(Exception):
    pass

_deadline = 0
_nodes = 0

def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 255) == 0:
        if time.perf_counter() > _deadline:
            raise _TO()

def _quiesce(board, side, alpha, beta, ply):
    _check_time()
    # win/loss by piece count
    # quick piece existence check
    has_w = False
    has_b = False
    for v in board:
        if v == 3 or v == 4:
            has_w = True
        elif v == 1 or v == 2:
            has_b = True
        if has_w and has_b:
            break
    if not has_w or not has_b:
        if side == 'w':
            return (WIN - ply) if has_w else (-WIN + ply)
        else:
            return (WIN - ply) if has_b else (-WIN + ply)
    caps, _ = _gen_moves(board, side)
    ev = _eval_white(board)
    stand = ev if side == 'w' else -ev
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand
    if ply > 12:
        return alpha
    if not caps:
        return alpha
    caps.sort(key=lambda m: (m[6], m[7]), reverse=True)
    opp = 'b' if side == 'w' else 'w'
    for m in caps:
        nb = _apply(board, m, side)
        sc = -_quiesce(nb, opp, -beta, -alpha, ply+1)
        if sc >= beta:
            return beta
        if sc > alpha:
            alpha = sc
    return alpha

def _negamax(board, side, depth, alpha, beta, ply):
    _check_time()
    # terminal by pieces
    has_w = False
    has_b = False
    for v in board:
        if v == 3 or v == 4:
            has_w = True
        elif v == 1 or v == 2:
            has_b = True
        if has_w and has_b:
            break
    if not has_w or not has_b:
        if side == 'w':
            return (WIN - ply) if has_w else (-WIN + ply)
        else:
            return (WIN - ply) if has_b else (-WIN + ply)
    if depth <= 0:
        return _quiesce(board, side, alpha, beta, ply)
    caps, quiets = _gen_moves(board, side)
    moves = caps if caps else quiets
    if not moves:
        return -WIN + ply  # stalemate = loss
    # order
    moves.sort(key=lambda m: (1 if m[4] != -1 else 0, m[6], m[7]), reverse=True)
    opp = 'b' if side == 'w' else 'w'
    best = -INF
    for m in moves:
        nb = _apply(board, m, side)
        sc = -_negamax(nb, opp, depth-1, -beta, -alpha, ply+1)
        if sc > best:
            best = sc
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    global _deadline, _nodes
    try:
        board = _build_board(list(my_men), list(my_kings), list(opp_men), list(opp_kings), color)
        caps, quiets = _gen_moves(board, color)
        legal = caps if caps else quiets
        if not legal:
            # no moves: return anything with own piece
            try:
                if my_men:
                    fr = tuple(my_men[0])
                elif my_kings:
                    fr = tuple(my_kings[0])
                else:
                    return ((2, 2), (3, 3))
                r, c = fr
                # find empty neighbour
                for dr, dc in [(1,1),(1,-1),(-1,1),(-1,-1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        return ((int(r), int(c)), (int(nr), int(nc)))
                return ((int(r), int(c)), (int((r+1)%8), int((c+1)%8)))
            except Exception:
                return ((2, 2), (3, 3))
        if len(legal) == 1:
            m = legal[0]
            return ((int(m[0]), int(m[1])), (int(m[2]), int(m[3])))
        # iterative deepening
        start = time.perf_counter()
        _deadline = start + 0.85
        _nodes = 0
        # order initial
        legal.sort(key=lambda m: (m[6], m[7]), reverse=True)
        # piece count to set max depth
        pcs = sum(1 for v in board if v != 0)
        max_depth = 7 if pcs < 10 else (6 if pcs < 16 else 5)
        best_move = legal[0]
        # try depths
        opp = 'b' if color == 'w' else 'w'
        try:
            for depth in range(1, max_depth+1):
                alpha = -INF
                beta = INF
                local_best = None
                local_best_sc = -INF
                # shuffle slightly among equals via tiny random
                for m in legal:
                    nb = _apply(board, m, color)
                    sc = -_negamax(nb, opp, depth-1, -beta, -alpha, 1)
                    # tiny tie breaker
                    sc += random.random()*0.5
                    if sc > local_best_sc:
                        local_best_sc = sc
                        local_best = m
                    if sc > alpha:
                        alpha = sc
                    if time.perf_counter() > _deadline:
                        raise _TO()
                best_move = local_best
                # reorder for next depth
                # re-score? keep best first
                legal.remove(best_move)
                legal.insert(0, best_move)
                if local_best_sc > WIN-100:
                    break
                if time.perf_counter() > _deadline:
                    break
        except _TO:
            pass
        return ((int(best_move[0]), int(best_move[1])), (int(best_move[2]), int(best_move[3])))
    except Exception:
        # ultimate fallback: try to return any capture else any quiet using simple scan
        try:
            # rebuild simple
            mine = list(my_men) + list(my_kings)
            occupied = set(map(tuple, list(my_men)+list(my_kings)+list(opp_men)+list(opp_kings)))
            opp_set = set(map(tuple, list(opp_men)+list(opp_kings)))
            is_king_set = set(map(tuple, list(my_kings)))
            fwd_dr = 1 if color == 'w' else -1
            # captures first
            for (r,c) in mine:
                is_k = (r,c) in is_king_set
                dirs = [(1,1),(1,-1),(-1,1),(-1,-1)] if is_k else [(fwd_dr,1),(fwd_dr,-1)]
                # for men also try backward captures
                if not is_k:
                    dirs = [(1,1),(1,-1),(-1,1),(-1,-1)]
                for dr,dc in dirs:
                    mr, mc = r+dr, c+dc
                    tr, tc = r+2*dr, c+2*dc
                    if 0 <= tr < 8 and 0 <= tc < 8:
                        if (mr,mc) in opp_set and (tr,tc) not in occupied:
                            return ((int(r),int(c)),(int(tr),int(tc)))
            for (r,c) in mine:
                is_k = (r,c) in is_king_set
                dirs = [(1,1),(1,-1),(-1,1),(-1,-1)] if is_k else [(fwd_dr,1),(fwd_dr,-1)]
                for dr,dc in dirs:
                    tr, tc = r+dr, c+dc
                    if 0 <= tr < 8 and 0 <= tc < 8:
                        if (tr,tc) not in occupied:
                            return ((int(r),int(c)),(int(tr),int(tc)))
            r,c = mine[0]
            return ((int(r),int(c)), (int((r+fwd_dr)%8), int((c+1)%8)))
        except Exception:
            return ((2,3),(3,4))
