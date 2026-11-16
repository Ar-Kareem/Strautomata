
import time

try:
    _popcount = int.bit_count
except AttributeError:
    def _popcount(x):
        return bin(x).count("1")


_N = 8
_SQ = 64
_WIN = 1000000
_INF = 1000000000
_TIME_LIMIT = 0.88

_BITS = [1 << i for i in range(_SQ)]
_ROW = [i // 8 for i in range(_SQ)]
_COL = [i & 7 for i in range(_SQ)]
_RANGE8 = range(8)

# Directions: up, down, left, right, up-left, down-right, up-right, down-left.
_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
         (-1, -1), (1, 1), (-1, 1), (1, -1)]
# Axis ids: 0 row, 1 column, 2 r-c diagonal, 3 r+c diagonal.
_DIR_AXIS = [1, 1, 0, 0, 2, 2, 3, 3]

_ROW_MASKS = []
_COL_MASKS = []
for r in range(8):
    m = 0
    for c in range(8):
        m |= _BITS[r * 8 + c]
    _ROW_MASKS.append(m)

for c in range(8):
    m = 0
    for r in range(8):
        m |= _BITS[r * 8 + c]
    _COL_MASKS.append(m)

_D1_MASKS = [0] * 15  # r - c + 7
_D2_MASKS = [0] * 15  # r + c
for i in range(64):
    r, c = _ROW[i], _COL[i]
    _D1_MASKS[r - c + 7] |= _BITS[i]
    _D2_MASKS[r + c] |= _BITS[i]

_LINE_MASK = [[0] * 64 for _ in range(4)]
for i in range(64):
    r, c = _ROW[i], _COL[i]
    _LINE_MASK[0][i] = _ROW_MASKS[r]
    _LINE_MASK[1][i] = _COL_MASKS[c]
    _LINE_MASK[2][i] = _D1_MASKS[r - c + 7]
    _LINE_MASK[3][i] = _D2_MASKS[r + c]

_DIR_LINE_MASK = [_LINE_MASK[a] for a in _DIR_AXIS]

_DEST = [[[-1 for _ in range(9)] for _ in range(64)] for _ in range(8)]
_PATH = [[[0 for _ in range(9)] for _ in range(64)] for _ in range(8)]

for d, (dr, dc) in enumerate(_DIRS):
    for i in range(64):
        r, c = _ROW[i], _COL[i]
        for n in range(1, 9):
            tr, tc = r + dr * n, c + dc * n
            if 0 <= tr < 8 and 0 <= tc < 8:
                _DEST[d][i][n] = tr * 8 + tc
                pm = 0
                for step in range(1, n):
                    pr, pc = r + dr * step, c + dc * step
                    pm |= _BITS[pr * 8 + pc]
                _PATH[d][i][n] = pm

_NEIGH = [0] * 64
for i in range(64):
    r, c = _ROW[i], _COL[i]
    m = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < 8 and 0 <= cc < 8:
                m |= _BITS[rr * 8 + cc]
    _NEIGH[i] = m

# Center score: center squares high, corners low.
_CENTER = []
for i in range(64):
    r, c = _ROW[i], _COL[i]
    dist = (2 * r - 7) * (2 * r - 7) + (2 * c - 7) * (2 * c - 7)
    _CENTER.append(98 - dist)

_CHEB = [[0] * 64 for _ in range(64)]
for i in range(64):
    ri, ci = _ROW[i], _COL[i]
    for j in range(64):
        _CHEB[i][j] = max(abs(ri - _ROW[j]), abs(ci - _COL[j]))

_QUAD_MASKS = []
for r in range(7):
    for c in range(7):
        _QUAD_MASKS.append(
            _BITS[r * 8 + c] |
            _BITS[r * 8 + c + 1] |
            _BITS[(r + 1) * 8 + c] |
            _BITS[(r + 1) * 8 + c + 1]
        )
_QUAD_VALUES = (0, 0, 1, 3, 6)

_deadline = 0.0
_nodes = 0
_tt = {}
_component_cache = {}
_side_cache = {}
_history = {}
_killers = []


class _SearchTimeout(Exception):
    pass


def _to_masks(board):
    own = 0
    opp = 0
    for r in range(8):
        row = board[r]
        base = r * 8
        for c in range(8):
            v = row[c]
            if v == 1:
                own |= _BITS[base + c]
            elif v == -1:
                opp |= _BITS[base + c]
    return own, opp


def _generate_moves(own, opp):
    occ = own | opp
    moves = []
    bits = _BITS
    dest = _DEST
    path = _PATH
    line = _DIR_LINE_MASK
    pc = _popcount

    m = own
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        m ^= lsb

        for d in _RANGE8:
            n = pc(occ & line[d][i])
            j = dest[d][i][n]
            if j != -1:
                bj = bits[j]
                if (own & bj) == 0 and (path[d][i][n] & opp) == 0:
                    moves.append((i << 6) | j)
    return moves


def _make_child(own, opp, move):
    i = move >> 6
    j = move & 63
    fb = _BITS[i]
    tb = _BITS[j]

    moved_own = (own & ~fb) | tb
    remaining_opp = opp & ~tb

    # Return from the next player's perspective.
    return remaining_opp, moved_own


