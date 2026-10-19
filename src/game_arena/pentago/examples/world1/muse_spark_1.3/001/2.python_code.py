
import time

# ---------- precomputation ----------
WIN_MASKS = []
for r in range(6):
    for c in range(2):
        m = 0
        for i in range(5):
            m |= 1 << (r*6 + c + i)
        WIN_MASKS.append(m)
for c in range(6):
    for r in range(2):
        m = 0
        for i in range(5):
            m |= 1 << ((r+i)*6 + c)
        WIN_MASKS.append(m)
for sr in range(2):
    for sc in range(2):
        m = 0
        for i in range(5):
            m |= 1 << ((sr+i)*6 + sc + i)
        WIN_MASKS.append(m)
for sr in range(2):
    for sc in range(4, 6):
        m = 0
        for i in range(5):
            m |= 1 << ((sr+i)*6 + sc - i)
        WIN_MASKS.append(m)

QUAD_ORIGIN = [(0,0),(0,3),(3,0),(3,3)]
QUAD_POS = []
QUAD_MASK = []
for (br,bc) in QUAD_ORIGIN:
    cells = []
    mask = 0
    for dr in range(3):
        for dc in range(3):
            p = (br+dr)*6 + bc + dc
            cells.append(p)
            mask |= 1 << p
    QUAD_POS.append(cells)
    QUAD_MASK.append(mask)

# ROT_PAIRS[q][di] list of (src,dst), di 0=L,1=R
ROT_PAIRS = []
for q,(br,bc) in enumerate(QUAD_ORIGIN):
    for di, dch in enumerate(['L','R']):
        pairs = []
        for lr in range(3):
            for lc in range(3):
                src = (br+lr)*6 + bc + lc
                if dch == 'R':
                    lr2, lc2 = lc, 2-lr
                else:
                    lr2, lc2 = 2-lc, lr
                dst = (br+lr2)*6 + bc + lc2
                pairs.append((src,dst))
        if len(ROT_PAIRS) <= q:
            ROT_PAIRS.append([])
        ROT_PAIRS[q].append(pairs)

# POS_ROT[idx][p] where idx=q*2+di
POS_ROT = [[0]*36 for _ in range(8)]
for q in range(4):
    br,bc = QUAD_ORIGIN[q]
    for di,dch in enumerate(['L','R']):
        idx = q*2+di
        mp = {}
        for (s,d) in ROT_PAIRS[q][di]:
            mp[s]=d
        for p in range(36):
            POS_ROT[idx][p] = mp.get(p, p)

CENTER_MASK = 0
for (r,c) in [(2,2),(2,3),(3,2),(3,3)]:
    CENTER_MASK |= 1 << (r*6+c)

WM = [0,1,12,130,6000,1000000]
WO = [0,2,25,320,15000,1000000]
INF = 10**9

def _pc(x):
    try:
        return x.bit_count()
    except AttributeError:
        return bin(x).count("1")

def _rotate_bits(bits, q, di):
    m = QUAD_MASK[q]
    if bits & m == 0:
        return bits
    res = bits & (~m)
    for s,d in ROT_PAIRS[q][di]:
        if (bits >> s) & 1:
            res |= 1 << d
    return res

def _eval_and_win(my, opp):
    my_win = False
    opp_win = False
    s = 0
    for m in WIN_MASKS:
        a = my & m
        if a:
            ca = _pc(a)
            # quick: if a==m then win (all 5 bits)
            if a == m:
                my_win = True
                # still need opp_win? check opp separately but can continue
                # evaluate as huge but terminal handled outside
            b = opp & m
            if b:
                if b == m:
                    opp_win = True
                continue  # blocked
            else:
                if ca == 5:
                    pass
                else:
                    s += WM[ca]
        else:
            b = opp & m
            if b:
                if b == m:
                    opp_win = True
                else:
                    s -= WO[_pc(b)]
    s += (_pc(my & CENTER_MASK) - _pc(opp & CENTER_MASK)) * 3
    return my_win, opp_win, s

def _has_win(bits):
    for m in WIN_MASKS:
        if (bits & m) == m:
            return True
    return False

class _Timeout(Exception):
    pass

