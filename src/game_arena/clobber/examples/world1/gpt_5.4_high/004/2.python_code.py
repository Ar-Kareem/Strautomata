
from time import perf_counter

ROWS, COLS = 5, 6
N = ROWS * COLS

BOARD_MASK = (1 << N) - 1
WIN_SCORE = 100000
INF = 10**9

# Bit masks for board edges
COL0_MASK = 0
COL5_MASK = 0
for r in range(ROWS):
    COL0_MASK |= 1 << (r * COLS)
    COL5_MASK |= 1 << (r * COLS + (COLS - 1))

ROW0_MASK = (1 << COLS) - 1
ROW4_MASK = ROW0_MASK << ((ROWS - 1) * COLS)

NOT_COL0 = BOARD_MASK ^ COL0_MASK
NOT_COL5 = BOARD_MASK ^ COL5_MASK
NOT_ROW0 = BOARD_MASK ^ ROW0_MASK
NOT_ROW4 = BOARD_MASK ^ ROW4_MASK

# Positional masks
INNER_MASK = 0
for r in range(1, ROWS - 1):
    for c in range(1, COLS - 1):
        INNER_MASK |= 1 << (r * COLS + c)

CORNER_MASK = (1 << 0) | (1 << (COLS - 1)) | (1 << ((ROWS - 1) * COLS)) | (1 << (N - 1))

# Adjacency
ADJ = [[] for _ in range(N)]          # (dst, dir_char, dir_idx)
NEIGH_MASK = [0] * N

DIRS = [(-1, 0, 'U', 0), (0, 1, 'R', 1), (1, 0, 'D', 2), (0, -1, 'L', 3)]

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        mask = 0
        for dr, dc, ch, didx in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                j = nr * COLS + nc
                ADJ[i].append((j, ch, didx))
                mask |= 1 << j
        NEIGH_MASK[i] = mask

# Search tables
_EXACT, _LOWER, _UPPER = 0, 1, 2
TT = {}
MAX_TT = 400000

history = [0] * (N * 4)
killers = [[-1, -1] for _ in range(64)]

deadline = 0.0
nodes = 0


class _Timeout(Exception):
    pass


def _to_bits(arr):
    """Convert nested list / flat list / numpy array to a 30-bit int."""
    if hasattr(arr, "ravel"):
        flat = arr.ravel()
    else:
        if len(arr) == N and not hasattr(arr[0], "__len__"):
            flat = arr
        else:
            flat = []
            for row in arr:
                flat.extend(row)

    bits = 0
    for i, v in enumerate(flat):
        if int(v):
            bits |= 1 << i
    return bits


def _count_moves(y, o):
    """Count legal moves for side y against o."""
    return (
        ((((y & NOT_COL5) << 1) & o).bit_count()) +
        ((((y & NOT_COL0) >> 1) & o).bit_count()) +
        ((((y & NOT_ROW4) << COLS) & o).bit_count()) +
        ((((y & NOT_ROW0) >> COLS) & o).bit_count())
    )


def _neighbor_union(bits):
    """All orthogonally adjacent cells to a bitboard."""
    return (
        ((bits & NOT_COL5) << 1) |
        ((bits & NOT_COL0) >> 1) |
        ((bits & NOT_ROW4) << COLS) |
        ((bits & NOT_ROW0) >> COLS)
    )


def _evaluate(y, o, my_moves=None):
    """Heuristic evaluation from side-to-move perspective."""
    if my_moves is None:
        my_moves = _count_moves(y, o)
    if my_moves == 0:
        return -WIN_SCORE

    opp_moves = _count_moves(o, y)

    adj_y = _neighbor_union(y)
    adj_o = _neighbor_union(o)

    # Active pieces: pieces adjacent to an enemy
    active_you = (adj_o & y).bit_count()
    active_opp = (adj_y & o).bit_count()

    inner_diff = (y & INNER_MASK).bit_count() - (o & INNER_MASK).bit_count()
    corner_diff = (y & CORNER_MASK).bit_count() - (o & CORNER_MASK).bit_count()
    piece_diff = y.bit_count() - o.bit_count()

    score = 96 * (my_moves - opp_moves)
    score += 14 * (active_you - active_opp)
    score += 4 * inner_diff
    score -= 3 * corner_diff
    score += 2 * piece_diff
    return score


def _gen_ordered_moves(y, o, tt_move=-1, ply=0):
    """
    Generate legal moves with ordering info.
    Returned tuple:
    (score, opp_mobility, move_code, src, dst, dir_char, next_you, next_opp)
    """
    out = []
    yb = y

    killer0 = killers[ply][0]
    killer1 = killers[ply][1]

    while yb:
        lsb = yb & -yb
        src = lsb.bit_length() - 1
        yb ^= lsb

        for dst, dch, didx in ADJ[src]:
            if (o >> dst) & 1:
                ny = o ^ (1 << dst)
                no = (y ^ (1 << src)) | (1 << dst)
                code = src * 4 + didx

                opp_mob = _count_moves(ny, no)
                vuln = (NEIGH_MASK[dst] & ny).bit_count()

                score = history[code]

                if code == tt_move:
                    score += 10_000_000
                if code == killer0:
                    score += 5_000_000
                elif code == killer1:
                    score += 4_000_000
                if opp_mob == 0:
                    score += 9_000_000

                # Prefer moves that cut opponent mobility and land on less vulnerable squares
                score += (50 - opp_mob) * 1000
                score -= vuln * 25

                out.append((score, opp_mob, code, src, dst, dch, ny, no))

    out.sort(key=lambda t: t[0], reverse=True)
    return out


