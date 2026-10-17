
import time
import numpy as np

FULL = (1 << 64) - 1
A_FILE = 0x0101010101010101
H_FILE = 0x8080808080808080
NOT_A = FULL ^ A_FILE
NOT_H = FULL ^ H_FILE
INNER_FILES = 0x7E7E7E7E7E7E7E7E
CORNERS = 0x8100000000000081
EDGES = 0xFF818181818181FF
PACK_COLUMN = 0x0102040810204080
WIN = 100000

# Rays used to locate the first non-opponent disc in each direction.
RAYS = []
for r in range(8):
    for c in range(8):
        positive, negative = [], []
        for dr, dc in (
            (-1, -1), (-1, 0), (-1, 1), (0, -1),
            (0, 1), (1, -1), (1, 0), (1, 1)
        ):
            rr, cc = r + dr, c + dc
            ray = 0
            while 0 <= rr < 8 and 0 <= cc < 8:
                ray |= 1 << (rr * 8 + cc)
                rr += dr
                cc += dc
            if ray:
                if dr * 8 + dc > 0:
                    positive.append(ray)
                else:
                    negative.append(ray)
        RAYS.append((tuple(positive), tuple(negative)))

# Stable runs along an edge, anchored at either endpoint.
EDGE_STABILITY = []
for pattern in range(256):
    stable = 0
    for i in range(8):
        if pattern & (1 << i):
            stable |= 1 << i
        else:
            break
    for i in range(7, -1, -1):
        if pattern & (1 << i):
            stable |= 1 << i
        else:
            break
    EDGE_STABILITY.append(stable.bit_count())

CORNER_NEIGHBORS = (
    (1 << 0, 1 << 9, (1 << 1) | (1 << 8)),
    (1 << 7, 1 << 14, (1 << 6) | (1 << 15)),
    (1 << 56, 1 << 49, (1 << 48) | (1 << 57)),
    (1 << 63, 1 << 54, (1 << 55) | (1 << 62)),
)

INNER = 0
SECOND_RING = 0
ORDER_VALUE = [0] * 64
RISK_CORNER = [0] * 64
RISK_PENALTY = [0] * 64
for r in range(8):
    for c in range(8):
        i = r * 8 + c
        b = 1 << i
        if 2 <= r <= 5 and 2 <= c <= 5:
            INNER |= b
        if (r in (1, 6) or c in (1, 6)) and 1 <= r <= 6 and 1 <= c <= 6:
            SECOND_RING |= b
        ORDER_VALUE[i] = 12
        if r in (0, 7) or c in (0, 7):
            ORDER_VALUE[i] = 65
        if b & CORNERS:
            ORDER_VALUE[i] = 3000

for corner, x_square, c_squares in CORNER_NEIGHBORS:
    i = x_square.bit_length() - 1
    RISK_CORNER[i] = corner
    RISK_PENALTY[i] = 420
    remaining = c_squares
    while remaining:
        b = remaining & -remaining
        remaining ^= b
        i = b.bit_length() - 1
        RISK_CORNER[i] = corner
        RISK_PENALTY[i] = 180

WEIGHTS = [
    (
        42 + min(e, 32),       # actual mobility
        3 + e // 6,           # potential mobility
        6 + e // 4,           # frontier exposure
        -2 if e > 24 else 2 * (24 - e),
        115 + (60 - e) // 2,  # stable edges
    )
    for e in range(65)
]