def policy(you, opponent) -> str:
    start = time.time()
    deadline = start + 0.90
    try:
        my = 0
        opp = 0
        for r in range(6):
            yr = you[r]
            orr = opponent[r]
            for c in range(6):
                try:
                    yv = int(yr[c])
                except Exception:
                    yv = 0
                try:
                    ov = int(orr[c])
                except Exception:
                    ov = 0
                if yv == 1:
                    my |= 1 << (r*6+c)
                if ov == 1:
                    opp |= 1 << (r*6+c)
        occ = my | opp
        empties = [i for i in range(36) if not (occ >> i) & 1]
        if not empties:
            return "1,1,0,R"

        def check_deadline():
            if time.time() > deadline:
                raise _Timeout()

        # precompute rotated boards for root reuse
        # ---- immediate winning move ----
        my_rs0 = [0]*8
        opp_rs0 = [0]*8
        for q in range(4):
            for di in range(2):
                idx = q*2+di
                my_rs0[idx] = _rotate_bits(my, q, di)
                opp_rs0[idx] = _rotate_bits(opp, q, di)
        # order empties a bit central first for faster win find
        empties_sorted = sorted(empties, key=lambda p: (abs((p//6)-2.5)+abs((p%6)-2.5)))
        for pos in empties_sorted:
            r = pos // 6
            c = pos % 6
            for q in range(4):
                for di in range(2):
                    idx = q*2+di
                    pr = POS_ROT[idx][pos]
                    nm = my_rs0[idx] | (1 << pr)
                    no = opp_rs0[idx]
                    # fast win check
                    mw = _has_win(nm)
                    if mw:
                        ow = _has_win(no)
                        if not ow:
                            return f"{r+1},{c+1},{q},{'L' if di==0 else 'R'}"
            check_deadline() if len(empties) > 30 else None

        # fallback legal
        fr = empties[0] // 6 + 1
        fc = empties[0] % 6 + 1
        best_move = (empties[0]//6, empties[0]%6, 0, 1)
        best_str = f"{fr},{fc},0,R"

        # quick static ordering for root
        root_cands = []  # (score, pos,q,di,nm,no,mw,ow)
        for pos in empties:
            for q in range(4):
                for di in range(2):
                    idx = q*2+di
                    pr = POS_ROT[idx][pos]
                    nm = my_rs0[idx] | (1 << pr)
                    no = opp_rs0[idx]
                    mw, ow, sc = _eval_and_win(nm, no)
                    if mw and not ow:
                        # already handled above, shouldn't happen
                        return f"{pos//6+1},{pos%6+1},{q},{'L' if di==0 else 'R'}"
                    if ow and not mw:
                        sc = -INF + 1  # suicide, deprioritize
                        # keep but very low
                    root_cands.append((sc, pos, q, di, nm, no))
        root_cands.sort(key=lambda x: x[0], reverse=True)
        if root_cands:
            sc0, p0, q0, di0, _, _ = root_cands[0]
            best_move = (p0//6, p0%6, q0, di0)
            best_str = f"{p0//6+1},{p0%6+1},{q0},{'L' if di0==0 else 'R'}"

        # dedup rotations per pos for search width (keep best per board)
        # alpha-beta with fast generation
        nodes = [0]

        def alphabeta(cur_my, cur_opp, turn_max, depth, alpha, beta):
            nodes[0] += 1
            if nodes[0] & 127 == 0 and time.time() > deadline:
                raise _Timeout()
            if depth <= 0:
                _, _, sc = _eval_and_win(cur_my, cur_opp)
                return sc
            # rotated versions
            mrs = [0]*8
            ors = [0]*8
            for q in range(4):
                for di in range(2):
                    idx = q*2+di
                    mrs[idx] = _rotate_bits(cur_my, q, di)
                    ors[idx] = _rotate_bits(cur_opp, q, di)
            occ2 = cur_my | cur_opp
            em2 = [i for i in range(36) if not (occ2 >> i) & 1]
            if not em2:
                _, _, sc = _eval_and_win(cur_my, cur_opp)
                return sc
            if turn_max:
                # depth 1: just max eval
                if depth == 1:
                    best = -INF
                    for pos in em2:
                        for idx in range(8):
                            pr = POS_ROT[idx][pos]
                            nm = mrs[idx] | (1 << pr)
                            no = ors[idx]
                            mw, ow, sc = _eval_and_win(nm, no)
                            if mw and ow:
                                v = 0
                            elif mw:
                                return INF  # found win
                            elif ow:
                                v = -INF
                            else:
                                v = sc
                            if v > best:
                                best = v
                                if best >= beta:
                                    return best
                    return best
                # depth >1 : build candidates then recurse
                cands = []
                for pos in em2:
                    for idx in range(8):
                        pr = POS_ROT[idx][pos]
                        nm = mrs[idx] | (1 << pr)
                        no = ors[idx]
                        mw, ow, sc = _eval_and_win(nm, no)
                        if mw and ow:
                            cands.append((0, nm, no))
                        elif mw:
                            return INF
                        elif ow:
                            # suicide move, keep with very low score (still must consider if all suicide)
                            cands.append((-INF+1, nm, no))
                        else:
                            cands.append((sc, nm, no))
                # width limit
                lim = 25 if depth == 2 else (15 if depth == 3 else 10)
                if len(cands) > lim:
                    cands.sort(key=lambda x: x[0], reverse=True)
                    cands = cands[:lim]
                else:
                    cands.sort(key=lambda x: x[0], reverse=True)
                best = -INF
                for _, nm, no in cands:
                    v = alphabeta(nm, no, False, depth-1, alpha, beta)
                    if v > best:
                        best = v
                    if best >= beta:
                        return best
                    if best > alpha:
                        alpha = best
                return best
            else:
                if depth == 1:
                    best = INF
                    for pos in em2:
                        for idx in range(8):
                            pr = POS_ROT[idx][pos]
                            no = ors[idx] | (1 << pr)
                            nm = mrs[idx]
                            mw, ow, sc = _eval_and_win(nm, no)
                            if mw and ow:
                                v = 0
                            elif ow:
                                return -INF
                            elif mw:
                                v = INF
                            else:
                                v = sc
                            if v < best:
                                best = v
                                if best <= alpha:
                                    return best
                    return best
                cands = []
                for pos in em2:
                    for idx in range(8):
                        pr = POS_ROT[idx][pos]
                        no = ors[idx] | (1 << pr)
                        nm = mrs[idx]
                        mw, ow, sc = _eval_and_win(nm, no)
                        if mw and ow:
                            cands.append((0, nm, no))
                        elif ow:
                            return -INF
                        elif mw:
                            cands.append((INF-1, nm, no))
                        else:
                            cands.append((sc, nm, no))
                lim = 25 if depth == 2 else (15 if depth == 3 else 10)
                if len(cands) > lim:
                    cands.sort(key=lambda x: x[0])
                    cands = cands[:lim]
                else:
                    cands.sort(key=lambda x: x[0])
                best = INF
                for _, nm, no in cands:
                    v = alphabeta(nm, no, True, depth-1, alpha, beta)
                    if v < best:
                        best = v
                    if best <= alpha:
                        return best
                    if best < beta:
                        beta = best
                return best

        def root_search(depth, cands, alpha=-INF, beta=INF):
            best_v = -INF
            best_local = cands[0] if cands else None
            # optionally narrow root width for deep search
            use = cands
            if depth >= 3 and len(use) > 32:
                use = use[:32]
            if depth >= 4 and len(use) > 20:
                use = use[:20]
            for (sc, pos, q, di, nm, no) in use:
                if time.time() > deadline:
                    raise _Timeout()
                mw, ow, _ = _eval_and_win(nm, no)
                if mw and not ow:
                    return INF, (pos, q, di)
                if ow and not mw:
                    v = -INF
                elif depth-1 == 0:
                    v = sc
                else:
                    v = alphabeta(nm, no, False, depth-1, alpha, beta)
                if v > best_v:
                    best_v = v
                    best_local = (sc, pos, q, di, nm, no)
                    if best_v > alpha:
                        alpha = best_v
                    if best_v >= INF:
                        break
            if best_local is None:
                raise _Timeout()
            _, bp, bq, bdi, _, _ = best_local
            return best_v, (bp, bq, bdi)

        # iterative deepening
        try:
            # depth 2
            v2, mv2 = root_search(2, root_cands)
            best_move = (mv2[0]//6, mv2[0]%6, mv2[1], mv2[2])
            best_str = f"{mv2[0]//6+1},{mv2[0]%6+1},{mv2[1]},{'L' if mv2[2]==0 else 'R'}"
            if v2 >= INF//2:
                return best_str
            # depth 3 if time and board not too open
            if time.time() < deadline - 0.35:
                # reorder root by depth2? keep static order, already good
                v3, mv3 = root_search(3, root_cands)
                best_move = (mv3[0]//6, mv3[0]%6, mv3[1], mv3[2])
                best_str = f"{mv3[0]//6+1},{mv3[0]%6+1},{mv3[1]},{'L' if mv3[2]==0 else 'R'}"
                if v3 >= INF//2:
                    return best_str
                if time.time() < deadline - 0.25 and len(empties) < 16:
                    v4, mv4 = root_search(4, root_cands)
                    best_move = (mv4[0]//6, mv4[0]%6, mv4[1], mv4[2])
                    best_str = f"{mv4[0]//6+1},{mv4[0]%6+1},{mv4[1]},{'L' if mv4[2]==0 else 'R'}"
        except _Timeout:
            pass
        return best_str
    except Exception:
        try:
            for r in range(6):
                for c in range(6):
                    if you[r][c] == 0 and opponent[r][c] == 0:
                        return f"{r+1},{c+1},0,R"
        except Exception:
            pass
        return "1,1,0,R"
