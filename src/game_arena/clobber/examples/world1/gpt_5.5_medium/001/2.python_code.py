
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

WIN = 1000000
INF = 10**9

# Precomputed neighborhood data.
MOVES_FROM = [[] for _ in range(N)]
ADJ_MASK = [0] * N

_dirs = [(-1, 0, "U"), (0, 1, "R"), (1, 0, "D"), (0, -1, "L")]
for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        mask = 0
        for dr, dc, ch in _dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                j = nr * COLS + nc
                b = 1 << j
                mask |= b
                MOVES_FROM[i].append((j, ch, b))
        ADJ_MASK[i] = mask

TT = {}
DEADLINE = 0.0
NODES = 0


class Timeout(Exception):
    pass


def _cell(arr, r, c):
    """Accept nested lists, numpy arrays, or flat arrays."""
    try:
        return arr[r][c]
    except Exception:
        return arr[r * COLS + c]


def _to_bits(you, opponent):
    y = 0
    o = 0
    for r in range(ROWS):
        for c in range(COLS):
            bit = 1 << (r * COLS + c)
            if _cell(you, r, c):
                y |= bit
            elif _cell(opponent, r, c):
                o |= bit
    return y, o


def _generate_moves(y, o):
    moves = []
    yy = y
    while yy:
        lsb = yy & -yy
        src = lsb.bit_length() - 1
        yy ^= lsb
        for dst, ch, b in MOVES_FROM[src]:
            if o & b:
                moves.append((src, dst, ch))
    return moves


def _count_moves(y, o):
    cnt = 0
    yy = y
    while yy:
        lsb = yy & -yy
        src = lsb.bit_length() - 1
        yy ^= lsb
        cnt += (ADJ_MASK[src] & o).bit_count()
    return cnt


def _count_active(bits, other):
    cnt = 0
    bb = bits
    while bb:
        lsb = bb & -bb
        i = lsb.bit_length() - 1
        bb ^= lsb
        if ADJ_MASK[i] & other:
            cnt += 1
    return cnt


def _apply_move(y, o, move):
    src, dst, _ = move
    sb = 1 << src
    db = 1 << dst

    # After our move, perspective switches:
    # next player owns old opponent pieces minus captured dst.
    ny = o & ~db
    # Their opponent owns our old pieces, moved from src to dst.
    no = (y & ~sb) | db
    return ny, no


def _move_order_score(y, o, move):
    ny, no = _apply_move(y, o, move)
    replies = _count_moves(ny, no)
    if replies == 0:
        return 100000

    # Prefer moves that sharply reduce opponent activity.
    active_next = _count_active(ny, no)

    src, dst, _ = move
    captured_degree = (ADJ_MASK[dst] & y).bit_count()
    source_degree = (ADJ_MASK[src] & o).bit_count()

    return -120 * replies - 15 * active_next + 4 * captured_degree - source_degree


def _ordered_moves(y, o, preferred=None):
    moves = _generate_moves(y, o)
    if len(moves) <= 1:
        return moves

    def key(m):
        s = _move_order_score(y, o, m)
        if preferred is not None and m == preferred:
            s += 1000000
        return s

    moves.sort(key=key, reverse=True)
    return moves


