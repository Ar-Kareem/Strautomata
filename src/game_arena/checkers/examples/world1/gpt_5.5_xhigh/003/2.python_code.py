
from __future__ import annotations

from time import perf_counter


INF = 10**9
WIN_SCORE = 10_000_000

EXACT = 0
LOWER = 1
UPPER = 2

try:
    (1).bit_count
    def _popcount(x: int) -> int:
        return x.bit_count()
except AttributeError:
    def _popcount(x: int) -> int:
        return bin(x).count("1")


_BB = tuple(1 << i for i in range(64))
_ROW = tuple(i // 8 for i in range(64))
_COL = tuple(i % 8 for i in range(64))

_ROW_MASK = tuple(
    sum(1 << (r * 8 + c) for c in range(8))
    for r in range(8)
)

_MAN_STEPS = {1: [[] for _ in range(64)], -1: [[] for _ in range(64)]}
_MAN_JUMPS = {1: [[] for _ in range(64)], -1: [[] for _ in range(64)]}
_KING_STEPS = [[] for _ in range(64)]
_KING_JUMPS = [[] for _ in range(64)]

for r in range(8):
    for c in range(8):
        i = r * 8 + c
        for dr in (-1, 1):
            for dc in (-1, 1):
                r1, c1 = r + dr, c + dc
                if 0 <= r1 < 8 and 0 <= c1 < 8:
                    j = r1 * 8 + c1
                    _KING_STEPS[i].append(j)
                    _MAN_STEPS[dr][i].append(j)

                r2, c2 = r + 2 * dr, c + 2 * dc
                if 0 <= r1 < 8 and 0 <= c1 < 8 and 0 <= r2 < 8 and 0 <= c2 < 8:
                    mid = r1 * 8 + c1
                    land = r2 * 8 + c2
                    _KING_JUMPS[i].append((mid, land))
                    _MAN_JUMPS[dr][i].append((mid, land))

_CENTER = tuple(
    max(0, 14 - (abs((i // 8) * 2 - 7) + abs((i % 8) * 2 - 7)))
    for i in range(64)
)

_DIR0 = 1
_DIR1 = -1
_PROMO0 = 7
_PROMO1 = 0

_DEADLINE = 0.0
_NODES = 0
_TT = {}


class _Timeout(Exception):
    pass


def _to_mask(squares) -> int:
    mask = 0
    for r, c in squares:
        r = int(r)
        c = int(c)
        if 0 <= r < 8 and 0 <= c < 8:
            mask |= 1 << (r * 8 + c)
    return mask


def _coord(idx: int) -> tuple[int, int]:
    return (_ROW[idx], _COL[idx])


def _tick() -> None:
    global _NODES
    _NODES += 1
    if (_NODES & 2047) == 0 and perf_counter() > _DEADLINE:
        raise _Timeout()


def _gen_moves(m0: int, k0: int, m1: int, k1: int, side: int):
    if side == 0:
        own_m, own_k = m0, k0
        enemy_m, enemy_k = m1, k1
        direction = _DIR0
    else:
        own_m, own_k = m1, k1
        enemy_m, enemy_k = m0, k0
        direction = _DIR1

    enemy_all = enemy_m | enemy_k
    occ = m0 | k0 | m1 | k1
    bb = _BB

    captures = []

    jumps = _MAN_JUMPS[direction]
    mask = own_m
    while mask:
        lsb = mask & -mask
        fr = lsb.bit_length() - 1
        mask ^= lsb
        for mid, to in jumps[fr]:
            if (enemy_all & bb[mid]) and not (occ & bb[to]):
                captures.append((fr, to, mid))

    mask = own_k
    while mask:
        lsb = mask & -mask
        fr = lsb.bit_length() - 1
        mask ^= lsb
        for mid, to in _KING_JUMPS[fr]:
            if (enemy_all & bb[mid]) and not (occ & bb[to]):
                captures.append((fr, to, mid))

    if captures:
        return captures

    moves = []

    steps = _MAN_STEPS[direction]
    mask = own_m
    while mask:
        lsb = mask & -mask
        fr = lsb.bit_length() - 1
        mask ^= lsb
        for to in steps[fr]:
            if not (occ & bb[to]):
                moves.append((fr, to, -1))

    mask = own_k
    while mask:
        lsb = mask & -mask
        fr = lsb.bit_length() - 1
        mask ^= lsb
        for to in _KING_STEPS[fr]:
            if not (occ & bb[to]):
                moves.append((fr, to, -1))

    return moves


def _apply_move(m0: int, k0: int, m1: int, k1: int, side: int, mv):
    fr, to, cap = mv
    fb = _BB[fr]
    tb = _BB[to]

    if side == 0:
        if k0 & fb:
            k0 = (k0 & ~fb) | tb
        else:
            m0 &= ~fb
            if _ROW[to] == _PROMO0:
                k0 |= tb
            else:
                m0 |= tb

        if cap >= 0:
            cb = _BB[cap]
            m1 &= ~cb
            k1 &= ~cb
    else:
        if k1 & fb:
            k1 = (k1 & ~fb) | tb
        else:
            m1 &= ~fb
            if _ROW[to] == _PROMO1:
                k1 |= tb
            else:
                m1 |= tb

        if cap >= 0:
            cb = _BB[cap]
            m0 &= ~cb
            k0 &= ~cb

    return m0, k0, m1, k1


def _capture_potential(m0: int, k0: int, m1: int, k1: int, side: int):
    if side == 0:
        own_m, own_k = m0, k0
        enemy_m, enemy_k = m1, k1
        direction = _DIR0
        promo = _PROMO0
    else:
        own_m, own_k = m1, k1
        enemy_m, enemy_k = m0, k0
        direction = _DIR1
        promo = _PROMO1

    enemy_all = enemy_m | enemy_k
    occ = m0 | k0 | m1 | k1
    bb = _BB

    count = 0
    value = 0

    jumps = _MAN_JUMPS[direction]
    mask = own_m
    while mask:
        lsb = mask & -mask
        fr = lsb.bit_length() - 1
        mask ^= lsb
        for mid, to in jumps[fr]:
            mb = bb[mid]
            if (enemy_all & mb) and not (occ & bb[to]):
                count += 1
                value += 24
                if enemy_k & mb:
                    value += 32
                if _ROW[to] == promo:
                    value += 18

    mask = own_k
    while mask:
        lsb = mask & -mask
        fr = lsb.bit_length() - 1
        mask ^= lsb
        for mid, to in _KING_JUMPS[fr]:
            mb = bb[mid]
            if (enemy_all & mb) and not (occ & bb[to]):
                count += 1
                value += 26
                if enemy_k & mb:
                    value += 34

    return count, value


def _quiet_count(m0: int, k0: int, m1: int, k1: int, side: int) -> int:
    if side == 0:
        own_m, own_k = m0, k0
        direction = _DIR0
    else:
        own_m, own_k = m1, k1
        direction = _DIR1

    occ = m0 | k0 | m1 | k1
    bb = _BB
    count = 0

    steps = _MAN_STEPS[direction]
    mask = own_m
    while mask:
        lsb = mask & -mask
        fr = lsb.bit_length() - 1
        mask ^= lsb
        for to in steps[fr]:
            if not (occ & bb[to]):
                count += 1

    mask = own_k
    while mask:
        lsb = mask & -mask
        fr = lsb.bit_length() - 1
        mask ^= lsb
        for to in _KING_STEPS[fr]:
            if not (occ & bb[to]):
                count += 1

    return count


def _side_static(men: int, kings: int, own_all: int, direction: int) -> int:
    score = 0
    home = 0 if direction > 0 else 7

    mask = men
    while mask:
        lsb = mask & -mask
        idx = lsb.bit_length() - 1
        mask ^= lsb

        r = _ROW[idx]
        c = _COL[idx]
        progress = r if direction > 0 else 7 - r

        s = 100
        s += progress * 5
        if progress > 4:
            s += (progress - 4) * 7
        if progress == 6:
            s += 12

        s += _CENTER[idx] * 2

        if c == 0 or c == 7:
            s += 4
        if r == home:
            s += 5

        support = 0
        br = r - direction
        if 0 <= br < 8:
            if c > 0 and (own_all & _BB[br * 8 + c - 1]):
                support += 1
            if c < 7 and (own_all & _BB[br * 8 + c + 1]):
                support += 1

        if support:
            s += 5 * support
        elif progress >= 4 and c not in (0, 7):
            s -= 5

        score += s

    mask = kings
    while mask:
        lsb = mask & -mask
        idx = lsb.bit_length() - 1
        mask ^= lsb

        c = _COL[idx]
        s = 180 + _CENTER[idx] * 4
        if c == 0 or c == 7:
            s -= 4
        score += s

    return score


def _evaluate(m0: int, k0: int, m1: int, k1: int) -> int:
    my_all = m0 | k0
    opp_all = m1 | k1

    score = _side_static(m0, k0, my_all, _DIR0)
    score -= _side_static(m1, k1, opp_all, _DIR1)

    my_caps, my_cap_score = _capture_potential(m0, k0, m1, k1, 0)
    opp_caps, opp_cap_score = _capture_potential(m0, k0, m1, k1, 1)
    score += my_cap_score - opp_cap_score

    my_mob = my_caps if my_caps else _quiet_count(m0, k0, m1, k1, 0)
    opp_mob = opp_caps if opp_caps else _quiet_count(m0, k0, m1, k1, 1)
    score += 3 * (my_mob - opp_mob)

    my_material = 100 * _popcount(m0) + 180 * _popcount(k0)
    opp_material = 100 * _popcount(m1) + 180 * _popcount(k1)
    raw = my_material - opp_material
    total = _popcount(m0) + _popcount(k0) + _popcount(m1) + _popcount(k1)
    trade_bonus = max(0, 24 - total)

    if raw > 0:
        score += (raw // 100) * trade_bonus
    elif raw < 0:
        score -= ((-raw) // 100) * trade_bonus

    return score


def _move_order_score(mv, m0: int, k0: int, m1: int, k1: int, side: int) -> int:
    fr, to, cap = mv

    if side == 0:
        own_m, own_k = m0, k0
        enemy_m, enemy_k = m1, k1
        direction = _DIR0
        promo = _PROMO0
    else:
        own_m, own_k = m1, k1
        enemy_m, enemy_k = m0, k0
        direction = _DIR1
        promo = _PROMO1

    fb = _BB[fr]
    score = 0

    if cap >= 0:
        cb = _BB[cap]
        score += 10000
        score += 700 if (enemy_k & cb) else 450

    if own_m & fb:
        if _ROW[to] == promo:
            score += 900
        progress = _ROW[to] if direction > 0 else 7 - _ROW[to]
        score += progress * 12
    else:
        score += 150 + _CENTER[to] * 8

    score += _CENTER[to] * 5

    if _COL[to] == 0 or _COL[to] == 7:
        score += 20 if cap >= 0 else 3

    return score


def _order_moves(moves, m0: int, k0: int, m1: int, k1: int, side: int, preferred=None):
    if len(moves) <= 1:
        return moves
    return sorted(
        moves,
        key=lambda mv: (
            1 if preferred is not None and mv == preferred else 0,
            _move_order_score(mv, m0, k0, m1, k1, side),
        ),
        reverse=True,
    )


def _store_tt(key, depth: int, qdepth: int, value: int, flag: int, best_move) -> None:
    old = _TT.get(key)
    if old is None or depth > old[0] or (depth == old[0] and qdepth >= old[1]):
        _TT[key] = (depth, qdepth, value, flag, best_move)


def _search(
    m0: int,
    k0: int,
    m1: int,
    k1: int,
    side: int,
    depth: int,
    qdepth: int,
    alpha: int,
    beta: int,
    ply: int,
) -> int:
    _tick()

    if not (m0 | k0):
        return -WIN_SCORE + ply
    if not (m1 | k1):
        return WIN_SCORE - ply

    key = (m0, k0, m1, k1, side)
    alpha_orig = alpha
    beta_orig = beta
    tt_move = None

    entry = _TT.get(key)
    if entry is not None:
        edepth, eqdepth, val, flag, move = entry
        tt_move = move
        if edepth >= depth and eqdepth >= qdepth:
            if flag == EXACT:
                return val
            if flag == LOWER:
                alpha = max(alpha, val)
            elif flag == UPPER:
                beta = min(beta, val)
            if alpha >= beta:
                return val

    moves = _gen_moves(m0, k0, m1, k1, side)

    if not moves:
        return (-WIN_SCORE + ply) if side == 0 else (WIN_SCORE - ply)

    is_capture = moves[0][2] >= 0

    if depth <= 0 and not (is_capture and qdepth > 0):
        val = _evaluate(m0, k0, m1, k1)
        _store_tt(key, depth, qdepth, val, EXACT, None)
        return val

    moves = _order_moves(moves, m0, k0, m1, k1, side, tt_move)

    next_depth = depth - 1 if depth > 0 else 0
    next_qdepth = qdepth if depth > 0 else qdepth - 1

    best_move = moves[0]

    if side == 0:
        value = -INF
        for mv in moves:
            nm0, nk0, nm1, nk1 = _apply_move(m0, k0, m1, k1, side, mv)
            child = _search(nm0, nk0, nm1, nk1, 1, next_depth, next_qdepth, alpha, beta, ply + 1)

            if child > value:
                value = child
                best_move = mv
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
    else:
        value = INF
        for mv in moves:
            nm0, nk0, nm1, nk1 = _apply_move(m0, k0, m1, k1, side, mv)
            child = _search(nm0, nk0, nm1, nk1, 0, next_depth, next_qdepth, alpha, beta, ply + 1)

            if child < value:
                value = child
                best_move = mv
            if value < beta:
                beta = value
            if alpha >= beta:
                break

    if value <= alpha_orig:
        flag = UPPER
    elif value >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    _store_tt(key, depth, qdepth, value, flag, best_move)
    return value


def _root_search(m0: int, k0: int, m1: int, k1: int, depth: int, preferred):
    moves = _gen_moves(m0, k0, m1, k1, 0)
    if not moves:
        return -WIN_SCORE, None

    moves = _order_moves(moves, m0, k0, m1, k1, 0, preferred)

    best_value = -INF
    best_move = moves[0]
    alpha = -INF
    beta = INF

    qdepth = 5 if (_popcount(m0) + _popcount(k0) + _popcount(m1) + _popcount(k1)) <= 12 else 4
    child_depth = max(0, depth - 1)

    for mv in moves:
        nm0, nk0, nm1, nk1 = _apply_move(m0, k0, m1, k1, 0, mv)
        value = _search(nm0, nk0, nm1, nk1, 1, child_depth, qdepth, alpha, beta, 1)

        if value > best_value:
            best_value = value
            best_move = mv

        if best_value > alpha:
            alpha = best_value

        if perf_counter() > _DEADLINE:
            raise _Timeout()

        if best_value >= WIN_SCORE - 1000:
            break

    return best_value, best_move


def _policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    global _DIR0, _DIR1, _PROMO0, _PROMO1, _DEADLINE, _NODES, _TT

    color_s = str(color).lower()
    _DIR0 = -1 if color_s.startswith("b") else 1
    _DIR1 = -_DIR0
    _PROMO0 = 0 if _DIR0 < 0 else 7
    _PROMO1 = 0 if _DIR1 < 0 else 7

    m0 = _to_mask(my_men)
    k0 = _to_mask(my_kings)
    m1 = _to_mask(opp_men)
    k1 = _to_mask(opp_kings)

    m0 &= ~k0
    m1 &= ~k1

    promote0 = m0 & _ROW_MASK[_PROMO0]
    promote1 = m1 & _ROW_MASK[_PROMO1]
    if promote0:
        m0 &= ~promote0
        k0 |= promote0
    if promote1:
        m1 &= ~promote1
        k1 |= promote1

    root_moves = _gen_moves(m0, k0, m1, k1, 0)
    if not root_moves:
        return _fallback(my_men, my_kings, opp_men, opp_kings, color)

    root_moves = _order_moves(root_moves, m0, k0, m1, k1, 0, None)
    best = root_moves[0]

    if len(root_moves) == 1:
        return (_coord(best[0]), _coord(best[1]))

    total_pieces = _popcount(m0) + _popcount(k0) + _popcount(m1) + _popcount(k1)

    if total_pieces <= 6:
        max_depth = 14
    elif total_pieces <= 10:
        max_depth = 12
    elif total_pieces <= 16:
        max_depth = 10
    elif total_pieces <= 22:
        max_depth = 8
    else:
        max_depth = 7

    if root_moves[0][2] >= 0:
        max_depth += 2

    _TT = {}
    _NODES = 0
    _DEADLINE = perf_counter() + 0.85

    preferred = best
    best_score = -INF

    for depth in range(1, max_depth + 1):
        if perf_counter() > _DEADLINE:
            break
        try:
            score, mv = _root_search(m0, k0, m1, k1, depth, preferred)
        except _Timeout:
            break

        if mv is not None:
            best = mv
            preferred = mv
            best_score = score

        if best_score >= WIN_SCORE - 1000:
            break

    return (_coord(best[0]), _coord(best[1]))


def _fallback(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    try:
        direction = -1 if str(color).lower().startswith("b") else 1

        men = [(int(r), int(c)) for r, c in my_men]
        kings = [(int(r), int(c)) for r, c in my_kings]
        opp = set((int(r), int(c)) for r, c in opp_men) | set((int(r), int(c)) for r, c in opp_kings)
        occ = set(men) | set(kings) | opp

        def inside(p):
            return 0 <= p[0] < 8 and 0 <= p[1] < 8

        # Mandatory captures first.
        for r, c in men:
            for dc in (-1, 1):
                mid = (r + direction, c + dc)
                to = (r + 2 * direction, c + 2 * dc)
                if inside(to) and mid in opp and to not in occ:
                    return ((r, c), to)

        for r, c in kings:
            for dr in (-1, 1):
                for dc in (-1, 1):
                    mid = (r + dr, c + dc)
                    to = (r + 2 * dr, c + 2 * dc)
                    if inside(to) and mid in opp and to not in occ:
                        return ((r, c), to)

        # Quiet moves.
        for r, c in men:
            for dc in (-1, 1):
                to = (r + direction, c + dc)
                if inside(to) and to not in occ:
                    return ((r, c), to)

        for r, c in kings:
            for dr in (-1, 1):
                for dc in (-1, 1):
                    to = (r + dr, c + dc)
                    if inside(to) and to not in occ:
                        return ((r, c), to)

        if men:
            return (men[0], men[0])
        if kings:
            return (kings[0], kings[0])
    except Exception:
        pass

    return ((0, 0), (0, 0))


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    try:
        return _policy(my_men, my_kings, opp_men, opp_kings, color)
    except Exception:
        return _fallback(my_men, my_kings, opp_men, opp_kings, color)
