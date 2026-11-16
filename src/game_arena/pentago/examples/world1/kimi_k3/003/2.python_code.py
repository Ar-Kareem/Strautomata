
import time

# ------------------------------------------------------------------ constants
INF = 10**12
WIN = 10**10
# reward for an open (single-colour) line of length 0..4
W = (0, 1, 8, 60, 600, 0)
DIRS = ('L', 'R')

# ------------------------------------------------------------------ line masks
def _build_lines():
    lines = []
    # horizontal segments (start col 0..1 in every row)
    for r in range(6):
        for c in range(2):
            m = 0
            for k in range(5):
                m |= 1 << (r * 6 + c + k)
            lines.append(m)
    # vertical segments
    for c in range(6):
        for r in range(2):
            m = 0
            for k in range(5):
                m |= 1 << ((r + k) * 6 + c)
            lines.append(m)
    # diagonal down-right
    for r in range(2):
        for c in range(2):
            m = 0
            for k in range(5):
                m |= 1 << ((r + k) * 6 + (c + k))
            lines.append(m)
    # diagonal down-left
    for r in range(2):
        for c in range(4, 6):
            m = 0
            for k in range(5):
                m |= 1 << ((r + k) * 6 + (c - k))
            lines.append(m)
    return tuple(lines)

LINES = _build_lines()

# ------------------------------------------------------- quadrant / rotations
_QUAD_ORIGINS = ((0, 0), (0, 3), (3, 0), (3, 3))
QUAD_MASK = [0] * 4
# ROT[q][0] = L pairs, ROT[q][1] = R pairs ; each pair is (src_cell, dst_cell)
ROT = [[None, None] for _ in range(4)]

for q, (r0, c0) in enumerate(_QUAD_ORIGINS):
    cells = [(r0 + r) * 6 + (c0 + c) for r in range(3) for c in range(3)]
    QUAD_MASK[q] = sum(1 << x for x in cells)
    for di, d in enumerate(DIRS):
        pairs = []
        for r in range(3):
            for c in range(3):
                src = (r0 + r) * 6 + (c0 + c)
                if d == 'R':            # clockwise
                    dr, dc = c, 2 - r
                else:                   # anticlockwise
                    dr, dc = 2 - c, r
                dst = (r0 + dr) * 6 + (c0 + dc)
                pairs.append((src, dst))
        ROT[q][di] = tuple(pairs)

# ------------------------------------------------------------------ helpers
def _rotate_pair(me, opp, q, di):
    qm = QUAD_MASK[q]
    rm = me & ~qm
    ro = opp & ~qm
    for src, dst in ROT[q][di]:
        sb = 1 << src
        db = 1 << dst
        if me & sb:
            rm |= db
        if opp & sb:
            ro |= db
    return rm, ro

def _evaluate(me, opp):
    s = 0
    for m in LINES:
        a = (me & m).bit_count()
        b = (opp & m).bit_count()
        if b == 0:
            if a == 5:
                return WIN
            s += W[a]
        elif a == 0:
            if b == 5:
                return -WIN
            s -= W[b]
    return s

def _gen_moves(me, opp):
    """yield (new_me, new_opp) for every distinct resulting position."""
    occ = me | opp
    seen = set()
    for cell in range(36):
        if (occ >> cell) & 1:
            continue
        nm = me | (1 << cell)
        for q in range(4):
            for di in range(2):
                rm, ro = _rotate_pair(nm, opp, q, di)
                key = (rm << 40) | ro
                if key in seen:
                    continue
                seen.add(key)
                yield (rm, ro)

# ------------------------------------------------------------------ search
class _Timeout(Exception):
    pass

_nodes = 0
DEPTH = 2

def _negamax(me, opp, depth, alpha, beta, deadline):
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0 and time.time() > deadline:
        raise _Timeout
    if depth == 0:
        return _evaluate(me, opp)
    best = -INF
    any_move = False
    for rm, ro in _gen_moves(me, opp):
        any_move = True
        val = -_negamax(ro, rm, depth - 1, -beta, -alpha, deadline)
        if val > best:
            best = val
            if best > alpha:
                alpha = best
                if alpha >= beta:
                    break
    if not any_move:
        return _evaluate(me, opp)
    return best

# ------------------------------------------------------------------ policy
def policy(you, opponent):
    global _nodes
    me = 0
    opp = 0
    for r in range(6):
        for c in range(6):
            i = r * 6 + c
            if you[r][c]:
                me |= 1 << i
            elif opponent[r][c]:
                opp |= 1 << i

    deadline = time.time() + 0.85
    occ = me | opp

    # generate root moves with their strings, deduplicated
    seen = set()
    moves = []
    for cell in range(36):
        if (occ >> cell) & 1:
            continue
        nm = me | (1 << cell)
        row = cell // 6 + 1
        col = cell % 6 + 1
        for q in range(4):
            for di in range(2):
                rm, ro = _rotate_pair(nm, opp, q, di)
                key = (rm << 40) | ro
                if key in seen:
                    continue
                seen.add(key)
                moves.append((str(row) + "," + str(col) + "," + str(q) + DIRS[di],
                              rm, ro))
    if not moves:
        return "1,1,0,L"            # safety fallback (never reached)

    # order moves by static evaluation (best first, wins come first)
    moves.sort(key=lambda x: _evaluate(x[1], x[2]), reverse=True)

    best_move = moves[0][0]
    best_val = -INF
    try:
        for mv, rm, ro in moves:
            beta_child = -best_val if best_val > -INF else INF
            val = -_negamax(ro, rm, DEPTH - 1, -INF, beta_child, deadline)
            if val > best_val:
                best_val = val
                best_move = mv
    except _Timeout:
        pass
    return best_move