def _search(y, o, depth, alpha, beta, ply):
    global nodes, deadline

    nodes += 1
    if (nodes & 1023) == 0 and perf_counter() >= deadline:
        raise _Timeout

    key = y | (o << N)
    alpha0, beta0 = alpha, beta

    my_moves = _count_moves(y, o)
    if my_moves == 0:
        return -WIN_SCORE

    total = y.bit_count() + o.bit_count()

    # Exact-search extension in endgames / low-mobility states
    if my_moves == 1 or total <= 14 or (total <= 16 and my_moves <= 8):
        if depth < total:
            depth = total

    entry = TT.get(key)
    tt_move = -1
    if entry is not None:
        e_depth, e_flag, e_val, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == _EXACT:
                return e_val
            elif e_flag == _LOWER:
                if e_val > alpha:
                    alpha = e_val
            else:
                if e_val < beta:
                    beta = e_val
            if alpha >= beta:
                return e_val

    if depth <= 0:
        return _evaluate(y, o, my_moves)

    moves = _gen_ordered_moves(y, o, tt_move, ply)
    best = -INF
    best_code = moves[0][2]

    first = True
    next_ply = ply + 1 if ply + 1 < 64 else 63

    for _, _, code, _, _, _, ny, no in moves:
        if first:
            val = -_search(ny, no, depth - 1, -beta, -alpha, next_ply)
            first = False
        else:
            # PVS / null-window first
            val = -_search(ny, no, depth - 1, -alpha - 1, -alpha, next_ply)
            if alpha < val < beta:
                val = -_search(ny, no, depth - 1, -beta, -alpha, next_ply)

        if val > best:
            best = val
            best_code = code
        if val > alpha:
            alpha = val
        if alpha >= beta:
            if killers[ply][0] != code:
                killers[ply][1] = killers[ply][0]
                killers[ply][0] = code
            history[code] += depth * depth
            break

    if best <= alpha0:
        flag = _UPPER
    elif best >= beta0:
        flag = _LOWER
    else:
        flag = _EXACT

    TT[key] = (depth, flag, best, best_code)
    return best


def _search_root(y, o, depth):
    key = y | (o << N)
    entry = TT.get(key)
    tt_move = entry[3] if entry is not None else -1

    moves = _gen_ordered_moves(y, o, tt_move, 0)

    best = -INF
    best_move = moves[0]
    alpha, beta = -INF, INF

    first = True
    for move in moves:
        _, _, _, _, _, _, ny, no = move

        if first:
            val = -_search(ny, no, depth - 1, -beta, -alpha, 1)
            first = False
        else:
            val = -_search(ny, no, depth - 1, -alpha - 1, -alpha, 1)
            if alpha < val < beta:
                val = -_search(ny, no, depth - 1, -beta, -alpha, 1)

        if val > best:
            best = val
            best_move = move
        if val > alpha:
            alpha = val

    TT[key] = (depth, _EXACT, best, best_move[2])
    return best, best_move


def _move_to_str(move):
    src = move[3]
    dch = move[5]
    return f"{src // COLS},{src % COLS},{dch}"


def policy(you, opponent):
    global deadline, nodes

    y = _to_bits(you)
    o = _to_bits(opponent)

    # Periodic cleanup to bound memory
    if len(TT) > MAX_TT:
        TT.clear()
        # Mild decay of history instead of full reset
        for i in range(len(history)):
            history[i] //= 2

    root_key = y | (o << N)
    entry = TT.get(root_key)
    tt_move = entry[3] if entry is not None else -1

    root_moves = _gen_ordered_moves(y, o, tt_move, 0)

    # Terminal states should normally not be queried, but return a valid-format fallback.
    if not root_moves:
        return "0,0,U"

    # Immediate tactical win
    for mv in root_moves:
        if mv[1] == 0:
            return _move_to_str(mv)

    # Only one legal move
    if len(root_moves) == 1:
        return _move_to_str(root_moves[0])

    best_move = root_moves[0]

    total = y.bit_count() + o.bit_count()
    deadline = perf_counter() + 0.95
    nodes = 0

    try:
        # Exact endgame solve when plausible
        if total <= 14 or (total <= 16 and len(root_moves) <= 8):
            score, move = _search_root(y, o, total)
            best_move = move
            return _move_to_str(best_move)

        max_depth = min(total, 20)
        for depth in range(1, max_depth + 1):
            score, move = _search_root(y, o, depth)
            best_move = move

            # Proven win/loss found
            if abs(score) >= WIN_SCORE:
                break

            if perf_counter() >= deadline - 0.02:
                break

    except _Timeout:
        pass

    return _move_to_str(best_move)
