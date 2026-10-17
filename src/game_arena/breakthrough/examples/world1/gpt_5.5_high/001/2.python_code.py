
import time

_WIN = 100_000_000
_INF = 1_000_000_000

_EXACT, _LOWER, _UPPER = 0, 1, 2

_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


_ROW_MASKS = tuple(0xFF << (8 * r) for r in range(8))
_GOAL = {1: _ROW_MASKS[7], -1: _ROW_MASKS[0]}
_PENULT = {1: _ROW_MASKS[6], -1: _ROW_MASKS[1]}

_CENTER = (0, 4, 7, 9, 9, 7, 4, 0)
_ADV = (0, 7, 22, 50, 95, 170, 310, 500)
_PASS = (0, 1000, 430, 190, 80, 25, 0, 0)          # indexed by distance to goal
_PASS_ORDER = (0, 5000, 1500, 600, 220, 80, 20, 0)  # move-ordering bonus
_CLOSE = (0, 620, 240, 95, 35, 10, 0, 0)            # closest-piece bonus

_PROG = {1: [0] * 64, -1: [0] * 64}
_DIST = {1: [0] * 64, -1: [0] * 64}
_FRONT = {1: [0] * 64, -1: [0] * 64}
_ATTACKERS = {1: [0] * 64, -1: [0] * 64}
_TARGETS = {1: [0] * 64, -1: [0] * 64}

for _d in (1, -1):
    for _i in range(64):
        _r, _c = divmod(_i, 8)

        _PROG[_d][_i] = _r if _d == 1 else 7 - _r
        _DIST[_d][_i] = 7 - _r if _d == 1 else _r

        # Squares in the forward cone: same/adjacent files on all rows ahead.
        _mask = 0
        _nr = _r + _d
        while 0 <= _nr < 8:
            for _dc in (-1, 0, 1):
                _nc = _c + _dc
                if 0 <= _nc < 8:
                    _mask |= 1 << (8 * _nr + _nc)
            _nr += _d
        _FRONT[_d][_i] = _mask

        # Friendly/enemy pieces moving direction d that can diagonally capture square i.
        _mask = 0
        _sr = _r - _d
        if 0 <= _sr < 8:
            if _c > 0:
                _mask |= 1 << (8 * _sr + _c - 1)
            if _c < 7:
                _mask |= 1 << (8 * _sr + _c + 1)
        _ATTACKERS[_d][_i] = _mask

        # Diagonal forward target squares from i for a piece moving direction d.
        _mask = 0
        _tr = _r + _d
        if 0 <= _tr < 8:
            if _c > 0:
                _mask |= 1 << (8 * _tr + _c - 1)
            if _c < 7:
                _mask |= 1 << (8 * _tr + _c + 1)
        _TARGETS[_d][_i] = _mask

    _PROG[_d] = tuple(_PROG[_d])
    _DIST[_d] = tuple(_DIST[_d])
    _FRONT[_d] = tuple(_FRONT[_d])
    _ATTACKERS[_d] = tuple(_ATTACKERS[_d])
    _TARGETS[_d] = tuple(_TARGETS[_d])


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout


def _make_bits(pieces):
    b = 0
    for r, c in pieces:
        if 0 <= r < 8 and 0 <= c < 8:
            b |= 1 << (8 * r + c)
    return b


def _to_coords(move):
    i, t = move
    return ((i >> 3, i & 7), (t >> 3, t & 7))


def _terminal_score(p, e, d, ply):
    if p == 0:
        return -_WIN + ply
    if e == 0:
        return _WIN - ply
    if e & _GOAL[-d]:
        return -_WIN + ply
    if p & _GOAL[d]:
        return _WIN - ply
    return None


def _has_goal_move(p, e, d):
    b = p & _PENULT[d]
    if not b:
        return False

    occ = p | e
    off = 8 * d

    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb

        c = i & 7
        t = i + off
        tb = 1 << t

        # Straight forward only if empty.
        if not (occ & tb):
            return True

        # Diagonal into the goal row is legal if not occupied by own piece.
        if c > 0 and not (p & (1 << (t - 1))):
            return True
        if c < 7 and not (p & (1 << (t + 1))):
            return True

    return False


