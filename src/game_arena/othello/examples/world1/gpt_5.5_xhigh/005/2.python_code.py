
import time
import numpy as np

ALL = (1 << 64) - 1
FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
NOT_A = ALL ^ FILE_A
NOT_H = ALL ^ FILE_H

BITS = tuple(1 << i for i in range(64))
CORNERS = BITS[0] | BITS[7] | BITS[56] | BITS[63]

MOVE_NAMES = tuple(chr(97 + (i & 7)) + str((i >> 3) + 1) for i in range(64))

INF = 10 ** 18
TERMINAL_UNIT = 1_000_000

EXACT, LOWER, UPPER = 0, 1, 2
TT_LIMIT = 250_000

# Classic Othello square values. Dynamic corner-danger logic below adjusts these.
POS = (
    120, -35,  20,   5,   5,  20, -35, 120,
    -35, -60,  -5,  -5,  -5,  -5, -60, -35,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -35, -60,  -5,  -5,  -5,  -5, -60, -35,
    120, -35,  20,   5,   5,  20, -35, 120,
)
ORDER_SCORE = tuple(v * 100 for v in POS)

BYTE_WEIGHT = []
for r in range(8):
    row = []
    base = r * 8
    for byte in range(256):
        s = 0
        for c in range(8):
            if byte & (1 << c):
                s += POS[base + c]
        row.append(s)
    BYTE_WEIGHT.append(tuple(row))
BYTE_WEIGHT = tuple(BYTE_WEIGHT)

# corner, diagonal X-square, orthogonal C-squares, all adjacent-to-corner squares
CORNER_DATA = (
    (BITS[0],  BITS[9],  BITS[1]  | BITS[8],  BITS[1]  | BITS[8]  | BITS[9]),
    (BITS[7],  BITS[14], BITS[6]  | BITS[15], BITS[6]  | BITS[15] | BITS[14]),
    (BITS[56], BITS[49], BITS[48] | BITS[57], BITS[48] | BITS[57] | BITS[49]),
    (BITS[63], BITS[54], BITS[55] | BITS[62], BITS[55] | BITS[62] | BITS[54]),
)

def _ray(r, c, dr, dc):
    out = []
    r += dr
    c += dc
    while 0 <= r < 8 and 0 <= c < 8:
        out.append(1 << (r * 8 + c))
        r += dr
        c += dc
    return tuple(out)

CORNER_RAYS = (
    (BITS[0],  _ray(0, 0, 0, 1),  _ray(0, 0, 1, 0)),
    (BITS[7],  _ray(0, 7, 0, -1), _ray(0, 7, 1, 0)),
    (BITS[56], _ray(7, 0, 0, 1),  _ray(7, 0, -1, 0)),
    (BITS[63], _ray(7, 7, 0, -1), _ray(7, 7, -1, 0)),
)

_TT = {}
_DEADLINE = 0.0
_NODES = 0
_HISTORY = [0] * 64
_KILLER = [0] * 65


class _SearchTimeout(Exception):
    pass


def _array_to_bits(a: np.ndarray) -> int:
    b = 0
    flat = a.ravel()
    for i in range(64):
        if flat[i]:
            b |= 1 << i
    return b