def _component_info(mask):
    cached = _component_cache.get(mask)
    if cached is not None:
        return cached

    if mask == 0:
        res = (0, 0, ())
        _component_cache[mask] = res
        return res

    comps = []
    largest = 0
    rem = mask
    neigh = _NEIGH
    pc = _popcount

    while rem:
        start = rem & -rem
        comp = 0
        frontier = start

        while frontier:
            comp |= frontier
            nb = 0
            f = frontier
            while f:
                lsb = f & -f
                nb |= neigh[lsb.bit_length() - 1]
                f ^= lsb
            frontier = nb & mask & ~comp

        comps.append(comp)
        size = pc(comp)
        if size > largest:
            largest = size
        rem &= ~comp

    res = (len(comps), largest, tuple(comps))
    _component_cache[mask] = res
    return res


def _is_connected(mask):
    if mask == 0:
        return False
    if (mask & (mask - 1)) == 0:
        return True
    return _component_info(mask)[0] == 1


def _terminal_value(own, opp, ply):
    if own == 0:
        return -_WIN + ply
    if opp == 0:
        return _WIN - ply

    # At a searched node, opp is the previous mover. If both are connected,
    # the previous mover gets priority, which matches standard LOA.
    if _is_connected(opp):
        return -_WIN + ply
    if _is_connected(own):
        return _WIN - ply
    return None


def _side_score(mask):
    cached = _side_cache.get(mask)
    if cached is not None:
        return cached

    pc = _popcount
    n = pc(mask)
    if n == 0:
        return -_WIN

    comps, largest, comp_masks = _component_info(mask)

    idxs = []
    center_sum = 0
    adj = 0
    minr, maxr = 8, -1
    minc, maxc = 8, -1

    m = mask
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        m ^= lsb

        idxs.append(i)
        r, c = _ROW[i], _COL[i]
        if r < minr:
            minr = r
        if r > maxr:
            maxr = r
        if c < minc:
            minc = c
        if c > maxc:
            maxc = c
        center_sum += _CENTER[i]
        adj += pc(_NEIGH[i] & mask)

    adj //= 2
    area = (maxr - minr + 1) * (maxc - minc + 1)
    density = (100 * n) // area
    largest_pct = (100 * largest) // n
    adj_per_piece = (100 * adj) // n
    center_avg = center_sum // n

    size_sq = 0
    for cm in comp_masks:
        s = pc(cm)
        size_sq += s * s
    cohesion = (100 * size_sq) // (n * n)

    pd = 0
    pair_count = n * (n - 1) // 2
    if pair_count:
        for a in range(n - 1):
            da = _CHEB[idxs[a]]
            for b in range(a + 1, n):
                pd += da[idxs[b]]
        avgdist100 = (100 * pd) // pair_count
    else:
        avgdist100 = 0

    # Sum of nearest-component distances. This rewards bridge-building:
    # two far components may be worse than several close bridge components.
    gap = 0
    if comps > 1:
        cheb = _CHEB
        for cm in comp_masks:
            other = mask ^ cm
            mind = 8
            x = cm
            while x:
                lsb = x & -x
                i = lsb.bit_length() - 1
                y = other
                di = cheb[i]
                while y:
                    lsb2 = y & -y
                    j = lsb2.bit_length() - 1
                    d = di[j]
                    if d < mind:
                        mind = d
                        if mind <= 2:
                            break
                    y ^= lsb2
                if mind <= 2:
                    break
                x ^= lsb
            gap += mind

    quad = 0
    qv = _QUAD_VALUES
    for qm in _QUAD_MASKS:
        quad += qv[pc(mask & qm)]

    score = (
        -1650 * comps
        -220 * gap
        + 14 * largest_pct
        + 10 * cohesion
        + 7 * adj_per_piece
        + 4 * density
        - 5 * avgdist100
        + 3 * center_avg
        - 8 * area
        + 16 * quad
        - 12 * n
    )

    _side_cache[mask] = score
    return score


def _evaluate(own, opp):
    # Small tempo bonus because this value is from the side-to-move perspective.
    return _side_score(own) - _side_score(opp) + 8


def _ordering_score(own, opp, move, tt_move, ply):
    i = move >> 6
    j = move & 63

    s = 0
    if move == tt_move:
        s += 10000000

    if ply < len(_killers):
        k0, k1 = _killers[ply]
        if move == k0:
            s += 800000
        elif move == k1:
            s += 650000

    s += _history.get(move, 0)

    tb = _BITS[j]
    fb = _BITS[i]

    if opp & tb:
        s += 50000

    friends_after = own & ~fb
    s += 1500 * _popcount(_NEIGH[j] & friends_after)
    s -= 250 * _popcount(_NEIGH[i] & friends_after)
    s += 8 * _CENTER[j] - 3 * _CENTER[i]

    return s


def _order_moves(own, opp, moves, tt_move, ply):
    if len(moves) <= 1:
        return moves
    return sorted(moves, key=lambda m: _ordering_score(own, opp, m, tt_move, ply), reverse=True)


