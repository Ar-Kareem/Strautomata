
_LINES = []
for r in range(6):
    for c in range(2):
        m = 0
        for i in range(5): m |= 1 << (r*6 + c+i)
        _LINES.append(m)
for c in range(6):
    for r in range(2):
        m = 0
        for i in range(5): m |= 1 << ((r+i)*6 + c)
        _LINES.append(m)
for r in range(2):
    for c in range(2):
        m = 0
        for i in range(5): m |= 1 << ((r+i)*6 + c+i)
        _LINES.append(m)
for r in range(2):
    for c in range(4, 6):
        m = 0
        for i in range(5): m |= 1 << ((r+i)*6 + c-i)
        _LINES.append(m)

_QUAD_MASK = [0]*4
_ROT_PERM = {}
_ROT_POS = {}
for q in range(4):
    r0 = 3*(q//2); c0 = 3*(q%2)
    qm = 0; pr = []; pl = []
    for i in range(3):
        for j in range(3):
            src = (r0+i)*6 + (c0+j)
            qm |= 1 << src
            pr.append((src, (r0+j)*6 + (c0+2-i)))
            pl.append((src, (r0+2-j)*6 + (c0+i)))
    _QUAD_MASK[q] = qm
    _ROT_PERM[(q,'R')] = pr
    _ROT_PERM[(q,'L')] = pl
for q in range(4):
    for d in ('L','R'):
        mp = list(range(36))
        for src,dst in _ROT_PERM[(q,d)]: mp[src] = dst
        _ROT_POS[(q,d)] = mp

_FULL = (1<<36)-1
_VALS = [0,1,8,64,512,100000]

def _rotate(bits, q, d):
    nb = bits & ~_QUAD_MASK[q]
    for src,dst in _ROT_PERM[(q,d)]:
        if bits & (1<<src): nb |= 1<<dst
    return nb

def _has_win(bits):
    for lm in _LINES:
        if (bits & lm) == lm: return True
    return False

def _evaluate(m, o):
    s = 0
    for lm in _LINES:
        mx = m & lm; ox = o & lm
        if mx and ox: continue
        if mx: s += _VALS[bin(mx).count('1')]
        elif ox: s -= _VALS[bin(ox).count('1')]
    return s

def policy(you, opponent):
    me = 0; op = 0
    for r in range(6):
        for c in range(6):
            if you[r][c]: me |= 1 << (r*6+c)
            if opponent[r][c]: op |= 1 << (r*6+c)
    empty = _FULL & ~(me|op)
    legal_pos = [p for p in range(36) if empty & (1<<p)]
    draw_moves = []; candidates = []; suicide = []
    for pos in legal_pos:
        r, c = pos//6, pos%6; bit = 1<<pos
        for q in range(4):
            for d in ('L','R'):
                m2 = _rotate(me|bit, q, d)
                o2 = _rotate(op, q, d)
                iw = _has_win(m2); ow = _has_win(o2)
                if iw and not ow:
                    return f"{r+1},{c+1},{q},{d}"
                if iw and ow:
                    draw_moves.append((r,c,q,d)); continue
                if ow:
                    suicide.append((r,c,q,d)); continue
                candidates.append((r,c,q,d,m2,o2))
    if not candidates:
        if draw_moves:
            r,c,q,d = draw_moves[0]; return f"{r+1},{c+1},{q},{d}"
        if suicide:
            r,c,q,d = suicide[0]; return f"{r+1},{c+1},{q},{d}"
        p = legal_pos[0]; return f"{p//6+1},{p%6+1},0,R"
    safe = []; unsafe = []
    for (r,c,q,d,m2,o2) in candidates:
        opp_win = False
        oe = _FULL & ~(m2|o2)
        for qq in range(4):
            if opp_win: break
            for dd in ('L','R'):
                rot_o = _rotate(o2, qq, dd)
                rot_m = _rotate(m2, qq, dd)
                mw = _has_win(rot_m)
                rp = _ROT_POS[(qq,dd)]
                eb = oe
                while eb:
                    low = eb & -eb
                    p = low.bit_length() - 1
                    eb ^= low
                    o3 = rot_o | (1 << rp[p])
                    if _has_win(o3) and not mw:
                        opp_win = True; break
                if opp_win: break
        sc = _evaluate(m2, o2)
        if opp_win: unsafe.append((sc,r,c,q,d))
        else: safe.append((sc,r,c,q,d))
    pool = safe if safe else unsafe
    pool.sort(key=lambda x: -x[0])
    _, r, c, q, d = pool[0]
    return f"{r+1},{c+1},{q},{d}"
