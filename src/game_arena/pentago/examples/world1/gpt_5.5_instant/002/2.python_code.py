
import math
import time

# Pentago policy: returns "row,col,quad,dir"

N = 6
DIRS = ("L", "R")
QUADS = (0, 1, 2, 3)

# All length-5 and length-6 line segments that can contain a five-in-row.
LINES = []
for r in range(N):
    LINES.append([(r, c) for c in range(N)])
for c in range(N):
    LINES.append([(r, c) for r in range(N)])
for r0 in range(N):
    d = []
    r, c = r0, 0
    while r < N and c < N:
        d.append((r, c))
        r += 1
        c += 1
    if len(d) >= 5:
        LINES.append(d)
for c0 in range(1, N):
    d = []
    r, c = 0, c0
    while r < N and c < N:
        d.append((r, c))
        r += 1
        c += 1
    if len(d) >= 5:
        LINES.append(d)
for r0 in range(N):
    d = []
    r, c = r0, 0
    while r >= 0 and c < N:
        d.append((r, c))
        r -= 1
        c += 1
    if len(d) >= 5:
        LINES.append(d)
for c0 in range(1, N):
    d = []
    r, c = N - 1, c0
    while r >= 0 and c < N:
        d.append((r, c))
        r -= 1
        c += 1
    if len(d) >= 5:
        LINES.append(d)

WINDOWS = []
for line in LINES:
    if len(line) == 5:
        WINDOWS.append(line)
    elif len(line) == 6:
        WINDOWS.append(line[:5])
        WINDOWS.append(line[1:])

# Precompute quadrant rotations as index permutations.
ROT_MAP = {}
for q in QUADS:
    r0 = 0 if q < 2 else 3
    c0 = 0 if q % 2 == 0 else 3
    for d in DIRS:
        mp = {}
        for rr in range(3):
            for cc in range(3):
                if d == "R":
                    nr, nc = cc, 2 - rr
                else:
                    nr, nc = 2 - cc, rr
                mp[(r0 + rr, c0 + cc)] = (r0 + nr, c0 + nc)
        ROT_MAP[(q, d)] = mp

CENTER_WEIGHTS = [
    [1, 2, 2, 2, 2, 1],
    [2, 4, 5, 5, 4, 2],
    [2, 5, 7, 7, 5, 2],
    [2, 5, 7, 7, 5, 2],
    [2, 4, 5, 5, 4, 2],
    [1, 2, 2, 2, 2, 1],
]

SCORES = [0, 2, 12, 80, 650, 1000000]


def _to_int_board(arr):
    b = [[0] * N for _ in range(N)]
    for r in range(N):
        row = arr[r]
        for c in range(N):
            if row[c]:
                b[r][c] = 1
    return b


def _has_win(b):
    for w in WINDOWS:
        ok = True
        for r, c in w:
            if b[r][c] == 0:
                ok = False
                break
        if ok:
            return True
    return False


def _rotate_inplace(y, o, q, d):
    mp = ROT_MAP[(q, d)]
    oldy = {}
    oldo = {}
    for pos in mp:
        r, c = pos
        oldy[pos] = y[r][c]
        oldo[pos] = o[r][c]
    for src, dst in mp.items():
        sr, sc = src
        dr, dc = dst
        y[dr][dc] = oldy[(sr, sc)]
        o[dr][dc] = oldo[(sr, sc)]


def _copy_apply(y, o, move):
    r, c, q, d = move
    yy = [row[:] for row in y]
    oo = [row[:] for row in o]
    yy[r][c] = 1
    _rotate_inplace(yy, oo, q, d)
    return yy, oo


def _legal_moves(y, o):
    # Prefer strong cells first for better alpha-beta pruning.
    empties = []
    for r in range(N):
        for c in range(N):
            if y[r][c] == 0 and o[r][c] == 0:
                empties.append((r, c))
    empties.sort(key=lambda p: -CENTER_WEIGHTS[p[0]][p[1]])
    for r, c in empties:
        for q in QUADS:
            for d in DIRS:
                yield (r, c, q, d)


def _terminal_after(y, o):
    yw = _has_win(y)
    ow = _has_win(o)
    if yw and ow:
        return 0
    if yw:
        return 10000000
    if ow:
        return -10000000
    return None


