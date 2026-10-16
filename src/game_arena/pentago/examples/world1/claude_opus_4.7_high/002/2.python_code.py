
import time

QUADS = [(0,0),(0,3),(3,0),(3,3)]

QUAD_MASKS = []
for qr, qc in QUADS:
    m = 0
    for lr in range(3):
        for lc in range(3):
            m |= 1 << ((qr+lr)*6 + qc+lc)
    QUAD_MASKS.append(m)

ROT_PAIRS = [[[], []] for _ in range(4)]
for q in range(4):
    qr, qc = QUADS[q]
    for di, d in enumerate(['L','R']):
        pairs = []
        for lr in range(3):
            for lc in range(3):
                if d == 'R':
                    nlr, nlc = lc, 2-lr
                else:
                    nlr, nlc = 2-lc, lr
                src = (qr+lr)*6 + qc+lc
                dst = (qr+nlr)*6 + qc+nlc
                pairs.append((1 << src, 1 << dst))
        ROT_PAIRS[q][di] = pairs

WIN_MASKS = []
for r in range(6):
    for c in range(2):
        m = 0
        for k in range(5): m |= 1 << (r*6 + c+k)
        WIN_MASKS.append(m)
for c in range(6):
    for r in range(2):
        m = 0
        for k in range(5): m |= 1 << ((r+k)*6 + c)
        WIN_MASKS.append(m)
for r in range(2):
    for c in range(2):
        m = 0
        for k in range(5): m |= 1 << ((r+k)*6 + c+k)
        WIN_MASKS.append(m)
for r in range(2):
    for c in range(4, 6):
        m = 0
        for k in range(5): m |= 1 << ((r+k)*6 + c-k)
        WIN_MASKS.append(m)
WIN_MASKS = tuple(WIN_MASKS)

DIRS = ('L', 'R')
VALS = (0, 1, 5, 25, 125, 10000)

def rotate(board, q, di):
    qmask = QUAD_MASKS[q]
    nb = board & ~qmask
    for sbit, dbit in ROT_PAIRS[q][di]:
        if board & sbit:
            nb |= dbit
    return nb

def has_win(board):
    for m in WIN_MASKS:
        if (board & m) == m:
            return True
    return False

def eval_board(my, op):
    score = 0
    for m in WIN_MASKS:
        mc = bin(my & m).count('1')
        oc = bin(op & m).count('1')
        if oc == 0 and mc > 0:
            score += VALS[mc]
        elif mc == 0 and oc > 0:
            score -= VALS[oc]
    return score

def policy(you, opponent):
    start = time.time()
    TIME_LIMIT = 0.85
    my = 0; op = 0
    for r in range(6):
        for c in range(6):
            if you[r][c]: my |= 1 << (r*6+c)
            if opponent[r][c]: op |= 1 << (r*6+c)
    occupied = my | op
    empty = [i for i in range(36) if not ((occupied >> i) & 1)]
    candidates = []
    draw_moves = []
    losing_moves = []
    any_move = None
    for cell in empty:
        cbit = 1 << cell
        m1 = my | cbit
        rL = cell // 6 + 1
        cL = cell % 6 + 1
        for q in range(4):
            for di in range(2):
                nm = rotate(m1, q, di)
                no_ = rotate(op, q, di)
                mw = has_win(nm); ow = has_win(no_)
                ms = f"{rL},{cL},{q},{DIRS[di]}"
                if any_move is None: any_move = ms
                if mw and not ow: return ms
                if mw and ow: draw_moves.append(ms); continue
                if ow and not mw: losing_moves.append(ms); continue
                prelim = eval_board(nm, no_)
                candidates.append((prelim, ms, nm, no_))
    if not candidates:
        if draw_moves: return draw_moves[0]
        if losing_moves: return losing_moves[0]
        return any_move
    candidates.sort(key=lambda x: -x[0])
    first_safe = None
    checked_all = True
    for prelim, ms, nm, no_ in candidates:
        if time.time() - start > TIME_LIMIT:
            checked_all = False
            break
        opp_can_win = False
        opp_occ = nm | no_
        for ocell in range(36):
            if (opp_occ >> ocell) & 1: continue
            obit = 1 << ocell
            o1 = no_ | obit
            for oq in range(4):
                for odi in range(2):
                    nm2 = rotate(nm, oq, odi)
                    no2 = rotate(o1, oq, odi)
                    if has_win(no2) and not has_win(nm2):
                        opp_can_win = True; break
                if opp_can_win: break
            if opp_can_win: break
        if not opp_can_win:
            first_safe = ms
            break
    if first_safe: return first_safe
    if checked_all and draw_moves: return draw_moves[0]
    return candidates[0][1]
