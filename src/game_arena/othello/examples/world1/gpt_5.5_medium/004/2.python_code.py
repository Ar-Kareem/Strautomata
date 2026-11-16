
import time
import numpy as np

FULL = (1 << 64) - 1

A_FILE = 0
H_FILE = 0
for _r in range(8):
    A_FILE |= 1 << (_r * 8)
    H_FILE |= 1 << (_r * 8 + 7)

NOT_A = FULL ^ A_FILE
NOT_H = FULL ^ H_FILE

INF = 10 ** 12

# Othello positional table, indexed by r*8+c.
POS = (
    120, -25,  25,   8,   8,  25, -25, 120,
    -25, -55, -10,  -5,  -5, -10, -55, -25,
     25, -10,  18,   4,   4,  18, -10,  25,
      8,  -5,   4,   2,   2,   4,  -5,   8,
      8,  -5,   4,   2,   2,   4,  -5,   8,
     25, -10,  18,   4,   4,  18, -10,  25,
    -25, -55, -10,  -5,  -5, -10, -55, -25,
    120, -25,  25,   8,   8,  25, -25, 120,
)

CORNER_MASK = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

# Adjacent-to-corner danger masks, used only while the corner is empty.
CORNER_ADJ = (
    (1 << 0,  (1 << 1)  | (1 << 8)  | (1 << 9)),
    (1 << 7,  (1 << 6)  | (1 << 14) | (1 << 15)),
    (1 << 56, (1 << 48) | (1 << 49) | (1 << 57)),
    (1 << 63, (1 << 54) | (1 << 55) | (1 << 62)),
)

X_CORNER = {
    9: 0,
    14: 7,
    49: 56,
    54: 63,
}

C_CORNER = {
    1: 0, 8: 0,
    6: 7, 15: 7,
    48: 56, 57: 56,
    55: 63, 62: 63,
}


def _e(x):
    return (x & NOT_H) << 1


def _w(x):
    return (x & NOT_A) >> 1


def _s(x):
    return (x << 8) & FULL


def _n(x):
    return x >> 8


def _se(x):
    return ((x & NOT_H) << 9) & FULL


def _sw(x):
    return ((x & NOT_A) << 7) & FULL


def _ne(x):
    return (x & NOT_H) >> 7


def _nw(x):
    return (x & NOT_A) >> 9


SHIFTS = (_e, _w, _s, _n, _se, _sw, _ne, _nw)


def _adjacent(x):
    return (
        _e(x) | _w(x) | _s(x) | _n(x) |
        _se(x) | _sw(x) | _ne(x) | _nw(x)
    ) & FULL


def _legal_moves(p, o):
    empty = (~(p | o)) & FULL
    moves = 0
    for sh in SHIFTS:
        x = sh(p) & o
        x |= sh(x) & o
        x |= sh(x) & o
        x |= sh(x) & o
        x |= sh(x) & o
        x |= sh(x) & o
        moves |= sh(x) & empty
    return moves


def _make_move(p, o, move):
    flips = 0
    for sh in SHIFTS:
        captured = 0
        cur = sh(move)
        while cur & o:
            captured |= cur
            cur = sh(cur)
        if cur & p:
            flips |= captured
    return p | move | flips, o & ~flips


def _bits(mask):
    while mask:
        b = mask & -mask
        yield b
        mask -= b


def _weighted_sum(b):
    s = 0
    while b:
        lsb = b & -b
        s += POS[lsb.bit_length() - 1]
        b -= lsb
    return s