def _legal_moves(P: int, O: int) -> int:
    empty = ALL ^ (P | O)
    moves = 0

    # East
    x = ((P & NOT_H) << 1) & O
    x |= ((x & NOT_H) << 1) & O
    x |= ((x & NOT_H) << 1) & O
    x |= ((x & NOT_H) << 1) & O
    x |= ((x & NOT_H) << 1) & O
    x |= ((x & NOT_H) << 1) & O
    moves |= ((x & NOT_H) << 1) & empty

    # West
    x = ((P & NOT_A) >> 1) & O
    x |= ((x & NOT_A) >> 1) & O
    x |= ((x & NOT_A) >> 1) & O
    x |= ((x & NOT_A) >> 1) & O
    x |= ((x & NOT_A) >> 1) & O
    x |= ((x & NOT_A) >> 1) & O
    moves |= ((x & NOT_A) >> 1) & empty

    # South
    x = (P << 8) & O
    x |= (x << 8) & O
    x |= (x << 8) & O
    x |= (x << 8) & O
    x |= (x << 8) & O
    x |= (x << 8) & O
    moves |= (x << 8) & empty

    # North
    x = (P >> 8) & O
    x |= (x >> 8) & O
    x |= (x >> 8) & O
    x |= (x >> 8) & O
    x |= (x >> 8) & O
    x |= (x >> 8) & O
    moves |= (x >> 8) & empty

    # South-East
    x = ((P & NOT_H) << 9) & O
    x |= ((x & NOT_H) << 9) & O
    x |= ((x & NOT_H) << 9) & O
    x |= ((x & NOT_H) << 9) & O
    x |= ((x & NOT_H) << 9) & O
    x |= ((x & NOT_H) << 9) & O
    moves |= ((x & NOT_H) << 9) & empty

    # South-West
    x = ((P & NOT_A) << 7) & O
    x |= ((x & NOT_A) << 7) & O
    x |= ((x & NOT_A) << 7) & O
    x |= ((x & NOT_A) << 7) & O
    x |= ((x & NOT_A) << 7) & O
    x |= ((x & NOT_A) << 7) & O
    moves |= ((x & NOT_A) << 7) & empty

    # North-East
    x = ((P & NOT_H) >> 7) & O
    x |= ((x & NOT_H) >> 7) & O
    x |= ((x & NOT_H) >> 7) & O
    x |= ((x & NOT_H) >> 7) & O
    x |= ((x & NOT_H) >> 7) & O
    x |= ((x & NOT_H) >> 7) & O
    moves |= ((x & NOT_H) >> 7) & empty

    # North-West
    x = ((P & NOT_A) >> 9) & O
    x |= ((x & NOT_A) >> 9) & O
    x |= ((x & NOT_A) >> 9) & O
    x |= ((x & NOT_A) >> 9) & O
    x |= ((x & NOT_A) >> 9) & O
    x |= ((x & NOT_A) >> 9) & O
    moves |= ((x & NOT_A) >> 9) & empty

    return moves


def _make_move(P: int, O: int, move: int):
    flips = 0

    cap = 0
    x = (move & NOT_H) << 1
    while x & O:
        cap |= x
        x = (x & NOT_H) << 1
    if x & P:
        flips |= cap

    cap = 0
    x = (move & NOT_A) >> 1
    while x & O:
        cap |= x
        x = (x & NOT_A) >> 1
    if x & P:
        flips |= cap

    cap = 0
    x = (move << 8) & ALL
    while x & O:
        cap |= x
        x = (x << 8) & ALL
    if x & P:
        flips |= cap

    cap = 0
    x = move >> 8
    while x & O:
        cap |= x
        x >>= 8
    if x & P:
        flips |= cap

    cap = 0
    x = ((move & NOT_H) << 9) & ALL
    while x & O:
        cap |= x
        x = ((x & NOT_H) << 9) & ALL
    if x & P:
        flips |= cap

    cap = 0
    x = ((move & NOT_A) << 7) & ALL
    while x & O:
        cap |= x
        x = ((x & NOT_A) << 7) & ALL
    if x & P:
        flips |= cap

    cap = 0
    x = (move & NOT_H) >> 7
    while x & O:
        cap |= x
        x = (x & NOT_H) >> 7
    if x & P:
        flips |= cap

    cap = 0
    x = (move & NOT_A) >> 9
    while x & O:
        cap |= x
        x = (x & NOT_A) >> 9
    if x & P:
        flips |= cap

    return P | move | flips, O ^ flips, flips


def _adjacent(x: int) -> int:
    return (
        ((x & NOT_H) << 1) |
        ((x & NOT_A) >> 1) |
        ((x << 8) & ALL) |
        (x >> 8) |
        (((x & NOT_H) << 9) & ALL) |
        (((x & NOT_A) << 7) & ALL) |
        ((x & NOT_H) >> 7) |
        ((x & NOT_A) >> 9)
    )


def _pos_sum(bb: int) -> int:
    bw = BYTE_WEIGHT
    return (
        bw[0][bb & 255] +
        bw[1][(bb >> 8) & 255] +
        bw[2][(bb >> 16) & 255] +
        bw[3][(bb >> 24) & 255] +
        bw[4][(bb >> 32) & 255] +
        bw[5][(bb >> 40) & 255] +
        bw[6][(bb >> 48) & 255] +
        bw[7][(bb >> 56) & 255]
    )


def _edge_stable_count(bb: int) -> int:
    stable = 0
    for corner, ray1, ray2 in CORNER_RAYS:
        if bb & corner:
            stable |= corner
            for b in ray1:
                if bb & b:
                    stable |= b
                else:
                    break
            for b in ray2:
                if bb & b:
                    stable |= b
                else:
                    break
    return stable.bit_count()


def _ratio(a: int, b: int) -> int:
    s = a + b
    if s == 0:
        return 0
    return (100 * (a - b)) // s


def _terminal_score(P: int, O: int) -> int:
    return (P.bit_count() - O.bit_count()) * TERMINAL_UNIT