_TT = {}
_HISTORY = [0] * 64
_KILLERS = [[0, 0] for _ in range(130)]
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _legal(p, o):
    """All legal moves for p, as a bitboard."""
    horizontal = o & INNER_FILES

    m = horizontal
    a = m & (p << 1)
    b = m & (p >> 1)
    a |= m & (a << 1)
    b |= m & (b >> 1)
    ma = m & (m << 1)
    mb = m & (m >> 1)
    a |= ma & (a << 2)
    b |= mb & (b >> 2)
    a |= ma & (a << 2)
    b |= mb & (b >> 2)
    result = (a << 1) | (b >> 1)

    m = o
    a = m & (p << 8)
    b = m & (p >> 8)
    a |= m & (a << 8)
    b |= m & (b >> 8)
    ma = m & (m << 8)
    mb = m & (m >> 8)
    a |= ma & (a << 16)
    b |= mb & (b >> 16)
    a |= ma & (a << 16)
    b |= mb & (b >> 16)
    result |= (a << 8) | (b >> 8)

    m = horizontal
    a = m & (p << 7)
    b = m & (p >> 7)
    a |= m & (a << 7)
    b |= m & (b >> 7)
    ma = m & (m << 7)
    mb = m & (m >> 7)
    a |= ma & (a << 14)
    b |= mb & (b >> 14)
    a |= ma & (a << 14)
    b |= mb & (b >> 14)
    result |= (a << 7) | (b >> 7)

    a = m & (p << 9)
    b = m & (p >> 9)
    a |= m & (a << 9)
    b |= m & (b >> 9)
    ma = m & (m << 9)
    mb = m & (m >> 9)
    a |= ma & (a << 18)
    b |= mb & (b >> 18)
    a |= ma & (a << 18)
    b |= mb & (b >> 18)
    result |= (a << 9) | (b >> 9)

    return result & (FULL ^ (p | o))


def _flips(p, o, square):
    positive, negative = RAYS[square]
    not_o = ~o
    result = 0

    for ray in positive:
        blockers = ray & not_o
        first = blockers & -blockers
        if first & p:
            result |= ray & (first - 1)

    for ray in negative:
        blockers = ray & not_o
        if blockers:
            first = 1 << (blockers.bit_length() - 1)
            if first & p:
                result |= ray & -(first << 1)

    return result


def _adjacent(b):
    horizontal = ((b & NOT_A) >> 1) | ((b & NOT_H) << 1)
    expanded = b | horizontal
    return (horizontal | (expanded << 8) | (expanded >> 8)) & FULL


def _line_stability(a, b):
    if (a | b) == 255:
        return a.bit_count() - b.bit_count()
    return EDGE_STABILITY[a] - EDGE_STABILITY[b]


def _stable_difference(p, o, corner_difference):
    result = _line_stability(p & 255, o & 255)
    result += _line_stability(p >> 56, o >> 56)

    pa = (((p & A_FILE) * PACK_COLUMN) >> 56) & 255
    oa = (((o & A_FILE) * PACK_COLUMN) >> 56) & 255
    result += _line_stability(pa, oa)

    ph = ((((p >> 7) & A_FILE) * PACK_COLUMN) >> 56) & 255
    oh = ((((o >> 7) & A_FILE) * PACK_COLUMN) >> 56) & 255
    result += _line_stability(ph, oh)

    # Corners were included in both their incident edges.
    return result - corner_difference


def _evaluate(p, o, moves, empties):
    occupied = p | o
    empty = FULL ^ occupied
    opponent_moves = _legal(o, p)
    wm, wp, wf, wd, ws = WEIGHTS[empties]

    score = wm * (moves.bit_count() - opponent_moves.bit_count())
    score += 300 * (
        (moves & CORNERS).bit_count()
        - (opponent_moves & CORNERS).bit_count()
    )

    score += wp * (
        (empty & _adjacent(o)).bit_count()
        - (empty & _adjacent(p)).bit_count()
    )

    frontier = _adjacent(empty)
    score += wf * (
        (o & frontier).bit_count() - (p & frontier).bit_count()
    )

    corner_difference = (
        (p & CORNERS).bit_count() - (o & CORNERS).bit_count()
    )
    score += 950 * corner_difference

    if occupied & CORNERS:
        score += ws * _stable_difference(p, o, corner_difference)

    for corner, x_square, c_squares in CORNER_NEIGHBORS:
        if not (occupied & corner):
            score -= 280 * (
                (p & x_square).bit_count() - (o & x_square).bit_count()
            )
            score -= 115 * (
                (p & c_squares).bit_count() - (o & c_squares).bit_count()
            )

    score += 15 * ((p & EDGES).bit_count() - (o & EDGES).bit_count())
    score += 12 * ((p & INNER).bit_count() - (o & INNER).bit_count())
    score -= 8 * (
        (p & SECOND_RING).bit_count() - (o & SECOND_RING).bit_count()
    )
    score += wd * (p.bit_count() - o.bit_count())

    if empties <= 18:
        score += 8 if empties & 1 else -8

    return score