def _edge_stability_like(b):
    # Not a full stability solver, but rewards discs made safer by owned corners.
    score = 0

    if b & (1 << 0):
        for c in range(8):
            if b & (1 << c):
                score += 1
            else:
                break
        for r in range(1, 8):
            if b & (1 << (r * 8)):
                score += 1
            else:
                break

    if b & (1 << 7):
        for c in range(7, -1, -1):
            if b & (1 << c):
                score += 1
            else:
                break
        for r in range(1, 8):
            if b & (1 << (r * 8 + 7)):
                score += 1
            else:
                break

    if b & (1 << 56):
        for c in range(8):
            if b & (1 << (56 + c)):
                score += 1
            else:
                break
        for r in range(6, -1, -1):
            if b & (1 << (r * 8)):
                score += 1
            else:
                break

    if b & (1 << 63):
        for c in range(7, -1, -1):
            if b & (1 << (56 + c)):
                score += 1
            else:
                break
        for r in range(6, -1, -1):
            if b & (1 << (r * 8 + 7)):
                score += 1
            else:
                break

    return score


def _evaluate(p, o):
    occupied = p | o
    empty = (~occupied) & FULL
    empties = 64 - occupied.bit_count()

    pc = p.bit_count()
    oc = o.bit_count()

    my_moves = _legal_moves(p, o).bit_count()
    op_moves = _legal_moves(o, p).bit_count()

    # Mobility is one of the most important midgame features.
    mobility = 0
    if my_moves + op_moves:
        mobility = int(420 * (my_moves - op_moves) / (my_moves + op_moves))

    my_corners = (p & CORNER_MASK).bit_count()
    op_corners = (o & CORNER_MASK).bit_count()
    corner_score = 1250 * (my_corners - op_corners)

    # Penalize occupying squares next to empty corners.
    corner_closeness = 0
    for corner, adj in CORNER_ADJ:
        if not (occupied & corner):
            corner_closeness -= 260 * ((p & adj).bit_count() - (o & adj).bit_count())

    # Frontier discs are vulnerable.
    adj_empty = _adjacent(empty)
    my_front = (p & adj_empty).bit_count()
    op_front = (o & adj_empty).bit_count()
    frontier = 0
    if my_front + op_front:
        frontier = int(-170 * (my_front - op_front) / (my_front + op_front))

    # Potential mobility: empty squares adjacent to opponent discs.
    my_pot = (_adjacent(o) & empty).bit_count()
    op_pot = (_adjacent(p) & empty).bit_count()
    potential = 0
    if my_pot + op_pot:
        potential = int(110 * (my_pot - op_pot) / (my_pot + op_pot))

    pos_diff = _weighted_sum(p) - _weighted_sum(o)
    if empties > 24:
        pos_term = 4 * pos_diff
        parity = 2 * (pc - oc)
    elif empties > 10:
        pos_term = 2 * pos_diff
        parity = 8 * (pc - oc)
    else:
        pos_term = pos_diff
        parity = 75 * (pc - oc)

    edge_safe = 65 * (_edge_stability_like(p) - _edge_stability_like(o))

    return (
        mobility +
        corner_score +
        corner_closeness +
        frontier +
        potential +
        pos_term +
        parity +
        edge_safe
    )


def _move_order_score(p, o, move, tt_best=0):
    if move == tt_best:
        return 10 ** 9

    idx = move.bit_length() - 1
    score = POS[idx] * 10

    if move & CORNER_MASK:
        score += 1_000_000

    occupied = p | o

    if idx in X_CORNER:
        corner_bit = 1 << X_CORNER[idx]
        if not (occupied & corner_bit):
            score -= 200_000
        elif p & corner_bit:
            score += 5_000

    if idx in C_CORNER:
        corner_bit = 1 << C_CORNER[idx]
        if not (occupied & corner_bit):
            score -= 70_000
        elif p & corner_bit:
            score += 3_000

    # Prefer moves that immediately reduce opponent mobility.
    np_, no_ = _make_move(p, o, move)
    opp_mob = _legal_moves(no_, np_).bit_count()
    score -= 120 * opp_mob

    return score


def _ordered_moves(p, o, moves_mask, tt_best=0):
    arr = list(_bits(moves_mask))
    arr.sort(key=lambda m: _move_order_score(p, o, m, tt_best), reverse=True)
    return arr


def _to_bitboards(you, opponent):
    p = 0
    o = 0
    # Convert using Python loops; reliable for any integer numpy dtype.
    for r in range(8):
        base = r * 8
        yr = you[r]
        orow = opponent[r]
        for c in range(8):
            bit = 1 << (base + c)
            if int(yr[c]):
                p |= bit
            elif int(orow[c]):
                o |= bit
    return p, o