def _can_capture_last(p, e, d):
    if e and (e & (e - 1)) == 0:
        target = (e & -e).bit_length() - 1
        return bool(p & _ATTACKERS[d][target])
    return False


def _side_score(bits, enemy, d):
    count = bits.bit_count()
    score = count * 100

    prog_arr = _PROG[d]
    dist_arr = _DIST[d]
    front_arr = _FRONT[d]
    friend_attackers = _ATTACKERS[d]
    enemy_attackers = _ATTACKERS[-d]
    targets_arr = _TARGETS[d]

    min_dist = 8
    b = bits

    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb

        c = i & 7
        prog = prog_arr[i]
        dist = dist_arr[i]
        if dist < min_dist:
            min_dist = dist

        score += _ADV[prog] + _CENTER[c]

        # Passed/runner piece: no enemy in the forward cone.
        if not (enemy & front_arr[i]):
            score += _PASS[dist]

        if dist == 1:
            score += 420
        elif dist == 2:
            score += 150

        defenders = (bits & friend_attackers[i]).bit_count()
        if defenders:
            score += 14 + 6 * defenders

        attackers = (enemy & enemy_attackers[i]).bit_count()
        if attackers:
            danger = 35 + 12 * prog
            if dist == 1:
                danger += 260
            elif dist == 2:
                danger += 120
            if defenders:
                danger //= 2
            score -= danger + 35 * (attackers - 1)

        capture_targets = (enemy & targets_arr[i]).bit_count()
        if capture_targets:
            score += 25 * capture_targets

        # Small formation bonus.
        if c > 0 and (bits & (1 << (i - 1))):
            score += 3
        if c < 7 and (bits & (1 << (i + 1))):
            score += 3

    if min_dist < 8:
        score += _CLOSE[min_dist]

    return score


def _evaluate(p, e, d):
    cur_win_next = _has_goal_move(p, e, d) or _can_capture_last(p, e, d)
    opp_win_next = False if cur_win_next else (_has_goal_move(e, p, -d) or _can_capture_last(e, p, -d))

    score = _side_score(p, e, d) - _side_score(e, p, -d) + 4

    if cur_win_next:
        score += _WIN // 4
    elif opp_win_next:
        score -= _WIN // 4

    return score


def _order_score(i, t, p, e, d):
    tb = 1 << t
    cap = bool(e & tb)
    dist = _DIST[d][t]
    prog = _PROG[d][t]
    c = t & 7

    if dist == 0:
        return 10_000_000 + (1000 if cap else 0)

    score = prog * 24 + _CENTER[c]

    if cap:
        score += 1200 + _PROG[-d][t] * 70
    elif (i & 7) != c:
        score += 20

    if not (e & _FRONT[d][t]):
        score += _PASS_ORDER[dist]

    if dist == 1:
        score += 1400
    elif dist == 2:
        score += 300

    p2 = (p & ~(1 << i)) | tb

    if e & _ATTACKERS[-d][t]:
        score -= 500 if dist <= 2 else 90

    if p2 & _ATTACKERS[d][t]:
        score += 80

    attacks = (e & _TARGETS[d][t]).bit_count()
    if attacks:
        score += 120 * attacks

    return score


def _ordered_moves(p, e, d, preferred=None):
    occ = p | e
    off = 8 * d
    moves = []
    b = p

    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb

        r = i >> 3
        c = i & 7
        nr = r + d
        if nr < 0 or nr > 7:
            continue

        # Straight forward: only to empty.
        t = i + off
        tb = 1 << t
        if not (occ & tb):
            s = _order_score(i, t, p, e, d)
            if preferred is not None and preferred[0] == i and preferred[1] == t:
                s += 20_000_000
            moves.append((s, i, t))

        # Diagonal left: empty move or capture, but not onto own piece.
        if c > 0:
            t = i + off - 1
            tb = 1 << t
            if not (p & tb):
                s = _order_score(i, t, p, e, d)
                if preferred is not None and preferred[0] == i and preferred[1] == t:
                    s += 20_000_000
                moves.append((s, i, t))

        # Diagonal right: empty move or capture, but not onto own piece.
        if c < 7:
            t = i + off + 1
            tb = 1 << t
            if not (p & tb):
                s = _order_score(i, t, p, e, d)
                if preferred is not None and preferred[0] == i and preferred[1] == t:
                    s += 20_000_000
                moves.append((s, i, t))

    moves.sort(reverse=True)
    return moves


