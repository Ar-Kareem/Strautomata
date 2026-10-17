
from time import perf_counter


_FULL = (1 << 64) - 1
_BITS = tuple(1 << i for i in range(64))
_NOT_A = _FULL ^ 0x0101010101010101
_NOT_H = _FULL ^ 0x8080808080808080

_GOAL = (0xFF00000000000000, 0x00000000000000FF)
_NEAR = (0x00FF000000000000, 0x000000000000FF00)
_ADVANCED = (_FULL ^ ((1 << 24) - 1), (1 << 40) - 1)
_DANGER = (_FULL ^ ((1 << 40) - 1), (1 << 24) - 1)

_RANK = (
    tuple(s >> 3 for s in range(64)),
    tuple(7 - (s >> 3) for s in range(64)),
)
_CENTER = (0, 2, 3, 4, 4, 3, 2, 0)
_ADV_VALUE = (0, 3, 9, 20, 39, 75, 180, 0)
_PASS_VALUE = (0, 0, 12, 40, 100, 250, 700, 0)
_SEMI_VALUE = (0, 0, 0, 5, 14, 30, 60, 0)
_GUARD = (0, 12, 20, 25, 28, 30, 30, 30, 30)

_PST = tuple(
    tuple(
        100 + _ADV_VALUE[_RANK[d][s]]
        + _CENTER[s & 7] * (2 if _RANK[d][s] <= 3 else 1)
        for s in range(64)
    )
    for d in range(2)
)

_SUPPORT = [[0] * 64 for _ in range(2)]
_PATH = [[0] * 64 for _ in range(2)]
_CATCH_FIRST = [[0] * 64 for _ in range(2)]
_CATCH_SECOND = [[0] * 64 for _ in range(2)]


def _initialize_tables():
    for direction in range(2):
        step = 1 if direction == 0 else -1
        for square in range(64):
            row, col = divmod(square, 8)

            source_row = row - step
            if 0 <= source_row < 8:
                for source_col in (col - 1, col + 1):
                    if 0 <= source_col < 8:
                        _SUPPORT[direction][square] |= (
                            1 << (source_row * 8 + source_col)
                        )

            target_row = row + step
            gap = 1
            while 0 <= target_row < 8:
                _PATH[direction][square] |= (
                    1 << (target_row * 8 + col)
                )
                for target_col in range(8):
                    distance = abs(target_col - col)
                    bit = 1 << (target_row * 8 + target_col)
                    if distance <= gap // 2:
                        _CATCH_FIRST[direction][square] |= bit
                    if distance <= (gap + 1) // 2:
                        _CATCH_SECOND[direction][square] |= bit
                target_row += step
                gap += 1

    rows = []
    for row in range(8):
        table = [0] * 256
        for mask in range(1, 256):
            bit = mask & -mask
            col = bit.bit_length() - 1
            table[mask] = table[mask ^ bit] + _PST[0][row * 8 + col]
        rows.append(tuple(table))
    return tuple(rows)


_ROW_UP = _initialize_tables()
_ROW_DOWN = tuple(reversed(_ROW_UP))

_MATE = 30000
_INF = 40000


def _attacks(pieces, direction):
    if direction == 0:
        return (
            ((pieces & _NOT_A) << 7)
            | ((pieces & _NOT_H) << 9)
        ) & _FULL
    return (
        ((pieces & _NOT_A) >> 9)
        | ((pieces & _NOT_H) >> 7)
    )


def _moves(pieces, enemies, direction, tactical=False):
    empty = ~(pieces | enemies)
    not_own = ~pieces

    if direction == 0:
        forward = (pieces << 8) & empty & _FULL
        left = ((pieces & _NOT_A) << 7) & not_own & _FULL
        right = ((pieces & _NOT_H) << 9) & not_own & _FULL
        deltas = (8, 7, 9)
    else:
        forward = (pieces >> 8) & empty
        left = ((pieces & _NOT_A) >> 9) & not_own
        right = ((pieces & _NOT_H) >> 7) & not_own
        deltas = (-8, -9, -7)

    if tactical:
        forward &= _NEAR[direction]
        targets = enemies | _NEAR[direction]
        left &= targets
        right &= targets

    result = []
    for destinations, delta in zip((forward, left, right), deltas):
        while destinations:
            bit = destinations & -destinations
            destinations ^= bit
            target = bit.bit_length() - 1
            result.append(((target - delta) << 6) | target)
    return result


