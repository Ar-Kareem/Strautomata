
import time

QUADS = [(0,0),(0,3),(3,0),(3,3)]
TOTAL_MASK = (1 << 36) - 1

def _build():
    qmasks = [0]*4
    qmasks_inv = [0]*4
    rot_tables = [[None,None] for _ in range(4)]
    pack_shifts = []
    new_pos = [[[0]*2 for _ in range(4)] for _ in range(36)]
    for q,(r0,c0) in enumerate(QUADS):
        mask = 0
        for i in range(3):
            for j in range(3):
                mask |= 1 << ((r0+i)*6 + (c0+j))
        qmasks[q] = mask
        qmasks_inv[q] = TOTAL_MASK ^ mask
        pack_shifts.append(r0*6+c0)
        for d_idx, direction in enumerate(['L','R']):
            dst_map = []
            for i in range(3):
                for j in range(3):
                    if direction == 'R':
                        dr, dc = j, 2-i
                    else:
                        dr, dc = 2-j, i
                    dst_map.append((r0+dr)*6 + (c0+dc))
            table = [0]*512
            for bits in range(512):
                out = 0
                for k in range(9):
                    if bits & (1<<k):
                        out |= 1 << dst_map[k]
                table[bits] = out
            rot_tables[q][d_idx] = table
    for pos in range(36):
        r, c = pos // 6, pos % 6
        for q,(r0,c0) in enumerate(QUADS):
            for d_idx, direction in enumerate(['L','R']):
                if r0 <= r < r0+3 and c0 <= c < c0+3:
                    i, j = r-r0, c-c0
                    if direction == 'R':
                        dr, dc = j, 2-i
                    else:
                        dr, dc = 2-j, i
                    new_r = r0 + dr
                    new_c = c0 + dc
                else:
                    new_r, new_c = r, c
                new_pos[pos][q][d_idx] = new_r * 6 + new_c
    lines = []
    for r in range(6):
        for cs in range(2):
            L = 0
            for k in range(5):
                L |= 1 << (r*6 + cs + k)
            lines.append(L)
    for c in range(6):
        for rs in range(2):
            L = 0
            for k in range(5):
                L |= 1 << ((rs+k)*6 + c)
            lines.append(L)
    for sr, sc, length in [(0,0,6),(0,1,5),(1,0,5)]:
        for off in range(length-4):
            L = 0
            for k in range(5):
                L |= 1 << ((sr+off+k)*6 + (sc+off+k))
            lines.append(L)
    for sr, sc, length in [(0,5,6),(0,4,5),(1,5,5)]:
        for off in range(length-4):
            L = 0
            for k in range(5):
                L |= 1 << ((sr+off+k)*6 + (sc-off-k))
            lines.append(L)
    return qmasks, qmasks_inv, rot_tables, pack_shifts, tuple(lines), new_pos

QMASKS, QMASKS_INV, ROT_TABLES, PACK_SHIFTS, LINES, NEW_POS = _build()

_bc = getattr(int, 'bit_count', None)
if _bc is not None:
    def popcount(x): return x.bit_count()
else:
    def popcount(x): return bin(x).count('1')

def rotate(bb, q, d):
    s0 = PACK_SHIFTS[q]
    packed = ((bb >> s0) & 7) | ((bb >> (s0+3)) & 56) | ((bb >> (s0+6)) & 448)
    return (bb & QMASKS_INV[q]) | ROT_TABLES[q][d][packed]

def check_win(bb):
    for L in LINES:
        if (bb & L) == L:
            return True
    return False

LINE_SCORES = (0, 1, 4, 20, 100, 1000)

def evaluate(my_bb, op_bb):
    score = 0
    for L in LINES:
        m_bits = my_bb & L
        o_bits = op_bb & L
        if m_bits:
            if not o_bits:
                score += LINE_SCORES[popcount(m_bits)]
        elif o_bits:
            score -= LINE_SCORES[popcount(o_bits)]
    return score

WIN = 1000000

def negamax(bb_me, bb_op, depth, alpha, beta, deadline):
    occupied = bb_me | bb_op
    rotated_op = [[0]*2 for _ in range(4)]
    rotated_me = [[0]*2 for _ in range(4)]
    op_wins = [[False]*2 for _ in range(4)]
    for q in range(4):
        for d in (0, 1):
            ro = rotate(bb_op, q, d)
            rm = rotate(bb_me, q, d)
            rotated_op[q][d] = ro
            rotated_me[q][d] = rm
            op_wins[q][d] = check_win(ro)
    candidates = []
    for pos in range(36):
        if occupied & (1 << pos):
            continue
        for q in range(4):
            for d in (0, 1):
                new_bit = 1 << NEW_POS[pos][q][d]
                rm = rotated_me[q][d]
                no = rotated_op[q][d]
                nm = rm | new_bit
                mw = check_win(nm)
                ow = op_wins[q][d]
                if mw and not ow:
                    return WIN + depth, (pos, q, d)
                if mw and ow:
                    s = 0
                elif ow:
                    s = -WIN - depth
                else:
                    s = evaluate(nm, no)
                candidates.append((s, pos, q, d, nm, no, mw, ow))
    if not candidates:
        return 0, None
    if depth <= 1:
        best_s = candidates[0][0]
        best_m = (candidates[0][1], candidates[0][2], candidates[0][3])
        for cand in candidates[1:]:
            if cand[0] > best_s:
                best_s = cand[0]
                best_m = (cand[1], cand[2], cand[3])
        return best_s, best_m
    candidates.sort(key=lambda x: -x[0])
    best_score = -WIN * 10
    best_move = (candidates[0][1], candidates[0][2], candidates[0][3])
    for s, pos, q, d, nm, no, mw, ow in candidates:
        if time.time() > deadline:
            break
        if mw and ow:
            val = 0
        elif ow:
            val = -WIN - depth
        else:
            sub, _ = negamax(no, nm, depth-1, -beta, -alpha, deadline)
            val = -sub
        if val > best_score:
            best_score = val
            best_move = (pos, q, d)
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break
    return best_score, best_move

def policy(you, opponent):
    start = time.time()
    my_bb = 0
    op_bb = 0
    for r in range(6):
        for c in range(6):
            if you[r][c]:
                my_bb |= 1 << (r*6+c)
            if opponent[r][c]:
                op_bb |= 1 << (r*6+c)
    _, best_move = negamax(my_bb, op_bb, 1, -WIN*10, WIN*10, start + 0.95)
    if time.time() - start < 0.3:
        deadline = start + 0.85
        _, mv2 = negamax(my_bb, op_bb, 2, -WIN*10, WIN*10, deadline)
        if mv2 is not None:
            best_move = mv2
    if best_move is None:
        for pos in range(36):
            if not ((my_bb|op_bb) & (1<<pos)):
                r, c = pos//6, pos%6
                return f"{r+1},{c+1},0,R"
        return "1,1,0,R"
    pos, q, d = best_move
    r, c = pos//6, pos%6
    direction = 'L' if d == 0 else 'R'
    return f"{r+1},{c+1},{q},{direction}"