def _search(p, e, d, depth, alpha, beta, ply):
    _check_time()

    term = _terminal_score(p, e, d, ply)
    if term is not None:
        return term

    if depth <= 0:
        return _evaluate(p, e, d)

    alpha_orig = alpha
    beta_orig = beta
    key = (p, e, d)

    rec = _TT.get(key)
    tt_move = rec[3] if rec is not None else None

    if rec is not None and rec[0] >= depth:
        val, flag = rec[1], rec[2]
        if flag == _EXACT:
            return val
        if flag == _LOWER:
            if val >= beta:
                return val
            if val > alpha:
                alpha = val
        elif flag == _UPPER:
            if val <= alpha:
                return val
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    moves = _ordered_moves(p, e, d, tt_move)
    if not moves:
        return -_WIN + ply

    best = -_INF
    best_move = None
    first = True

    for _, i, t in moves:
        tb = 1 << t
        p2 = (p & ~(1 << i)) | tb
        e2 = e & ~tb

        if first:
            val = -_search(e2, p2, -d, depth - 1, -beta, -alpha, ply + 1)
            first = False
        else:
            val = -_search(e2, p2, -d, depth - 1, -alpha - 1, -alpha, ply + 1)
            if alpha < val < beta:
                val = -_search(e2, p2, -d, depth - 1, -beta, -alpha, ply + 1)

        if val > best:
            best = val
            best_move = (i, t)

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best <= alpha_orig:
        flag = _UPPER
    elif best >= beta_orig:
        flag = _LOWER
    else:
        flag = _EXACT

    if len(_TT) < 300_000:
        _TT[key] = (depth, best, flag, best_move)

    return best


def _root_search(p, e, d, depth, preferred):
    alpha = -_INF
    beta = _INF
    best = -_INF
    best_move = preferred

    moves = _ordered_moves(p, e, d, preferred)
    if not moves:
        return -_WIN, None

    first = True

    for _, i, t in moves:
        _check_time()

        tb = 1 << t
        p2 = (p & ~(1 << i)) | tb
        e2 = e & ~tb

        if first:
            val = -_search(e2, p2, -d, depth - 1, -beta, -alpha, 1)
            first = False
        else:
            val = -_search(e2, p2, -d, depth - 1, -alpha - 1, -alpha, 1)
            if alpha < val < beta:
                val = -_search(e2, p2, -d, depth - 1, -beta, -alpha, 1)

        if val > best:
            best = val
            best_move = (i, t)

        if val > alpha:
            alpha = val

    return best, best_move


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global _TT, _DEADLINE, _NODES

    start = time.perf_counter()
    _DEADLINE = start + 0.88
    _NODES = 0
    _TT = {}

    d = -1 if color == "b" else 1

    p = _make_bits(me)
    e = _make_bits(opp)

    moves = _ordered_moves(p, e, d, None)

    # Terminal/no-legal fallback. In normal arena play this should not be reached
    # except after the game is already over.
    if not moves:
        if me:
            return (me[0], me[0])
        return ((0, 0), (0, 0))

    # Always take an immediate win.
    for _, i, t in moves:
        tb = 1 << t
        if _DIST[d][t] == 0 or ((e & tb) and (e & (e - 1)) == 0):
            return _to_coords((i, t))

    if len(moves) == 1:
        return _to_coords((moves[0][1], moves[0][2]))

    best_move = (moves[0][1], moves[0][2])
    best_val = -_INF

    total_pieces = (p | e).bit_count()
    if total_pieces <= 6:
        max_depth = 12
    elif total_pieces <= 10:
        max_depth = 10
    elif total_pieces <= 16:
        max_depth = 9
    elif total_pieces <= 24:
        max_depth = 7
    else:
        max_depth = 6

    for depth in range(1, max_depth + 1):
        if time.perf_counter() > _DEADLINE - 0.02:
            break

        try:
            val, mv = _root_search(p, e, d, depth, best_move)
            if mv is not None:
                best_move = mv
                best_val = val

            if best_val > _WIN // 2:
                break

        except _Timeout:
            break

    return _to_coords(best_move)