def _terminal(p, o):
    difference = p.bit_count() - o.bit_count()
    if difference > 0:
        return WIN
    if difference < 0:
        return -WIN
    return 0


def _odd_regions(empty):
    remaining = empty
    odd = 0
    while remaining:
        region = remaining & -remaining
        while True:
            neighbors = (
                ((region & NOT_A) >> 1)
                | ((region & NOT_H) << 1)
                | (region >> 8)
                | (region << 8)
            )
            expanded = region | (neighbors & empty)
            if expanded == region:
                break
            region = expanded
        remaining &= ~region
        if region.bit_count() & 1:
            odd |= region
    return odd


def _ordered_moves(p, o, moves, tt_move, depth, empties, ply):
    # Yield the hash move before preparing the remaining candidates.
    # A cutoff here avoids all the subsequent ordering work.
    if tt_move & moves:
        i = tt_move.bit_length() - 1
        yield tt_move, _flips(p, o, i), -1
        moves ^= tt_move

    if not moves:
        return

    occupied = p | o
    odd = 0
    if empties <= 12 and depth >= 3:
        odd = _odd_regions(FULL ^ occupied)

    killer1, killer2 = _KILLERS[ply]
    candidates = []
    while moves:
        move = moves & -moves
        moves ^= move
        i = move.bit_length() - 1

        value = ORDER_VALUE[i] + min(_HISTORY[i], 450)
        if move == killer1:
            value += 350
        elif move == killer2:
            value += 220

        corner = RISK_CORNER[i]
        if corner and not (occupied & corner):
            value -= RISK_PENALTY[i]

        if move & odd:
            value += 140

        flips = -1
        child_moves = -1
        if depth >= 3:
            flips = _flips(p, o, i)
            child_p = o ^ flips
            child_o = p | move | flips
            child_moves = _legal(child_p, child_o)
            value -= 80 * child_moves.bit_count()
            value -= 800 * (child_moves & CORNERS).bit_count()
            if not child_moves:
                value += 300

        candidates.append((value, move, flips, child_moves))

    candidates.sort(reverse=True)
    for _, move, flips, child_moves in candidates:
        yield move, flips, child_moves


