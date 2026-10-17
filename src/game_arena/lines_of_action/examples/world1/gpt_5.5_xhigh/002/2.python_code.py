
import time

# Lines of Action policy for an 8x8 board.
# Board encoding expected by policy:
#   1  = side to move
#  -1  = opponent
#   0  = empty

_DIRS = (
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (1, 1), (-1, 1), (1, -1)
)

_WIN = 100000000
_INF = 1000000000
_TIME_LIMIT = 0.88

_ROWS = [i // 8 for i in range(64)]
_COLS = [i & 7 for i in range(64)]

_NEIGH = [0] * 64
_CENTER = [0] * 64
_EDGE = [0] * 64
_CHEB = [[0] * 64 for _ in range(64)]

_ROW_MASKS = [0] * 8
_COL_MASKS = [0] * 8
_DIAG1_MASKS = [0] * 15
_DIAG2_MASKS = [0] * 15

for r in range(8):
    for c in range(8):
        i = r * 8 + c
        bit = 1 << i
        _ROW_MASKS[r] |= bit
        _COL_MASKS[c] |= bit
        _DIAG1_MASKS[r - c + 7] |= bit
        _DIAG2_MASKS[r + c] |= bit

for r in range(8):
    for c in range(8):
        i = r * 8 + c
        m = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if 0 <= rr < 8 and 0 <= cc < 8:
                    m |= 1 << (rr * 8 + cc)
        _NEIGH[i] = m
        # Higher is better; center four squares are best.
        _CENTER[i] = 50 - ((2 * r - 7) * (2 * r - 7) + (2 * c - 7) * (2 * c - 7))
        _EDGE[i] = 1 if (r == 0 or r == 7 or c == 0 or c == 7) else 0

for i in range(64):
    ri, ci = _ROWS[i], _COLS[i]
    for j in range(64):
        _CHEB[i][j] = max(abs(ri - _ROWS[j]), abs(ci - _COLS[j]))

_LINE_MASKS = [[0] * 8 for _ in range(64)]
_TARGETS = [[[-1] * 9 for _ in range(8)] for _ in range(64)]
_PATH_MASKS = [[[0] * 9 for _ in range(8)] for _ in range(64)]

for src in range(64):
    r, c = _ROWS[src], _COLS[src]
    for d, (dr, dc) in enumerate(_DIRS):
        if dr == 0:
            _LINE_MASKS[src][d] = _ROW_MASKS[r]
        elif dc == 0:
            _LINE_MASKS[src][d] = _COL_MASKS[c]
        elif dr == dc:
            _LINE_MASKS[src][d] = _DIAG1_MASKS[r - c + 7]
        else:
            _LINE_MASKS[src][d] = _DIAG2_MASKS[r + c]

        for dist in range(1, 9):
            rr, cc = r + dr * dist, c + dc * dist
            if 0 <= rr < 8 and 0 <= cc < 8:
                _TARGETS[src][d][dist] = rr * 8 + cc

            pm = 0
            for step in range(1, dist):
                sr, sc = r + dr * step, c + dc * step
                if 0 <= sr < 8 and 0 <= sc < 8:
                    pm |= 1 << (sr * 8 + sc)
            _PATH_MASKS[src][d][dist] = pm

_TT = {}
_CONN_CACHE = {}
_FEAT_CACHE = {}
_KILLERS = [[None, None] for _ in range(64)]
_HISTORY = [[0] * 64 for _ in range(64)]

_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _board_to_masks(board):
    own = 0
    opp = 0
    for r in range(8):
        row = board[r]
        for c in range(8):
            v = int(row[c])
            if v == 1:
                own |= 1 << (r * 8 + c)
            elif v == -1:
                opp |= 1 << (r * 8 + c)
    return own, opp


def _move_to_str(move):
    src, dst = move
    return f"{src // 8},{src & 7}:{dst // 8},{dst & 7}"


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() >= _DEADLINE:
        raise _Timeout()


def _flood(start, mask):
    seen = 0
    frontier = start
    while frontier:
        seen |= frontier
        nbrs = 0
        f = frontier
        while f:
            b = f & -f
            nbrs |= _NEIGH[b.bit_length() - 1]
            f -= b
        frontier = nbrs & mask & ~seen
    return seen


def _is_connected(mask):
    if mask == 0:
        return False
    if (mask & (mask - 1)) == 0:
        return True

    cached = _CONN_CACHE.get(mask)
    if cached is not None:
        return cached

    group = _flood(mask & -mask, mask)
    res = (group == mask)
    _CONN_CACHE[mask] = res
    return res


def _component_stats(mask):
    remaining = mask
    comps = 0
    largest = 0
    while remaining:
        start = remaining & -remaining
        group = _flood(start, mask)
        sz = group.bit_count()
        if sz > largest:
            largest = sz
        comps += 1
        remaining &= ~group
    return comps, largest


def _side_feature(mask):
    cached = _FEAT_CACHE.get(mask)
    if cached is not None:
        return cached

    n = mask.bit_count()
    if n == 0:
        return -50000.0

    comps, largest = _component_stats(mask)

    positions = []
    temp = mask
    minr, maxr = 8, -1
    minc, maxc = 8, -1
    center_sum = 0
    edge_count = 0

    while temp:
        b = temp & -temp
        i = b.bit_length() - 1
        temp -= b
        positions.append(i)

        r, c = _ROWS[i], _COLS[i]
        if r < minr:
            minr = r
        if r > maxr:
            maxr = r
        if c < minc:
            minc = c
        if c > maxc:
            maxc = c
        center_sum += _CENTER[i]
        edge_count += _EDGE[i]

    adj_twice = 0
    for i in positions:
        adj_twice += (_NEIGH[i] & mask).bit_count()
    adj_pairs = adj_twice * 0.5

    if n > 1:
        pair_sum = 0
        nearest_sum = 0
        for a in range(n):
            ia = positions[a]
            rowdist = _CHEB[ia]
            nearest = 9
            for b in range(n):
                if a == b:
                    continue
                d = rowdist[positions[b]]
                if d < nearest:
                    nearest = d
                if b > a:
                    pair_sum += d
            nearest_sum += nearest

        avg_pair = pair_sum / (n * (n - 1) * 0.5)
        avg_nearest = nearest_sum / n
    else:
        avg_pair = 0.0
        avg_nearest = 0.0

    area = (maxr - minr + 1) * (maxc - minc + 1)

    score = 0.0
    score -= 1350.0 * (comps - 1)
    score += 1000.0 * (largest / n)
    score += 320.0 * (adj_pairs / max(1, n - 1))
    score -= 85.0 * avg_pair
    score -= 120.0 * avg_nearest
    score -= 18.0 * area
    score += 5.0 * (center_sum / n)
    score -= 25.0 * (edge_count / n)

    _FEAT_CACHE[mask] = score
    return score


def _terminal_value(own, opp):
    if own == 0:
        return -_WIN
    if opp == 0:
        return _WIN

    # At a just-reached node, opp is the player who just moved.
    # If both are connected, the mover is treated as the winner.
    if _is_connected(opp):
        return -_WIN
    if _is_connected(own):
        return _WIN
    return None


def _evaluate(own, opp):
    return _side_feature(own) - _side_feature(opp)


def _generate_moves(own, opp, tt_move=None, ply=0):
    occ = own | opp
    moves = []

    killer0 = killer1 = None
    if ply < len(_KILLERS):
        killer0, killer1 = _KILLERS[ply]

    pieces = own
    while pieces:
        sbit = pieces & -pieces
        src = sbit.bit_length() - 1
        pieces -= sbit

        own_without_src = own & ~sbit
        before_adj = (_NEIGH[src] & own_without_src).bit_count()

        for d in range(8):
            dist = (occ & _LINE_MASKS[src][d]).bit_count()
            dst = _TARGETS[src][d][dist]
            if dst < 0:
                continue

            dbit = 1 << dst
            if own & dbit:
                continue
            if opp & _PATH_MASKS[src][d][dist]:
                continue

            move = (src, dst)
            after_adj = (_NEIGH[dst] & own_without_src).bit_count()
            capture = 1 if (opp & dbit) else 0

            score = _HISTORY[src][dst]
            score += 35 * after_adj - 18 * before_adj
            score += 3 * (_CENTER[dst] - _CENTER[src])

            if capture:
                score += 90 + 12 * ((_NEIGH[dst] & (opp & ~dbit)).bit_count())
            if before_adj == 0 and after_adj > 0:
                score += 45
            if after_adj >= 2:
                score += 25

            if move == tt_move:
                score += 1000000
            elif move == killer0:
                score += 500000
            elif move == killer1:
                score += 400000

            moves.append((score, move))

    moves.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in moves]


