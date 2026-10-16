
import time

_FULL = (1 << 64) - 1
_MATE = 30000
_INF = 32000
_TT = {}


# Direction entries: (square displacement, step-source mask, jump-source mask).
_RAW_DIRECTIONS = []
for _dr, _dc in ((1, -1), (1, 1), (-1, 1), (-1, -1)):
    _step_mask = 0
    _jump_mask = 0
    for _r in range(8):
        for _c in range(8):
            _bit = 1 << (8 * _r + _c)
            if 0 <= _r + _dr < 8 and 0 <= _c + _dc < 8:
                _step_mask |= _bit
            if 0 <= _r + 2 * _dr < 8 and 0 <= _c + 2 * _dc < 8:
                _jump_mask |= _bit
    _RAW_DIRECTIONS.append((8 * _dr + _dc, _step_mask, _jump_mask))

# Side 0 moves toward higher rows; side 1 toward lower rows.
_DIRECTIONS = (
    tuple(_RAW_DIRECTIONS),
    tuple(_RAW_DIRECTIONS[2:] + _RAW_DIRECTIONS[:2]),
)
_CROWN = (0xFF << 56, 0xFF)
_HOME = (0xFF, 0xFF << 56)
_ADVANCED = (_FULL ^ ((1 << 32) - 1), (1 << 32) - 1)

_CENTER = (0, 1, 3, 4, 4, 3, 1, 0)
_ADVANCE = (0, 1, 3, 6, 10, 16, 25, 70)

_MPST = [[], []]
_KPST = []
for _s in range(64):
    _r, _c = divmod(_s, 8)
    _central = _CENTER[_c] + (2 if 2 <= _r <= 5 else 0)
    _edge = 1 if _c in (0, 7) else 0
    _MPST[0].append(100 + _ADVANCE[_r] + _central + _edge)
    _MPST[1].append(100 + _ADVANCE[7 - _r] + _central + _edge)
    _KPST.append(175 + 2 * _CENTER[_r] + 2 * _CENTER[_c])


def _make_byte_tables(pst):
    tables = []
    for row in range(8):
        table = [0] * 256
        for mask in range(1, 256):
            bit = mask & -mask
            table[mask] = (
                table[mask ^ bit] + pst[8 * row + bit.bit_length() - 1]
            )
        tables.append(table)
    return tuple(tables)


_MT = (_make_byte_tables(_MPST[0]), _make_byte_tables(_MPST[1]))
_KT = _make_byte_tables(_KPST)

# Squares reachable by an unobstructed man before promotion.
_CONE = [[0] * 64 for _ in range(2)]
for _side in range(2):
    for _s in range(64):
        _r, _c = divmod(_s, 8)
        _rows = range(_r + 1, 8) if _side == 0 else range(_r - 1, -1, -1)
        _mask = 0
        for _rr in _rows:
            _distance = abs(_rr - _r)
            for _cc in range(8):
                if (
                    abs(_cc - _c) <= _distance
                    and ((_rr + _cc - _r - _c) & 1) == 0
                ):
                    _mask |= 1 << (8 * _rr + _cc)
        _CONE[_side][_s] = _mask


def _sum_pst(board, tables):
    return (
        tables[0][board & 255]
        + tables[1][(board >> 8) & 255]
        + tables[2][(board >> 16) & 255]
        + tables[3][(board >> 24) & 255]
        + tables[4][(board >> 32) & 255]
        + tables[5][(board >> 40) & 255]
        + tables[6][(board >> 48) & 255]
        + tables[7][(board >> 56) & 255]
    )


def _captures(m, k, om, ok, side):
    enemy = om | ok
    empty = _FULL ^ (m | k | enemy)
    pieces = m | k
    result = []

    for i, (delta, step_mask, jump_mask) in enumerate(_DIRECTIONS[side]):
        movers = pieces if i < 2 else k
        if not movers:
            continue

        if delta > 0:
            sources = movers & jump_mask & (enemy >> delta) & (empty >> (2 * delta))
            while sources:
                src = sources & -sources
                sources ^= src
                result.append((src, src << (2 * delta), src << delta))
        else:
            shift = -delta
            sources = movers & jump_mask & (enemy << shift) & (empty << (2 * shift))
            while sources:
                src = sources & -sources
                sources ^= src
                result.append((src, src >> (2 * shift), src >> shift))

    return result


