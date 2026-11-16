
import time

# Precompute winning line masks (5-in-a-row on 6x6)
_WIN_MASKS = []
for r in range(6):
    for c in range(2):
        m = 0
        for i in range(5): m |= 1 << (r*6 + c+i)
        _WIN_MASKS.append(m)
for c in range(6):
    for r in range(2):
        m = 0
        for i in range(5): m |= 1 << ((r+i)*6 + c)
        _WIN_MASKS.append(m)
for r in range(2):
    for c in range(2):
        m = 0
        for i in range(5): m |= 1 << ((r+i)*6 + c+i)
        _WIN_MASKS.append(m)
for r in range(2):
    for c in range(4, 6):
        m = 0
        for i in range(5): m |= 1 << ((r+i)*6 + c-i)
        _WIN_MASKS.append(m)
_WIN_MASKS = tuple(_WIN_MASKS)

_QUAD_MASK = [0, 0, 0, 0]
for q in range(4):
    r0 = (q // 2) * 3; c0 = (q % 2) * 3
    for i in range(3):
        for j in range(3):
            _QUAD_MASK[q] |= 1 << ((r0+i)*6 + (c0+j))
_QUAD_MASK = tuple(_QUAD_MASK)

_ROT_L = [None]*4
_ROT_R = [None]*4
for q in range(4):
    r0 = (q // 2) * 3; c0 = (q % 2) * 3
    mL = []; mR = []
    for i in range(3):
        for j in range(3):
            old = (r0+i)*6 + (c0+j)
            nR = (r0+j)*6 + (c0+2-i)
            nL = (r0+2-j)*6 + (c0+i)
            mR.append((old, nR))
            mL.append((old, nL))
    _ROT_L[q] = tuple(mL)
    _ROT_R[q] = tuple(mR)

def _popcount(x):
    return bin(x).count('1')

def rotate_bb(bb, q, d):
    qmask = _QUAD_MASK[q]
    result = bb & ~qmask
    rot = _ROT_L[q] if d == 0 else _ROT_R[q]
    for old, new in rot:
        if bb >> old & 1:
            result |= 1 << new
    return result

def has_win(bb):
    for m in _WIN_MASKS:
        if (bb & m) == m:
            return True
    return False

_WEIGHTS = (0, 1, 5, 25, 125, 10000)

def evaluate(my_bb, op_bb):
    score = 0
    for m in _WIN_MASKS:
        ma = my_bb & m
        oa = op_bb & m
        if ma and not oa:
            score += _WEIGHTS[_popcount(ma)]
        elif oa and not ma:
            score -= _WEIGHTS[_popcount(oa)]
    return score

def generate_moves(my_bb, op_bb):
    occupied = my_bb | op_bb
    moves = []
    for bit in range(36):
        if occupied >> bit & 1:
            continue
        r = bit // 6; c = bit % 6
        placed = my_bb | (1 << bit)
        for q in range(4):
            for d in (0, 1):
                nmy = rotate_bb(placed, q, d)
                nop = rotate_bb(op_bb, q, d)
                moves.append((r, c, q, d, nmy, nop))
    return moves

def _fmt(mv):
    r, c, q, d, _, _ = mv
    return str(r+1) + "," + str(c+1) + "," + str(q) + "," + ("L" if d == 0 else "R")

def policy(you, opponent):
    start = time.time()
    deadline = start + 0.85
    
    my_bb = 0
    op_bb = 0
    for r in range(6):
        for c in range(6):
            if you[r][c]:
                my_bb |= 1 << (r*6+c)
            if opponent[r][c]:
                op_bb |= 1 << (r*6+c)
    
    moves = generate_moves(my_bb, op_bb)
    if not moves:
        return "1,1,0,R"
    
    WIN = 1_000_000
    LOSS = -1_000_000
    
    scored = []
    for mv in moves:
        r, c, q, d, nmy, nop = mv
        mw = has_win(nmy)
        ow = has_win(nop)
        if mw and not ow:
            return _fmt(mv)
        if mw and ow:
            s = -500  # draw, slightly bad
        elif ow:
            s = LOSS
        else:
            s = evaluate(nmy, nop)
        scored.append((s, mv))
    
    scored.sort(reverse=True, key=lambda x: x[0])
    
    best_score = -10**18
    best_move = scored[0][1]
    
    K = 40
    for idx, (init_s, mv) in enumerate(scored):
        if idx >= K:
            break
        if time.time() > deadline:
            break
        r, c, q, d, nmy, nop = mv
        
        if init_s <= LOSS:
            score = LOSS
        else:
            mw = has_win(nmy); ow = has_win(nop)
            if mw and ow:
                score = -500
            else:
                opp_moves = generate_moves(nop, nmy)
                worst = 10**18
                for omv in opp_moves:
                    _, _, _, _, nnop, nnmy = omv
                    ow2 = has_win(nnop)
                    mw2 = has_win(nnmy)
                    if ow2 and not mw2:
                        worst = LOSS
                        break
                    elif mw2 and not ow2:
                        s2 = WIN
                    elif mw2 and ow2:
                        s2 = -500
                    else:
                        s2 = evaluate(nnmy, nnop)
                    if s2 < worst:
                        worst = s2
                score = worst
        
        if score > best_score:
            best_score = score
            best_move = mv
            if score >= WIN:
                break
    
    return _fmt(best_move)