def _evaluate(P: int, O: int, my_moves=None) -> int:
    occupied = P | O
    empty = ALL ^ occupied
    pc = P.bit_count()
    oc = O.bit_count()
    empties = 64 - pc - oc

    if my_moves is None:
        my_moves = _legal_moves(P, O)
    opp_moves = _legal_moves(O, P)

    if my_moves == 0 and opp_moves == 0:
        return _terminal_score(P, O)

    my_mob = my_moves.bit_count()
    opp_mob = opp_moves.bit_count()
    mobility = _ratio(my_mob, opp_mob)

    my_potential = (_adjacent(O) & empty).bit_count()
    opp_potential = (_adjacent(P) & empty).bit_count()
    potential = _ratio(my_potential, opp_potential)

    adj_empty = _adjacent(empty)
    my_frontier = (P & adj_empty).bit_count()
    opp_frontier = (O & adj_empty).bit_count()
    frontier = _ratio(opp_frontier, my_frontier)  # fewer frontier discs is better

    corner_diff = (P & CORNERS).bit_count() - (O & CORNERS).bit_count()
    corner_move_diff = (my_moves & CORNERS).bit_count() - (opp_moves & CORNERS).bit_count()

    danger = 0
    for corner, xmask, cmask, _ in CORNER_DATA:
        if not (occupied & corner):
            # Own discs next to an empty corner are dangerous; opponent's are exploitable.
            danger += 3 * ((O & xmask).bit_count() - (P & xmask).bit_count())
            danger += ((O & cmask).bit_count() - (P & cmask).bit_count())

    stable_diff = _edge_stable_count(P) - _edge_stable_count(O)
    pos_diff = _pos_sum(P) - _pos_sum(O)
    disc_diff = pc - oc

    if empties > 44:
        w_mob, w_pot, w_front, w_pos, w_disc, w_danger = 85, 40, 35, 18, -8, 3800
    elif empties > 20:
        w_mob, w_pot, w_front, w_pos, w_disc, w_danger = 100, 30, 30, 12, 4, 4200
    else:
        w_mob, w_pot, w_front, w_pos = 65, 10, 12, 6
        w_disc = 40 + (20 - empties) * 30
        w_danger = 3000

    w_corner = 28_000 if empties > 20 else 32_000
    w_stable = 1400 if empties > 20 else 1800

    score = 0
    score += w_mob * mobility
    score += w_pot * potential
    score += w_front * frontier
    score += w_pos * pos_diff
    score += w_disc * disc_diff
    score += w_corner * corner_diff
    score += 9000 * corner_move_diff
    score += w_danger * danger
    score += w_stable * stable_diff

    if opp_mob == 0 and my_mob > 0:
        score += 6000
    elif my_mob == 0 and opp_mob > 0:
        score -= 6000

    if empties <= 16:
        score += 300 if (empties & 1) else -300

    return score


def _time_check():
    if time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout()


def _store_tt(key, depth, value, flag, move):
    old = _TT.get(key)
    if old is None:
        if len(_TT) < TT_LIMIT:
            _TT[key] = (depth, value, flag, move)
    elif depth >= old[0]:
        _TT[key] = (depth, value, flag, move)


def _ordered_children(P: int, O: int, moves: int, hash_move: int, depth: int):
    occupied = P | O
    empties = 64 - occupied.bit_count()
    children = []

    m = moves
    while m:
        move = m & -m
        m ^= move

        P2, O2, flips = _make_move(P, O, move)
        sq = move.bit_length() - 1

        score = ORDER_SCORE[sq] + _HISTORY[sq]

        if move == hash_move:
            score += 10_000_000
        if depth < len(_KILLER) and move == _KILLER[depth]:
            score += 80_000
        if move & CORNERS:
            score += 2_000_000

        # Avoid giving away empty-corner access by playing X/C squares.
        for corner, xmask, cmask, _ in CORNER_DATA:
            if not (occupied & corner):
                if move & xmask:
                    score -= 300_000
                elif move & cmask:
                    score -= 120_000

        if depth >= 2:
            opp_moves = _legal_moves(O2, P2)
            opp_corner_moves = (opp_moves & CORNERS).bit_count()
            opp_mob = opp_moves.bit_count()

            score -= 220_000 * opp_corner_moves
            score -= 1500 * opp_mob
            if opp_mob == 0:
                score += 100_000

        fc = flips.bit_count()
        if empties <= 18:
            score += 300 * fc
        else:
            score -= 30 * fc

        children.append((score, move, P2, O2))

    children.sort(key=lambda t: t[0], reverse=True)
    return children


