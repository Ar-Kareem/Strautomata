
import time
import numpy as np

FULL_MASK = (1 << 64) - 1
A_FILE = 0x0101010101010101
H_FILE = 0x8080808080808080
NOT_A_FILE = FULL_MASK ^ A_FILE
NOT_H_FILE = FULL_MASK ^ H_FILE

DIRS = (1, -1, 8, -8, 9, 7, -7, -9)
COLS = "abcdefgh"

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)
EDGES = A_FILE | H_FILE | 0x00000000000000FF | 0xFF00000000000000

POSITION = [
    120, -25,  20,   8,   8,  20, -25, 120,
    -25, -45,  -5,  -5,  -5,  -5, -45, -25,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      8,  -5,   3,   3,   3,   3,  -5,   8,
      8,  -5,   3,   3,   3,   3,  -5,   8,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -25, -45,  -5,  -5,  -5,  -5, -45, -25,
    120, -25,  20,   8,   8,  20, -25, 120,
]

POS_BYTE = []
for row in range(8):
    table = []
    base = row * 8
    for b in range(256):
        s = 0
        x = b
        while x:
            lsb = x & -x
            s += POSITION[base + lsb.bit_length() - 1]
            x ^= lsb
        table.append(s)
    POS_BYTE.append(table)

CORNER_INFO = (
    (1 << 0,  (1 << 1) | (1 << 8),   1 << 9,  (1 << 1) | (1 << 8) | (1 << 9)),
    (1 << 7,  (1 << 6) | (1 << 15),  1 << 14, (1 << 6) | (1 << 15) | (1 << 14)),
    (1 << 56, (1 << 48) | (1 << 57), 1 << 49, (1 << 48) | (1 << 57) | (1 << 49)),
    (1 << 63, (1 << 55) | (1 << 62), 1 << 54, (1 << 55) | (1 << 62) | (1 << 54)),
)

EDGE_LINES = (
    (1 << 0,  tuple(range(0, 8))),
    (1 << 0,  tuple(range(0, 57, 8))),
    (1 << 7,  tuple(range(7, -1, -1))),
    (1 << 7,  tuple(range(7, 64, 8))),
    (1 << 56, tuple(range(56, 64))),
    (1 << 56, tuple(range(56, -1, -8))),
    (1 << 63, tuple(range(63, 55, -1))),
    (1 << 63, tuple(range(63, 6, -8))),
)

INF = 1_000_000_000
EXACT, LOWER, UPPER = 0, 1, 2


class _Timeout(Exception):
    pass


def _array_to_bb(arr):
    bb = 0
    flat = arr.ravel()
    for i in range(64):
        if flat[i]:
            bb |= 1 << i
    return bb


def _move_to_str(move):
    i = move.bit_length() - 1
    return COLS[i & 7] + str((i >> 3) + 1)


def _shift(bb, d):
    if d == 1:
        return (bb << 1) & NOT_A_FILE
    if d == -1:
        return (bb >> 1) & NOT_H_FILE
    if d == 8:
        return (bb << 8) & FULL_MASK
    if d == -8:
        return bb >> 8
    if d == 9:
        return (bb << 9) & NOT_A_FILE
    if d == 7:
        return (bb << 7) & NOT_H_FILE
    if d == -7:
        return (bb >> 7) & NOT_A_FILE
    return (bb >> 9) & NOT_H_FILE


def _adjacent(bb):
    return (
        ((bb << 1) & NOT_A_FILE) |
        ((bb >> 1) & NOT_H_FILE) |
        ((bb << 8) & FULL_MASK) |
        (bb >> 8) |
        ((bb << 9) & NOT_A_FILE) |
        ((bb << 7) & NOT_H_FILE) |
        ((bb >> 7) & NOT_A_FILE) |
        ((bb >> 9) & NOT_H_FILE)
    ) & FULL_MASK


def _legal_moves(p, o):
    empty = (~(p | o)) & FULL_MASK
    moves = 0

    x = ((p << 1) & NOT_A_FILE) & o
    for _ in range(5):
        x |= ((x << 1) & NOT_A_FILE) & o
    moves |= ((x << 1) & NOT_A_FILE) & empty

    x = ((p >> 1) & NOT_H_FILE) & o
    for _ in range(5):
        x |= ((x >> 1) & NOT_H_FILE) & o
    moves |= ((x >> 1) & NOT_H_FILE) & empty

    x = (p << 8) & o
    for _ in range(5):
        x |= (x << 8) & o
    moves |= (x << 8) & empty

    x = (p >> 8) & o
    for _ in range(5):
        x |= (x >> 8) & o
    moves |= (x >> 8) & empty

    x = ((p << 9) & NOT_A_FILE) & o
    for _ in range(5):
        x |= ((x << 9) & NOT_A_FILE) & o
    moves |= ((x << 9) & NOT_A_FILE) & empty

    x = ((p << 7) & NOT_H_FILE) & o
    for _ in range(5):
        x |= ((x << 7) & NOT_H_FILE) & o
    moves |= ((x << 7) & NOT_H_FILE) & empty

    x = ((p >> 7) & NOT_A_FILE) & o
    for _ in range(5):
        x |= ((x >> 7) & NOT_A_FILE) & o
    moves |= ((x >> 7) & NOT_A_FILE) & empty

    x = ((p >> 9) & NOT_H_FILE) & o
    for _ in range(5):
        x |= ((x >> 9) & NOT_H_FILE) & o
    moves |= ((x >> 9) & NOT_H_FILE) & empty

    return moves & FULL_MASK


