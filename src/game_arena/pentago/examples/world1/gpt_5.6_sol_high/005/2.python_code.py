
import time

FULL = (1 << 36) - 1
WIN_SCORE = 1_000_000
INF = 2_000_000

# All possible five-cell winning segments.
WIN_MASKS = []
for r in range(6):
    for c in range(2):
        m = 0
        for i in range(5):
            m |= 1 << (r * 6 + c + i)
        WIN_MASKS.append(m)

for c in range(6):
    for r in range(2):
        m = 0
        for i in range(5):
            m |= 1 << ((r + i) * 6 + c)
        WIN_MASKS.append(m)

for r in range(2):
    for c in range(2):
        m = 0
        for i in range(5):
            m |= 1 << ((r + i) * 6 + c + i)
        WIN_MASKS.append(m)

for r in range(2):
    for c in (4, 5):
        m = 0
        for i in range(5):
            m |= 1 << ((r + i) * 6 + c - i)
        WIN_MASKS.append(m)

# Starting cells for fast five-in-a-row detection.
H_START = sum(1 << (r * 6 + c) for r in range(6) for c in range(2))
V_START = sum(1 << (r * 6 + c) for r in range(2) for c in range(6))
D_START = sum(1 << (r * 6 + c) for r in range(2) for c in range(2))
A_START = sum(1 << (r * 6 + c) for r in range(2) for c in (4, 5))

