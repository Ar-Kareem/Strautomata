
# Pentago policy: legal-move-safe alpha-beta search with tactical checks.
# Required API:
#   def policy(you, opponent) -> str

import time
import math

N = 6
DIRS = ((0, 1), (1, 0), (1, 1), (1, -1))
QUAD_OFF = ((0, 0), (0, 3), (3, 0), (3, 3))

# All length-5 windows on a 6x6 board in four directions.
LINES5 = []
for r in range(N):
    for c in range(N):
        for dr, dc in DIRS:
            cells = []
            rr, cc = r, c
            ok = True
            for _ in range(5):
                if not (0 <= rr < N and 0 <= cc < N):
                    ok = False
                    break
                cells.append(rr * N + cc)
                rr += dr
                cc += dc
            if ok:
                LINES5.append(tuple(cells))

# Useful slightly-longer lines for pattern potential.
LINES_ALL = []
for line in LINES5:
    LINES_ALL.append(line)

# Positional preference: centers of quadrants and global middle area are valuable.
POS_W = [
    3, 4, 4, 4, 4, 3,
    4, 7, 7, 7, 7, 4,
    4, 7, 8, 8, 7, 4,
    4, 7, 8, 8, 7, 4,
    4, 7, 7, 7, 7, 4,
    3, 4, 4, 4, 4, 3,
]


def _to_bits(a):
    b = 0
    for r in range(6):
        row = a[r]
        for c in range(6):
            if int(row[c]):
                b |= 1 << (r * 6 + c)
    return b


def _has_win(bits):
    for line in LINES5:
        m = 0
        for p in line:
            m |= 1 << p
        if (bits & m) == m:
            return True
    return False


LINE_MASKS = []
for line in LINES5:
    m = 0
    for p in line:
        m |= 1 << p
    LINE_MASKS.append(m)


def _rot_map_for(q, d):
    r0, c0 = QUAD_OFF[q]
    mp = list(range(36))
    for rr in range(3):
        for cc in range(3):
            old = (r0 + rr) * 6 + (c0 + cc)
            if d == "R":
                nr, nc = cc, 2 - rr
            else:
                nr, nc = 2 - cc, rr
            new = (r0 + nr) * 6 + (c0 + nc)
            mp[old] = new
    return mp


ROT_MAPS = {(q, d): _rot_map_for(q, d) for q in range(4) for d in ("L", "R")}


def _rotate_bits(bits, q, d):
    mp = ROT_MAPS[(q, d)]
    nb = bits
    # Clear quadrant then re-add rotated stones.
    r0, c0 = QUAD_OFF[q]
    qmask = 0
    for rr in range(3):
        for cc in range(3):
            qmask |= 1 << ((r0 + rr) * 6 + (c0 + cc))
    nb &= ~qmask
    x = bits & qmask
    while x:
        lsb = x & -x
        p = lsb.bit_length() - 1
        nb |= 1 << mp[p]
        x -= lsb
    return nb


def _apply(my, op, pos, q, d):
    my2 = my | (1 << pos)
    return _rotate_bits(my2, q, d), _rotate_bits(op, q, d)


def _legal_moves(my, op):
    occ = my | op
    moves = []
    for pos in range(36):
        if not (occ >> pos) & 1:
            r, c = divmod(pos, 6)
            # Prefer rotations that actually have tactical variety; all are legal.
            for q in range(4):
                moves.append((pos, q, "L"))
                moves.append((pos, q, "R"))
    return moves


def _move_to_str(m):
    pos, q, d = m
    r, c = divmod(pos, 6)
    return f"{r+1},{c+1},{q},{d}"


def _terminal_score(my, op, ply):
    mw = _has_win(my)
    ow = _has_win(op)
    if mw and ow:
        return 0
    if mw:
        return 1000000 - ply
    if ow:
        return -1000000 + ply
    if (my | op) == (1 << 36) - 1:
        return 0
    return None


def _evaluate(my, op):
    term = _terminal_score(my, op, 0)
    if term is not None:
        return term

    score = 0

    # Positional score
    x = my
    while x:
        lsb = x & -x
        p = lsb.bit_length() - 1
        score += POS_W[p]
        x -= lsb
    x = op
    while x:
        lsb = x & -x
        p = lsb.bit_length() - 1
        score -= POS_W[p]
        x -= lsb

    # Line-window score. Open uncontested lines matter most.
    vals = [0, 2, 12, 75, 650, 100000]
    for m in LINE_MASKS:
        a = (my & m).bit_count()
        b = (op & m).bit_count()
        if a and b:
            continue
        if a:
            score += vals[a]
            if a == 4:
                score += 400
        elif b:
            score -= vals[b] * 1.12
            if b == 4:
                score -= 650
        else:
            score += 1

    return int(score)