def _quiets(m, k, om, ok, side):
    empty = _FULL ^ (m | k | om | ok)
    pieces = m | k
    result = []

    for i, (delta, step_mask, jump_mask) in enumerate(_DIRECTIONS[side]):
        movers = pieces if i < 2 else k
        if not movers:
            continue

        if delta > 0:
            sources = movers & step_mask & (empty >> delta)
            while sources:
                src = sources & -sources
                sources ^= src
                result.append((src, src << delta, 0))
        else:
            shift = -delta
            sources = movers & step_mask & (empty << shift)
            while sources:
                src = sources & -sources
                sources ^= src
                result.append((src, src >> shift, 0))

    return result


def _has_quiet(m, k, om, ok, side):
    empty = _FULL ^ (m | k | om | ok)
    pieces = m | k
    for i, (delta, mask, _) in enumerate(_DIRECTIONS[side]):
        movers = pieces if i < 2 else k
        if delta > 0:
            if movers & mask & (empty >> delta):
                return True
        elif movers & mask & (empty << -delta):
            return True
    return False


def _mobility(m, k, occupied, side):
    empty = _FULL ^ occupied
    pieces = m | k
    count = 0
    for i, (delta, mask, _) in enumerate(_DIRECTIONS[side]):
        movers = pieces if i < 2 else k
        if delta > 0:
            count += (movers & mask & (empty >> delta)).bit_count()
        else:
            count += (movers & mask & (empty << -delta)).bit_count()
    return count


def _play(m, k, om, ok, side, move):
    src, dst, captured = move

    if src & m:
        nm = m ^ src
        nk = k
        if dst & _CROWN[side]:
            nk |= dst
        else:
            nm |= dst
    else:
        nm = m
        nk = k ^ src ^ dst

    # Return the position from the next player's perspective.
    return om & ~captured, ok & ~captured, nm, nk, side ^ 1


def _pursuit(kings, enemies):
    targets = []
    while enemies:
        bit = enemies & -enemies
        enemies ^= bit
        s = bit.bit_length() - 1
        targets.append((s >> 3, s & 7))

    count = kings.bit_count()
    distance_sum = 0
    while kings:
        bit = kings & -kings
        kings ^= bit
        s = bit.bit_length() - 1
        r, c = s >> 3, s & 7
        best = 8
        for er, ec in targets:
            distance = max(abs(r - er), abs(c - ec))
            if distance < best:
                best = distance
        distance_sum += best

    return 6 * (7 * count - distance_sum) // count if count else 0


def _evaluate(m, k, om, ok, side):
    other = side ^ 1
    mc, kc = m.bit_count(), k.bit_count()
    oc, okc = om.bit_count(), ok.bit_count()
    total = mc + kc + oc + okc
    material = 100 * (mc - oc) + 175 * (kc - okc)

    score = (
        _sum_pst(m, _MT[side])
        + _sum_pst(k, _KT)
        - _sum_pst(om, _MT[other])
        - _sum_pst(ok, _KT)
    )

    # Kings gain value as the board opens up.
    score += (kc - okc) * max(0, 12 - total)

    # Favor simplifying when materially ahead.
    trade = abs(material) * max(0, 24 - total) // 96
    score += trade if material >= 0 else -trade

    guard = min(24, total) * 6 // 24
    score += guard * (
        (m & _HOME[side]).bit_count()
        - (om & _HOME[other]).bit_count()
    )

    mine, theirs = m | k, om | ok
    occupied = mine | theirs
    score += 2 * (
        _mobility(m, k, occupied, side)
        - _mobility(om, ok, occupied, other)
    )

    # Diagonal connections discourage loose, easily exchanged formations.
    for delta, mask, _ in _RAW_DIRECTIONS[:2]:
        score += 2 * (
            (((mine & mask) << delta) & mine).bit_count()
            - (((theirs & mask) << delta) & theirs).bit_count()
        )

    if total <= 12:
        if not ok:
            runners = m & _ADVANCED[side]
            while runners:
                bit = runners & -runners
                runners ^= bit
                s = bit.bit_length() - 1
                if not (_CONE[side][s] & theirs):
                    advance = (s >> 3) if side == 0 else 7 - (s >> 3)
                    score += 5 * (advance - 3)

        if not k:
            runners = om & _ADVANCED[other]
            while runners:
                bit = runners & -runners
                runners ^= bit
                s = bit.bit_length() - 1
                if not (_CONE[other][s] & mine):
                    advance = (s >> 3) if other == 0 else 7 - (s >> 3)
                    score -= 5 * (advance - 3)

    if total <= 10:
        if material > 40 and k and theirs:
            score += _pursuit(k, theirs)
        elif material < -40 and ok and mine:
            score -= _pursuit(ok, mine)

    return score