def _play(own, opp, move):
    src, dst = move
    sbit = 1 << src
    dbit = 1 << dst
    moved_own = (own & ~sbit) | dbit
    new_opp = opp & ~dbit
    # Switch perspective for negamax.
    return new_opp, moved_own


def _moved_own_mask(own, move):
    src, dst = move
    return (own & ~(1 << src)) | (1 << dst)


def _negamax(own, opp, depth, alpha, beta, ply):
    _check_time()

    tv = _terminal_value(own, opp)
    if tv is not None:
        return tv

    key = (own, opp)
    entry = _TT.get(key)
    tt_move = None
    if entry is not None:
        edepth, flag, val, emove = entry
        tt_move = emove
        if edepth >= depth:
            if flag == 0:
                return val
            if flag == 1:
                if val > alpha:
                    alpha = val
            elif flag == 2:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val

    if depth <= 0:
        return _evaluate(own, opp)

    orig_alpha = alpha
    moves = _generate_moves(own, opp, tt_move, ply)
    if not moves:
        return -_WIN

    best_val = -_INF
    best_move = moves[0]

    for move in moves:
        child_own, child_opp = _play(own, opp, move)
        val = -_negamax(child_own, child_opp, depth - 1, -beta, -alpha, ply + 1)

        if val > best_val:
            best_val = val
            best_move = move
        if val > alpha:
            alpha = val

        if alpha >= beta:
            dst = move[1]
            if not (opp & (1 << dst)) and ply < len(_KILLERS):
                k0 = _KILLERS[ply][0]
                if move != k0:
                    _KILLERS[ply][1] = k0
                    _KILLERS[ply][0] = move
                _HISTORY[move[0]][move[1]] += depth * depth
            break

    if best_val <= orig_alpha:
        flag = 2  # upper bound
    elif best_val >= beta:
        flag = 1  # lower bound
    else:
        flag = 0  # exact

    _TT[key] = (depth, flag, best_val, best_move)
    return best_val