def _ordered_moves(my, op, limit=None):
    moves = _legal_moves(my, op)
    scored = []
    for m in moves:
        my2, op2 = _apply(my, op, m[0], m[1], m[2])
        term = _terminal_score(my2, op2, 0)
        if term is not None:
            s = term
        else:
            # Cheap local ordering.
            s = _evaluate(my2, op2)
        scored.append((s, m))
    scored.sort(reverse=True, key=lambda x: x[0])
    if limit is not None and len(scored) > limit:
        scored = scored[:limit]
    return [m for _, m in scored]


def _opponent_has_winning_reply(my, op, time_end):
    # Here opponent is to move; if they can make a non-drawing win, return True.
    for m in _legal_moves(op, my):
        if time.time() > time_end:
            return False
        op2, my2 = _apply(op, my, m[0], m[1], m[2])
        ow = _has_win(op2)
        mw = _has_win(my2)
        if ow and not mw:
            return True
    return False


def policy(you, opponent) -> str:
    start = time.time()
    time_end = start + 0.92

    my = _to_bits(you)
    op = _to_bits(opponent)

    legal = _legal_moves(my, op)
    if not legal:
        return "1,1,0,L"  # Should never happen per prompt.

    fallback = _move_to_str(legal[0])

    # 1) Take an immediate non-drawing win. Keep drawing win as secondary.
    drawing_win = None
    for m in legal:
        my2, op2 = _apply(my, op, m[0], m[1], m[2])
        mw = _has_win(my2)
        ow = _has_win(op2)
        if mw and not ow:
            return _move_to_str(m)
        if mw and ow and drawing_win is None:
            drawing_win = m

    # 2) Prefer moves that do not allow an immediate opponent win.
    safe_moves = []
    for m in _ordered_moves(my, op, limit=min(len(legal), 80)):
        if time.time() > time_end:
            break
        my2, op2 = _apply(my, op, m[0], m[1], m[2])
        if not _opponent_has_winning_reply(my2, op2, time_end):
            safe_moves.append(m)

    if drawing_win is not None and not safe_moves:
        return _move_to_str(drawing_win)

    root_moves = safe_moves if safe_moves else _ordered_moves(my, op, limit=min(len(legal), 80))
    if not root_moves:
        return fallback

    best_move = root_moves[0]
    best_score = -10**18

    # Depth based on empties. Branching is large, so use selective move caps.
    empties = 36 - (my | op).bit_count()
    if empties <= 8:
        max_depth = 3
        cap = 48
    elif empties <= 18:
        max_depth = 2
        cap = 36
    else:
        max_depth = 2
        cap = 28

    def negamax(cur_my, cur_op, depth, alpha, beta, ply):
        if time.time() > time_end:
            raise TimeoutError

        term = _terminal_score(cur_my, cur_op, ply)
        if term is not None:
            return term
        if depth <= 0:
            return _evaluate(cur_my, cur_op)

        moves = _ordered_moves(cur_my, cur_op, limit=cap)
        if not moves:
            return _evaluate(cur_my, cur_op)

        val = -10**18
        for m in moves:
            nmy, nop = _apply(cur_my, cur_op, m[0], m[1], m[2])
            # Swap perspective for opponent turn. Terminal score must be from current root
            # perspective, so use negation with swapped bitboards.
            sc = -negamax(nop, nmy, depth - 1, -beta, -alpha, ply + 1)
            if sc > val:
                val = sc
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break
        return val

    try:
        # Iterative deepening gives a valid answer even if time expires.
        for depth in range(1, max_depth + 1):
            if time.time() > time_end:
                break
            local_best = best_move
            local_score = -10**18
            alpha = -10**18
            beta = 10**18
            for m in root_moves:
                if time.time() > time_end:
                    raise TimeoutError
                my2, op2 = _apply(my, op, m[0], m[1], m[2])
                term = _terminal_score(my2, op2, 1)
                if term is not None:
                    sc = term
                else:
                    sc = -negamax(op2, my2, depth - 1, -beta, -alpha, 1)
                if sc > local_score:
                    local_score = sc
                    local_best = m
                if sc > alpha:
                    alpha = sc
            best_move = local_best
            best_score = local_score
    except Exception:
        pass

    return _move_to_str(best_move)