def _move_to_string(move):
    idx = move.bit_length() - 1
    r, c = divmod(idx, 8)
    return chr(ord("a") + c) + str(r + 1)


def _fallback_policy(you, opponent):
    p, o = _to_bitboards(you, opponent)
    moves = _legal_moves(p, o)
    if not moves:
        return "pass"

    # Safe emergency fallback: choose best statically ordered legal move.
    move = _ordered_moves(p, o, moves)[0]
    return _move_to_string(move)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    try:
        start = time.perf_counter()
        deadline = start + 0.90

        p, o = _to_bitboards(you, opponent)
        root_moves_mask = _legal_moves(p, o)

        if not root_moves_mask:
            return "pass"

        root_moves = _ordered_moves(p, o, root_moves_mask)
        best_move = root_moves[0]

        occupied = p | o
        empties = 64 - occupied.bit_count()

        # Iterative deepening. Endgames are searched deeper when possible.
        if empties <= 10:
            max_depth = 64
        elif empties <= 14:
            max_depth = 18
        elif empties <= 22:
            max_depth = 12
        elif empties <= 42:
            max_depth = 9
        else:
            max_depth = 7

        tt = {}
        nodes = 0

        def negamax(cp, co, depth, alpha, beta):
            nonlocal nodes

            nodes += 1
            if (nodes & 1023) == 0 and time.perf_counter() > deadline:
                raise TimeoutError

            alpha_orig = alpha
            key = (cp, co)
            entry = tt.get(key)
            tt_best = 0
            if entry is not None:
                e_depth, e_val, e_flag, e_best = entry
                tt_best = e_best
                if e_depth >= depth:
                    if e_flag == 0:
                        return e_val
                    if e_flag == 1:
                        alpha = max(alpha, e_val)
                    elif e_flag == 2:
                        beta = min(beta, e_val)
                    if alpha >= beta:
                        return e_val

            moves = _legal_moves(cp, co)

            if not moves:
                opp_moves = _legal_moves(co, cp)
                if not opp_moves:
                    diff = cp.bit_count() - co.bit_count()
                    return diff * 1_000_000
                return -negamax(co, cp, depth - 1, -beta, -alpha)

            if depth <= 0:
                return _evaluate(cp, co)

            best_val = -INF
            best_local = 0

            for mv in _ordered_moves(cp, co, moves, tt_best):
                np_, no_ = _make_move(cp, co, mv)
                val = -negamax(no_, np_, depth - 1, -beta, -alpha)

                if val > best_val:
                    best_val = val
                    best_local = mv

                if val > alpha:
                    alpha = val

                if alpha >= beta:
                    break

            if best_val <= alpha_orig:
                flag = 2  # upper bound
            elif best_val >= beta:
                flag = 1  # lower bound
            else:
                flag = 0  # exact

            tt[key] = (depth, best_val, flag, best_local)
            return best_val

        # Search from shallow to deep; keep last fully completed result.
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break

            try:
                alpha = -INF
                beta = INF
                current_best = best_move
                current_best_val = -INF
                scored = []

                for mv in root_moves:
                    if time.perf_counter() > deadline:
                        raise TimeoutError

                    np_, no_ = _make_move(p, o, mv)
                    val = -negamax(no_, np_, depth - 1, -beta, -alpha)
                    scored.append((val, mv))

                    if val > current_best_val:
                        current_best_val = val
                        current_best = mv

                    if val > alpha:
                        alpha = val

                best_move = current_best
                scored.sort(reverse=True)
                root_moves = [mv for _, mv in scored]

                # If a complete exact endgame search was reached, no need to go deeper.
                if depth >= empties + 2:
                    break

            except TimeoutError:
                break

        return _move_to_string(best_move)

    except Exception:
        # Never risk an illegal/non-string response.
        return _fallback_policy(you, opponent)
