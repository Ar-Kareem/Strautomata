
import time

_QUAD_ORIGINS = [(0,0),(0,3),(3,0),(3,3)]
_QUAD_CELLS = []
_QUAD_MASK = []
for (r0,c0) in _QUAD_ORIGINS:
    cells = []
    mask = 0
    for i in range(3):
        for j in range(3):
            r = r0+i
            c = c0+j
            idx = r*6+c
            cells.append(idx)
            mask |= (1<<idx)
    _QUAD_CELLS.append(cells)
    _QUAD_MASK.append(mask)

_ROT_R = []
_ROT_L = []
for q in range(4):
    cells = _QUAD_CELLS[q]
    pr = []
    pl = []
    for i in range(3):
        for j in range(3):
            old = cells[i*3+j]
            newR = cells[j*3+(2-i)]
            newL = cells[(2-j)*3+i]
            pr.append((old,newR))
            pl.append((old,newL))
    _ROT_R.append(pr)
    _ROT_L.append(pl)

_WIN_MASKS = []
for r in range(6):
    for c in (0,1):
        m=0
        for k in range(5):
            m|=(1<<((r)*6+(c+k)))
        _WIN_MASKS.append(m)
for c in range(6):
    for r in (0,1):
        m=0
        for k in range(5):
            m|=(1<<((r+k)*6+c))
        _WIN_MASKS.append(m)
for r in (0,1):
    for c in (0,1):
        m=0
        for k in range(5):
            m|=(1<<((r+k)*6+(c+k)))
        _WIN_MASKS.append(m)
for r in (0,1):
    for c in (4,5):
        m=0
        for k in range(5):
            m|=(1<<((r+k)*6+(c-k)))
        _WIN_MASKS.append(m)

_W_MY = [0,1,10,100,1000,1000000]
_W_OPP = [0,2,20,200,2000,1000000]
_HAS_BC = hasattr(int,"bit_count")

def _pop(x):
    if _HAS_BC:
        return x.bit_count()
    return bin(x).count("1")

