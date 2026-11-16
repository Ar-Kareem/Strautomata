
import time

# Lines of Action policy for an 8x8 board.
# Board input uses: 1 = side to move, -1 = opponent, 0 = empty.

_INF = 10 ** 12
_WIN = 10 ** 9

_DIRS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (1, 1), (-1, 1), (1, -1)
]

_BIT = [1 << i for i in range(64)]
_NEIGH = [0] * 64
_CENTER = [0] * 64
_DIST = [[0] * 64 for _ in range(64)]
_LINE_MASK = [[0] * 8 for _ in range(64)]
_DEST = [[[-1] * 9 for _ in range(8)] for _ in range(64)]
_PATH = [[[0] * 9 for _ in range(8)] for _ in range(64)]

# Caches retained across calls.
_CONN_CACHE = {}
_COMP_CACHE = {}
_METRIC_CACHE = {}

_TT = {}
_DEADLINE = 0.0
_NODES = 0

_EXACT, _LOWER, _UPPER = 0, 1, 2


def _init_tables():
    for r in range(8):
        for c in range(8):
            p = r * 8 + c

            # 8-neighbor connectivity mask.
            nb = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < 8 and 0 <= cc < 8:
                        nb |= _BIT[rr * 8 + cc]
            _NEIGH[p] = nb

            # Center preference: corners low, central four squares high.
            _CENTER[p] = 14 - (abs(2 * r - 7) + abs(2 * c - 7))

    for a in range(64):
        ar, ac = divmod(a, 8)
        for b in range(64):
            br, bc = divmod(b, 8)
            _DIST[a][b] = max(abs(ar - br), abs(ac - bc))

    for p in range(64):
        r, c = divmod(p, 8)
        for d, (dr, dc) in enumerate(_DIRS):
            # Full row/column/diagonal line mask for movement count.
            mask = 0
            if dr == 0:
                for cc in range(8):
                    mask |= _BIT[r * 8 + cc]
            elif dc == 0:
                for rr in range(8):
                    mask |= _BIT[rr * 8 + c]
            elif dr == dc:
                diff = r - c
                for rr in range(8):
                    cc = rr - diff
                    if 0 <= cc < 8:
                        mask |= _BIT[rr * 8 + cc]
            else:
                s = r + c
                for rr in range(8):
                    cc = s - rr
                    if 0 <= cc < 8:
                        mask |= _BIT[rr * 8 + cc]
            _LINE_MASK[p][d] = mask

            # Destination and intervening path masks for distances 1..8.
            for dist in range(1, 9):
                rr, cc = r + dr * dist, c + dc * dist
                if 0 <= rr < 8 and 0 <= cc < 8:
                    _DEST[p][d][dist] = rr * 8 + cc
                    path = 0
                    for step in range(1, dist):
                        pr, pc = r + dr * step, c + dc * step
                        path |= _BIT[pr * 8 + pc]
                    _PATH[p][d][dist] = path


_init_tables()


class _SearchTimeout(Exception):
    pass


def _board_to_bits(board):
    own = 0
    opp = 0
    for r in range(8):
        row = board[r]
        base = r * 8
        for c in range(8):
            v = row[c]
            if v == 1:
                own |= _BIT[base + c]
            elif v == -1:
                opp |= _BIT[base + c]
    return own, opp


def _format_move(move):
    src, dst = move
    return f"{src // 8},{src % 8}:{dst // 8},{dst % 8}"


def _generate_moves(own, opp):
    occ = own | opp
    moves = []
    pieces = own

    while pieces:
        lsb = pieces & -pieces
        src = lsb.bit_length() - 1
        pieces ^= lsb

        for d in range(8):
            dist = (occ & _LINE_MASK[src][d]).bit_count()
            dst = _DEST[src][d][dist]
            if dst < 0:
                continue

            db = _BIT[dst]
            if own & db:
                continue

            # Enemy pieces may not be jumped over, but may be captured on dst.
            if opp & _PATH[src][d][dist]:
                continue

            moves.append((src, dst))

    return moves


def _make_move(own, opp, move):
    src, dst = move
    sb = _BIT[src]
    db = _BIT[dst]

    # After the move, perspective switches.
    moved_side = (own & ~sb) | db
    next_side = opp & ~db
    return next_side, moved_side


def _flood(bits, start):
    seen = 0
    frontier = start
    while frontier:
        seen |= frontier
        around = 0
        f = frontier
        while f:
            lsb = f & -f
            idx = lsb.bit_length() - 1
            around |= _NEIGH[idx]
            f ^= lsb
        frontier = around & bits & ~seen
    return seen


