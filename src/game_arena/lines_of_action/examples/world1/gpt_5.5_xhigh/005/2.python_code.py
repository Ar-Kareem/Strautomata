
import time

# Lines of Action policy for an 8x8 board.
# Public API: policy(board) -> str

_BOARD_SIZE = 8
_SQUARES = 64
_WIN_SCORE = 10_000_000
_INF = 1_000_000_000
_TIME_LIMIT = 0.86

_DIRS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (1, 1), (-1, 1), (1, -1)
]

_BIT = [1 << i for i in range(_SQUARES)]
_ROW = [i >> 3 for i in range(_SQUARES)]
_COL = [i & 7 for i in range(_SQUARES)]

_ROW_MASKS = []
for r in range(8):
    m = 0
    for c in range(8):
        m |= _BIT[r * 8 + c]
    _ROW_MASKS.append(m)

_COL_MASKS = []
for c in range(8):
    m = 0
    for r in range(8):
        m |= _BIT[r * 8 + c]
    _COL_MASKS.append(m)

_DIAG_DIFF_MASKS = [0] * 15
_DIAG_SUM_MASKS = [0] * 15
for s in range(_SQUARES):
    r, c = _ROW[s], _COL[s]
    _DIAG_DIFF_MASKS[r - c + 7] |= _BIT[s]
    _DIAG_SUM_MASKS[r + c] |= _BIT[s]

_LINE_MASK = [[0 for _ in range(8)] for _ in range(_SQUARES)]
_DEST = [[[-1 for _ in range(9)] for _ in range(8)] for _ in range(_SQUARES)]
_BETWEEN = [[[0 for _ in range(9)] for _ in range(8)] for _ in range(_SQUARES)]

for s in range(_SQUARES):
    r, c = _ROW[s], _COL[s]
    for k, (dr, dc) in enumerate(_DIRS):
        if dr == 0:
            _LINE_MASK[s][k] = _ROW_MASKS[r]
        elif dc == 0:
            _LINE_MASK[s][k] = _COL_MASKS[c]
        elif dr == dc:
            _LINE_MASK[s][k] = _DIAG_DIFF_MASKS[r - c + 7]
        else:
            _LINE_MASK[s][k] = _DIAG_SUM_MASKS[r + c]

        for dist in range(1, 9):
            rr = r + dr * dist
            cc = c + dc * dist
            if 0 <= rr < 8 and 0 <= cc < 8:
                _DEST[s][k][dist] = rr * 8 + cc
                bm = 0
                for step in range(1, dist):
                    bm |= _BIT[(r + dr * step) * 8 + (c + dc * step)]
                _BETWEEN[s][k][dist] = bm

_NEIGH_MASK = [0] * _SQUARES
_EDGE = [0] * _SQUARES
_CENTER_SCORE = [0] * _SQUARES

for s in range(_SQUARES):
    r, c = _ROW[s], _COL[s]
    nm = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < 8 and 0 <= cc < 8:
                nm |= _BIT[rr * 8 + cc]
    _NEIGH_MASK[s] = nm
    _EDGE[s] = 1 if r == 0 or r == 7 or c == 0 or c == 7 else 0
    # 0 at corners, 96 at the four central squares.
    _CENTER_SCORE[s] = 98 - ((2 * r - 7) * (2 * r - 7) + (2 * c - 7) * (2 * c - 7))

_CHEB = [[0] * _SQUARES for _ in range(_SQUARES)]
for a in range(_SQUARES):
    for b in range(_SQUARES):
        dr = abs(_ROW[a] - _ROW[b])
        dc = abs(_COL[a] - _COL[b])
        _CHEB[a][b] = dr if dr > dc else dc

_MOVE_STRINGS = [""] * (_SQUARES * _SQUARES)
for s in range(_SQUARES):
    for t in range(_SQUARES):
        _MOVE_STRINGS[(s << 6) | t] = f"{s // 8},{s % 8}:{t // 8},{t % 8}"

_FLAG_EXACT = 0
_FLAG_LOWER = 1
_FLAG_UPPER = 2

_TT = {}
_EVAL_CACHE = {}
_WINMOVE_CACHE = {}

_COMP_CACHE = {0: (0, 0)}
_CONN_CACHE = {0: False}
_SHAPE_ZERO = (0, 0, 0, 0, 0, 0, 0)
_SHAPE_CACHE = {0: _SHAPE_ZERO}

_START_TIME = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _time_check():
    if time.perf_counter() - _START_TIME > _TIME_LIMIT:
        raise _Timeout()


