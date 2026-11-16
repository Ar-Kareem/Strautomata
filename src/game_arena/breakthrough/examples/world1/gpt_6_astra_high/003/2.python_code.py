
import time

_FULL = (1 << 64) - 1
_FA = 0x0101010101010101
_FH = 0x8080808080808080
_NA = _FULL ^ _FA
_NH = _FULL ^ _FH

_RANK = tuple(255 << (8 * r) for r in range(8))
_GOAL = (_RANK[7], _RANK[0])
_PEN = (_RANK[6], _RANK[1])
_PRE = (_RANK[5], _RANK[2])
_ADVANCED = (_FULL ^ ((1 << 32) - 1), (1 << 32) - 1)

_ADV = (0, 3, 10, 23, 48, 95, 220, 1200)
_PASS_BONUS = (0, 0, 8, 30, 75, 160, 250, 0)
_CENTER = (0, 1, 2, 3, 3, 2, 1, 0)
_CENTER_SCALE = (0, 2, 3, 3, 2, 1, 0, 0)

_MATE = 30000
_INF = 32000

# Byte-indexed piece-square tables.
_PST = []
for _r in range(8):
    _table = [0] * 256
    _base = 100 + _ADV[_r] + (6 if _r == 0 else 2 if _r == 1 else 0)
    for _mask in range(1, 256):
        _bit = _mask & -_mask
        _c = _bit.bit_length() - 1
        _table[_mask] = (
            _table[_mask ^ _bit]
            + _base
            + _CENTER[_c] * _CENTER_SCALE[_r]
        )
    _PST.append(_table)

# Conservative interception cones for straight-running pawns.
_PASS_UP = [0] * 64
_PASS_DOWN = [0] * 64
_FRONT_UP = [0] * 64
_FRONT_DOWN = [0] * 64

for _s in range(64):
    _r, _c = divmod(_s, 8)
    for _rr in range(8):
        if _rr == _r:
            continue
        _distance = abs(_rr - _r)
        _width = (_distance + 1) // 2
        _cone = 0
        for _cc in range(max(0, _c - _width), min(7, _c + _width) + 1):
            _cone |= 1 << (8 * _rr + _cc)
        if _rr > _r:
            _PASS_UP[_s] |= _cone
            _FRONT_UP[_s] |= 1 << (8 * _rr + _c)
        else:
            _PASS_DOWN[_s] |= _cone
            _FRONT_DOWN[_s] |= 1 << (8 * _rr + _c)


def _attacks(pieces, side):
    if side == 0:
        return (((pieces & _NA) << 7) | ((pieces & _NH) << 9)) & _FULL
    return ((pieces & _NA) >> 9) | ((pieces & _NH) >> 7)


def _safe_penultimate_push(a, b, side):
    p = a & _PRE[side]
    if not p:
        return False
    if side == 0:
        straight = (p << 8) & ~(a | b)
        diagonal = (((p & _NA) << 7) | ((p & _NH) << 9)) & ~a
    else:
        straight = (p >> 8) & ~(a | b)
        diagonal = (((p & _NA) >> 9) | ((p & _NH) >> 7)) & ~a
    targets = (straight | diagonal) & _PEN[side]
    return bool(targets & ~_attacks(b, side ^ 1))


def _evaluate(a, b, side):
    if side == 0:
        w, bl = a, b
    else:
        w, bl = b, a

    p = _PST
    score = (
        p[0][w & 255] - p[7][bl & 255]
        + p[1][(w >> 8) & 255] - p[6][(bl >> 8) & 255]
        + p[2][(w >> 16) & 255] - p[5][(bl >> 16) & 255]
        + p[3][(w >> 24) & 255] - p[4][(bl >> 24) & 255]
        + p[4][(w >> 32) & 255] - p[3][(bl >> 32) & 255]
        + p[5][(w >> 40) & 255] - p[2][(bl >> 40) & 255]
        + p[6][(w >> 48) & 255] - p[1][(bl >> 48) & 255]
        + p[7][w >> 56] - p[0][bl >> 56]
    )

    wa = _attacks(w, 0)
    ba = _attacks(bl, 1)

    score += 8 * ((w & wa).bit_count() - (bl & ba).bit_count())

    wh = w & ba & ~wa
    bh = bl & wa & ~ba
    score += 13 * (bh.bit_count() - wh.bit_count())
    score += 16 * (
        (bh & ((1 << 32) - 1)).bit_count()
        - (wh & (_FULL ^ ((1 << 32) - 1))).bit_count()
    )

    score += 3 * (
        (w & ((w & _NH) << 1)).bit_count()
        - (bl & ((bl & _NH) << 1)).bit_count()
    )
    score += 2 * (
        (wa & ~w & ~ba).bit_count()
        - (ba & ~bl & ~wa).bit_count()
    )

    safe_w = 9
    safe_b = 9

    pawns = w & (_FULL ^ ((1 << 24) - 1))
    while pawns:
        bit = pawns & -pawns
        pawns ^= bit
        s = bit.bit_length() - 1
        if not (bl & _PASS_UP[s]) and not (w & _FRONT_UP[s]):
            r = s >> 3
            score += _PASS_BONUS[r]
            safe_w = min(safe_w, 7 - r)

    pawns = bl & ((1 << 40) - 1)
    while pawns:
        bit = pawns & -pawns
        pawns ^= bit
        s = bit.bit_length() - 1
        if not (w & _PASS_DOWN[s]) and not (bl & _FRONT_DOWN[s]):
            r = s >> 3
            score -= _PASS_BONUS[7 - r]
            safe_b = min(safe_b, r)

    # A safe runner that finishes before even the opponent's fastest
    # theoretically possible runner is a certified race winner.
    if safe_w < 9 or safe_b < 9:
        fastest_w = 7 - ((w.bit_length() - 1) >> 3)
        fastest_b = ((bl & -bl).bit_length() - 1) >> 3

        if safe_w < fastest_b or (side == 0 and safe_w == fastest_b):
            score = 24000 - 30 * safe_w
        elif safe_b < fastest_w or (side == 1 and safe_b == fastest_w):
            score = -24000 + 30 * safe_b

    return (score if side == 0 else -score) + 8


