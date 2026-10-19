
import time
import random

class _Timeout(Exception):
    pass

_LINES = []
for r in range(6):
    for c in range(2):
        m = 0
        for k in range(5):
            m |= 1 << (r*6 + c + k)
        _LINES.append(m)
for c in range(6):
    for r in range(2):
        m = 0
        for k in range(5):
            m |= 1 << ((r+k)*6 + c)
        _LINES.append(m)
for r in range(2):
    for c in range(2):
        m = 0
        for k in range(5):
            m |= 1 << ((r+k)*6 + c + k)
        _LINES.append(m)
for r in range(2):
    for c in range(4, 6):
        m = 0
        for k in range(5):
            m |= 1 << ((r+k)*6 + c - k)
        _LINES.append(m)

_PERMS = [[[0]*36 for _ in range(2)] for _ in range(4)]
for q in range(4):
    br = (q // 2) * 3
    bc = (q % 2) * 3
    for r in range(6):
        for c in range(6):
            idx = r*6+c
            if br <= r < br+3 and bc <= c < bc+3:
                lr = r - br
                lc = c - bc
                # R clockwise: (lr,lc)->(lc,2-lr)
                nrR = br + lc
                ncR = bc + 2 - lr
                # L anticlockwise: (lr,lc)->(2-lc,lr)
                nrL = br + 2 - lc
                ncL = bc + lr
                _PERMS[q][1][idx] = nrR*6+ncR
                _PERMS[q][0][idx] = nrL*6+ncL
            else:
                _PERMS[q][1][idx] = idx
                _PERMS[q][0][idx] = idx
# flat list of 8 perms: pi = q*2+d
_FLAT_PERMS = []
for q in range(4):
    for d in range(2):
        _FLAT_PERMS.append(_PERMS[q][d])

_QCENTER = (1<<7)|(1<<10)|(1<<25)|(1<<28)

_MY = [0,2,20,400,15000,1000000]
_OP = [0,3,30,800,30000,1000000]
_INF = 10000000

try:
    _bc = int.bit_count
    def _popcnt(x):
        return x.bit_count()
except Exception:
    def _popcnt(x):
        return bin(x).count("1")

def _permute(mask, perm):
    res = 0
    while mask:
        lsb = mask & -mask
        i = (lsb.bit_length() - 1)
        res |= 1 << perm[i]
        mask ^= lsb
    return res

def _is_win(mask):
    for lm in _LINES:
        if (mask & lm) == lm:
            return True
    return False

def _evaluate(a, b):
    s = 0
    for lm in _LINES:
        ya = a & lm
        if ya:
            if b & lm:
                continue
            c = _popcnt(ya)
            if c >= 6:
                c = 5
            s += _MY[c]
        else:
            ob = b & lm
            if ob:
                c = _popcnt(ob)
                if c >= 6:
                    c = 5
                s -= _OP[c]
    s += _popcnt(a & _QCENTER) * 6
    s -= _popcnt(b & _QCENTER) * 6
    return s

def policy(you, opponent) -> str:
    start = time.time()
    LIMIT = 0.90
    # parse board
    you_mask = 0
    opp_mask = 0
    empties0 = []
    try:
        for r in range(6):
            yr = you[r]
            opr = opponent[r]
            for c in range(6):
                y = int(yr[c])
                o = int(opr[c])
                idx = r*6+c
                if y:
                    you_mask |= 1 << idx
                elif o:
                    opp_mask |= 1 << idx
                else:
                    empties0.append(idx)
    except Exception:
        # fallback parse attempt
        try:
            import numpy as np
            ya = np.asarray(you)
            oa = np.asarray(opponent)
            you_mask = 0
            opp_mask = 0
            empties0 = []
            for r in range(6):
                for c in range(6):
                    idx = r*6+c
                    if int(ya[r,c]):
                        you_mask |= 1 << idx
                    elif int(oa[r,c]):
                        opp_mask |= 1 << idx
                    else:
                        empties0.append(idx)
        except Exception:
            return "1,1,0,R"
    if not empties0:
        return "1,1,0,R"
    def move_str(e, q, d):
        r = e // 6
        c = e % 6
        dc = 'L' if d == 0 else 'R'
        return f"{r+1},{c+1},{q},{dc}"
    fallback = move_str(empties0[0], 0, 1)

    try:
        # precompute permuted existing stones for root immediate win check
        # yps[pi], ops[pi]
        yps0 = [_permute(you_mask, _FLAT_PERMS[pi]) for pi in range(8)]
        ops0 = [_permute(opp_mask, _FLAT_PERMS[pi]) for pi in range(8)]
        occ = you_mask | opp_mask
        full = (occ.bit_count() if hasattr(int, "bit_count") else bin(occ).count("1")) == 36
        # immediate pure win scan (deduplicated not needed)
        first_draw = None
        # iterate
        for e in empties0:
            for pi in range(8):
                q = pi // 2
                d = pi % 2
                dest = _FLAT_PERMS[pi][e]
                ny = yps0[pi] | (1 << dest)
                no = ops0[pi]
                wy = _is_win(ny)
                if wy:
                    wo = _is_win(no)
                    if not wo:
                        return move_str(e, q, d)
                    else:
                        if first_draw is None:
                            first_draw = move_str(e, q, d)
        # if board almost full and no win, draw fallback is fine but continue search
        # helper to generate moves for a node
        def gen_ordered(y_m, o_m):
            occ_l = y_m | o_m
            # empties
            em = []
            for i in range(36):
                if not (occ_l >> i) & 1:
                    em.append(i)
            if not em:
                return []
            yps = [_permute(y_m, _FLAT_PERMS[pi]) for pi in range(8)]
            ops = [_permute(o_m, _FLAT_PERMS[pi]) for pi in range(8)]
            best_dict = {}
            for e in em:
                for pi in range(8):
                    q = pi // 2
                    d = pi % 2
                    dest = _FLAT_PERMS[pi][e]
                    ny = yps[pi] | (1 << dest)
                    no = ops[pi]
                    key = (ny, no)
                    if key in best_dict:
                        continue
                    wy = _is_win(ny)
                    if wy:
                        wo = _is_win(no)
                        if wo:
                            term = 0
                            stat = 0
                        else:
                            # winning move: keep with INF
                            # store directly
                            best_dict[key] = (100000000, e, q, d, ny, no, _INF)
                            continue
                    else:
                        if _popcnt(ny | no) == 36:
                            best_dict[key] = (0, e, q, d, ny, no, 0)
                            continue
                        stat = _evaluate(ny, no)
                        best_dict[key] = (stat, e, q, d, ny, no, None)
            lst = list(best_dict.values())
            # random tie break
            random.shuffle(lst)
            lst.sort(key=lambda x: x[0], reverse=True)
            return lst

        # root ordered
        root_list = gen_ordered(you_mask, opp_mask)
        if not root_list:
            if first_draw is not None:
                return first_draw
            return fallback
        # if only one distinct board, return it
        if len(root_list) == 1:
            _, e, q, d, _, _, _ = root_list[0]
            return move_str(e, q, d)

        # check time left
        if time.time() - start > LIMIT - 0.05:
            _, e, q, d, _, _, _ = root_list[0]
            return move_str(e, q, d)

        # negamax with alpha-beta, breadth limit
        # use closure for timeout
        def negamax(y_m, o_m, depth, alpha, beta):
            if time.time() - start > LIMIT:
                raise _Timeout()
            if depth == 0:
                return _evaluate(y_m, o_m)
            occ_l = y_m | o_m
            # quick full check
            # generate
            # inline generation for speed (duplicate of gen_ordered but with early win exit)
            em = []
            for i in range(36):
                if not (occ_l >> i) & 1:
                    em.append(i)
            if not em:
                return 0
            yps = [_permute(y_m, _FLAT_PERMS[pi]) for pi in range(8)]
            ops = [_permute(o_m, _FLAT_PERMS[pi]) for pi in range(8)]
            # first check winning move existence without full eval? we need eval for ordering anyway
            # Use dict
            dct = {}
            win_found = False
            for e in em:
                for pi in range(8):
                    dest = _FLAT_PERMS[pi][e]
                    ny = yps[pi] | (1 << dest)
                    no = ops[pi]
                    key = (ny, no)
                    if key in dct:
                        continue
                    if _is_win(ny):
                        if not _is_win(no):
                            return _INF
                        else:
                            dct[key] = (0, ny, no, 0)
                    else:
                        if _popcnt(ny | no) == 36:
                            dct[key] = (0, ny, no, 0)
                        else:
                            # defer eval? compute now
                            st = _evaluate(ny, no)
                            dct[key] = (st, ny, no, None)
            lst = list(dct.values())
            if not lst:
                return 0
            # order
            # small random shuffle for variety when equal? skip shuffle inside for speed, sort
            lst.sort(key=lambda x: x[0], reverse=True)
            # breadth limit for depth>1
            if depth > 1 and len(lst) > 12:
                lst = lst[:12]
            best = -_INF - 1
            for st, ny, no, term in lst:
                if term is not None:
                    score = term  # 0 draw
                elif depth == 1:
                    score = st
                else:
                    score = -negamax(no, ny, depth-1, -beta, -alpha)
                if score > best:
                    best = score
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best

        n_empty = len(empties0)
        if n_empty > 24:
            depths = [2, 3]
            ROOT_K = 24
        elif n_empty > 14:
            depths = [2, 3, 4]
            ROOT_K = 20
        elif n_empty > 8:
            depths = [2, 3, 4, 5]
            ROOT_K = 20
        else:
            depths = [2, 3, 4, 5, 6]
            ROOT_K = 30

        # truncate root for deep search
        # keep top ROOT_K for depth>=3, all for depth 2 if small
        best_move = None
        # depth 2 first with possibly larger root set
        # we will iterate depths
        current_best_str = fallback
        # initialize with greedy best
        try:
            _, be, bq, bd, _, _, _ = root_list[0]
            current_best_str = move_str(be, bq, bd)
        except Exception:
            pass

        for D in depths:
            if time.time() - start > LIMIT - 0.08:
                break
            # select root subset
            if D >= 3 and len(root_list) > ROOT_K:
                rsub = root_list[:ROOT_K]
            elif D == 2 and len(root_list) > 40:
                rsub = root_list[:40]
            else:
                rsub = root_list
            alpha = -_INF - 1
            beta = _INF + 1
            local_best_score = -_INF - 1
            local_best = None
            for stat, e, q, d, ny, no, term in rsub:
                if time.time() - start > LIMIT:
                    raise _Timeout()
                if term is not None:
                    score = term
                    # term INF would have returned earlier, so only 0 here
                else:
                    if D == 1:
                        score = stat
                    else:
                        # opponent reply
                        opp_score = negamax(no, ny, D-1, -beta, -alpha)
                        score = -opp_score
                if score > local_best_score:
                    local_best_score = score
                    local_best = (e, q, d)
                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    break
                # early exit if winning
                if local_best_score >= _INF:
                    break
            if local_best is not None:
                be, bq, bd = local_best
                current_best_str = move_str(be, bq, bd)
                # if winning, return immediately
                if local_best_score >= _INF:
                    return current_best_str
            # if all moves lose (-INF) and we have a draw, prefer draw
            if local_best_score <= -_INF + 1 and first_draw is not None:
                # check if draw is better (0 > -INF)
                return first_draw
        return current_best_str
    except _Timeout:
        # return best so far if available else fallback
        try:
            return current_best_str
        except Exception:
            return fallback
    except Exception:
        try:
            return current_best_str
        except Exception:
            return fallback