def _trim_caches():
    if len(_TT) > 350000:
        _TT.clear()
    if len(_EVAL_CACHE) > 250000:
        _EVAL_CACHE.clear()
    if len(_WINMOVE_CACHE) > 200000:
        _WINMOVE_CACHE.clear()
    if len(_COMP_CACHE) > 200000:
        _COMP_CACHE.clear()
        _COMP_CACHE[0] = (0, 0)
        _CONN_CACHE.clear()
        _CONN_CACHE[0] = False
        _SHAPE_CACHE.clear()
        _SHAPE_CACHE[0] = _SHAPE_ZERO


def _parse_board(board):
    my = 0
    opp = 0
    for r in range(8):
        row = board[r]
        base = r * 8
        for c in range(8):
            v = int(row[c])
            if v == 1:
                my |= _BIT[base + c]
            elif v == -1:
                opp |= _BIT[base + c]
    return my, opp


def _move_to_str(m):
    return _MOVE_STRINGS[m]


def _apply_move(my, opp, m):
    src = m >> 6
    dst = m & 63
    fb = _BIT[src]
    tb = _BIT[dst]
    return (my & ~fb) | tb, opp & ~tb


def _generate_legal_moves(my, opp):
    occ = my | opp
    moves = []
    pieces = my

    line_mask = _LINE_MASK
    dest_table = _DEST
    between_table = _BETWEEN
    bit = _BIT

    while pieces:
        lsb = pieces & -pieces
        s = lsb.bit_length() - 1
        pieces ^= lsb

        for k in range(8):
            dist = (occ & line_mask[s][k]).bit_count()
            t = dest_table[s][k][dist]
            if t >= 0:
                tb = bit[t]
                if (my & tb) == 0 and (opp & between_table[s][k][dist]) == 0:
                    moves.append((s << 6) | t)

    return moves


def _flood_component(start_bit, bits):
    seen = 0
    frontier = start_bit
    neigh = _NEIGH_MASK

    while frontier:
        seen |= frontier
        f = frontier
        nb = 0
        while f:
            lsb = f & -f
            nb |= neigh[lsb.bit_length() - 1]
            f ^= lsb
        frontier = nb & bits & ~seen

    return seen


def _connected(bits):
    try:
        return _CONN_CACHE[bits]
    except KeyError:
        pass

    if bits == 0:
        ans = False
    elif bits & (bits - 1) == 0:
        ans = True
        _COMP_CACHE[bits] = (1, 1)
    else:
        ans = (_flood_component(bits & -bits, bits) == bits)
        if ans:
            _COMP_CACHE[bits] = (1, bits.bit_count())

    _CONN_CACHE[bits] = ans
    return ans


def _component_info(bits):
    try:
        return _COMP_CACHE[bits]
    except KeyError:
        pass

    rem = bits
    comps = 0
    largest = 0

    while rem:
        start = rem & -rem
        comp = _flood_component(start, bits)
        comps += 1
        size = comp.bit_count()
        if size > largest:
            largest = size
        rem &= ~comp

    result = (comps, largest)
    _COMP_CACHE[bits] = result
    _CONN_CACHE[bits] = (comps == 1 and bits != 0)
    return result


def _terminal_value(my, opp):
    if my == 0:
        return -_WIN_SCORE
    if opp == 0:
        return _WIN_SCORE

    my_conn = _connected(my)
    opp_conn = _connected(opp)

    # If both are connected at the start of this node, the previous mover
    # created the double-connection and wins.
    if my_conn and opp_conn:
        return -_WIN_SCORE
    if my_conn:
        return _WIN_SCORE
    if opp_conn:
        return -_WIN_SCORE
    return None


def _shape_metrics(bits):
    try:
        return _SHAPE_CACHE[bits]
    except KeyError:
        pass

    if bits == 0:
        return _SHAPE_ZERO

    squares = []
    tmp = bits
    minr, maxr = 8, -1
    minc, maxc = 8, -1
    center = 0
    edge_count = 0

    while tmp:
        lsb = tmp & -tmp
        s = lsb.bit_length() - 1
        tmp ^= lsb
        squares.append(s)

        r, c = _ROW[s], _COL[s]
        if r < minr:
            minr = r
        if r > maxr:
            maxr = r
        if c < minc:
            minc = c
        if c > maxc:
            maxc = c

        center += _CENTER_SCORE[s]
        edge_count += _EDGE[s]

    n = len(squares)
    pair_sum = 0
    nearest_sum = 0
    adj_pairs = 0
    diameter = 0

    if n > 1:
        mins = [99] * n
        cheb = _CHEB
        for i in range(n - 1):
            si = squares[i]
            row_cheb = cheb[si]
            for j in range(i + 1, n):
                d = row_cheb[squares[j]]
                pair_sum += d
                if d < mins[i]:
                    mins[i] = d
                if d < mins[j]:
                    mins[j] = d
                if d == 1:
                    adj_pairs += 1
                if d > diameter:
                    diameter = d
        nearest_sum = sum(mins)

    area = (maxr - minr + 1) * (maxc - minc + 1)
    result = (pair_sum, nearest_sum, area, center, adj_pairs, diameter, edge_count)
    _SHAPE_CACHE[bits] = result
    return result