class _SearchTimeout(Exception):
    pass


class _Engine:
    def __init__(self, deadline, fallback):
        self.deadline = deadline
        self.tt = _TT
        self.nodes = 0
        self.path = set()
        self.killers = [[None, None] for _ in range(96)]
        self.history = {}
        self.root_best = fallback

    def _ordered(self, m, k, om, ok, side, moves, ttmove, ply):
        if len(moves) <= 1:
            return moves

        killers = self.killers[ply]
        man_pst = _MPST[side]
        ranked = []

        for move in moves:
            if move == ttmove:
                ranked.append((10**12, move))
                continue

            src, dst, captured = move
            a = src.bit_length() - 1
            b = dst.bit_length() - 1
            is_man = bool(src & m)
            promotes = is_man and bool(dst & _CROWN[side])

            if is_man:
                positional = (_KPST[b] if promotes else man_pst[b]) - man_pst[a]
            else:
                positional = _KPST[b] - _KPST[a]

            value = 8 * positional
            if captured:
                value += 100000
                value += 2500 if captured & ok else 1200
                if not is_man:
                    value -= 250
            else:
                value += self.history.get((side, move), 0)
                if move == killers[0]:
                    value += 50000
                elif move == killers[1]:
                    value += 40000

            if promotes:
                value += 60000

            ranked.append((value, move))

        ranked.sort(reverse=True)
        return [move for _, move in ranked]

    def search(self, m, k, om, ok, side, depth, alpha, beta, ply):
        self.nodes += 1
        if (self.nodes & 127) == 0 and time.perf_counter() >= self.deadline:
            raise _SearchTimeout

        if not (m | k):
            return -_MATE + ply
        if not (om | ok):
            return _MATE - ply
        if ply >= 90:
            return _evaluate(m, k, om, ok, side)

        key = (m, k, om, ok, side)
        if key in self.path:
            return 0

        original_alpha = alpha
        entry = self.tt.get(key)
        ttmove = entry[3] if entry is not None else None

        if entry is not None and entry[0] >= depth:
            value = entry[1]
            if value > _MATE - 100:
                value -= ply
            elif value < -_MATE + 100:
                value += ply

            flag = entry[2]
            if flag == 0:
                if ply == 0 and ttmove is not None:
                    self.root_best = ttmove
                return value
            if flag == 1:
                alpha = max(alpha, value)
            else:
                beta = min(beta, value)

            if alpha >= beta:
                if ply == 0 and ttmove is not None:
                    self.root_best = ttmove
                return value

        moves = _captures(m, k, om, ok, side)
        capturing = bool(moves)

        # Mandatory captures prohibit standing pat in quiescence.
        if depth == 0 and not capturing:
            if _has_quiet(m, k, om, ok, side):
                value = _evaluate(m, k, om, ok, side)
                stored = value
            else:
                value = -_MATE + ply
                stored = -_MATE

            if entry is None or entry[0] == 0:
                self.tt[key] = (0, stored, 0, None)
            return value

        if not capturing:
            moves = _quiets(m, k, om, ok, side)
            if not moves:
                self.tt[key] = (depth, -_MATE, 0, None)
                return -_MATE + ply

        moves = self._ordered(m, k, om, ok, side, moves, ttmove, ply)
        self.path.add(key)

        best = -_INF
        best_move = moves[0]
        next_depth = max(0, depth - 1)
        sufficiently_many_pieces = (m | k | om | ok).bit_count() > 6

        for index, move in enumerate(moves):
            child = _play(m, k, om, ok, side, move)

            if index == 0:
                value = -self.search(
                    *child, next_depth, -beta, -alpha, ply + 1
                )
            else:
                reduction = 0
                promotes = bool((move[0] & m) and (move[1] & _CROWN[side]))

                if (
                    depth >= 3
                    and ply > 0
                    and index >= 4
                    and not capturing
                    and not promotes
                    and sufficiently_many_pieces
                    and move not in self.killers[ply]
                ):
                    reduction = 2 if depth >= 7 and index >= 8 else 1

                value = -self.search(
                    *child,
                    max(0, next_depth - reduction),
                    -alpha - 1,
                    -alpha,
                    ply + 1
                )

                if reduction and value > alpha:
                    value = -self.search(
                        *child, next_depth, -alpha - 1, -alpha, ply + 1
                    )

                if alpha < value < beta:
                    value = -self.search(
                        *child, next_depth, -beta, -alpha, ply + 1
                    )

            if value > best:
                best = value
                best_move = move
                if ply == 0:
                    self.root_best = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                if not capturing and depth > 0:
                    killers = self.killers[ply]
                    if move != killers[0]:
                        killers[1] = killers[0]
                        killers[0] = move
                    hkey = (side, move)
                    self.history[hkey] = min(
                        30000,
                        self.history.get(hkey, 0) + 32 * depth * depth
                    )
                break

        self.path.remove(key)

        if best <= original_alpha:
            flag = 2  # Upper bound.
        elif best >= beta:
            flag = 1  # Lower bound.
        else:
            flag = 0  # Exact.

        stored = best
        if best > _MATE - 100:
            stored += ply
        elif best < -_MATE + 100:
            stored -= ply

        if entry is None or depth >= entry[0]:
            self.tt[key] = (depth, stored, flag, best_move)

        return best