def _is_connected(bits):
    if bits == 0:
        return False
    if bits & (bits - 1) == 0:
        return True

    cached = _CONN_CACHE.get(bits)
    if cached is not None:
        return cached

    comp = _flood(bits, bits & -bits)
    res = (comp == bits)
    _CONN_CACHE[bits] = res
    if res:
        _COMP_CACHE[bits] = (1, bits.bit_count())
    return res


def _component_info(bits):
    cached = _COMP_CACHE.get(bits)
    if cached is not None:
        return cached

    if bits == 0:
        res = (0, 0)
        _COMP_CACHE[bits] = res
        _CONN_CACHE[bits] = False
        return res

    remaining = bits
    comps = 0
    largest = 0
    while remaining:
        start = remaining & -remaining
        comp = _flood(bits, start)
        cnt = comp.bit_count()
        if cnt > largest:
            largest = cnt
        comps += 1
        remaining &= ~comp

    res = (comps, largest)
    _COMP_CACHE[bits] = res
    _CONN_CACHE[bits] = (comps == 1)
    return res


def _metrics(bits):
    cached = _METRIC_CACHE.get(bits)
    if cached is not None:
        return cached

    n = bits.bit_count()
    if n == 0:
        res = (0, 0, 0, 999, 99, 0, 0, 0)
        _METRIC_CACHE[bits] = res
        return res

    comps, largest = _component_info(bits)

    positions = []
    b = bits
    minr, minc = 8, 8
    maxr, maxc = -1, -1
    center_sum = 0
    adj_twice = 0

    while b:
        lsb = b & -b
        p = lsb.bit_length() - 1
        positions.append(p)
        r, c = divmod(p, 8)
        if r < minr:
            minr = r
        if r > maxr:
            maxr = r
        if c < minc:
            minc = c
        if c > maxc:
            maxc = c
        center_sum += _CENTER[p]
        adj_twice += (_NEIGH[p] & bits).bit_count()
        b ^= lsb

    if n < 2:
        avg_dist = 0
    else:
        s = 0
        for i in range(n):
            pi = positions[i]
            rowdist = _DIST[pi]
            for j in range(i + 1, n):
                s += rowdist[positions[j]]
        avg_dist = (s * 200) // (n * (n - 1))  # average * 100

    box = (maxr - minr) + (maxc - minc)
    adj = adj_twice // 2
    center_avg = (center_sum * 100) // n
    area = (maxr - minr + 1) * (maxc - minc + 1)
    density = (n * 100) // area

    res = (n, comps, largest, avg_dist, box, adj, center_avg, density)
    _METRIC_CACHE[bits] = res
    return res


def _terminal_value(own, opp, ply):
    # At a searched node, "opp" is the player who just moved.
    # If both are connected, the mover wins, so check opp first.
    if own == 0:
        return -_WIN + ply
    if opp == 0:
        return _WIN - ply
    if _is_connected(opp):
        return -_WIN + ply
    if _is_connected(own):
        return _WIN - ply
    return None


def _evaluate(own, opp):
    if own == 0:
        return -_WIN // 2
    if opp == 0:
        return _WIN // 2

    on, oc, ol, odist, obox, oadj, ocenter, odens = _metrics(own)
    pn, pc, pl, pdist, pbox, padj, pcenter, pdens = _metrics(opp)

    own_largest_ratio = (ol * 100) // on
    opp_largest_ratio = (pl * 100) // pn

    score = 0

    # Connectivity is the main objective.
    score += 3500 * (pc - oc)
    score += 10 * (own_largest_ratio - opp_largest_ratio)

    # Compactness: connected groups tend to be close together.
    score += 4 * (pdist - odist)
    score += 80 * (pbox - obox)

    # Local adjacency and density help complete the final connection.
    score += 110 * (oadj - padj)
    score += 5 * (odens - pdens)

    # Mild central preference.
    score += 2 * (ocenter - pcenter)

    # Very small material term; material is not the primary LOA goal.
    score += 8 * (on - pn)

    return score


def _move_order_score(own, opp, move, preferred=None):
    if preferred is not None and move == preferred:
        return 10_000_000

    src, dst = move
    sb = _BIT[src]
    db = _BIT[dst]
    friends = own & ~sb

    adj_dst = (_NEIGH[dst] & friends).bit_count()
    adj_src = (_NEIGH[src] & friends).bit_count()

    score = 0
    score += 300 * adj_dst
    score -= 120 * adj_src
    if opp & db:
        score += 250
    score += 10 * (_CENTER[dst] - _CENTER[src])
    return score