def _defenses(pieces, threat, direction):
    if not threat or threat & (threat - 1):
        return []
    target = threat.bit_length() - 1
    sources = pieces & _SUPPORT[direction][target]
    result = []
    while sources:
        bit = sources & -sources
        sources ^= bit
        result.append(((bit.bit_length() - 1) << 6) | target)
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
        self.killers = [[-1, -1] for _ in range(128)]

    def _tick(self):
        self.nodes += 1
        if (self.nodes & 127) == 0:
            if perf_counter() >= self.deadline:
                raise _Timeout

    def _order(self, moves, pieces, enemies, direction, ply,
               hash_move=-1):
        enemy_attacks = _attacks(enemies, direction ^ 1)
        history = self.history[direction]
        killer1, killer2 = self.killers[min(ply, 127)]
        ranks = _RANK[direction]
        support = _SUPPORT[direction]
        victim_values = _PST[direction ^ 1]

        def priority(move):
            if move == hash_move:
                return 1_000_000

            source = move >> 6
            target = move & 63
            source_bit = _BITS[source]
            target_bit = _BITS[target]
            rank = ranks[target]

            score = (
                history[move]
                + rank * rank * 65
                + _CENTER[target & 7] * 8
            )

            if enemies & target_bit:
                score += 16000 + 4 * victim_values[target]

            if enemy_attacks & target_bit:
                score -= 13000
                if support[target] & pieces & ~source_bit:
                    score += 6000
            else:
                score += 2500

            if rank == 6:
                score += 60000
            if enemy_attacks & source_bit:
                score += 1500

            if move == killer1:
                score += 13000
            elif move == killer2:
                score += 11000
            return score

        moves.sort(key=priority, reverse=True)
        return moves

    def _evaluate(self, pieces, enemies, direction):
        key = (pieces, enemies, direction)
        cached = self.eval_cache.get(key)
        if cached is not None:
            return cached

        if direction == 0:
            up, down = pieces, enemies
        else:
            up, down = enemies, pieces

        score = 0
        u, d = up, down
        for row in range(8):
            score += _ROW_UP[row][u & 255] - _ROW_DOWN[row][d & 255]
            u >>= 8
            d >>= 8

        up_attacks = _attacks(up, 0)
        down_attacks = _attacks(down, 1)

        up_supported = up & up_attacks
        down_supported = down & down_attacks
        score += 9 * (
            up_supported.bit_count() - down_supported.bit_count()
        )

        up_weak = up & down_attacks & ~up_attacks
        down_weak = down & up_attacks & ~down_attacks
        score -= (20 if direction == 0 else 42) * up_weak.bit_count()
        score += (42 if direction == 0 else 20) * down_weak.bit_count()

        score += 4 * (
            (down_supported & up_attacks).bit_count()
            - (up_supported & down_attacks).bit_count()
        )

        score += 5 * (
            (up & ((up & _NOT_H) << 1)).bit_count()
            - (down & ((down & _NOT_H) << 1)).bit_count()
        )

        empty = ~(up | down)
        score += 2 * (
            ((up << 8) & empty & _FULL).bit_count()
            - ((down >> 8) & empty).bit_count()
        )
        score += (
            (up_attacks & ~up).bit_count()
            - (down_attacks & ~down).bit_count()
        )

        score += _GUARD[(up & 255).bit_count()]
        score -= _GUARD[(down >> 56).bit_count()]

        fastest = [9, 9]
        for board, opposition, pawn_direction, sign in (
            (up, down, 0, 1),
            (down, up, 1, -1),
        ):
            candidates = board & _ADVANCED[pawn_direction]
            catch_table = (
                _CATCH_FIRST[pawn_direction]
                if direction == pawn_direction
                else _CATCH_SECOND[pawn_direction]
            )
            path_table = _PATH[pawn_direction]
            ranks = _RANK[pawn_direction]

            while candidates:
                bit = candidates & -candidates
                candidates ^= bit
                square = bit.bit_length() - 1
                rank = ranks[square]

                if board & path_table[square]:
                    continue

                interceptors = opposition & catch_table[square]
                if not interceptors:
                    score += sign * _PASS_VALUE[rank]
                    distance = 7 - rank
                    if distance < fastest[pawn_direction]:
                        fastest[pawn_direction] = distance
                elif not (interceptors & (interceptors - 1)):
                    score += sign * _SEMI_VALUE[rank]

        minimum_up = 7 - ((up.bit_length() - 1) >> 3)
        minimum_down = ((down & -down).bit_length() - 1) >> 3

        up_wins_race = (
            fastest[0] <= minimum_down
            if direction == 0
            else fastest[0] < minimum_down
        )
        down_wins_race = (
            fastest[1] <= minimum_up
            if direction == 1
            else fastest[1] < minimum_up
        )

        if up_wins_race:
            score = 12000 - 60 * fastest[0]
        elif down_wins_race:
            score = -12000 + 60 * fastest[1]

        result = (score if direction == 0 else -score) + 8
        self.eval_cache[key] = result
        return result

    def _quiescence(self, pieces, enemies, direction,
                    alpha, beta, ply, remaining):
        self._tick()

        if not pieces or enemies & _GOAL[direction ^ 1]:
            return -_MATE + ply
        if not enemies or pieces & _GOAL[direction]:
            return _MATE - ply
        if pieces & _NEAR[direction]:
            return _MATE - ply - 1

        threat = enemies & _NEAR[direction ^ 1]
        if threat:
            moves = _defenses(pieces, threat, direction)
            if not moves:
                return -_MATE + ply + 2
            best = -_INF
            next_remaining = remaining
        else:
            best = self._evaluate(pieces, enemies, direction)
            if best >= beta:
                return best
            if best > alpha:
                alpha = best
            if remaining <= 0:
                return best
            moves = _moves(pieces, enemies, direction, tactical=True)
            next_remaining = remaining - 1

        self._order(moves, pieces, enemies, direction, ply)
        for move in moves:
            source_bit = _BITS[move >> 6]
            target_bit = _BITS[move & 63]
            moved = pieces ^ source_bit ^ target_bit
            surviving = enemies & ~target_bit

            score = -self._quiescence(
                surviving, moved, direction ^ 1,
                -beta, -alpha, ply + 1, next_remaining
            )
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        return best

    def search(self, pieces, enemies, direction,
               depth, alpha, beta, ply=0):
        if depth <= 0:
            return self._quiescence(
                pieces, enemies, direction, alpha, beta, ply, 2
            )

        self._tick()

        if not pieces or enemies & _GOAL[direction ^ 1]:
            return -_MATE + ply
        if not enemies or pieces & _GOAL[direction]:
            return _MATE - ply
        if pieces & _NEAR[direction]:
            return _MATE - ply - 1

        threat = enemies & _NEAR[direction ^ 1]
        forced = bool(threat)
        if forced:
            moves = _defenses(pieces, threat, direction)
            if not moves:
                return -_MATE + ply + 2
        else:
            moves = None

        key = (pieces, enemies, direction)
        entry = self.tt.get(key)
        hash_move = -1
        if entry is not None:
            stored_depth, value, flag, hash_move = entry
            if value > 29000:
                value -= ply
            elif value < -29000:
                value += ply

            if stored_depth >= depth:
                if flag == 0:
                    return value
                if flag == 1 and value >= beta:
                    return value
                if flag == 2 and value <= alpha:
                    return value

        if moves is None:
            moves = _moves(pieces, enemies, direction)
        if not moves:
            return -_MATE + ply

        self._order(moves, pieces, enemies, direction, ply, hash_move)

        original_alpha = alpha
        best = -_INF
        best_move = moves[0]
        killer1, killer2 = self.killers[min(ply, 127)]
        enemy_attacks = _attacks(enemies, direction ^ 1)
        dangerous_enemy = bool(enemies & _DANGER[direction ^ 1])

        for index, move in enumerate(moves):
            source = move >> 6
            target = move & 63
            source_bit = _BITS[source]
            target_bit = _BITS[target]
            capture = bool(enemies & target_bit)

            moved = pieces ^ source_bit ^ target_bit
            surviving = enemies & ~target_bit
            next_depth = depth - 1

            if index == 0:
                score = -self.search(
                    surviving, moved, direction ^ 1,
                    next_depth, -beta, -alpha, ply + 1
                )
            else:
                reduction = 0
                if (
                    depth >= 3
                    and index >= 4
                    and not capture
                    and not forced
                    and not dangerous_enemy
                    and _RANK[direction][target] < 5
                    and not (source_bit & enemy_attacks)
                    and move != killer1
                    and move != killer2
                ):
                    reduction = 1
                    if depth >= 6 and index >= 12:
                        reduction = 2

                score = -self.search(
                    surviving, moved, direction ^ 1,
                    next_depth - reduction,
                    -alpha - 1, -alpha, ply + 1
                )

                if reduction and score > alpha:
                    score = -self.search(
                        surviving, moved, direction ^ 1,
                        next_depth, -alpha - 1, -alpha, ply + 1
                    )

                if alpha < score < beta:
                    score = -self.search(
                        surviving, moved, direction ^ 1,
                        next_depth, -beta, -alpha, ply + 1
                    )

            if score > best:
                best = score
                best_move = move
            if score > alpha:
                alpha = score

            if alpha >= beta:
                if not capture:
                    killers = self.killers[min(ply, 127)]
                    if killers[0] != move:
                        killers[1] = killers[0]
                        killers[0] = move

                    history = self.history[direction]
                    bonus = min(2048, depth * depth * 40)
                    old = history[move]
                    history[move] = old + bonus - old * bonus // 16384
                break

        if best <= original_alpha:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0

        stored_score = best
        if stored_score > 29000:
            stored_score += ply
        elif stored_score < -29000:
            stored_score -= ply

        self.tt[key] = (depth, stored_score, flag, best_move)
        return best


