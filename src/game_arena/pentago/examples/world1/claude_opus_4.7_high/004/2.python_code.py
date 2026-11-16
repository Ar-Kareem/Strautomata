
import time

_LINES = []
for r in range(6):
    for c in range(2):
        m = 0
        for i in range(5):
            m |= 1 << (r * 6 + c + i)
        _LINES.append(m)
for c in range(6):
    for r in range(2):
        m = 0
        for i in range(5):
            m |= 1 << ((r + i) * 6 + c)
        _LINES.append(m)
for r in range(6):
    for c in range(6):
        if r + 4 < 6 and c + 4 < 6:
            m = 0
            for i in range(5):
                m |= 1 << ((r + i) * 6 + c + i)
            _LINES.append(m)
        if r + 4 < 6 and c - 4 >= 0:
            m = 0
            for i in range(5):
                m |= 1 << ((r + i) * 6 + c - i)
            _LINES.append(m)
_LINES = tuple(_LINES)

_QUAD_MASK = []
_QUAD_BASE = []
for q in range(4):
    qr = (q // 2) * 3
    qc = (q % 2) * 3
    m = 0
    for r in range(3):
        for c in range(3):
            m |= 1 << ((qr + r) * 6 + (qc + c))
    _QUAD_MASK.append(m)
    _QUAD_BASE.append(qr * 6 + qc)

_ROT_LUT = {}
for q in range(4):
    qr = (q // 2) * 3
    qc = (q % 2) * 3
    for d in ('L', 'R'):
        lut = [0] * 512
        for state in range(512):
            rot = 0
            for i in range(9):
                if (state >> i) & 1:
                    lr, lc = i // 3, i % 3
                    if d == 'R':
                        nr, nc = lc, 2 - lr
                    else:
                        nr, nc = 2 - lc, lr
                    rot |= 1 << ((qr + nr) * 6 + (qc + nc))
            lut[state] = rot
        _ROT_LUT[(q, d)] = lut

_MOVES = tuple((q, d, _QUAD_BASE[q], _QUAD_MASK[q], _ROT_LUT[(q, d)])
               for q in range(4) for d in ('L', 'R'))

def _rot(board, base, qmask, lut):
    local = ((board >> base) & 7) | (((board >> (base + 6)) & 7) << 3) | (((board >> (base + 12)) & 7) << 6)
    return (board & ~qmask) | lut[local]

def _has_win(board):
    for line in _LINES:
        if (board & line) == line:
            return True
    return False

_SCORES = (0, 1, 8, 64, 512, 100000)

def _evaluate(me, opp):
    score = 0
    for line in _LINES:
        mm = me & line
        oo = opp & line
        if mm:
            if not oo:
                score += _SCORES[bin(mm).count('1')]
        elif oo:
            score -= _SCORES[bin(oo).count('1')]
    return score

_WIN = 1000000

def policy(you, opponent):
    me = 0
    opp = 0
    for r in range(6):
        ry = you[r]
        ro = opponent[r]
        for c in range(6):
            if ry[c]:
                me |= 1 << (r * 6 + c)
            elif ro[c]:
                opp |= 1 << (r * 6 + c)

    occupied = me | opp
    empties = [i for i in range(36) if not ((occupied >> i) & 1)]

    start = time.time()
    limit = 0.85

    my_moves = []
    for pos in empties:
        pb = 1 << pos
        mep = me | pb
        for q, d, base, qmask, lut in _MOVES:
            nm = _rot(mep, base, qmask, lut)
            no = _rot(opp, base, qmask, lut)
            mw = _has_win(nm)
            ow = _has_win(no)

            if mw and not ow:
                return "{},{},{},{}".format(pos // 6 + 1, pos % 6 + 1, q, d)

            if ow and not mw:
                my_moves.append((-_WIN, pos, q, d, nm, no, 'lose'))
            elif mw and ow:
                my_moves.append((0, pos, q, d, nm, no, 'draw'))
            else:
                ev = _evaluate(nm, no)
                my_moves.append((ev, pos, q, d, nm, no, 'normal'))

    my_moves.sort(key=lambda x: -x[0])

    best_move = None
    best_score = -_WIN * 2

    for ev, pos, q, d, nm, no, tp in my_moves:
        if best_move is not None and time.time() - start > limit:
            break

        if tp == 'lose':
            worst = -_WIN
        elif tp == 'draw':
            worst = 0
        else:
            occ2 = nm | no
            worst = _WIN * 2
            cut = False
            for opos in range(36):
                if (occ2 >> opos) & 1:
                    continue
                if cut:
                    break
                opb = 1 << opos
                opp_p = no | opb
                for oq, od, obase, oqmask, olut in _MOVES:
                    ono = _rot(opp_p, obase, oqmask, olut)
                    onm = _rot(nm, obase, oqmask, olut)
                    ow2 = _has_win(ono)
                    mw2 = _has_win(onm)
                    if ow2 and not mw2:
                        s = -_WIN
                    elif mw2 and not ow2:
                        s = _WIN
                    elif mw2 and ow2:
                        s = 0
                    else:
                        s = _evaluate(onm, ono)
                    if s < worst:
                        worst = s
                        if worst <= best_score:
                            cut = True
                            break

        if worst > best_score:
            best_score = worst
            best_move = (pos, q, d)

    if best_move is None:
        if my_moves:
            _, pos, q, d, _, _, _ = my_moves[0]
        else:
            pos = empties[0]
            q, d = 0, 'R'
    else:
        pos, q, d = best_move

    return "{},{},{},{}".format(pos // 6 + 1, pos % 6 + 1, q, d)
