
import time

_FULL = (1 << 64) - 1
_NOT_A = 0xFEFEFEFEFEFEFEFE
_NOT_H = 0x7F7F7F7F7F7F7F7F
_BITS = [1 << s for s in range(64)]

_GOAL = (0xFF00000000000000, 0xFF)
_PREGOAL = (0x00FF000000000000, 0xFF00)
_DANGER = (
    0x00FFFF0000000000,
    0x0000000000FFFF00,
)

_MATE = 100000
_MATE_BOUND = 90000
_INF = 1000000

_ADV = (0, 2, 8, 18, 36, 68, 180, 5000)
_CENTER = (0, 3, 5, 7, 7, 5, 3, 0)
_PASS_BONUS = (0, 0, 18, 48, 110, 220, 500, 0)

_PST = [[0] * 64 for _ in range(2)]
_ATTACK = [[0] * 64 for _ in range(2)]
_FORWARD = [[0] * 64 for _ in range(2)]
_STOP = [[[0] * 64 for _ in range(2)] for _ in range(2)]
_BASE = [[0] * 4096 for _ in range(2)]

for _side in range(2):
    _step = 1 if _side == 0 else -1
    for _s in range(64):
        _r, _c = divmod(_s, 8)
        _progress = _r if _side == 0 else 7 - _r
        _PST[_side][_s] = 100 + _ADV[_progress] + _CENTER[_c]

        _rr = _r + _step
        if 0 <= _rr < 8:
            for _cc in (_c - 1, _c + 1):
                if 0 <= _cc < 8:
                    _ATTACK[_side][_s] |= _BITS[8 * _rr + _cc]

        for _distance in range(1, 8):
            _rr = _r + _step * _distance
            if not 0 <= _rr < 8:
                break
            _FORWARD[_side][_s] |= _BITS[8 * _rr + _c]
            for _wait in range(2):
                _width = (_distance + _wait) // 2
                for _cc in range(max(0, _c - _width),
                                 min(7, _c + _width) + 1):
                    _STOP[_wait][_side][_s] |= _BITS[8 * _rr + _cc]

for _side in range(2):
    _step = 1 if _side == 0 else -1
    for _s in range(64):
        _r, _c = divmod(_s, 8)
        _rr = _r + _step
        if not 0 <= _rr < 8:
            continue
        for _cc in range(max(0, _c - 1), min(7, _c + 1) + 1):
            _t = 8 * _rr + _cc
            _progress = _rr if _side == 0 else 7 - _rr
            _BASE[_side][(_s << 6) | _t] = (
                12 * (_PST[_side][_t] - _PST[_side][_s])
                + 28 * _progress
            )

_ROW = []
for _r in range(8):
    _table = [0] * 256
    for _byte in range(1, 256):
        _bit = _byte & -_byte
        _c = _bit.bit_length() - 1
        _table[_byte] = (
            _table[_byte ^ _bit] + _PST[0][8 * _r + _c]
        )
    _ROW.append(_table)


def _attacks(pieces, side):
    if side == 0:
        return (
            ((pieces << 7) & _NOT_H)
            | ((pieces << 9) & _NOT_A)
        ) & _FULL
    return (
        ((pieces >> 9) & _NOT_H)
        | ((pieces >> 7) & _NOT_A)
    )


def _moves(a, b, side, tactical=False):
    occupied = a | b
    allowed = (_FULL ^ a)
    if tactical:
        allowed &= b | _PREGOAL[side]

    if side == 0:
        groups = (
            (8, ((a << 8) & _FULL) & ~occupied & allowed),
            (7, ((a << 7) & _NOT_H & _FULL) & allowed),
            (9, ((a << 9) & _NOT_A & _FULL) & allowed),
        )
    else:
        groups = (
            (-8, (a >> 8) & ~occupied & allowed),
            (-9, (a >> 9) & _NOT_H & allowed),
            (-7, (a >> 7) & _NOT_A & allowed),
        )

    result = []
    for offset, targets in groups:
        while targets:
            bit = targets & -targets
            targets ^= bit
            target = bit.bit_length() - 1
            result.append(((target - offset) << 6) | target)
    return result


