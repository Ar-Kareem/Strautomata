
import time

# Lines of Action policy for an 8x8 board.
# Public API:
#     policy(board) -> "from_row,from_col:to_row,to_col"

_N = 8
_FULL = (1 << 64) - 1
_TIME = time.perf_counter

_DIRS = (
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (1, 1), (-1, 1), (1, -1)
)

_BITS = [1 << i for i in range(64)]
_ROW = [i // 8 for i in range(64)]
_COL = [i % 8 for i in range(64)]
_CENTER = [((2 * _ROW[i] - 7) ** 2 + (2 * _COL[i] - 7) ** 2) for i in range(64)]
_CHEB = [[max(abs(_ROW[i] - _ROW[j]), abs(_COL[i] - _COL[j])) for j in range(64)] for i in range(64)]

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

_LINE_MASKS = [[0 for _ in range(8)] for _ in range(64)]
_DESTS = [[[-1 for _ in range(9)] for _ in range(8)] for _ in range(64)]
_PATHS = [[[0 for _ in range(9)] for _ in range(8)] for _ in range(64)]

for i in range(64):
    r, c = _ROW[i], _COL[i]
    for d, (dr, dc) in enumerate(_DIRS):
        if dr == 0:
            line = _ROW_MASKS[r]
        elif dc == 0:
            line = _COL_MASKS[c]
        elif dr == dc:
            line = _D1_MASKS[r - c + 7]
        else:
            line = _D2_MASKS[r + c]
        _LINE_MASKS[i][d] = line

        for n in range(1, 9):
            tr, tc = r + dr * n, c + dc * n
            if 0 <= tr < 8 and 0 <= tc < 8:
                _DESTS[i][d][n] = tr * 8 + tc

            pm = 0
            rr, cc = r + dr, c + dc
            for _ in range(1, n):
                if 0 <= rr < 8 and 0 <= cc < 8:
                    pm |= _BITS[rr * 8 + cc]
                rr += dr
                cc += dc
            _PATHS[i][d][n] = pm

_FILE_A = 0
_FILE_H = 0
for r in range(8):
    _FILE_A |= _BITS[r * 8]
    _FILE_H |= _BITS[r * 8 + 7]
_NOT_FILE_A = _FULL ^ _FILE_A
_NOT_FILE_H = _FULL ^ _FILE_H


def _neighbors(x):
    return (
        (x >> 8)
        | ((x & _NOT_FILE_A) >> 1)
        | ((x & _NOT_FILE_H) << 1)
        | ((x & _NOT_FILE_A) >> 9)
        | ((x & _NOT_FILE_H) >> 7)
        | (((x << 8) | ((x & _NOT_FILE_A) << 7) | ((x & _NOT_FILE_H) << 9)) & _FULL)
    )


_ADJ = [_neighbors(_BITS[i]) for i in range(64)]

_QUAD_MASKS = []
for r in range(7):
    for c in range(7):
        _QUAD_MASKS.append(
            _BITS[r * 8 + c]
            | _BITS[r * 8 + c + 1]
            | _BITS[(r + 1) * 8 + c]
            | _BITS[(r + 1) * 8 + c + 1]
        )
_QUAD_W = (0, -4, 5, 16, 28)

_WIN = 10_000_000
_INF = 1_000_000_000
_EXACT, _LOWER, _UPPER = 0, 1, 2

_TT = {}
_FEATURE_CACHE = {}
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _board_to_bits(board):
    own = 0
    opp = 0
    for r in range(8):
        for c in range(8):
            v = board[r][c]
            if v == 1:
                own |= _BITS[r * 8 + c]
            elif v == -1:
                opp |= _BITS[r * 8 + c]
    return own, opp


def _move_to_string(mv):
    i, j = mv
    return f"{_ROW[i]},{_COL[i]}:{_ROW[j]},{_COL[j]}"


def _connected(bb):
    if bb == 0 or (bb & (bb - 1)) == 0:
        return True
    seen = 0
    frontier = bb & -bb
    while frontier:
        seen |= frontier
        frontier = _neighbors(frontier) & bb & ~seen
    return seen == bb


def _terminal_value(own, opp, side_to_move):
    own_conn = _connected(own)
    opp_conn = _connected(opp)
    if not own_conn and not opp_conn:
        return None

    if own_conn and opp_conn:
        # In simultaneous connection, the player who just moved wins.
        winner = -side_to_move
    elif own_conn:
        winner = 1
    else:
        winner = -1

    return _WIN if winner == 1 else -_WIN


def _component_info(bb):
    if bb == 0:
        return 0, 0
    remaining = bb
    comps = 0
    largest = 0
    while remaining:
        comps += 1
        seen = 0
        frontier = remaining & -remaining
        while frontier:
            seen |= frontier
            frontier = _neighbors(frontier) & bb & ~seen
        sz = seen.bit_count()
        if sz > largest:
            largest = sz
        remaining &= ~seen
    return comps, largest


def _indices(bb):
    out = []
    while bb:
        b = bb & -bb
        out.append(b.bit_length() - 1)
        bb ^= b
    return out


def _mst_length(ids):
    n = len(ids)
    if n <= 1:
        return 0

    used = [False] * n
    dist = [99] * n
    dist[0] = 0
    total = 0

    for _ in range(n):
        k = -1
        best = 99
        for i in range(n):
            if not used[i] and dist[i] < best:
                best = dist[i]
                k = i

        used[k] = True
        total += best
        row = _CHEB[ids[k]]

        for j in range(n):
            if not used[j]:
                d = row[ids[j]]
                if d < dist[j]:
                    dist[j] = d

    return total


def _side_score(bb):
    cached = _FEATURE_CACHE.get(bb)
    if cached is not None:
        return cached

    n = bb.bit_count()
    if n <= 1:
        score = 500_000
    else:
        ids = _indices(bb)
        comps, largest = _component_info(bb)

        edges = 0
        for i in ids:
            edges += (_ADJ[i] & bb).bit_count()
        edges //= 2

        mst = _mst_length(ids)
        extra = mst - (n - 1)
        if extra < 0:
            extra = 0

        minr = minc = 8
        maxr = maxc = -1
        center = 0
        for i in ids:
            r, c = _ROW[i], _COL[i]
            if r < minr:
                minr = r
            if r > maxr:
                maxr = r
            if c < minc:
                minc = c
            if c > maxc:
                maxc = c
            center += _CENTER[i]

        area = (maxr - minr + 1) * (maxc - minc + 1)
        span = (maxr - minr) + (maxc - minc)

        quad = 0
        for qm in _QUAD_MASKS:
            quad += _QUAD_W[(bb & qm).bit_count()]

        score = 0
        score -= 2400 * (comps - 1)
        score += (1800 * largest) // n
        score -= 350 * extra
        score += 70 * edges
        score += 8 * quad
        score -= 45 * span
        score -= 12 * (area - n)
        score -= 2 * center
        score += 4 * n

    if len(_FEATURE_CACHE) < 120_000:
        _FEATURE_CACHE[bb] = score
    return score


def _evaluate(own, opp):
    return _side_score(own) - _side_score(opp)


def _generate_moves(own, opp, side):
    occ = own | opp
    if side == 1:
        friends, enemies = own, opp
    else:
        friends, enemies = opp, own

    moves = []
    bb = friends
    while bb:
        b = bb & -bb
        i = b.bit_length() - 1
        bb ^= b

        line_masks = _LINE_MASKS[i]
        dests = _DESTS[i]
        paths = _PATHS[i]

        for d in range(8):
            n = (occ & line_masks[d]).bit_count()
            j = dests[d][n]
            if j < 0:
                continue

            tb = _BITS[j]
            if friends & tb:
                continue
            if paths[d][n] & enemies:
                continue

            moves.append((i, j))

    return moves


def _do_move(own, opp, side, mv):
    i, j = mv
    fb = _BITS[i]
    tb = _BITS[j]
    if side == 1:
        return ((own & ~fb) | tb), (opp & ~tb)
    else:
        return (own & ~tb), ((opp & ~fb) | tb)


def _move_order_score(own, opp, side, mv, tt_move=None):
    if tt_move == mv:
        return 1_000_000_000

    i, j = mv
    fb = _BITS[i]
    tb = _BITS[j]

    if side == 1:
        friends, enemies = own, opp
    else:
        friends, enemies = opp, own

    friends_without = friends & ~fb

    score = 0
    if enemies & tb:
        score += 1200

    score += 90 * (_ADJ[j] & friends_without).bit_count()
    score -= 35 * (_ADJ[i] & friends_without).bit_count()
    score += 4 * (_CENTER[i] - _CENTER[j])
    score += 3 * (_ADJ[j] & enemies).bit_count()
    score += ((i * 17 + j * 31) & 7)
    return score


def _alphabeta(own, opp, side, depth, alpha, beta):
    global _NODES

    _NODES += 1
    if (_NODES & 511) == 0 and _TIME() > _DEADLINE:
        raise _SearchTimeout()

    tv = _terminal_value(own, opp, side)
    if tv is not None:
        return tv

    if depth <= 0:
        return _evaluate(own, opp)

    key = None
    tt_move = None

    if depth >= 2:
        key = (own, opp, side)
        entry = _TT.get(key)
        if entry is not None:
            edepth, flag, val, mv = entry
            tt_move = mv
            if edepth >= depth:
                if flag == _EXACT:
                    return val
                if flag == _LOWER and val >= beta:
                    return val
                if flag == _UPPER and val <= alpha:
                    return val

    moves = _generate_moves(own, opp, side)
    if not moves:
        return -_WIN // 2 if side == 1 else _WIN // 2

    moves.sort(key=lambda m: _move_order_score(own, opp, side, m, tt_move), reverse=True)

    alpha0, beta0 = alpha, beta
    best_move = moves[0]

    if side == 1:
        value = -_INF
        for mv in moves:
            no, np = _do_move(own, opp, side, mv)
            val = _alphabeta(no, np, -1, depth - 1, alpha, beta)
            if val > value:
                value = val
                best_move = mv
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
    else:
        value = _INF
        for mv in moves:
            no, np = _do_move(own, opp, side, mv)
            val = _alphabeta(no, np, 1, depth - 1, alpha, beta)
            if val < value:
                value = val
                best_move = mv
            if value < beta:
                beta = value
            if alpha >= beta:
                break

    if key is not None and len(_TT) < 250_000:
        if value <= alpha0:
            flag = _UPPER
        elif value >= beta0:
            flag = _LOWER
        else:
            flag = _EXACT
        _TT[key] = (depth, flag, value, best_move)

    return value


def _root_static_value(own, opp, mv):
    no, np = _do_move(own, opp, 1, mv)
    tv = _terminal_value(no, np, -1)
    if tv is not None:
        return tv
    return _evaluate(no, np) + _move_order_score(own, opp, 1, mv) // 5


def _opponent_has_immediate_win(own, opp):
    for mv in _generate_moves(own, opp, -1):
        no, np = _do_move(own, opp, -1, mv)
        if _terminal_value(no, np, 1) == -_WIN:
            return True
    return False


def policy(board) -> str:
    global _DEADLINE, _NODES

    try:
        own, opp = _board_to_bits(board)
        all_moves = _generate_moves(own, opp, 1)
    except Exception:
        return "0,0:0,0"

    if not all_moves:
        return "0,0:0,0"

    fallback = all_moves[0]

    try:
        if len(_TT) > 300_000:
            _TT.clear()
        if len(_FEATURE_CACHE) > 180_000:
            _FEATURE_CACHE.clear()

        _DEADLINE = _TIME() + 0.90
        _NODES = 0

        # 1. Take an immediate win; otherwise avoid moves that immediately lose.
        non_losing = []
        for mv in all_moves:
            no, np = _do_move(own, opp, 1, mv)
            tv = _terminal_value(no, np, -1)
            if tv == _WIN:
                return _move_to_string(mv)
            if tv != -_WIN:
                non_losing.append(mv)

        moves = non_losing if non_losing else all_moves

        # 2. If affordable, avoid allowing the opponent a one-move win.
        if non_losing and _TIME() < _DEADLINE - 0.20:
            safe = []
            checked_all = True
            for mv in non_losing:
                if _TIME() > _DEADLINE - 0.20:
                    checked_all = False
                    break
                no, np = _do_move(own, opp, 1, mv)
                if not _opponent_has_immediate_win(no, np):
                    safe.append(mv)
            if checked_all and safe:
                moves = safe

        static_scores = {mv: _root_static_value(own, opp, mv) for mv in moves}
        best_move = max(moves, key=lambda m: static_scores[m])
        root_scores = dict(static_scores)

        total_pieces = (own | opp).bit_count()
        legal_count = len(moves)
        if total_pieces <= 8 or legal_count <= 12:
            max_depth = 7
        elif total_pieces <= 14:
            max_depth = 6
        else:
            max_depth = 5

        # 3. Iterative deepening alpha-beta.
        for depth in range(1, max_depth + 1):
            if _TIME() > _DEADLINE:
                break

            ordered = list(moves)
            ordered.sort(
                key=lambda m: (m == best_move, root_scores.get(m, static_scores.get(m, 0))),
                reverse=True,
            )

            try:
                alpha = -_INF
                beta = _INF
                iter_best = best_move
                iter_score = -_INF
                current_scores = {}

                for mv in ordered:
                    if _TIME() > _DEADLINE:
                        raise _SearchTimeout()

                    no, np = _do_move(own, opp, 1, mv)
                    val = _alphabeta(no, np, -1, depth - 1, alpha, beta)
                    current_scores[mv] = val

                    if val > iter_score:
                        iter_score = val
                        iter_best = mv
                    if val > alpha:
                        alpha = val

                best_move = iter_best
                root_scores = current_scores

                if iter_score >= _WIN // 2:
                    break

            except _SearchTimeout:
                break

        return _move_to_string(best_move)

    except Exception:
        return _move_to_string(fallback)