class _Timeout(Exception):
    pass


class _Engine:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}
        self.history = [[0] * 4096 for _ in range(2)]
        self.killers = [[-1, -1] for _ in range(128)]

    def ordered(self, a, b, side, ttmove=-1, ply=0,
                forced=0, tactical=False):
        occupied = a | b
        if side == 0:
            left = ((a & _NA) << 7) & _FULL
            right = ((a & _NH) << 9) & _FULL
            directions = (
                ((a << 8) & _FULL & ~occupied, 8),
                (left & ~a, 7),
                (right & ~a, 9),
            )
        else:
            left = (a & _NA) >> 9
            right = (a & _NH) >> 7
            directions = (
                ((a >> 8) & ~occupied, -8),
                (left & ~a, -9),
                (right & ~a, -7),
            )

        limit = forced if forced else ((b | _PEN[side]) if tactical else _FULL)
        own_attacks = left | right
        double_support = left & right
        enemy_attacks = _attacks(b, side ^ 1)
        history = self.history[side]
        killer0, killer1 = self.killers[ply]
        result = []

        for targets, delta in directions:
            targets &= limit
            support = own_attacks if abs(delta) == 8 else double_support
            while targets:
                tb = targets & -targets
                targets ^= tb
                to_sq = tb.bit_length() - 1
                from_sq = to_sq - delta
                fb = 1 << from_sq
                move = (from_sq << 6) | to_sq

                if move == ttmove:
                    value = 1000000
                else:
                    rank = to_sq >> 3
                    progress = rank if side == 0 else 7 - rank
                    value = history[move] + 24 * (
                        _ADV[progress] - _ADV[progress - 1]
                    )
                    if tb & b:
                        value += 24000 + 36 * _ADV[7 - progress]
                    elif move == killer0:
                        value += 20000
                    elif move == killer1:
                        value += 18000

                    if tb & enemy_attacks:
                        value -= 5000 + 10 * _ADV[progress]
                    if tb & support:
                        value += 900
                    if fb & enemy_attacks:
                        value += 1500

                result.append((value, move, fb, tb))

        result.sort(reverse=True)
        return result

    def search(self, a, b, side, depth, alpha, beta, ply):
        self.nodes += 1
        if not (self.nodes & 127) and time.perf_counter() >= self.deadline:
            raise _Timeout

        if not a or (b & _GOAL[side ^ 1]):
            return -_MATE + ply
        if not b or (a & _GOAL[side]):
            return _MATE - ply

        # In a nonterminal position a penultimate-rank pawn always
        # has a legal winning diagonal or straight move.
        if a & _PEN[side]:
            return _MATE - ply - 1

        forced = b & _PEN[side ^ 1]
        if forced and (forced & (forced - 1)):
            return -_MATE + ply + 2

        if not forced and _safe_penultimate_push(a, b, side):
            return _MATE - ply - 3

        original_alpha = alpha
        ttmove = -1
        key = None
        if depth > 0:
            key = (a, b, side)
            entry = self.tt.get(key)
            if entry is not None:
                old_depth, value, flag, ttmove = entry
                if value > _MATE - 256:
                    value -= ply
                elif value < -_MATE + 256:
                    value += ply
                if old_depth >= depth:
                    if flag == 0:
                        return value
                    if flag == 1 and value >= beta:
                        return value
                    if flag == 2 and value <= alpha:
                        return value

        quiescent = depth <= 0
        best = -_INF
        if quiescent and not forced:
            best = _evaluate(a, b, side)
            if best >= beta or depth <= -2:
                return best
            if best > alpha:
                alpha = best

        moves = self.ordered(
            a, b, side, ttmove, ply,
            forced=forced,
            tactical=quiescent and not forced,
        )

        if not moves:
            if forced:
                return -_MATE + ply + 2
            if quiescent:
                return best
            return -_MATE + ply

        best_move = moves[0][1]
        child_depth = depth - 1
        if forced and depth > 0 and len(moves) == 1:
            child_depth = depth

        for index, (_, move, fb, tb) in enumerate(moves):
            new_a = (a ^ fb) | tb
            new_b = b & ~tb
            capture = bool(b & tb)

            if index == 0 or quiescent:
                value = -self.search(
                    new_b, new_a, side ^ 1, child_depth,
                    -beta, -alpha, ply + 1,
                )
            else:
                reduction = 0
                if (
                    depth >= 3
                    and index >= 5
                    and not forced
                    and not capture
                    and not (tb & _ADVANCED[side])
                    and move not in self.killers[ply]
                ):
                    reduction = 1
                    if depth >= 6 and index >= 12:
                        reduction = 2

                value = -self.search(
                    new_b, new_a, side ^ 1, child_depth - reduction,
                    -alpha - 1, -alpha, ply + 1,
                )
                if reduction and value > alpha:
                    value = -self.search(
                        new_b, new_a, side ^ 1, child_depth,
                        -alpha - 1, -alpha, ply + 1,
                    )
                if alpha < value < beta:
                    value = -self.search(
                        new_b, new_a, side ^ 1, child_depth,
                        -beta, -alpha, ply + 1,
                    )

            if value > best:
                best = value
                best_move = move
            if value > alpha:
                alpha = value

            if alpha >= beta:
                if not capture and depth > 0:
                    killers = self.killers[ply]
                    if killers[0] != move:
                        killers[1] = killers[0]
                        killers[0] = move
                    bonus = min(2048, depth * depth * 16)
                    old = self.history[side][move]
                    self.history[side][move] = old + bonus - old * bonus // 8192
                break

        if key is not None:
            flag = 2 if best <= original_alpha else 1 if best >= beta else 0
            stored = best
            if stored > _MATE - 256:
                stored += ply
            elif stored < -_MATE + 256:
                stored -= ply
            self.tt[key] = (depth, stored, flag, best_move)

        return best

    def choose(self, a, b):
        moves = self.ordered(a, b, 0)

        # The arena supplies nonterminal positions with legal moves.
        fallback = moves[0][1]

        for _, move, _, tb in moves:
            if tb & _GOAL[0] or not (b & ~tb):
                return move

        threat = b & _PEN[1]

        if not threat:
            enemy_attacks = _attacks(b, 1)
            for _, move, _, tb in moves:
                if tb & _PEN[0] and not (tb & enemy_attacks):
                    return move

        # Execute a provably winning straight-line race without searching.
        if b:
            enemy_distance = ((b & -b).bit_length() - 1) >> 3
            pawns = a
            while pawns:
                s = pawns.bit_length() - 1
                pawns ^= 1 << s
                distance = 7 - (s >> 3)
                if (
                    0 < distance <= enemy_distance
                    and not (b & _PASS_UP[s])
                    and not (a & _FRONT_UP[s])
                ):
                    return (s << 6) | (s + 8)

        if threat and not (threat & (threat - 1)):
            defenses = [m for m in moves if m[3] & threat]
            if defenses:
                moves = defenses
                fallback = moves[0][1]

        if len(moves) == 1:
            return moves[0][1]

        completed_best = fallback

        try:
            for depth in range(1, 41):
                if time.perf_counter() >= self.deadline:
                    break

                alpha = -_INF
                iteration_best = moves[0][1]
                ranked = []

                for index, item in enumerate(moves):
                    if time.perf_counter() >= self.deadline:
                        raise _Timeout

                    _, move, fb, tb = item
                    new_a = (a ^ fb) | tb
                    new_b = b & ~tb

                    if index == 0:
                        value = -self.search(
                            new_b, new_a, 1, depth - 1,
                            -_INF, _INF, 1,
                        )
                    else:
                        value = -self.search(
                            new_b, new_a, 1, depth - 1,
                            -alpha - 1, -alpha, 1,
                        )
                        if value > alpha:
                            value = -self.search(
                                new_b, new_a, 1, depth - 1,
                                -_INF, -alpha, 1,
                            )

                    ranked.append((value, item))
                    if value > alpha:
                        alpha = value
                        iteration_best = move

                completed_best = iteration_best
                ranked.sort(key=lambda x: x[0], reverse=True)
                moves = [item for _, item in ranked]

                if alpha >= 23000 or alpha <= -_MATE + 128:
                    break

        except _Timeout:
            pass

        return completed_best


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str,
) -> tuple[tuple[int, int], tuple[int, int]]:
    deadline = time.perf_counter() + 0.88

    # Normalize our pieces to move toward increasing row numbers.
    flip = color == "b"
    a = 0
    b = 0

    for r, c in me:
        if flip:
            r = 7 - r
        a |= 1 << (8 * r + c)

    for r, c in opp:
        if flip:
            r = 7 - r
        b |= 1 << (8 * r + c)

    move = _Engine(deadline).choose(a, b)
    source, target = move >> 6, move & 63
    from_r, from_c = divmod(source, 8)
    to_r, to_c = divmod(target, 8)

    if flip:
        from_r = 7 - from_r
        to_r = 7 - to_r

    return ((from_r, from_c), (to_r, to_c))