def _static_eval(y, o):
    moves = _generate_moves(y, o)
    if not moves:
        return -WIN

    # If current player can immediately leave opponent with no move,
    # this is nearly decisive even at a horizon leaf.
    cur_best = 999
    cur_sum = 0
    for m in moves:
        ny, no = _apply_move(y, o, m)
        e = _count_moves(ny, no)
        if e == 0:
            return 200000
        if e < cur_best:
            cur_best = e
        cur_sum += e

    # Symmetric "what if opponent were to move" pressure estimate.
    opp_moves = _generate_moves(o, y)
    opp_best = 999
    opp_sum = 0
    for m in opp_moves:
        ny, no = _apply_move(o, y, m)
        e = _count_moves(ny, no)
        if e < opp_best:
            opp_best = e
        opp_sum += e

    active_y = _count_active(y, o)
    active_o = _count_active(o, y)

    py = y.bit_count()
    po = o.bit_count()

    cur_avg = cur_sum / max(1, len(moves))
    opp_avg = opp_sum / max(1, len(opp_moves))

    score = 0
    score += 35 * (active_y - active_o)
    score += 6 * (py - po)
    score += 14 * (opp_best - cur_best)
    score += int(3 * (opp_avg - cur_avg))

    # If opponent has a hypothetical immediate killing move, treat as danger.
    if opp_best == 0:
        score -= 1200

    if score > 250000:
        score = 250000
    elif score < -250000:
        score = -250000
    return score


def _search(y, o, depth, alpha, beta):
    global NODES

    NODES += 1
    if (NODES & 2047) == 0 and time.perf_counter() > DEADLINE:
        raise Timeout()

    key = (y, o)
    entry = TT.get(key)
    if entry is not None:
        e_depth, e_val, e_flag, e_best = entry
        if e_depth >= depth:
            if e_flag == 0:
                return e_val
            if e_flag == 1:
                alpha = max(alpha, e_val)
            elif e_flag == 2:
                beta = min(beta, e_val)
            if alpha >= beta:
                return e_val
    else:
        e_best = None

    moves = _generate_moves(y, o)
    if not moves:
        return -WIN

    if depth <= 0:
        val = _static_eval(y, o)
        TT[key] = (depth, val, 0, None)
        return val

    if len(moves) > 1:
        moves.sort(key=lambda m: _move_order_score(y, o, m) + (1000000 if m == e_best else 0),
                   reverse=True)

    original_alpha = alpha
    best_val = -INF
    best_move = moves[0]

    for m in moves:
        ny, no = _apply_move(y, o, m)
        val = -_search(ny, no, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_val <= original_alpha:
        flag = 2  # upper bound
    elif best_val >= beta:
        flag = 1  # lower bound
    else:
        flag = 0  # exact

    TT[key] = (depth, best_val, flag, best_move)
    return best_val


def _format_move(move):
    src, _, ch = move
    r = src // COLS
    c = src % COLS
    return f"{r},{c},{ch}"


def policy(you: list[int], opponent: list[int]) -> str:
    global DEADLINE, NODES, TT

    # Keep memory bounded across repeated calls.
    if len(TT) > 300000:
        TT.clear()

    start = time.perf_counter()
    DEADLINE = start + 0.92
    NODES = 0

    y, o = _to_bits(you, opponent)
    root_moves = _generate_moves(y, o)

    # In normal play the arena should not ask for a move if none exists.
    # Return syntactically valid fallback anyway.
    if not root_moves:
        return "0,0,U"

    if len(root_moves) == 1:
        return _format_move(root_moves[0])

    root_moves.sort(key=lambda m: _move_order_score(y, o, m), reverse=True)
    best_move = root_moves[0]
    best_score = -INF

    total_pieces = (y | o).bit_count()
    max_depth = max(1, min(30, total_pieces))

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > DEADLINE:
                break

            local_best = best_move
            local_score = -INF

            ordered = list(root_moves)
            ordered.sort(
                key=lambda m: _move_order_score(y, o, m) + (1000000 if m == best_move else 0),
                reverse=True,
            )

            alpha = -INF
            beta = INF

            for m in ordered:
                if time.perf_counter() > DEADLINE:
                    raise Timeout()

                ny, no = _apply_move(y, o, m)
                val = -_search(ny, no, depth - 1, -beta, -alpha)

                if val > local_score:
                    local_score = val
                    local_best = m

                if val > alpha:
                    alpha = val

            best_move = local_best
            best_score = local_score

            # A proven forced win within the searched horizon.
            if best_score >= WIN:
                break

    except Timeout:
        pass

    return _format_move(best_move)