def _capture_moves(a, target, side):
    sources = a & _ATTACK[side ^ 1][target]
    result = []
    while sources:
        bit = sources & -sources
        sources ^= bit
        source = bit.bit_length() - 1
        result.append((source << 6) | target)
    return result


class _Timeout(Exception):
    pass


class _Engine:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}
        self.eval_cache = {}
        self.history = [[0] * 4096 for _ in range(2)]
        self.killers = [[0, 0] for _ in range(256)]
        self.root_best = 0

    def ordered(self, moves, a, b, side, ply, tt_move=0):
        enemy_attacks = _attacks(b, side ^ 1)
        history = self.history[side]
        base = _BASE[side]
        enemy_values = _PST[side ^ 1]
        killer1, killer2 = self.killers[min(ply, 255)]
        preg = _PREGOAL[side]
        scored = []

        for move in moves:
            if move == tt_move:
                scored.append((100000000, move))
                continue

            source = move >> 6
            target = move & 63
            target_bit = _BITS[target]
            score = base[move] + history[move]

            if target_bit & b:
                score += 14000 + 8 * enemy_values[target]
            elif move == killer1:
                score += 8500
            elif move == killer2:
                score += 8000

            if target_bit & preg:
                score += 60000
            if target_bit & enemy_attacks:
                score -= 1800
            if _BITS[source] & enemy_attacks:
                score += 400

            defenders = a & _ATTACK[side ^ 1][target]
            if defenders & ~_BITS[source]:
                score += 120

            scored.append((score, move))

        scored.sort(reverse=True)
        return [move for _, move in scored]

    def evaluate(self, a, b, side):
        key = (a, b, side)
        cached = self.eval_cache.get(key)
        if cached is not None:
            return cached

        if side == 0:
            up, down = a, b
        else:
            up, down = b, a

        # Piece-square scores, including material.
        score = 0
        uu, dd = up, down
        for row in range(8):
            score += _ROW[row][uu & 255]
            score -= _ROW[7 - row][dd & 255]
            uu >>= 8
            dd >>= 8

        up_attacks = _attacks(up, 0)
        down_attacks = _attacks(down, 1)

        score += 10 * (
            (up & up_attacks).bit_count()
            - (down & down_attacks).bit_count()
        )

        hanging_up = up & down_attacks & ~up_attacks
        hanging_down = down & up_attacks & ~down_attacks
        if side == 0:
            score -= 10 * hanging_up.bit_count()
            score += 26 * hanging_down.bit_count()
        else:
            score -= 26 * hanging_up.bit_count()
            score += 10 * hanging_down.bit_count()

        # Connected fronts are useful; vertically congested files less so.
        score += 5 * (
            (up & ((up << 1) & _NOT_A)).bit_count()
            - (down & ((down << 1) & _NOT_A)).bit_count()
        )
        score -= 5 * (
            (up & (up << 8)).bit_count()
            - (down & (down << 8)).bit_count()
        )

        score -= 14 * (
            hanging_up & 0x00FFFF0000000000
        ).bit_count()
        score += 14 * (
            hanging_down & 0x0000000000FFFF00
        ).bit_count()

        up_distance = 7 - ((up.bit_length() - 1) >> 3)
        down_distance = (
            ((down & -down).bit_length() - 1) >> 3
        )

        # A straight runner is safe if no enemy can reach either its
        # path or an interception square in time. These masks deliberately
        # overestimate the defenders' freedom of movement.
        best_up = total_up = 0
        candidates = up & (_FULL ^ ((1 << 24) - 1))
        stop = _STOP[0 if side == 0 else 1][0]
        while candidates:
            bit = candidates & -candidates
            candidates ^= bit
            square = bit.bit_length() - 1

            if (up & _FORWARD[0][square]) or (down & stop[square]):
                continue

            progress = square >> 3
            distance = 7 - progress
            first = side == 0
            wins_race = (
                distance <= down_distance if first
                else distance < down_distance
            )
            if wins_race:
                value = (
                    _MATE - (2 * distance - 1)
                    if first else -_MATE + 2 * distance
                )
                self.eval_cache[key] = value
                return value

            bonus = _PASS_BONUS[progress]
            total_up += bonus
            best_up = max(best_up, bonus)

        best_down = total_down = 0
        candidates = down & ((1 << 40) - 1)
        stop = _STOP[0 if side == 1 else 1][1]
        while candidates:
            bit = candidates & -candidates
            candidates ^= bit
            square = bit.bit_length() - 1

            if (down & _FORWARD[1][square]) or (up & stop[square]):
                continue

            distance = square >> 3
            progress = 7 - distance
            first = side == 1
            wins_race = (
                distance <= up_distance if first
                else distance < up_distance
            )
            if wins_race:
                value = (
                    _MATE - (2 * distance - 1)
                    if first else -_MATE + 2 * distance
                )
                self.eval_cache[key] = value
                return value

            bonus = _PASS_BONUS[progress]
            total_down += bonus
            best_down = max(best_down, bonus)

        score += best_up + total_up // 4
        score -= best_down + total_down // 4

        value = (score if side == 0 else -score) + 8
        self.eval_cache[key] = value
        return value

    def search(self, a, b, side, depth, alpha, beta, ply):
        self.nodes += 1
        if ply == 0 or (self.nodes & 127) == 0:
            if time.perf_counter() >= self.deadline:
                raise _Timeout

        if not a or (b & _GOAL[side ^ 1]):
            return -_MATE + ply
        if not b or (a & _GOAL[side]):
            return _MATE - ply

        # In a live position a penultimate-rank pawn can always finish
        # diagonally, irrespective of enemy occupancy.
        if a & _PREGOAL[side]:
            return _MATE - ply - 1

        forced = False
        legal = None
        enemy_threats = b & _PREGOAL[side ^ 1]
        if enemy_threats:
            if enemy_threats & (enemy_threats - 1):
                return -_MATE + ply + 2
            target = enemy_threats.bit_length() - 1
            legal = _capture_moves(a, target, side)
            if not legal:
                return -_MATE + ply + 2
            forced = True

        original_alpha = alpha
        key = None
        tt_move = 0

        if depth > 0:
            key = (a, b, side)
            entry = self.tt.get(key)
            if entry is not None:
                old_depth, value, flag, tt_move = entry
                if value > _MATE_BOUND:
                    value -= ply
                elif value < -_MATE_BOUND:
                    value += ply
                if old_depth >= depth and ply != 0:
                    if flag == 0:
                        return value
                    if flag == 1 and value >= beta:
                        return value
                    if flag == 2 and value <= alpha:
                        return value

        quiescence = depth <= 0
        best = -_INF
        best_move = 0

        if quiescence and not forced:
            stand = self.evaluate(a, b, side)
            if stand > _MATE_BOUND:
                return stand - ply
            if stand < -_MATE_BOUND:
                return stand + ply

            if stand >= beta or depth <= -2:
                return stand
            best = stand
            if stand > alpha:
                alpha = stand

        if legal is None:
            legal = _moves(a, b, side, tactical=quiescence)

        if not legal:
            if quiescence:
                return best
            return -_MATE + ply

        legal = self.ordered(legal, a, b, side, ply, tt_move)
        enemy_attacks = _attacks(b, side ^ 1)
        dangerous = bool(b & _DANGER[side ^ 1])
        killer1, killer2 = self.killers[min(ply, 255)]

        # Forced saves do not consume ordinary search depth.
        next_depth = depth if forced and depth > 0 else depth - 1

        for index, move in enumerate(legal):
            source = move >> 6
            target = move & 63
            source_bit = _BITS[source]
            target_bit = _BITS[target]
            capture = bool(target_bit & b)

            moved = (a ^ source_bit) | target_bit
            remaining = b & ~target_bit

            if index == 0 or quiescence:
                value = -self.search(
                    remaining, moved, side ^ 1, next_depth,
                    -beta, -alpha, ply + 1
                )
            else:
                reduction = 0
                progress = (target >> 3) if side == 0 else 7 - (target >> 3)

                if (
                    depth >= 3
                    and index >= 4
                    and not forced
                    and not capture
                    and not dangerous
                    and progress < 5
                    and move != killer1
                    and move != killer2
                    and not (source_bit & enemy_attacks)
                ):
                    reduction = 1
                    if depth >= 6 and index >= 10:
                        reduction = 2

                value = -self.search(
                    remaining, moved, side ^ 1,
                    next_depth - reduction,
                    -alpha - 1, -alpha, ply + 1
                )

                if reduction and value > alpha:
                    value = -self.search(
                        remaining, moved, side ^ 1, next_depth,
                        -alpha - 1, -alpha, ply + 1
                    )

                if alpha < value < beta:
                    value = -self.search(
                        remaining, moved, side ^ 1, next_depth,
                        -beta, -alpha, ply + 1
                    )

            if value > best:
                best = value
                best_move = move
                if ply == 0:
                    self.root_best = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                if depth > 0 and not capture:
                    killers = self.killers[min(ply, 255)]
                    if move != killers[0]:
                        killers[1] = killers[0]
                        killers[0] = move

                    history = self.history[side]
                    bonus = min(1600, 32 * depth * depth)
                    old = history[move]
                    history[move] = old + bonus - old * bonus // 8192
                break

        if depth > 0:
            if best <= original_alpha:
                flag = 2
            elif best >= beta:
                flag = 1
            else:
                flag = 0

            stored = best
            if stored > _MATE_BOUND:
                stored += ply
            elif stored < -_MATE_BOUND:
                stored -= ply

            self.tt[key] = (depth, stored, flag, best_move)

        return best


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str,
) -> tuple[tuple[int, int], tuple[int, int]]:
    start = time.perf_counter()

    # Normalize our direction to increasing rows.
    flip = 7 if color == 'b' else 0
    a = 0
    b = 0
    for row, col in me:
        a |= _BITS[((row ^ flip) << 3) | col]
    for row, col in opp:
        b |= _BITS[((row ^ flip) << 3) | col]

    legal = _moves(a, b, 0)

    def decode(move):
        source = move >> 6
        target = move & 63
        return (
            ((source >> 3) ^ flip, source & 7),
            ((target >> 3) ^ flip, target & 7),
        )

    # Arena calls are assumed to be nonterminal, so legal is nonempty.
    # Take either kind of immediate victory without searching.
    for move in legal:
        target_bit = _BITS[move & 63]
        if target_bit & _GOAL[0]:
            return decode(move)
        if b and not (b & ~target_bit):
            return decode(move)

    engine = _Engine(start + 0.90)
    ordered = engine.ordered(legal, a, b, 0, 0)
    fallback = ordered[0]

    threats = b & _PREGOAL[1]
    if threats:
        if threats & (threats - 1):
            return decode(fallback)
        saves = _capture_moves(a, threats.bit_length() - 1, 0)
        if not saves:
            return decode(fallback)
        if len(saves) == 1:
            return decode(saves[0])
        fallback = engine.ordered(saves, a, b, 0, 0)[0]

    if len(legal) == 1:
        return decode(legal[0])

    best_move = fallback
    engine.root_best = fallback
    previous_score = 0

    for depth in range(1, 33):
        try:
            if depth >= 3 and abs(previous_score) < _MATE_BOUND:
                low = previous_score - 90
                high = previous_score + 90
            else:
                low, high = -_INF, _INF

            score = engine.search(a, b, 0, depth, low, high, 0)

            if score <= low or score >= high:
                score = engine.search(
                    a, b, 0, depth, -_INF, _INF, 0
                )

            best_move = engine.root_best
            previous_score = score

            if abs(score) > _MATE_BOUND:
                break
        except _Timeout:
            break

    return decode(best_move)