def _flips(p, o, move):
    flips = 0
    for d in DIRS:
        cap = 0
        x = _shift(move, d)
        while x and (x & o):
            cap |= x
            x = _shift(x, d)
        if cap and (x & p):
            flips |= cap
    return flips


def _weighted_sum(bb):
    return (
        POS_BYTE[0][bb & 255] +
        POS_BYTE[1][(bb >> 8) & 255] +
        POS_BYTE[2][(bb >> 16) & 255] +
        POS_BYTE[3][(bb >> 24) & 255] +
        POS_BYTE[4][(bb >> 32) & 255] +
        POS_BYTE[5][(bb >> 40) & 255] +
        POS_BYTE[6][(bb >> 48) & 255] +
        POS_BYTE[7][(bb >> 56) & 255]
    )


def _edge_stable(bb):
    stable = 0
    for corner, line in EDGE_LINES:
        if bb & corner:
            for sq in line:
                bit = 1 << sq
                if bb & bit:
                    stable |= bit
                else:
                    break
    return stable.bit_count()


def _corner_safety_score(p, o):
    occ = p | o
    score = 0
    for corner, c_mask, x_mask, all_mask in CORNER_INFO:
        if not (occ & corner):
            score -= 35 * (p & c_mask).bit_count()
            score += 35 * (o & c_mask).bit_count()
            score -= 75 * (p & x_mask).bit_count()
            score += 75 * (o & x_mask).bit_count()
        elif p & corner:
            score += 10 * (p & all_mask).bit_count()
            score -= 5 * (o & all_mask).bit_count()
        else:
            score -= 10 * (o & all_mask).bit_count()
            score += 5 * (p & all_mask).bit_count()
    return score


def _norm_diff(a, b):
    s = a + b
    if s == 0:
        return 0
    return (100 * (a - b)) // s


def _evaluate(p, o):
    occ = p | o
    empty = (~occ) & FULL_MASK
    empties = empty.bit_count()

    my_discs = p.bit_count()
    op_discs = o.bit_count()
    disc_diff = my_discs - op_discs

    if empties == 0:
        return disc_diff * 1_000_000

    my_moves = _legal_moves(p, o).bit_count()
    op_moves = _legal_moves(o, p).bit_count()
    mobility = _norm_diff(my_moves, op_moves)

    my_potential = (_adjacent(o) & empty).bit_count()
    op_potential = (_adjacent(p) & empty).bit_count()
    potential = _norm_diff(my_potential, op_potential)

    adj_empty = _adjacent(empty)
    my_frontier = (p & adj_empty).bit_count()
    op_frontier = (o & adj_empty).bit_count()
    frontier = op_frontier - my_frontier

    corner_diff = (p & CORNERS).bit_count() - (o & CORNERS).bit_count()
    corner_safety = _corner_safety_score(p, o)
    pos_diff = _weighted_sum(p) - _weighted_sum(o)
    stable_diff = _edge_stable(p) - _edge_stable(o)

    if empties > 44:
        score = (
            25000 * corner_diff +
            120 * corner_safety +
            80 * mobility +
            35 * potential +
            35 * frontier +
            8 * pos_diff +
            400 * stable_diff -
            15 * disc_diff
        )
    elif empties > 18:
        score = (
            25000 * corner_diff +
            100 * corner_safety +
            100 * mobility +
            20 * potential +
            25 * frontier +
            5 * pos_diff +
            500 * stable_diff +
            10 * disc_diff
        )
    else:
        score = (
            25000 * corner_diff +
            50 * corner_safety +
            70 * mobility +
            5 * potential +
            5 * frontier +
            2 * pos_diff +
            800 * stable_diff +
            500 * disc_diff
        )
        score += 1000 if (empties & 1) else -1000

    return score


def _move_score(p, o, move, tt_best=0):
    if move == tt_best:
        return 10_000_000

    idx = move.bit_length() - 1
    score = POSITION[idx]

    if move & CORNERS:
        score += 1_000_000
    if move & EDGES:
        score += 100

    occ = p | o
    for corner, c_mask, x_mask, all_mask in CORNER_INFO:
        if not (occ & corner):
            if move & x_mask:
                score -= 500_000
            if move & c_mask:
                score -= 150_000
        elif p & corner:
            if move & all_mask:
                score += 2000
        elif o & corner:
            if move & all_mask:
                score -= 500

    return score