QUAD_MASKS = []
for q in range(4):
    qr = (q // 2) * 3
    qc = (q % 2) * 3
    m = 0
    for r in range(qr, qr + 3):
        for c in range(qc, qc + 3):
            m |= 1 << (r * 6 + c)
    QUAD_MASKS.append(m)

# ROT_TABLE[k][x] gives the globally positioned rotated version of a
# compact 9-bit quadrant x. k = quadrant * 2 + direction, with 0=L, 1=R.
ROT_TABLE = [[0] * 512 for _ in range(8)]
for q in range(4):
    qr = (q // 2) * 3
    qc = (q % 2) * 3
    for direction in range(2):
        k = q * 2 + direction
        for x in range(512):
            out = 0
            for lr in range(3):
                for lc in range(3):
                    if x & (1 << (lr * 3 + lc)):
                        if direction == 0:  # Left
                            nr, nc = 2 - lc, lr
                        else:               # Right
                            nr, nc = lc, 2 - lr
                        out |= 1 << ((qr + nr) * 6 + qc + nc)
            ROT_TABLE[k][x] = out

# Destination of a single placed marble after each possible rotation.
PLACED_BIT = [[0] * 36 for _ in range(8)]
for k in range(8):
    q = k // 2
    direction = k & 1
    qr = (q // 2) * 3
    qc = (q % 2) * 3
    for p in range(36):
        r, c = divmod(p, 6)
        if qr <= r < qr + 3 and qc <= c < qc + 3:
            lr, lc = r - qr, c - qc
            if direction == 0:
                nr, nc = 2 - lc, lr
            else:
                nr, nc = lc, 2 - lr
            PLACED_BIT[k][p] = 1 << ((qr + nr) * 6 + qc + nc)
        else:
            PLACED_BIT[k][p] = 1 << p

# The centers of quadrants do not move under rotation.
STABLE_CENTERS = (
    (1 << (1 * 6 + 1)) |
    (1 << (1 * 6 + 4)) |
    (1 << (4 * 6 + 1)) |
    (1 << (4 * 6 + 4))
)

LINE_VALUE = (0, 2, 13, 76, 520, WIN_SCORE)

_DEADLINE = 0.0
_NODES = 0
_TT = {}


class _SearchTimeout(Exception):
    pass


def _has_win(b):
    h = b & (b >> 1) & (b >> 2) & (b >> 3) & (b >> 4) & H_START
    if h:
        return True

    v = b & (b >> 6) & (b >> 12) & (b >> 18) & (b >> 24) & V_START
    if v:
        return True

    d = b & (b >> 7) & (b >> 14) & (b >> 21) & (b >> 28) & D_START
    if d:
        return True

    a = b & (b >> 5) & (b >> 10) & (b >> 15) & (b >> 20) & A_START
    return bool(a)


def _rotate_board(b, k):
    q = k // 2
    qr = (q // 2) * 3
    qc = (q % 2) * 3
    base = qr * 6 + qc

    x = (
        ((b >> base) & 7) |
        (((b >> (base + 6)) & 7) << 3) |
        (((b >> (base + 12)) & 7) << 6)
    )
    return (b & ~QUAD_MASKS[q]) | ROT_TABLE[k][x]


def _evaluate(a, b):
    score = 0

    for m in WIN_MASKS:
        am = a & m
        bm = b & m
        if not bm:
            score += LINE_VALUE[am.bit_count()]
        if not am:
            score -= LINE_VALUE[bm.bit_count()]

    score += 10 * (
        (a & STABLE_CENTERS).bit_count() -
        (b & STABLE_CENTERS).bit_count()
    )
    return score


def _terminal_value(a, b):
    wa = _has_win(a)
    wb = _has_win(b)

    if wa and wb:
        return 0
    if wa:
        return WIN_SCORE
    if wb:
        return -WIN_SCORE
    if (a | b) == FULL:
        return 0
    return None


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 7) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout


def _children(a, b):
    _check_time()

    occupied = a | b
    empty_bits = FULL ^ occupied
    empty_positions = []

    z = empty_bits
    while z:
        bit = z & -z
        empty_positions.append(bit.bit_length() - 1)
        z ^= bit

    result = []
    seen = set()

    for k in range(8):
        ra = _rotate_board(a, k)
        rb = _rotate_board(b, k)

        for p in empty_positions:
            na = ra | PLACED_BIT[k][p]
            nb = rb
            state_key = na | (nb << 36)

            if state_key in seen:
                continue
            seen.add(state_key)

            wa = _has_win(na)
            wb = _has_win(nb)

            if wa and wb:
                score = 0
            elif wa:
                score = WIN_SCORE
            elif wb:
                score = -WIN_SCORE
            elif (na | nb) == FULL:
                score = 0
            else:
                score = _evaluate(na, nb)

            result.append((score, na, nb, p, k))

    return result


def _search(a, b, depth, alpha, beta):
    terminal = _terminal_value(a, b)
    if terminal is not None:
        return terminal

    if depth <= 0:
        return _evaluate(a, b)

    key = (a, b, depth)
    cached = _TT.get(key)
    if cached is not None:
        return cached

    moves = _children(a, b)

    if depth == 1:
        value = max(m[0] for m in moves)
        _TT[key] = value
        return value

    moves.sort(key=lambda m: m[0], reverse=True)
    best = -INF
    completed = True

    for move_score, na, nb, _, _ in moves:
        if move_score == WIN_SCORE:
            value = WIN_SCORE
        else:
            value = -_search(nb, na, depth - 1, -beta, -alpha)

        if value > best:
            best = value
        if value > alpha:
            alpha = value

        if alpha >= beta:
            completed = False
            break

    if completed:
        _TT[key] = best
    return best


def _root_search(a, b, depth, preferred_state=None):
    moves = _children(a, b)

    if preferred_state is None:
        moves.sort(key=lambda m: m[0], reverse=True)
    else:
        pa, pb = preferred_state
        moves.sort(
            key=lambda m: ((m[1] == pa and m[2] == pb), m[0]),
            reverse=True
        )

    best_value = -INF
    best_move = moves[0]
    alpha = -INF

    for move in moves:
        move_score, na, nb, _, _ = move

        if depth == 1:
            value = move_score
        elif move_score == WIN_SCORE:
            value = WIN_SCORE
        else:
            value = -_search(nb, na, depth - 1, -INF, -alpha)

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if best_value == WIN_SCORE:
            break

    return best_value, best_move, (best_move[1], best_move[2])


def _format_move(move):
    _, _, _, p, k = move
    r, c = divmod(p, 6)
    q = k // 2
    direction = "L" if (k & 1) == 0 else "R"
    return f"{r + 1},{c + 1},{q},{direction}"


def policy(you, opponent) -> str:
    global _DEADLINE, _NODES, _TT

    a = 0
    b = 0
    fallback_p = None

    for r in range(6):
        for c in range(6):
            p = r * 6 + c
            if int(you[r][c]):
                a |= 1 << p
            elif int(opponent[r][c]):
                b |= 1 << p
            elif fallback_p is None:
                fallback_p = p

    # A legal move is established before any search is attempted.
    fr, fc = divmod(fallback_p, 6)
    fallback = f"{fr + 1},{fc + 1},0,L"

    # Strong, rotation-stable opening.
    if (a | b) == 0:
        return "2,2,0,L"

    _DEADLINE = time.perf_counter() + 0.92
    _NODES = 0
    _TT = {}

    empties = 36 - (a | b).bit_count()
    if empties >= 19:
        max_depth = 3
    elif empties >= 13:
        max_depth = 4
    elif empties >= 8:
        max_depth = 5
    else:
        max_depth = min(7, empties)

    best_string = fallback
    preferred_state = None

    try:
        for depth in range(1, max_depth + 1):
            value, move, state = _root_search(
                a, b, depth, preferred_state
            )
            best_string = _format_move(move)
            preferred_state = state

            if value == WIN_SCORE:
                break

    except _SearchTimeout:
        pass

    return best_string