def _search(p, o, depth, alpha, beta, empties, ply, moves=-1):
    global _NODES

    _NODES += 1
    if (_NODES & 63) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout

    if empties == 0:
        return _terminal(p, o)

    key = (p, o)
    original_alpha = alpha
    entry = _TT.get(key)
    tt_move = 0

    if entry is not None:
        old_depth, old_score, old_flag, tt_move = entry
        if old_depth >= depth:
            if old_flag == 0:
                return old_score
            if old_flag == 1 and old_score >= beta:
                return old_score
            if old_flag == 2 and old_score <= alpha:
                return old_score

    if moves == -1:
        moves = _legal(p, o)

    if not moves:
        opponent_moves = _legal(o, p)
        if not opponent_moves:
            value = _terminal(p, o)
            _TT[key] = (64, value, 0, 0)
            return value

        value = -_search(
            o, p, depth, -beta, -alpha, empties, ply + 1, opponent_moves
        )
        flag = 2 if value <= original_alpha else 1 if value >= beta else 0
        _TT[key] = (depth, value, flag, 0)
        return value

    # Solve the last square directly, even at the evaluation horizon.
    if empties == 1:
        move = moves & -moves
        flips = _flips(p, o, move.bit_length() - 1)
        difference = (
            p.bit_count() - o.bit_count() + 1 + 2 * flips.bit_count()
        )
        value = WIN if difference > 0 else -WIN if difference < 0 else 0
        _TT[key] = (64, value, 0, move)
        return value

    if depth <= 0:
        return _evaluate(p, o, moves, empties)

    best_value = -WIN - 1
    best_move = moves & -moves
    searched = 0
    exact_search = depth >= empties

    for move, flips, child_moves in _ordered_moves(
        p, o, moves, tt_move, depth, empties, ply
    ):
        if flips == -1:
            flips = _flips(p, o, move.bit_length() - 1)

        child_p = o ^ flips
        child_o = p | move | flips
        child_depth = depth - 1

        if searched == 0 or depth <= 2:
            value = -_search(
                child_p, child_o, child_depth,
                -beta, -alpha, empties - 1, ply + 1, child_moves
            )
        else:
            reduction = 0
            if (
                not exact_search
                and empties > 14
                and ply > 0
                and depth >= 4
                and searched >= 4
                and not (move & CORNERS)
                and child_moves != 0
                and move not in _KILLERS[ply]
            ):
                reduction = 1
                if depth >= 7 and searched >= 7:
                    reduction = 2

            value = -_search(
                child_p, child_o, child_depth - reduction,
                -alpha - 1, -alpha, empties - 1, ply + 1, child_moves
            )

            if reduction and value > alpha:
                value = -_search(
                    child_p, child_o, child_depth,
                    -alpha - 1, -alpha,
                    empties - 1, ply + 1, child_moves
                )

            if alpha < value < beta:
                value = -_search(
                    child_p, child_o, child_depth,
                    -beta, -alpha, empties - 1, ply + 1, child_moves
                )

        searched += 1
        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            i = move.bit_length() - 1
            _HISTORY[i] += depth * depth
            if _HISTORY[i] > 4000:
                for j in range(64):
                    _HISTORY[j] //= 2

            killers = _KILLERS[ply]
            if killers[0] != move:
                killers[1] = killers[0]
                killers[0] = move
            break

    flag = (
        2 if best_value <= original_alpha
        else 1 if best_value >= beta
        else 0
    )
    if entry is None or depth >= entry[0] or flag == 0:
        _TT[key] = (depth, best_value, flag, best_move)

    return best_value


def _move_string(move):
    square = move.bit_length() - 1
    return chr(ord("a") + (square & 7)) + str((square >> 3) + 1)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _TT, _HISTORY, _KILLERS, _DEADLINE, _NODES

    start = time.perf_counter()
    _DEADLINE = start + 0.88
    _NODES = 0

    p = 0
    o = 0
    for r in range(8):
        for c in range(8):
            bit = 1 << (8 * r + c)
            if you[r][c]:
                p |= bit
            elif opponent[r][c]:
                o |= bit

    legal = _legal(p, o)
    if not legal:
        return "pass"

    # Establish a legal answer before doing any potentially interrupted work.
    corners = legal & CORNERS
    best_move = (corners & -corners) if corners else (legal & -legal)

    if legal & (legal - 1) == 0:
        return _move_string(best_move)

    if len(_TT) > 160000:
        _TT = {}

    _HISTORY = [0] * 64
    _KILLERS = [[0, 0] for _ in range(130)]

    empties = 64 - (p | o).bit_count()
    root_key = (p, o)
    entry = _TT.get(root_key)
    if entry is not None and entry[3] & legal:
        best_move = entry[3]

    previous_score = 0
    depth = 1

    try:
        while depth <= empties:
            if time.perf_counter() >= _DEADLINE:
                break

            if depth >= 4 and depth < empties:
                low = max(-WIN - 1, previous_score - 400)
                high = min(WIN, previous_score + 400)
            else:
                low, high = -WIN - 1, WIN

            score = _search(p, o, depth, low, high, empties, 0, legal)

            # A proven win/loss needs no wider aspiration search.
            if abs(score) != WIN and (score <= low or score >= high):
                score = _search(
                    p, o, depth, -WIN - 1, WIN, empties, 0, legal
                )

            root_entry = _TT.get(root_key)
            if root_entry is not None and root_entry[3] & legal:
                best_move = root_entry[3]

            previous_score = score
            if abs(score) == WIN or depth >= empties:
                break

            if empties <= 10 and depth >= 4:
                depth = empties
            else:
                depth += 1

    except _SearchTimeout:
        pass

    # Keep the return contract independent of search completion.
    if not (best_move & legal) or best_move & (best_move - 1):
        best_move = legal & -legal
    return _move_string(best_move)