def _evaluate(y, o):
    term = _terminal_after(y, o)
    if term is not None:
        return term

    score = 0

    for w in WINDOWS:
        yc = 0
        oc = 0
        emp = 0
        for r, c in w:
            if y[r][c]:
                yc += 1
            elif o[r][c]:
                oc += 1
            else:
                emp += 1

        if oc == 0:
            score += SCORES[yc]
            if yc == 4 and emp == 1:
                score += 1200
            elif yc == 3 and emp == 2:
                score += 120
        elif yc == 0:
            score -= SCORES[oc]
            if oc == 4 and emp == 1:
                score -= 1500
            elif oc == 3 and emp == 2:
                score -= 150

    # Positional weighting.
    for r in range(N):
        for c in range(N):
            if y[r][c]:
                score += CENTER_WEIGHTS[r][c] * 3
            elif o[r][c]:
                score -= CENTER_WEIGHTS[r][c] * 3

    return score


def _move_score_guess(y, o, m):
    yy, oo = _copy_apply(y, o, m)
    t = _terminal_after(yy, oo)
    if t is not None:
        return t
    return _evaluate(yy, oo)


def _negamax(y, o, depth, alpha, beta, deadline):
    if time.time() > deadline:
        return _evaluate(y, o)

    term = _terminal_after(y, o)
    if term is not None:
        return term
    if depth <= 0:
        return _evaluate(y, o)

    moves = list(_legal_moves(y, o))
    if not moves:
        return 0

    # Current player in this node is represented by y; opponent by o.
    if depth >= 2:
        moves.sort(key=lambda m: -_move_score_guess(y, o, m))

    best = -100000000
    for m in moves:
        yy, oo = _copy_apply(y, o, m)
        val = _terminal_after(yy, oo)
        if val is None:
            # Swap perspective after a non-terminal move.
            val = -_negamax(oo, yy, depth - 1, -beta, -alpha, deadline)
        # If terminal, val is already from current player's perspective.
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
        if time.time() > deadline:
            break
    return best


def _format_move(m):
    r, c, q, d = m
    return f"{r+1},{c+1},{q},{d}"


def policy(you, opponent) -> str:
    start = time.time()
    deadline = start + 0.92

    y = _to_int_board(you)
    o = _to_int_board(opponent)

    moves = list(_legal_moves(y, o))
    if not moves:
        return "1,1,0,L"  # Should never be reached under the problem statement.

    fallback = moves[0]
    best_move = fallback

    # 1. Take immediate clean win if available; otherwise record draw/win fallback.
    immediate_draw = None
    for m in moves:
        yy, oo = _copy_apply(y, o, m)
        yw = _has_win(yy)
        ow = _has_win(oo)
        if yw and not ow:
            return _format_move(m)
        if yw and ow and immediate_draw is None:
            immediate_draw = m

    # 2. Identify opponent immediate winning replies and avoid them if possible.
    safe_moves = []
    for m in moves:
        if time.time() > deadline:
            break
        yy, oo = _copy_apply(y, o, m)
        term = _terminal_after(yy, oo)
        if term is not None:
            if term >= 0:
                safe_moves.append(m)
            continue

        opp_can_clean_win = False
        # From opponent perspective, oo is "you" and yy is "opponent".
        for rm in _legal_moves(oo, yy):
            ry, ro = _copy_apply(oo, yy, rm)
            if _has_win(ry) and not _has_win(ro):
                opp_can_clean_win = True
                break
        if not opp_can_clean_win:
            safe_moves.append(m)

    candidate_moves = safe_moves if safe_moves else moves

    # If only drawing immediate win exists and no clean win, it is usually better than risking loss.
    if immediate_draw is not None and not safe_moves:
        return _format_move(immediate_draw)

    # 3. Choose search depth based on empties.
    empties = sum(1 for r in range(N) for c in range(N) if y[r][c] == 0 and o[r][c] == 0)
    if empties <= 8:
        depth = 3
    elif empties <= 18:
        depth = 2
    else:
        depth = 1

    # Order candidates by heuristic.
    scored = []
    for m in candidate_moves:
        if time.time() > deadline:
            break
        scored.append((_move_score_guess(y, o, m), m))
    if not scored:
        return _format_move(fallback)

    scored.sort(reverse=True, key=lambda x: x[0])
    best_score = -100000000

    # Limit root branching when very early; rotations create many equivalent-looking moves.
    if empties > 24:
        root_list = scored[:80]
    elif empties > 16:
        root_list = scored[:140]
    else:
        root_list = scored

    for _, m in root_list:
        if time.time() > deadline:
            break
        yy, oo = _copy_apply(y, o, m)
        val = _terminal_after(yy, oo)
        if val is None:
            val = -_negamax(oo, yy, depth - 1, -100000000, 100000000, deadline)
        if val > best_score:
            best_score = val
            best_move = m

    return _format_move(best_move)