def policy(you, opponent) -> str:
    import time as _time
    t0 = _time.perf_counter()
    LIM = 0.90

    def timed_out():
        return (_time.perf_counter()-t0) > LIM

    # convert to bitboards
    my = 0
    opp = 0
    try:
        for r in range(6):
            yr = you[r]
            opr = opponent[r]
            for c in range(6):
                v1 = yr[c]
                if v1==1:
                    my |= (1<<(r*6+c))
                else:
                    try:
                        v2 = opr[c]
                    except Exception:
                        v2 = 0
                    if v2==1:
                        opp |= (1<<(r*6+c))
    except Exception:
        pass

    occ = my | opp
    empties = [i for i in range(36) if ((occ>>i)&1)==0]
    if not empties:
        return "1,1,0,R"

    WIN = _WIN_MASKS
    QM = _QUAD_MASK
    RR = _ROT_R
    RL = _ROT_L
    WMY = _W_MY
    WOP = _W_OPP

    def rotate_bits(bits, q, isR):
        mask = QM[q]
        qbits = bits & mask
        if qbits==0:
            return bits
        pairs = RR[q] if isR else RL[q]
        nq = 0
        # 9 iterations
        for old,new in pairs:
            if (bits>>old)&1:
                nq |= (1<<new)
        return (bits & (~mask)) | nq

    def apply_move(bmy, bopp, idx, q, isR, to_my):
        if to_my:
            bmy |= (1<<idx)
        else:
            bopp |= (1<<idx)
        bmy = rotate_bits(bmy,q,isR)
        bopp = rotate_bits(bopp,q,isR)
        return bmy,bopp

    def wins(bmy,bopp):
        mw=False
        ow=False
        for m in WIN:
            if not mw and (bmy & m)==m:
                mw=True
            if not ow and (bopp & m)==m:
                ow=True
            if mw and ow:
                break
        return mw,ow

    def evaluate(bmy,bopp):
        s=0
        for m in WIN:
            a = bmy & m
            if a:
                if bopp & m:
                    continue
                s += WMY[_pop(a)]
            else:
                b = bopp & m
                if b==0:
                    continue
                s -= WOP[_pop(b)]
        return s

    def opp_has_win(bmy,bopp,emp):
        # True if opponent to move can win immediately
        for idx in emp:
            bit = (1<<idx)
            for q in range(4):
                for isR in (True,False):
                    nmy,nopp = apply_move(bmy,bopp,idx,q,isR,False)
                    # quick win check
                    ow=False
                    mw=False
                    for m in WIN:
                        if not ow and (nopp & m)==m:
                            ow=True
                        if not mw and (nmy & m)==m:
                            mw=True
                            if ow:
                                break
                        if ow and mw:
                            break
                    if ow and not mw:
                        return True
                    if timed_out():
                        return False
        return False

    def my_has_win(bmy,bopp,emp):
        for idx in emp:
            for q in range(4):
                for isR in (True,False):
                    nmy,nopp = apply_move(bmy,bopp,idx,q,isR,True)
                    mw=False
                    ow=False
                    for m in WIN:
                        if not mw and (nmy & m)==m:
                            mw=True
                        if not ow and (nopp & m)==m:
                            ow=True
                            if mw:
                                break
                        if mw and ow:
                            break
                    if mw and not ow:
                        return True
        return False

    # fallback move
    fb_idx = empties[0]
    fb_str = f"{fb_idx//6+1},{fb_idx%6+1},0,R"

    try:
        # 1) immediate winning move
        for idx in empties:
            for q in range(4):
                for isR in (True,False):
                    nmy,nopp = apply_move(my,opp,idx,q,isR,True)
                    mw,ow = wins(nmy,nopp)
                    if mw and not ow:
                        d = 'R' if isR else 'L'
                        return f"{idx//6+1},{idx%6+1},{q},{d}"
                    if timed_out():
                        break
                if timed_out():
                    break
            if timed_out():
                break

        # 2) score all moves by evaluation (filter suicides)
        scored = []  # (score, idx,q,isR,nmy,nopp,emp1)
        for idx in empties:
            for q in range(4):
                for isR in (True,False):
                    nmy,nopp = apply_move(my,opp,idx,q,isR,True)
                    mw,ow = wins(nmy,nopp)
                    if ow and not mw:
                        # suicide immediate loss
                        scored.append((-10**12,idx,q,isR,nmy,nopp,None))
                    elif mw and ow:
                        # draw after move
                        scored.append((-50000,idx,q,isR,nmy,nopp,None))
                    else:
                        sc = evaluate(nmy,nopp)
                        # empties after move
                        # compute quickly: remove idx
                        # build emp1 list
                        # occ1 = nmy|nopp ; derive
                        scored.append((sc,idx,q,isR,nmy,nopp,None))
                    if timed_out():
                        break
                if timed_out():
                    break
            if timed_out():
                break
        if not scored:
            return fb_str
        scored.sort(key=lambda x: x[0], reverse=True)
        # update fallback to best scored
        b = scored[0]
        fb_str = f"{b[1]//6+1},{b[1]%6+1},{b[2]},{'R' if b[3] else 'L'}"
        if timed_out():
            return fb_str

        # 3) filter safe moves (opponent cannot win immediately)
        safe = []
        losing = []
        for sc,idx,q,isR,nmy,nopp,_ in scored:
            if sc <= -10**11:
                losing.append((sc,idx,q,isR,nmy,nopp))
                continue
            occ1 = nmy|nopp
            emp1 = [i for i in range(36) if ((occ1>>i)&1)==0]
            if opp_has_win(nmy,nopp,emp1):
                losing.append((sc-1000000,idx,q,isR,nmy,nopp))
            else:
                safe.append((sc,idx,q,isR,nmy,nopp,emp1))
            if timed_out():
                break
        if not safe:
            # all losing, return best scored (delay)
            scored.sort(key=lambda x: x[0], reverse=True)
            b = scored[0]
            return f"{b[1]//6+1},{b[1]%6+1},{b[2]},{'R' if b[3] else 'L'}"
        if timed_out():
            b = safe[0]
            return f"{b[1]//6+1},{b[1]%6+1},{b[2]},{'R' if b[3] else 'L'}"

        # limit safe breadth for deeper search
        # keep top by heuristic
        safe_sorted = sorted(safe, key=lambda x: x[0], reverse=True)
        top_safe = safe_sorted[:14] if len(safe_sorted)>14 else safe_sorted

        # 4) check forced win in 2 for very top moves (if time)
        # only if few empties or enough time
        if (_time.perf_counter()-t0) < 0.55:
            cand_force = top_safe[:6]
            for sc,idx,q,isR,nmy,nopp,emp1 in cand_force:
                if timed_out():
                    break
                forced = True
                # for every opp reply, I must have immediate win
                for oidx in emp1:
                    if not forced:
                        break
                    for oq in range(4):
                        if not forced:
                            break
                        for oisR in (True,False):
                            nmy2,nopp2 = apply_move(nmy,nopp,oidx,oq,oisR,False)
                            mw2,ow2 = wins(nmy2,nopp2)
                            if ow2 and not mw2:
                                # should not happen (safe filtered) but if happens, not forced win
                                forced=False
                                break
                            if mw2 and not ow2:
                                # opponent suicide, skip (good for us)
                                continue
                            if mw2 and ow2:
                                # draw, opponent would prefer over loss? not forced win
                                forced=False
                                break
                            occ2 = nmy2|nopp2
                            emp2 = [i for i in range(36) if ((occ2>>i)&1)==0]
                            if not my_has_win(nmy2,nopp2,emp2):
                                forced=False
                                break
                            if timed_out():
                                forced=False
                                break
                if forced:
                    return f"{idx//6+1},{idx%6+1},{q},{'R' if isR else 'L'}"

        # 5) min-eval (opponent best reply) ranking
        best_val = -10**18
        best_move = top_safe[0]
        for sc,idx,q,isR,nmy,nopp,emp1 in top_safe:
            if timed_out():
                break
            # opponent minimizes evaluation
            minv = 10**18
            # iterate opp moves
            for oidx in emp1:
                for oq in range(4):
                    for oisR in (True,False):
                        nmy2,nopp2 = apply_move(nmy,nopp,oidx,oq,oisR,False)
                        # wins already filtered for immediate opp win, but check suicide giving me win -> ignore (high)
                        # fast eval
                        v = evaluate(nmy2,nopp2)
                        if v < minv:
                            minv = v
                            # alpha prune: if minv already worse than best_val, no need to continue?
                            # opponent will push low, so if minv < best_val we can prune this root
                            if minv < best_val:
                                break
                    if minv < best_val:
                        break
                if minv < best_val:
                    break
                if timed_out():
                    break
            # combine with own heuristic slightly to prefer central/attacking when equal
            combined = minv*1.0 + sc*0.15
            if combined > best_val:
                best_val = combined
                best_move = (sc,idx,q,isR,nmy,nopp,emp1)
        b = best_move
        return f"{b[1]//6+1},{b[1]%6+1},{b[2]},{'R' if b[3] else 'L'}"
    except Exception:
        pass
    # ultimate fallback: first empty legal
    try:
        occ2 = my|opp
        for i in range(36):
            if ((occ2>>i)&1)==0:
                return f"{i//6+1},{i%6+1},0,R"
    except Exception:
        pass
    return fb_str