def _has_winning_move(my, opp):
    key = (my, opp)
    try:
        return _WINMOVE_CACHE[key]
    except KeyError:
        pass

    for m in _generate_legal_moves(my, opp):
        my2, _ = _apply_move(my, opp, m)
        if _connected(my2):
            _WINMOVE_CACHE[key] = True
            return True

    _WINMOVE_CACHE[key] = False
    return False


def _static_evaluate(my, opp):
    key = (my, opp)
    try:
        return _EVAL_CACHE[key]
    except KeyError:
        pass

    if my == 0:
        return -_WIN_SCORE
    if opp == 0:
        return _WIN_SCORE

    my_n = my.bit_count()
    opp_n = opp.bit_count()

    my_comp, my_largest = _component_info(my)
    opp_comp, opp_largest = _component_info(opp)

    if my_comp == 1 and opp_comp == 1:
        return -_WIN_SCORE
    if my_comp == 1:
        return _WIN_SCORE
    if opp_comp == 1:
        return -_WIN_SCORE

    my_pair, my_near, my_area, my_center, my_adj, my_diam, my_edge = _shape_metrics(my)
    op_pair, op_near, op_area, op_center, op_adj, op_diam, op_edge = _shape_metrics(opp)

    my_ratio = (my_largest * 100) // my_n
    op_ratio = (opp_largest * 100) // opp_n

    my_pairs = my_n * (my_n - 1) // 2
    op_pairs = opp_n * (opp_n - 1) // 2

    my_pair_avg = (my_pair * 100) // my_pairs if my_pairs else 0
    op_pair_avg = (op_pair * 100) // op_pairs if op_pairs else 0
    my_near_avg = (my_near * 100) // my_n if my_n else 0
    op_near_avg = (op_near * 100) // opp_n if opp_n else 0

    score = 0

    # Main LOA objective: fewer connected components and a larger main group.
    score += 1900 * (opp_comp - my_comp)
    score += 12 * (my_ratio - op_ratio)
    score += 95 * (my_largest - opp_largest)

    # Cohesion/compactness.
    score += 55 * (my_adj - op_adj)
    score += 5 * (op_near_avg - my_near_avg)
    score += 2 * (op_pair_avg - my_pair_avg)
    score += 16 * (op_area - my_area)
    score += 70 * (op_diam - my_diam)

    # Positional preferences: central connected formations are usually stronger.
    score += (my_center - op_center)
    score += 18 * (op_edge - my_edge)

    # Material is only a tiny factor in LOA; overvaluing captures is dangerous.
    score += 4 * (my_n - opp_n)

    # Horizon help: one-move connection threats. Gated to compact/late positions
    # so opening search remains fast.
    my_threat_zone = (
        my_comp <= 3 and
        (my_largest >= my_n - 2 or my_area <= 22 or my_diam <= 4)
    )
    op_threat_zone = (
        opp_comp <= 3 and
        (opp_largest >= opp_n - 2 or op_area <= 22 or op_diam <= 4)
    )

    if my_threat_zone and _has_winning_move(my, opp):
        score += 650000
    if op_threat_zone and _has_winning_move(opp, my):
        score -= 450000

    cap = _WIN_SCORE // 2
    if score > cap:
        score = cap
    elif score < -cap:
        score = -cap

    _EVAL_CACHE[key] = score
    return score


def _order_moves(moves, my, opp, tt_move=0):
    if len(moves) <= 1:
        return moves

    scored = []
    neigh = _NEIGH_MASK
    center = _CENTER_SCORE
    bit = _BIT

    for m in moves:
        src = m >> 6
        dst = m & 63
        fb = bit[src]
        tb = bit[dst]

        score = 0
        if m == tt_move:
            score += 10_000_000

        if opp & tb:
            score += 350

        my_without = my & ~fb
        adj_after = (neigh[dst] & my_without).bit_count()
        adj_before = (neigh[src] & my_without).bit_count()

        score += 220 * adj_after
        score -= 35 * adj_before
        score += center[dst] - center[src]

        scored.append((score, m))

    scored.sort(reverse=True)
    return [m for _, m in scored]


