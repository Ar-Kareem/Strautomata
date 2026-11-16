
import time

ROWS = 5
COLS = 6
N = ROWS * COLS
WIN = 1000000
INF = 10 ** 9

ADJ = [0] * N
DIR_FROM_TO = {}

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dr, dc, ch in [(-1, 0, "U"), (0, 1, "R"), (1, 0, "D"), (0, -1, "L")]:
            rr, cc = r + dr, c + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                j = rr * COLS + cc
                ADJ[i] |= 1 << j
                DIR_FROM_TO[(i, j)] = ch

TT = {}


def _bits(board):
    b = 0
    try:
        first = board[0]
        nested = hasattr(first, "__len__") and not isinstance(first, (int, bool))
    except Exception:
        nested = False

    if nested:
        for r in range(ROWS):
            row = board[r]
            base = r * COLS
            for c in range(COLS):
                if row[c]:
                    b |= 1 << (base + c)
    else:
        for i in range(N):
            if board[i]:
                b |= 1 << i
    return b


def _generate_moves(y, o):
    moves = []
    yy = y
    while yy:
        lb = yy & -yy
        s = lb.bit_length() - 1
        yy ^= lb
        targets = ADJ[s] & o
        while targets:
            tb = targets & -targets
            d = tb.bit_length() - 1
            targets ^= tb
            moves.append((s << 5) | d)
    return moves


def _make_move(y, o, m):
    s = m >> 5
    d = m & 31
    sb = 1 << s
    db = 1 << d
    y2 = (y & ~sb) | db
    o2 = o & ~db
    return y2, o2


def _edge_count(y, o):
    cnt = 0
    yy = y
    while yy:
        lb = yy & -yy
        s = lb.bit_length() - 1
        yy ^= lb
        cnt += (ADJ[s] & o).bit_count()
    return cnt


def _has_finishing_move(y, o):
    for m in _generate_moves(y, o):
        y2, o2 = _make_move(y, o, m)
        if _edge_count(o2, y2) == 0:
            return True
    return False


def _evaluate(y, o):
    e = _edge_count(y, o)
    if e == 0:
        return -WIN
    if e == 1:
        return 60000
    if e <= 3 and _has_finishing_move(y, o):
        return 60000

    yc = y.bit_count()
    oc = o.bit_count()

    front_y = front_o = 0
    sq_y = sq_o = 0

    yy = y
    while yy:
        lb = yy & -yy
        i = lb.bit_length() - 1
        yy ^= lb
        deg = (ADJ[i] & o).bit_count()
        if deg:
            front_y += 1
            sq_y += deg * deg

    oo = o
    while oo:
        lb = oo & -oo
        i = lb.bit_length() - 1
        oo ^= lb
        deg = (ADJ[i] & y).bit_count()
        if deg:
            front_o += 1
            sq_o += deg * deg

    isolated_y = yc - front_y
    isolated_o = oc - front_o

    score = 0
    score += 90 * (yc - oc)
    score += 45 * (front_o - front_y)
    score += 12 * (sq_o - sq_y)
    score += 8 * (isolated_y - isolated_o)

    if e & 1:
        score += 6
    else:
        score -= 6

    return score


def _order_score(m, y, o, hash_move):
    if m == hash_move:
        return 900000000

    s = m >> 5
    d = m & 31
    y2, o2 = _make_move(y, o, m)

    child_edges = _edge_count(o2, y2)
    if child_edges == 0:
        return 800000000

    danger = (ADJ[d] & o2).bit_count()
    support = (ADJ[d] & y2).bit_count()
    target_was_attacked_by = (ADJ[d] & y).bit_count()

    return (
        -35 * child_edges
        -90 * danger
        +25 * support
        +18 * target_was_attacked_by
    )


def _ordered_moves(moves, y, o, hash_move=None):
    if len(moves) <= 1:
        return moves
    return sorted(moves, key=lambda m: _order_score(m, y, o, hash_move), reverse=True)


def _move_to_str(m):
    s = m >> 5
    d = m & 31
    return f"{s // COLS},{s % COLS},{DIR_FROM_TO[(s, d)]}"


def policy(you: list[int], opponent: list[int]) -> str:
    y = _bits(you)
    o = _bits(opponent)

    moves = _generate_moves(y, o)

    if not moves:
        return "0,0,U"

    if len(moves) == 1:
        return _move_to_str(moves[0])

    for m in moves:
        y2, o2 = _make_move(y, o, m)
        if _edge_count(o2, y2) == 0:
            return _move_to_str(m)

    if len(TT) > 300000:
        TT.clear()

    deadline = time.perf_counter() + 0.88
    nodes = 0

    def search(cy, co, depth, alpha, beta):
        nonlocal nodes

        nodes += 1
        if (nodes & 2047) == 0 and time.perf_counter() > deadline:
            raise TimeoutError

        moves_here = _generate_moves(cy, co)
        if not moves_here:
            return -WIN

        if depth <= 0:
            return _evaluate(cy, co)

        key = (cy, co)
        entry = TT.get(key)
        hash_move = None

        if entry is not None:
            edepth, eval_score, flag, best_m = entry
            hash_move = best_m
            if edepth >= depth:
                if flag == 0:
                    return eval_score
                if flag == 1:
                    alpha = max(alpha, eval_score)
                elif flag == 2:
                    beta = min(beta, eval_score)
                if alpha >= beta:
                    return eval_score

        original_alpha = alpha
        best = -INF
        best_move = moves_here[0]

        for m in _ordered_moves(moves_here, cy, co, hash_move):
            y2, o2 = _make_move(cy, co, m)
            val = -search(o2, y2, depth - 1, -beta, -alpha)

            if val > best:
                best = val
                best_move = m

            if val > alpha:
                alpha = val

            if alpha >= beta:
                break

        if best <= original_alpha:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0

        old = TT.get(key)
        if old is None or depth >= old[0]:
            TT[key] = (depth, best, flag, best_move)

        return best

    best_move = _ordered_moves(moves, y, o)[0]
    best_score = -INF
    total_pieces = (y | o).bit_count()
    max_depth = max(1, min(30, total_pieces))

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break

            current_best = best_move
            current_score = -INF
            alpha = -INF
            beta = INF

            for m in _ordered_moves(moves, y, o, best_move):
                y2, o2 = _make_move(y, o, m)
                val = -search(o2, y2, depth - 1, -beta, -alpha)

                if val > current_score:
                    current_score = val
                    current_best = m

                if val > alpha:
                    alpha = val

                if time.perf_counter() > deadline:
                    raise TimeoutError

            best_move = current_best
            best_score = current_score

            if best_score >= WIN:
                break

    except TimeoutError:
        pass

    return _move_to_str(best_move)
