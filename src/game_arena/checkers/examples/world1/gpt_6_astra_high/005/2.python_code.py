
import time

_FULL = (1 << 64) - 1
_NOT_A = _FULL ^ 0x0101010101010101
_NOT_H = _FULL ^ 0x8080808080808080
_RANK = tuple(255 << (8 * r) for r in range(8))

_CENTER = sum(
    1 << (8 * r + c)
    for r in range(2, 6)
    for c in range(2, 6)
)
_INNER = sum(
    1 << (8 * r + c)
    for r in range(1, 7)
    for c in range(1, 7)
)

_ADVANCE = (0, 0, 1, 3, 7, 13, 24, 0)
_MAN_UP = tuple(
    _ADVANCE[r] + 2 * min(c, 7 - c) + (6 if r == 0 else 0)
    for r in range(8)
    for c in range(8)
)
_MAN_DOWN = tuple(
    _MAN_UP[(7 - r) * 8 + c]
    for r in range(8)
    for c in range(8)
)
_KING_PST = tuple(
    5 * min(r, 7 - r, c, 7 - c)
    for r in range(8)
    for c in range(8)
)
_DISTANCE = tuple(
    tuple(
        max(abs(a // 8 - b // 8), abs(a % 8 - b % 8))
        for b in range(64)
    )
    for a in range(64)
)

_WIN = 30000
_MATE_BOUND = 29000
_INF = 32000

# Entries: (depth, normalized_score, bound, best_move).
# Bounds: 0 = exact, 1 = lower, 2 = upper.
_TT = {}
_HISTORY = [0] * 8192


class _SearchTimeout(Exception):
    pass


def _bits(squares):
    result = 0
    for r, c in squares:
        result |= 1 << (8 * int(r) + int(c))
    return result


def _action(move):
    source = move[0].bit_length() - 1
    target = move[1].bit_length() - 1
    return ((source // 8, source % 8),
            (target // 8, target % 8))


def _captures(m, k, om, ok, up):
    """Moves are (source_bit, destination_bit, captured_bit)."""
    enemy = om | ok
    empty = _FULL ^ (m | k | enemy)
    forward = (m | k) if up else k
    backward = k if up else (m | k)
    enemy_a = enemy & _NOT_A
    enemy_h = enemy & _NOT_H
    moves = []

    targets = ((((forward & _NOT_A) << 7) & enemy_a) << 7) & empty
    while targets:
        t = targets & -targets
        targets ^= t
        moves.append((t >> 14, t, t >> 7))

    targets = ((((forward & _NOT_H) << 9) & enemy_h) << 9) & empty
    while targets:
        t = targets & -targets
        targets ^= t
        moves.append((t >> 18, t, t >> 9))

    targets = ((((backward & _NOT_A) >> 9) & enemy_a) >> 9) & empty
    while targets:
        t = targets & -targets
        targets ^= t
        moves.append((t << 18, t, t << 9))

    targets = ((((backward & _NOT_H) >> 7) & enemy_h) >> 7) & empty
    while targets:
        t = targets & -targets
        targets ^= t
        moves.append((t << 14, t, t << 7))

    return moves


def _quiet_moves(m, k, om, ok, up):
    empty = _FULL ^ (m | k | om | ok)
    forward = (m | k) if up else k
    backward = k if up else (m | k)
    moves = []

    targets = ((forward & _NOT_A) << 7) & empty
    while targets:
        t = targets & -targets
        targets ^= t
        moves.append((t >> 7, t, 0))

    targets = ((forward & _NOT_H) << 9) & empty
    while targets:
        t = targets & -targets
        targets ^= t
        moves.append((t >> 9, t, 0))

    targets = ((backward & _NOT_A) >> 9) & empty
    while targets:
        t = targets & -targets
        targets ^= t
        moves.append((t << 9, t, 0))

    targets = ((backward & _NOT_H) >> 7) & empty
    while targets:
        t = targets & -targets
        targets ^= t
        moves.append((t << 7, t, 0))

    return moves


def _evaluate(m, k, om, ok, up, ply):
    # Evaluate in fixed upward/downward coordinates, then change perspective.
    if up:
        wm, wk, bm, bk = m, k, om, ok
    else:
        wm, wk, bm, bk = om, ok, m, k

    wa = wm | wk
    ba = bm | bk
    empty = _FULL ^ (wa | ba)

    wu = (((wa & _NOT_A) << 7) | ((wa & _NOT_H) << 9)) & empty
    wd = (((wk & _NOT_A) >> 9) | ((wk & _NOT_H) >> 7)) & empty
    bd = (((ba & _NOT_A) >> 9) | ((ba & _NOT_H) >> 7)) & empty
    bu = (((bk & _NOT_A) << 7) | ((bk & _NOT_H) << 9)) & empty

    # This evaluator is called only when the mover has no capture.
    if (up and not (wu | wd)) or (not up and not (bd | bu)):
        return -_WIN + ply

    wmc, wkc = wm.bit_count(), wk.bit_count()
    bmc, bkc = bm.bit_count(), bk.bit_count()
    total = wmc + wkc + bmc + bkc

    king_value = 178 + 3 * max(0, 14 - total)
    white_material = 100 * wmc + king_value * wkc
    black_material = 100 * bmc + king_value * bkc
    material = white_material - black_material

    score = material
    # Prefer useful simplification when ahead.
    score += (60 * material) // (white_material + black_material + 1)

    advance = (
        (wm & _RANK[2]).bit_count() - (bm & _RANK[5]).bit_count()
        + 3 * ((wm & _RANK[3]).bit_count() - (bm & _RANK[4]).bit_count())
        + 7 * ((wm & _RANK[4]).bit_count() - (bm & _RANK[3]).bit_count())
        + 13 * ((wm & _RANK[5]).bit_count() - (bm & _RANK[2]).bit_count())
        + 24 * ((wm & _RANK[6]).bit_count() - (bm & _RANK[1]).bit_count())
    )
    score += advance * (2 if total <= 8 else 1)

    guard = 6 if total > 14 else (3 if total > 8 else 0)
    score += guard * (
        (wm & _RANK[0]).bit_count() - (bm & _RANK[7]).bit_count()
    )

    score += 4 * ((wm & _CENTER).bit_count() - (bm & _CENTER).bit_count())
    score += 7 * ((wk & _CENTER).bit_count() - (bk & _CENTER).bit_count())
    score += 4 * ((wk & _INNER).bit_count() - (bk & _INNER).bit_count())

    white_support = (
        ((wa & _NOT_A) << 7) | ((wa & _NOT_H) << 9)
    ) & wm
    black_support = (
        ((ba & _NOT_A) >> 9) | ((ba & _NOT_H) >> 7)
    ) & bm
    score += 3 * (white_support.bit_count() - black_support.bit_count())

    score += 2 * ((wu | wd).bit_count() - (bd | bu).bit_count())

    ready = wm & _RANK[6]
    if ready:
        promotions = (
            ((ready & _NOT_A) << 7) | ((ready & _NOT_H) << 9)
        ) & empty
        score += 12 * promotions.bit_count()

    ready = bm & _RANK[1]
    if ready:
        promotions = (
            ((ready & _NOT_A) >> 9) | ((ready & _NOT_H) >> 7)
        ) & empty
        score -= 12 * promotions.bit_count()

    # Help a superior king force engage rather than shuffle indefinitely.
    if total <= 8 and abs(material) > 50:
        if material > 0:
            attackers, defenders, sign = wk, ba, -1
        else:
            attackers, defenders, sign = bk, wa, 1

        if attackers and defenders:
            targets = []
            while defenders:
                bit = defenders & -defenders
                defenders ^= bit
                targets.append(bit.bit_length() - 1)

            distance_sum = 0
            while attackers:
                bit = attackers & -attackers
                attackers ^= bit
                distances = _DISTANCE[bit.bit_length() - 1]
                nearest = 8
                for target in targets:
                    d = distances[target]
                    if d < nearest:
                        nearest = d
                distance_sum += nearest

            score += sign * 3 * distance_sum

    return (score if up else -score) + 2


class _Searcher:
    __slots__ = ("deadline", "nodes", "tt", "history", "killers", "path")

    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = _TT
        self.history = _HISTORY
        self.killers = [[None, None] for _ in range(256)]
        self.path = set()

    def order(self, moves, m, k, ok, up, tt_move, ply):
        if len(moves) <= 1:
            return moves

        history = self.history
        killer1, killer2 = self.killers[ply]
        offset = 0 if up else 4096
        crown = _RANK[7] if up else _RANK[0]
        man_pst = _MAN_UP if up else _MAN_DOWN

        def rank(move):
            if move == tt_move:
                return 1000000000

            f, t, captured = move
            fi = f.bit_length() - 1
            ti = t.bit_length() - 1
            king = bool(f & k)
            pst = _KING_PST if king else man_pst
            value = pst[ti] - pst[fi]

            if captured:
                value += 100000
                if captured & ok:
                    value += 5000
                if king:
                    value -= 100
            else:
                value += history[offset | (fi << 6) | ti]
                if move == killer1:
                    value += 8000
                elif move == killer2:
                    value += 7000

            if not king and t & crown:
                value += 9000
            return value

        moves.sort(key=rank, reverse=True)
        return moves

    def search(self, m, k, om, ok, up, depth, alpha, beta, ply):
        self.nodes += 1
        if (self.nodes & 127) == 0:
            if time.perf_counter() >= self.deadline:
                raise _SearchTimeout

        if not (m | k):
            return -_WIN + ply
        if not (om | ok):
            return _WIN - ply

        key = (m, k, om, ok, up)
        if key in self.path:
            return 0

        tt = self.tt
        entry = tt.get(key)
        tt_move = None

        if entry is not None:
            stored_depth, value, bound, tt_move = entry
            if value > _MATE_BOUND:
                value -= ply
            elif value < -_MATE_BOUND:
                value += ply

            if stored_depth >= depth:
                if bound == 0:
                    return value
                if bound == 1 and value >= beta:
                    return value
                if bound == 2 and value <= alpha:
                    return value

        moves = _captures(m, k, om, ok, up)
        capturing = bool(moves)

        if not capturing:
            if depth <= 0:
                value = _evaluate(m, k, om, ok, up, ply)
                normalized = value
                if value > _MATE_BOUND:
                    normalized += ply
                elif value < -_MATE_BOUND:
                    normalized -= ply
                if entry is None or entry[0] <= 0:
                    tt[key] = (0, normalized, 0, None)
                return value

            moves = _quiet_moves(m, k, om, ok, up)
            if not moves:
                return -_WIN + ply

        self.order(moves, m, k, ok, up, tt_move, ply)

        original_alpha = alpha
        pv_node = beta - alpha > 1
        best_value = -_INF
        best_move = moves[0]
        crown = _RANK[7] if up else _RANK[0]

        next_depth = max(0, depth - 1)
        # Deterministic captures do not consume ordinary search depth.
        if capturing and len(moves) == 1 and depth > 0:
            next_depth = depth

        self.path.add(key)

        for index, move in enumerate(moves):
            f, t, captured = move
            promotion = bool((f & m) and (t & crown))

            if f & m:
                new_m = m ^ f
                new_k = k
                if promotion:
                    new_k |= t
                else:
                    new_m |= t
            else:
                new_m = m
                new_k = (k ^ f) | t

            other_m = om & ~captured
            other_k = ok & ~captured

            reduction = 0
            if (
                not capturing
                and depth >= 4
                and index >= 4
                and ply > 0
                and not promotion
                and move != self.killers[ply][0]
                and move != self.killers[ply][1]
                and (not pv_node or (depth >= 5 and index >= 6))
            ):
                reduction = 1
                if depth >= 7 and index >= 8 and not pv_node:
                    reduction = 2

            if index == 0 or depth < 2:
                value = -self.search(
                    other_m, other_k, new_m, new_k, not up,
                    next_depth, -beta, -alpha, ply + 1
                )
            else:
                value = -self.search(
                    other_m, other_k, new_m, new_k, not up,
                    max(0, next_depth - reduction),
                    -alpha - 1, -alpha, ply + 1
                )

                if reduction and value > alpha:
                    value = -self.search(
                        other_m, other_k, new_m, new_k, not up,
                        next_depth, -alpha - 1, -alpha, ply + 1
                    )

                if alpha < value < beta:
                    value = -self.search(
                        other_m, other_k, new_m, new_k, not up,
                        next_depth, -beta, -alpha, ply + 1
                    )

            if value > best_value:
                best_value = value
                best_move = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                if not capturing:
                    killers = self.killers[ply]
                    if move != killers[0]:
                        killers[1] = killers[0]
                        killers[0] = move

                    fi = f.bit_length() - 1
                    ti = t.bit_length() - 1
                    hi = (0 if up else 4096) | (fi << 6) | ti
                    bonus = min(1000, 8 * depth * depth)
                    h = self.history[hi]
                    self.history[hi] = h + bonus - h * bonus // 8192
                break

        self.path.remove(key)

        if best_value >= beta:
            bound = 1
        elif best_value <= original_alpha:
            bound = 2
        else:
            bound = 0

        normalized = best_value
        if normalized > _MATE_BOUND:
            normalized += ply
        elif normalized < -_MATE_BOUND:
            normalized -= ply

        if entry is None or depth >= entry[0]:
            tt[key] = (depth, normalized, bound, best_move)

        return best_value


def policy(
    my_men, my_kings, opp_men, opp_kings, color
) -> tuple[tuple[int, int], tuple[int, int]]:
    started = time.perf_counter()
    deadline = started + 0.90

    m = _bits(my_men)
    k = _bits(my_kings)
    om = _bits(opp_men)
    ok = _bits(opp_kings)
    up = color == "w"

    legal = _captures(m, k, om, ok, up)
    if not legal:
        legal = _quiet_moves(m, k, om, ok, up)

    if not legal:
        # Terminal positions have no legal move or pass in this API.
        return ((0, 0), (0, 0))

    if len(legal) == 1:
        return _action(legal[0])

    if len(_TT) > 140000:
        _TT.clear()

    _HISTORY[:] = [value // 2 for value in _HISTORY]

    engine = _Searcher(deadline)
    root_key = (m, k, om, ok, up)
    root_entry = _TT.get(root_key)
    cached_move = root_entry[3] if root_entry is not None else None

    engine.order(legal, m, k, ok, up, cached_move, 0)
    best_move = legal[0]
    last_score = 0

    for depth in range(1, 65):
        if time.perf_counter() >= deadline:
            break

        if depth >= 4 and abs(last_score) < _MATE_BOUND:
            low, high = last_score - 45, last_score + 45
        else:
            low, high = -_INF, _INF

        try:
            score = engine.search(
                m, k, om, ok, up, depth, low, high, 0
            )

            if score <= low or score >= high:
                if time.perf_counter() >= deadline:
                    break
                score = engine.search(
                    m, k, om, ok, up, depth, -_INF, _INF, 0
                )

            completed = _TT.get(root_key)
            if completed is not None and completed[3] in legal:
                best_move = completed[3]
            last_score = score

            if abs(score) > _MATE_BOUND:
                break

        except _SearchTimeout:
            break

    # best_move always comes from the initially generated legal move list.
    return _action(best_move)
