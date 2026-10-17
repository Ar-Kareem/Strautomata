
def policy(you, opponent):
    my_b = op_b = 0
    for r in range(6):
        for c in range(6):
            b = r * 6 + c
            if you[r][c]: my_b |= 1 << b
            if opponent[r][c]: op_b |= 1 << b

    LINES = []
    for r in range(6):
        for s in range(2):
            LINES.append(sum(1 << (r*6+s+i) for i in range(5)))
    for c in range(6):
        for s in range(2):
            LINES.append(sum(1 << ((s+i)*6+c) for i in range(5)))
    for s in range(2):
        for t in range(2):
            LINES.append(sum(1 << ((s+i)*6+t+i) for i in range(5)))
    for s in range(2):
        for t in range(4, 6):
            LINES.append(sum(1 << ((s+i)*6+t-i) for i in range(5)))

    ROTS = []
    for q in range(4):
        r0, c0 = (q >> 1) * 3, (q & 1) * 3
        qm = 0
        for dr in range(3):
            for dc in range(3):
                qm |= 1 << ((r0+dr)*6+c0+dc)
        for d in ('L', 'R'):
            mp = []
            for dr in range(3):
                for dc in range(3):
                    sb = 1 << ((r0+dr)*6+c0+dc)
                    tb = 1 << ((r0+dc)*6+c0+2-dr) if d == 'R' else 1 << ((r0+2-dc)*6+c0+dr)
                    mp.append((sb, tb))
            ROTS.append((q, d, qm, mp))

    def rot(bits, ri):
        _, _, qm, mp = ROTS[ri]
        r = bits & ~qm
        for s, t in mp:
            if bits & s: r |= t
        return r

    def wins(b):
        for m in LINES:
            if b & m == m: return True
        return False

    W = [0, 1, 15, 200, 50000]
    WO = [0, 2, 20, 400, 80000]

    def ev(mb, ob):
        sc = m4 = o4 = 0
        for m in LINES:
            mv = mb & m; ov = ob & m
            if not ov and mv:
                c = bin(mv).count('1')
                sc += W[c]; m4 += (c >= 4)
            elif not mv and ov:
                c = bin(ov).count('1')
                sc -= WO[c]; o4 += (c >= 4)
        if m4 >= 2: sc += 200000
        if o4 >= 2: sc -= 300000
        return sc

    occ = my_b | op_b
    empty = [i for i in range(36) if not (occ >> i & 1)]

    moves = []
    for bit in empty:
        nm = my_b | (1 << bit)
        for ri in range(8):
            nmr = rot(nm, ri)
            nor = rot(op_b, ri)
            mw = wins(nmr)
            ow = wins(nor)
            if mw and not ow:
                q, d = ROTS[ri][0], ROTS[ri][1]
                return f"{bit//6+1},{bit%6+1},{q},{d}"
            if ow and not mw: sc = -5000000
            elif mw and ow: sc = 100000
            else: sc = ev(nmr, nor)
            moves.append((sc, bit, ri, nmr, nor))

    moves.sort(reverse=True, key=lambda x: x[0])

    def opp_can_win(nmr, nor):
        oc2 = nmr | nor
        for b2 in range(36):
            if (oc2 >> b2) & 1: continue
            no2 = nor | (1 << b2)
            for ri2 in range(8):
                nor2 = rot(no2, ri2)
                if wins(nor2):
                    if not wins(rot(nmr, ri2)):
                        return True
        return False

    nc = min(20, len(moves))
    for i in range(nc):
        sc, bit, ri, nmr, nor = moves[i]
        if sc <= -4000000: break
        if not opp_can_win(nmr, nor):
            q, d = ROTS[ri][0], ROTS[ri][1]
            return f"{bit//6+1},{bit%6+1},{q},{d}"
        moves[i] = (sc - 2000000, moves[i][1], moves[i][2], moves[i][3], moves[i][4])

    moves.sort(reverse=True, key=lambda x: x[0])
    _, bit, ri, _, _ = moves[0]
    q, d = ROTS[ri][0], ROTS[ri][1]
    return f"{bit//6+1},{bit%6+1},{q},{d}"