def _root_search(own, opp, depth, ordered_moves):
    alpha = -_INF
    beta = _INF
    best_move = ordered_moves[0]
    best_val = -_INF
    scored = []

    for move in ordered_moves:
        if time.perf_counter() >= _DEADLINE:
            raise _Timeout()

        child_own, child_opp = _play(own, opp, move)
        val = -_negamax(child_own, child_opp, depth - 1, -beta, -alpha, 1)

        scored.append((val, move))

        if val > best_val:
            best_val = val
            best_move = move
        if val > alpha:
            alpha = val

        if best_val >= _WIN // 2:
            break

    return best_move, best_val, scored


def _emergency_move(own, opp):
    moves = _generate_moves(own, opp, None, 0)
    if moves:
        return _move_to_str(moves[0])

    # Degenerate fallback for already-terminal malformed positions.
    pieces = own
    while pieces:
        b = pieces & -pieces
        src = b.bit_length() - 1
        pieces -= b
        for d in range(8):
            dst = _TARGETS[src][d][1]
            if dst >= 0 and not (own & (1 << dst)):
                return _move_to_str((src, dst))

    return "0,0:0,0"


def policy(board) -> str:
    global _DEADLINE, _NODES

    start = time.perf_counter()
    _DEADLINE = start + _TIME_LIMIT
    _NODES = 0

    if len(_TT) > 300000:
        _TT.clear()
    if len(_FEAT_CACHE) > 200000:
        _FEAT_CACHE.clear()
    if len(_CONN_CACHE) > 200000:
        _CONN_CACHE.clear()

    for k in _KILLERS:
        k[0] = None
        k[1] = None

    # Gentle decay so old history helps but does not dominate forever.
    for r in range(64):
        row = _HISTORY[r]
        for c in range(64):
            row[c] >>= 1

    own, opp = _board_to_masks(board)
    moves = _generate_moves(own, opp, None, 0)

    if not moves:
        return _emergency_move(own, opp)

    # If any legal move connects us immediately, play it.
    for move in moves:
        moved = _moved_own_mask(own, move)
        if _is_connected(moved):
            return _move_to_str(move)

    # Safe legal fallback before spending time searching.
    fallback = moves[0]
    for move in moves:
        child_own, child_opp = _play(own, opp, move)
        tv = _terminal_value(child_own, child_opp)
        # From the child's perspective, WIN means the opponent wins immediately.
        if tv is None or tv < 0:
            fallback = move
            break

    best = fallback
    ordered = moves[:]

    try:
        for depth in range(1, 11):
            best_d, val, scored = _root_search(own, opp, depth, ordered)

            if scored:
                best = best_d
                scored.sort(key=lambda x: x[0], reverse=True)
                done = {m for _, m in scored}
                ordered = [m for _, m in scored] + [m for m in ordered if m not in done]

            if val >= _WIN // 2:
                break
            if time.perf_counter() >= _DEADLINE - 0.03:
                break

    except _Timeout:
        pass
    except Exception:
        # The fallback was produced by the legal move generator.
        pass

    if best not in moves:
        best = fallback

    return _move_to_str(best)