def _negamax(my, opp, depth, alpha, beta):
    global _NODES
    _NODES += 1
    if (_NODES & 127) == 0:
        _time_check()

    if depth <= 0:
        return _static_evaluate(my, opp)

    tv = _terminal_value(my, opp)
    if tv is not None:
        return tv

    key = (my, opp)
    tt_move = 0
    entry = _TT.get(key)

    if entry is not None:
        e_depth, e_flag, e_value, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == _FLAG_EXACT:
                return e_value
            if e_flag == _FLAG_LOWER:
                if e_value > alpha:
                    alpha = e_value
            elif e_flag == _FLAG_UPPER:
                if e_value < beta:
                    beta = e_value
            if alpha >= beta:
                return e_value

    moves = _generate_legal_moves(my, opp)
    if not moves:
        return -_WIN_SCORE

    moves = _order_moves(moves, my, opp, tt_move)

    orig_alpha = alpha
    orig_beta = beta
    best = -_INF
    best_move = moves[0]
    first = True

    for m in moves:
        my2, opp2 = _apply_move(my, opp, m)

        # The mover wins immediately if their own pieces become connected,
        # even if the opponent is also connected.
        if _connected(my2):
            value = _WIN_SCORE
        else:
            if first:
                value = -_negamax(opp2, my2, depth - 1, -beta, -alpha)
            else:
                # Principal variation search / null-window search.
                value = -_negamax(opp2, my2, depth - 1, -alpha - 1, -alpha)
                if alpha < value < beta:
                    value = -_negamax(opp2, my2, depth - 1, -beta, -alpha)

        first = False

        if value > best:
            best = value
            best_move = m

        if value > alpha:
            alpha = value
            if alpha >= beta:
                break

    if best <= orig_alpha:
        flag = _FLAG_UPPER
    elif best >= orig_beta:
        flag = _FLAG_LOWER
    else:
        flag = _FLAG_EXACT

    old = _TT.get(key)
    if old is None or depth >= old[0]:
        _TT[key] = (depth, flag, best, best_move)

    return best


def _emergency_move(board):
    # Independent slow fallback. In normal play this is never needed, but it
    # protects against malformed edge cases.
    for r in range(8):
        for c in range(8):
            if int(board[r][c]) != 1:
                continue

            for dr, dc in _DIRS:
                sr, sc = r, c
                while 0 <= sr - dr < 8 and 0 <= sc - dc < 8:
                    sr -= dr
                    sc -= dc

                count = 0
                rr, cc = sr, sc
                while 0 <= rr < 8 and 0 <= cc < 8:
                    if int(board[rr][cc]) != 0:
                        count += 1
                    rr += dr
                    cc += dc

                tr = r + dr * count
                tc = c + dc * count
                if not (0 <= tr < 8 and 0 <= tc < 8):
                    continue
                if int(board[tr][tc]) == 1:
                    continue

                blocked = False
                for step in range(1, count):
                    if int(board[r + dr * step][c + dc * step]) == -1:
                        blocked = True
                        break

                if not blocked:
                    return f"{r},{c}:{tr},{tc}"

    # If the position truly has no legal move, no legal string exists. Return
    # syntactically valid output as a last resort.
    for r in range(8):
        for c in range(8):
            if int(board[r][c]) == 1:
                return f"{r},{c}:{r},{c}"
    return "0,0:0,0"


def policy(board) -> str:
    global _START_TIME, _NODES

    _START_TIME = time.perf_counter()
    _NODES = 0
    _trim_caches()

    my, opp = _parse_board(board)
    root_moves = _generate_legal_moves(my, opp)

    if not root_moves:
        return _emergency_move(board)

    if len(root_moves) == 1:
        return _move_to_str(root_moves[0])

    # Static root ordering and safe fallback.
    scored = []
    best_move = root_moves[0]
    best_score = -_INF

    for m in root_moves:
        my2, opp2 = _apply_move(my, opp, m)

        if _connected(my2):
            return _move_to_str(m)

        value = -_static_evaluate(opp2, my2)
        scored.append((value, m))

        if value > best_score:
            best_score = value
            best_move = m

    scored.sort(reverse=True)
    root_moves = [m for _, m in scored]
    best_move = root_moves[0]
    best_score = scored[0][0]

    if len(root_moves) <= 10:
        max_depth = 16
    elif len(root_moves) <= 20:
        max_depth = 14
    else:
        max_depth = 12

    try:
        for depth in range(1, max_depth + 1):
            _time_check()

            local_scores = {}
            local_best = root_moves[0]
            local_best_score = -_INF
            alpha = -_INF
            beta = _INF

            for m in root_moves:
                _time_check()

                my2, opp2 = _apply_move(my, opp, m)

                if _connected(my2):
                    value = _WIN_SCORE
                else:
                    value = -_negamax(opp2, my2, depth - 1, -beta, -alpha)

                local_scores[m] = value

                if value > local_best_score:
                    local_best_score = value
                    local_best = m

                if value > alpha:
                    alpha = value

            # Depth completed: commit its best move.
            best_move = local_best
            best_score = local_best_score
            root_moves.sort(key=lambda mv: local_scores.get(mv, -_INF), reverse=True)

            if best_score >= _WIN_SCORE:
                break

    except _Timeout:
        pass

    return _move_to_str(best_move)