def _record_cutoff(move, depth, ply, is_capture):
    _history[move] = _history.get(move, 0) + depth * depth
    if not is_capture and ply < len(_killers):
        k0, _ = _killers[ply]
        if move != k0:
            _killers[ply][1] = k0
            _killers[ply][0] = move


def _negamax(own, opp, depth, alpha, beta, ply):
    global _nodes

    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() >= _deadline:
        raise _SearchTimeout()

    term = _terminal_value(own, opp, ply)
    if term is not None:
        return term

    if depth <= 0:
        return _evaluate(own, opp)

    alpha_orig = alpha
    beta_orig = beta
    key = (own, opp)
    tt_move = None

    entry = _tt.get(key)
    if entry is not None:
        edepth, eval_score, flag, stored_move = entry
        tt_move = stored_move
        if edepth >= depth:
            if flag == 0:       # exact
                return eval_score
            elif flag == 1:     # lower bound
                if eval_score > alpha:
                    alpha = eval_score
            else:               # upper bound
                if eval_score < beta:
                    beta = eval_score
            if alpha >= beta:
                return eval_score

    moves = _generate_moves(own, opp)
    if not moves:
        return -_WIN + ply

    moves = _order_moves(own, opp, moves, tt_move, ply)

    best = None
    value = -_INF
    searched = 0

    for move in moves:
        child_own, child_opp = _make_child(own, opp, move)

        # Principal variation search after the first move.
        if searched and depth > 1:
            score = -_negamax(child_own, child_opp, depth - 1, -alpha - 1, -alpha, ply + 1)
            if alpha < score < beta:
                score = -_negamax(child_own, child_opp, depth - 1, -beta, -alpha, ply + 1)
        else:
            score = -_negamax(child_own, child_opp, depth - 1, -beta, -alpha, ply + 1)

        searched += 1

        if score > value:
            value = score
            best = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            _record_cutoff(move, depth, ply, (opp & _BITS[move & 63]) != 0)
            break

    if value <= alpha_orig:
        flag = 2       # upper bound
    elif value >= beta_orig:
        flag = 1       # lower bound
    else:
        flag = 0       # exact

    _tt[key] = (depth, value, flag, best)
    return value


def _static_root_score(own, opp, move):
    child_own, child_opp = _make_child(own, opp, move)
    term = _terminal_value(child_own, child_opp, 1)
    if term is not None:
        return -term
    return -_evaluate(child_own, child_opp)


def _root_search(own, opp, moves, depth):
    alpha = -_INF
    beta = _INF
    best = moves[0]
    best_score = -_INF
    scores = []

    for idx, move in enumerate(moves):
        if time.perf_counter() >= _deadline:
            raise _SearchTimeout()

        child_own, child_opp = _make_child(own, opp, move)

        if idx and depth > 1:
            score = -_negamax(child_own, child_opp, depth - 1, -alpha - 1, -alpha, 1)
            if alpha < score < beta:
                score = -_negamax(child_own, child_opp, depth - 1, -beta, -alpha, 1)
        else:
            score = -_negamax(child_own, child_opp, depth - 1, -beta, -alpha, 1)

        scores.append((score, move))

        if score > best_score:
            best_score = score
            best = move
        if score > alpha:
            alpha = score

    scores.sort(reverse=True)
    return best_score, best, [m for _, m in scores]


def _format_move(move):
    i = move >> 6
    j = move & 63
    return f"{_ROW[i]},{_COL[i]}:{_ROW[j]},{_COL[j]}"


def policy(board) -> str:
    global _deadline, _nodes, _tt, _component_cache, _side_cache, _history, _killers

    start = time.perf_counter()
    _deadline = start + _TIME_LIMIT
    _nodes = 0
    _tt = {}
    _component_cache = {}
    _side_cache = {}
    _history = {}
    _killers = [[None, None] for _ in range(64)]

    own, opp = _to_masks(board)
    moves = _generate_moves(own, opp)

    # In normal LOA play there should be a legal move whenever policy is called.
    # This fallback is only for unreachable malformed/no-move states.
    if not moves:
        return "0,0:0,0"

    if len(moves) == 1:
        return _format_move(moves[0])

    scored = [(_static_root_score(own, opp, m), m) for m in moves]
    scored.sort(reverse=True)

    root_moves = [m for _, m in scored]
    best = root_moves[0]
    best_score = scored[0][0]

    # Immediate winning move.
    if best_score >= _WIN // 2:
        return _format_move(best)

    total_pieces = _popcount(own | opp)
    if total_pieces <= 8:
        max_depth = 16
    elif len(root_moves) <= 12:
        max_depth = 14
    elif len(root_moves) <= 25:
        max_depth = 12
    else:
        max_depth = 10

    for depth in range(2, max_depth + 1):
        if time.perf_counter() + 0.015 >= _deadline:
            break
        try:
            score, move, ordered = _root_search(own, opp, root_moves, depth)
            best = move
            best_score = score
            root_moves = ordered

            if best_score >= _WIN // 2 or best_score <= -_WIN // 2:
                break
        except _SearchTimeout:
            break

    return _format_move(best)