def _greedy_select(own, opp, moves):
    best = moves[0]
    best_val = -_INF
    best_order = -_INF

    for m in moves:
        co, cp = _make_move(own, opp, m)
        tv = _terminal_value(co, cp, 1)
        if tv is None:
            val = -_evaluate(co, cp)
        else:
            val = -tv

        order = _move_order_score(own, opp, m, None)
        if val > best_val or (val == best_val and order > best_order):
            best_val = val
            best_order = order
            best = m

    return best


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 511) == 0:
        if time.perf_counter() >= _DEADLINE:
            raise _SearchTimeout()


def _ordered_moves(own, opp, preferred=None):
    moves = _generate_moves(own, opp)
    if len(moves) > 1:
        moves.sort(key=lambda m: _move_order_score(own, opp, m, preferred), reverse=True)
    return moves


def _negamax(own, opp, depth, alpha, beta, ply):
    _check_time()

    tv = _terminal_value(own, opp, ply)
    if tv is not None:
        return tv

    if depth <= 0:
        return _evaluate(own, opp)

    key = (own, opp)
    entry = _TT.get(key)
    tt_move = None

    alpha_orig = alpha
    beta_orig = beta

    if entry is not None:
        edepth, flag, val, move = entry
        tt_move = move
        if edepth >= depth:
            if flag == _EXACT:
                return val
            if flag == _LOWER:
                if val > alpha:
                    alpha = val
            elif flag == _UPPER:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val

    moves = _ordered_moves(own, opp, tt_move)
    if not moves:
        return -_WIN // 3 + ply

    best_val = -_INF
    best_move = moves[0]

    for m in moves:
        co, cp = _make_move(own, opp, m)
        val = -_negamax(co, cp, depth - 1, -beta, -alpha, ply + 1)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_val <= alpha_orig:
        flag = _UPPER
    elif best_val >= beta_orig:
        flag = _LOWER
    else:
        flag = _EXACT

    if len(_TT) < 200000:
        _TT[key] = (depth, flag, best_val, best_move)

    return best_val


def _root_search(own, opp, depth, preferred):
    if time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout()

    moves = _generate_moves(own, opp)
    if not moves:
        return -_WIN, None

    moves.sort(key=lambda m: _move_order_score(own, opp, m, preferred), reverse=True)

    alpha = -_INF
    beta = _INF
    best_move = moves[0]
    best_score = -_INF

    for m in moves:
        if time.perf_counter() >= _DEADLINE:
            raise _SearchTimeout()

        co, cp = _make_move(own, opp, m)
        score = -_negamax(co, cp, depth - 1, -beta, -alpha, 1)

        if score > best_score:
            best_score = score
            best_move = m

        if score > alpha:
            alpha = score

    return best_score, best_move


def policy(board) -> str:
    global _TT, _DEADLINE, _NODES

    _DEADLINE = time.perf_counter() + 0.88
    _NODES = 0
    _TT = {}

    # Prevent unbounded cache growth over very long matches.
    if len(_METRIC_CACHE) > 250000:
        _METRIC_CACHE.clear()
        _COMP_CACHE.clear()
        _CONN_CACHE.clear()

    own, opp = _board_to_bits(board)
    moves = _generate_moves(own, opp)

    # In normal LOA positions this should not occur. There is no legal string
    # if there are truly no legal moves, but return syntactically valid fallback.
    if not moves:
        return "0,0:0,0"

    # If a legal move immediately connects us, take the win.
    for m in moves:
        src, dst = m
        new_own = (own & ~_BIT[src]) | _BIT[dst]
        if _is_connected(new_own):
            return _format_move(m)

    # Safe legal fallback before any deeper search.
    best = _greedy_select(own, opp, moves)
    preferred = best

    # Iterative deepening. Previous completed depth is always available.
    try:
        for depth in range(1, 7):
            if time.perf_counter() >= _DEADLINE:
                break

            score, move = _root_search(own, opp, depth, preferred)
            if move is not None:
                best = move
                preferred = move

            if abs(score) > _WIN // 2:
                break

            if time.perf_counter() >= _DEADLINE - 0.025:
                break

    except _SearchTimeout:
        pass

    return _format_move(best)