def _negamax(P: int, O: int, depth: int, alpha: int, beta: int) -> int:
    global _NODES

    _NODES += 1
    if (_NODES & 2047) == 0:
        _time_check()

    alpha0 = alpha
    beta0 = beta
    key = (P, O)

    entry = _TT.get(key)
    hash_move = 0
    if entry is not None:
        edepth, eval_, eflag, emove = entry
        hash_move = emove
        if edepth >= depth:
            if eflag == EXACT:
                return eval_
            elif eflag == LOWER:
                if eval_ > alpha:
                    alpha = eval_
            else:
                if eval_ < beta:
                    beta = eval_
            if alpha >= beta:
                return eval_

    moves = _legal_moves(P, O)

    if moves == 0:
        if _legal_moves(O, P) == 0:
            val = _terminal_score(P, O)
            _store_tt(key, depth, val, EXACT, 0)
            return val

        val = -_negamax(O, P, depth, -beta, -alpha)
        if val <= alpha0:
            flag = UPPER
        elif val >= beta0:
            flag = LOWER
        else:
            flag = EXACT
        _store_tt(key, depth, val, flag, 0)
        return val

    if depth <= 0:
        val = _evaluate(P, O, moves)
        _store_tt(key, 0, val, EXACT, 0)
        return val

    best_val = -INF
    best_move = 0
    first = True

    for _, move, P2, O2 in _ordered_children(P, O, moves, hash_move, depth):
        if first:
            val = -_negamax(O2, P2, depth - 1, -beta, -alpha)
            first = False
        else:
            # Principal variation search.
            val = -_negamax(O2, P2, depth - 1, -alpha - 1, -alpha)
            if alpha < val < beta:
                val = -_negamax(O2, P2, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = move

        if val > alpha:
            alpha = val

        if alpha >= beta:
            if depth < len(_KILLER):
                _KILLER[depth] = move
            _HISTORY[move.bit_length() - 1] += depth * depth * 20
            break

    if best_val <= alpha0:
        flag = UPPER
    elif best_val >= beta0:
        flag = LOWER
    else:
        flag = EXACT

    _store_tt(key, depth, best_val, flag, best_move)
    return best_val


def _root_search(P: int, O: int, depth: int, preferred: int):
    moves = _legal_moves(P, O)
    children = _ordered_children(P, O, moves, preferred, depth)

    best_val = -INF
    best_move = children[0][1]
    alpha = -INF
    beta = INF
    first = True

    for _, move, P2, O2 in children:
        _time_check()

        if first:
            val = -_negamax(O2, P2, depth - 1, -beta, -alpha)
            first = False
        else:
            val = -_negamax(O2, P2, depth - 1, -alpha - 1, -alpha)
            if alpha < val < beta:
                val = -_negamax(O2, P2, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = move

        if val > alpha:
            alpha = val

    _store_tt((P, O), depth, best_val, EXACT, best_move)
    return best_val, best_move


def _fallback_move(P: int, O: int, moves: int) -> int:
    best_move = moves & -moves
    best_val = -INF

    for _, move, P2, O2 in _ordered_children(P, O, moves, 0, 3):
        val = -_evaluate(O2, P2)
        if val > best_val:
            best_val = val
            best_move = move

    return best_move


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _TT, _DEADLINE, _NODES, _HISTORY, _KILLER

    start = time.perf_counter()
    _DEADLINE = start + 0.90

    P = _array_to_bits(you)
    O = _array_to_bits(opponent)

    moves = _legal_moves(P, O)
    if moves == 0:
        return "pass"

    _TT = {}
    _NODES = 0
    _HISTORY = [0] * 64
    _KILLER = [0] * 65

    best_move = _fallback_move(P, O, moves)

    # If there is only one legal move, return immediately.
    if moves & (moves - 1) == 0:
        return MOVE_NAMES[best_move.bit_length() - 1]

    empties = 64 - (P | O).bit_count()

    if empties <= 18:
        max_depth = empties
    elif empties <= 28:
        max_depth = 16
    else:
        max_depth = 12

    try:
        for depth in range(1, max_depth + 1):
            val, move = _root_search(P, O, depth, best_move)
            if move & moves:
                best_move = move

            if depth >= empties:
                break

            # Do not begin another iteration with almost no time left.
            if time.perf_counter() >= _DEADLINE - 0.025:
                break

            # A proven terminal result at full reachable depth is enough.
            if abs(val) >= TERMINAL_UNIT and depth >= empties:
                break

    except _SearchTimeout:
        pass
    except Exception:
        # Safety fallback: never risk an illegal/non-return due to an unexpected issue.
        if not (best_move & moves):
            best_move = moves & -moves

    if not (best_move & moves):
        best_move = moves & -moves

    return MOVE_NAMES[best_move.bit_length() - 1]