def _board(squares):
    result = 0
    for row, col in squares:
        result |= 1 << (8 * int(row) + int(col))
    return result


def _coordinates(move):
    src, dst, _ = move
    a = src.bit_length() - 1
    b = dst.bit_length() - 1
    return ((a >> 3, a & 7), (b >> 3, b & 7))


def policy(my_men, my_kings, opp_men, opp_kings, color):
    start = time.perf_counter()
    deadline = start + 0.88

    m = _board(my_men)
    k = _board(my_kings)
    om = _board(opp_men)
    ok = _board(opp_kings)
    side = 1 if color == "b" else 0

    legal = _captures(m, k, om, ok, side)
    if not legal:
        legal = _quiets(m, k, om, ok, side)

    # No legal action exists in a terminal position. Normally the arena
    # stops the game without calling policy in this case.
    if not legal:
        return ((0, 0), (0, 0))

    if len(legal) == 1:
        return _coordinates(legal[0])

    # Bound persistent memory without disrupting an active search.
    if len(_TT) > 150000:
        _TT.clear()

    engine = _Engine(deadline, legal[0])
    ordered = engine._ordered(m, k, om, ok, side, legal, None, 0)
    best_move = ordered[0]
    engine.root_best = best_move
    previous_score = 0

    try:
        for depth in range(1, 31):
            if time.perf_counter() >= deadline:
                break

            if depth >= 4:
                alpha = max(-_INF, previous_score - 45)
                beta = min(_INF, previous_score + 45)
            else:
                alpha, beta = -_INF, _INF

            score = engine.search(
                m, k, om, ok, side, depth, alpha, beta, 0
            )

            # Re-search an aspiration-window failure before accepting it.
            if score <= alpha or score >= beta:
                score = engine.search(
                    m, k, om, ok, side, depth, -_INF, _INF, 0
                )

            if engine.root_best in legal:
                best_move = engine.root_best
            previous_score = score

            if abs(score) > _MATE - 100:
                break

    except _SearchTimeout:
        pass

    return _coordinates(best_move)