def _decode(move, flipped):
    source, target = move >> 6, move & 63
    source_row, source_col = divmod(source, 8)
    target_row, target_col = divmod(target, 8)
    if flipped:
        source_row = 7 - source_row
        target_row = 7 - target_row
    return ((source_row, source_col), (target_row, target_col))


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str
) -> tuple[tuple[int, int], tuple[int, int]]:
    start = perf_counter()
    flipped = color == "b"

    pieces = 0
    enemies = 0
    for row, col in me:
        if flipped:
            row = 7 - row
        pieces |= 1 << (row * 8 + col)
    for row, col in opp:
        if flipped:
            row = 7 - row
        enemies |= 1 << (row * 8 + col)

    # After normalization, our pieces always move toward increasing rows.
    legal = _moves(pieces, enemies, 0)

    # Arena positions are nonterminal, so at least one legal move exists.
    for move in legal:
        target_bit = _BITS[move & 63]
        if target_bit & _GOAL[0] or not (enemies & ~target_bit):
            return _decode(move, flipped)

    threat = enemies & _NEAR[1]
    if threat:
        saves = _defenses(pieces, threat, 0)
        if saves:
            legal = saves

    if len(legal) == 1:
        return _decode(legal[0], flipped)

    # Prove a straight-running win when no enemy can intercept the
    # runner and even the opponent's fastest possible racer is too slow.
    if enemies:
        enemy_minimum = ((enemies & -enemies).bit_length() - 1) >> 3
        candidates = pieces
        while candidates:
            square = candidates.bit_length() - 1
            candidates ^= _BITS[square]
            distance = 7 - (square >> 3)
            if (
                0 < distance <= enemy_minimum
                and not (pieces & _PATH[0][square])
                and not (enemies & _CATCH_FIRST[0][square])
            ):
                move = (square << 6) | (square + 8)
                if move in legal:
                    return _decode(move, flipped)

    engine = _Engine(start + 0.90)
    engine._order(legal, pieces, enemies, 0, 0)
    chosen = legal[0]
    root_key = (pieces, enemies, 0)
    previous_score = 0

    try:
        for depth in range(1, 40):
            if perf_counter() >= engine.deadline:
                break

            if depth >= 3:
                alpha = max(-_INF, previous_score - 80)
                beta = min(_INF, previous_score + 80)
            else:
                alpha, beta = -_INF, _INF

            while True:
                score = engine.search(
                    pieces, enemies, 0, depth, alpha, beta
                )
                if score <= alpha and alpha != -_INF:
                    alpha = -_INF
                    continue
                if score >= beta and beta != _INF:
                    beta = _INF
                    continue
                break

            entry = engine.tt.get(root_key)
            if entry is not None and entry[3] in legal:
                chosen = entry[3]
            previous_score = score

            if abs(score) > 29000:
                break
    except _Timeout:
        pass

    return _decode(chosen, flipped)