def _order_moves(p, o, moves, tt_best=0):
    arr = []
    bb = moves
    while bb:
        m = bb & -bb
        arr.append(m)
        bb ^= m
    arr.sort(key=lambda m: _move_score(p, o, m, tt_best), reverse=True)
    return arr


def _slow_first_legal(you, opponent):
    dirs = (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1),
    )
    for r in range(8):
        for c in range(8):
            if you[r][c] or opponent[r][c]:
                continue
            for dr, dc in dirs:
                rr, cc = r + dr, c + dc
                seen = False
                while 0 <= rr < 8 and 0 <= cc < 8 and opponent[rr][cc]:
                    seen = True
                    rr += dr
                    cc += dc
                if seen and 0 <= rr < 8 and 0 <= cc < 8 and you[rr][cc]:
                    return COLS[c] + str(r + 1)
    return "pass"


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    try:
        p = _array_to_bb(you)
        o = _array_to_bb(opponent)

        root_moves = _legal_moves(p, o)
        if root_moves == 0:
            return "pass"

        if root_moves & (root_moves - 1) == 0:
            return _move_to_str(root_moves)

        deadline = time.perf_counter() + 0.88
        tt = {}
        nodes = 0

        ordered = _order_moves(p, o, root_moves, 0)
        best_move = ordered[0]
        empties = (FULL_MASK ^ (p | o)).bit_count()
        max_depth = max(1, empties)

        def negamax(cp, co, depth, alpha, beta):
            nonlocal nodes
            nodes += 1
            if (nodes & 1023) == 0 and time.perf_counter() > deadline:
                raise _Timeout()

            key = (cp, co)
            alpha_orig = alpha
            beta_orig = beta

            entry = tt.get(key)
            tt_best = 0
            if entry is not None:
                e_depth, e_val, e_flag, e_best = entry
                tt_best = e_best
                if e_depth >= depth:
                    if e_flag == EXACT:
                        return e_val
                    if e_flag == LOWER:
                        alpha = max(alpha, e_val)
                    elif e_flag == UPPER:
                        beta = min(beta, e_val)
                    if alpha >= beta:
                        return e_val

            moves = _legal_moves(cp, co)

            if moves == 0:
                if _legal_moves(co, cp) == 0:
                    return (cp.bit_count() - co.bit_count()) * 1_000_000
                val = -negamax(co, cp, depth, -beta, -alpha)
                if val <= alpha_orig:
                    flag = UPPER
                elif val >= beta_orig:
                    flag = LOWER
                else:
                    flag = EXACT
                tt[key] = (depth, val, flag, 0)
                return val

            if depth <= 0:
                val = _evaluate(cp, co)
                tt[key] = (depth, val, EXACT, 0)
                return val

            best_val = -INF
            best = 0
            first = True

            for m in _order_moves(cp, co, moves, tt_best):
                f = _flips(cp, co, m)
                if not f:
                    continue
                npb = cp | m | f
                nob = co & ~f

                if first:
                    val = -negamax(nob, npb, depth - 1, -beta, -alpha)
                    first = False
                else:
                    val = -negamax(nob, npb, depth - 1, -alpha - 1, -alpha)
                    if alpha < val < beta:
                        val = -negamax(nob, npb, depth - 1, -beta, -alpha)

                if val > best_val:
                    best_val = val
                    best = m
                if val > alpha:
                    alpha = val
                if alpha >= beta:
                    break

            if best_val <= alpha_orig:
                flag = UPPER
            elif best_val >= beta_orig:
                flag = LOWER
            else:
                flag = EXACT
            tt[key] = (depth, best_val, flag, best)

            return best_val

        try:
            for depth in range(1, max_depth + 1):
                if time.perf_counter() > deadline:
                    break

                local_best = best_move
                local_score = -INF
                alpha = -INF
                beta = INF

                for m in _order_moves(p, o, root_moves, best_move):
                    if time.perf_counter() > deadline:
                        raise _Timeout()

                    f = _flips(p, o, m)
                    if not f:
                        continue

                    npb = p | m | f
                    nob = o & ~f
                    val = -negamax(nob, npb, depth - 1, -beta, -alpha)

                    if val > local_score:
                        local_score = val
                        local_best = m
                    if val > alpha:
                        alpha = val

                best_move = local_best

                if depth >= empties:
                    break

        except _Timeout:
            pass

        if best_move & root_moves:
            return _move_to_str(best_move)

        return _move_to_str(ordered[0])

    except Exception:
        return _slow_first_legal(you, opponent)
