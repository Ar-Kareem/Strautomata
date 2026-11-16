
import time

FULL = (1 << 32) - 1
WIN = 30000
INF = 32000

_GEOMETRIES = {}
_TABLES = {}
_FOLLOW = None


class _Timeout(Exception):
    pass


def _bits(squares):
    result = 0
    for r, c in squares:
        result |= 1 << (4 * r + c // 2)
    return result


def _byte_tables(values):
    tables = []
    for block in range(4):
        table = [0] * 256
        offset = block * 8
        for x in range(1, 256):
            bit = x & -x
            table[x] = table[x ^ bit] + values[offset + bit.bit_length() - 1]
        tables.append(table)
    return tuple(tables)


def _table_sum(bits, tables):
    return (
        tables[0][bits & 255]
        + tables[1][(bits >> 8) & 255]
        + tables[2][(bits >> 16) & 255]
        + tables[3][bits >> 24]
    )


class _Geometry:
    def __init__(self, parity):
        self.coords = tuple(
            (i // 4, 2 * (i % 4) + (((i // 4) + parity) & 1))
            for i in range(32)
        )

        steps = []
        jump_groups = []
        jumps = []
        step_masks = []

        for directions in ((-1,), (1,), (-1, 1)):
            sg = {}
            jg = {}
            jl = [[] for _ in range(32)]
            sm = [0] * 32

            for i, (r, c) in enumerate(self.coords):
                for dr in directions:
                    for dc in (-1, 1):
                        rr, cc = r + dr, c + dc
                        if not (0 <= rr < 8 and 0 <= cc < 8):
                            continue

                        middle = 4 * rr + cc // 2
                        delta = middle - i
                        sg[delta] = sg.get(delta, 0) | (1 << i)
                        sm[i] |= 1 << middle

                        rr, cc = r + 2 * dr, c + 2 * dc
                        if 0 <= rr < 8 and 0 <= cc < 8:
                            destination = 4 * rr + cc // 2
                            key = (middle - i, destination - i)
                            jg[key] = jg.get(key, 0) | (1 << i)
                            jl[i].append(
                                (1 << middle, 1 << destination, destination)
                            )

            steps.append(tuple((mask, d) for d, mask in sg.items()))
            jump_groups.append(
                tuple((mask, a, b) for (a, b), mask in jg.items())
            )
            jumps.append(tuple(tuple(v) for v in jl))
            step_masks.append(tuple(sm))

        self.steps = tuple(steps)
        self.jump_groups = tuple(jump_groups)
        self.jumps = tuple(jumps)
        self.step_masks = tuple(step_masks)
        self.crowns = (15, 15 << 28)
        self.backs = (15 << 28, 15)

        advancement = (0, 2, 4, 7, 11, 17, 27, 0)
        self.man_ps = []
        self.progress = []
        self.cones = []
        self.near = []

        for side in (0, 1):
            ps = []
            progress_values = []
            cones = []
            near = 0
            dr = -1 if side == 0 else 1

            for i, (r, c) in enumerate(self.coords):
                progress = 7 - r if side == 0 else r
                progress_values.append(progress)

                value = advancement[progress] + 2 * min(c, 7 - c)
                if 2 <= r <= 5 and 2 <= c <= 5:
                    value += 4
                if progress == 0:
                    value += 8
                if c == 0 or c == 7:
                    value += 2
                ps.append(value)

                cone = 0
                for distance in range(1, 8 - progress):
                    rr = r + dr * distance
                    for cc in range(c - distance, c + distance + 1, 2):
                        if 0 <= cc < 8:
                            cone |= 1 << (4 * rr + cc // 2)
                cones.append(cone)

                if 4 <= progress <= 6:
                    near |= 1 << i

            self.man_ps.append(tuple(ps))
            self.progress.append(tuple(progress_values))
            self.cones.append(tuple(cones))
            self.near.append(near)

        self.king_ps = tuple(
            3 * (min(r, 7 - r) + min(c, 7 - c))
            for r, c in self.coords
        )
        self.man_tables = tuple(_byte_tables(v) for v in self.man_ps)
        self.king_tables = _byte_tables(self.king_ps)
        self.distance = tuple(
            tuple(max(abs(r - rr), abs(c - cc)) for rr, cc in self.coords)
            for r, c in self.coords
        )

    def reach(self, pieces, side):
        result = 0
        for mask, delta in self.steps[side]:
            if delta > 0:
                result |= (pieces & mask) << delta
            else:
                result |= (pieces & mask) >> -delta
        return result

    def capture_sources(self, position):
        men, kings, other_men, other_kings, side = position
        enemy = other_men | other_kings
        empty = FULL ^ (men | kings | enemy)
        result = 0

        for pieces, groups in (
            (men, self.jump_groups[side]),
            (kings, self.jump_groups[2]),
        ):
            for mask, middle_delta, end_delta in groups:
                sources = pieces & mask
                if middle_delta > 0:
                    sources &= enemy >> middle_delta
                    sources &= empty >> end_delta
                else:
                    sources &= enemy << -middle_delta
                    sources &= empty << -end_delta
                result |= sources

        return result

    def generate(self, position, captures_only=False, forced=-1):
        men, kings, other_men, other_kings, side = position
        starters = self.capture_sources(position)
        if forced >= 0:
            starters &= 1 << forced

        if starters:
            result = []
            crown = self.crowns[side]
            man_ps = self.man_ps[side]
            king_ps = self.king_ps
            jumps = self.jumps
            start_ps = 0

            def emit(a, b, x, y, square, is_king, action, gain):
                end_ps = king_ps[square] if is_king else man_ps[square]
                child = (x, y, a, b, side ^ 1)
                result.append((child, action, 20000 + gain + end_ps - start_ps))

            def walk(a, b, x, y, square, is_king, action, gain):
                enemy = x | y
                empty = ~(a | b | enemy)
                source_bit = 1 << square
                continued = False
                kind = 2 if is_king else side

                for middle, landing, destination in jumps[kind][square]:
                    if not (middle & enemy and landing & empty):
                        continue

                    continued = True
                    next_action = (
                        (square << 5) | destination if action < 0 else action
                    )
                    next_gain = gain + (175 if middle & y else 100)
                    xx, yy = x & ~middle, y & ~middle

                    if is_king:
                        walk(
                            a, (b ^ source_bit) | landing,
                            xx, yy, destination, True, next_action, next_gain
                        )
                    elif landing & crown:
                        # In English/American checkers, crowning ends the turn.
                        emit(
                            a ^ source_bit, b | landing,
                            xx, yy, destination, True, next_action,
                            next_gain + 80
                        )
                    else:
                        walk(
                            (a ^ source_bit) | landing, b,
                            xx, yy, destination, False, next_action, next_gain
                        )

                if not continued and action >= 0:
                    emit(a, b, x, y, square, is_king, action, gain)

            while starters:
                bit = starters & -starters
                starters ^= bit
                square = bit.bit_length() - 1
                is_king = bool(kings & bit)
                start_ps = king_ps[square] if is_king else man_ps[square]
                walk(
                    men, kings, other_men, other_kings,
                    square, is_king, -1, 0
                )

            # Different jump paths can reach the same resulting position.
            if len(result) > 1:
                unique = {}
                for entry in result:
                    if entry[0] not in unique:
                        unique[entry[0]] = entry
                result = list(unique.values())
            return result, True

        if captures_only or forced >= 0:
            return [], False

        result = []
        empty = FULL ^ (men | kings | other_men | other_kings)
        crown = self.crowns[side]

        for direction in (0, 1):
            eligible = kings | (men if direction == side else 0)
            for mask, delta in self.steps[direction]:
                sources = eligible & mask
                if delta > 0:
                    sources &= empty >> delta
                else:
                    sources &= empty << -delta

                while sources:
                    bit = sources & -sources
                    sources ^= bit
                    source = bit.bit_length() - 1
                    destination = source + delta
                    landing = 1 << destination
                    action = (source << 5) | destination

                    if kings & bit:
                        a, b = men, (kings ^ bit) | landing
                        order = self.king_ps[destination] - self.king_ps[source]
                    elif landing & crown:
                        a, b = men ^ bit, kings | landing
                        order = (
                            1200 + self.king_ps[destination]
                            - self.man_ps[side][source]
                        )
                    else:
                        a, b = (men ^ bit) | landing, kings
                        order = (
                            self.man_ps[side][destination]
                            - self.man_ps[side][source]
                        )

                    result.append(
                        ((other_men, other_kings, a, b, side ^ 1), action, order)
                    )

        return result, False


class _Engine:
    def __init__(self, geometry, table, deadline):
        self.g = geometry
        self.tt = table
        self.deadline = deadline
        self.nodes = 0
        self.path = set()
        self.history = [[0] * 1024 for _ in range(2)]
        self.killers = [[-1, -1] for _ in range(128)]

    def evaluate(self, position, ply=0, quiet=False):
        m, k, om, ok, side = position
        if not (m | k):
            return -WIN + ply
        if not (om | ok):
            return WIN - ply

        g = self.g
        opposite = side ^ 1
        own = m | k
        enemy = om | ok
        empty = FULL ^ (own | enemy)

        own_forward = g.reach(own, side)
        own_reach = own_forward | g.reach(k, opposite)
        own_mobility = (own_reach & empty).bit_count()
        if quiet and not own_mobility:
            return -WIN + ply

        enemy_forward = g.reach(enemy, opposite)
        enemy_reach = enemy_forward | g.reach(ok, side)
        enemy_mobility = (enemy_reach & empty).bit_count()

        nm, nk = m.bit_count(), k.bit_count()
        no, nok = om.bit_count(), ok.bit_count()
        total = nm + nk + no + nok
        phase = max(0, 24 - total)
        king_value = 175 + 2 * phase
        material = 100 * (nm - no) + king_value * (nk - nok)

        score = material
        exchange_bonus = abs(material) * phase // 160
        score += exchange_bonus if material >= 0 else -exchange_bonus

        score += _table_sum(m, g.man_tables[side])
        score -= _table_sum(om, g.man_tables[opposite])
        score += _table_sum(k, g.king_tables)
        score -= _table_sum(ok, g.king_tables)

        score += 3 * (own_mobility - enemy_mobility)
        score += 4 * (
            (m & own_forward).bit_count()
            - (om & enemy_forward).bit_count()
        )

        if total <= 10:
            score -= 6 * (
                (m & g.backs[side]).bit_count()
                - (om & g.backs[opposite]).bit_count()
            )

        for pieces, blockers, direction, sign in (
            (m, enemy, side, 1),
            (om, own, opposite, -1),
        ):
            candidates = pieces & g.near[direction]
            while candidates:
                bit = candidates & -candidates
                candidates ^= bit
                square = bit.bit_length() - 1
                if not (g.step_masks[direction][square] & empty):
                    score -= sign * 6
                elif not (g.cones[direction][square] & blockers):
                    score += sign * (
                        8 + 2 * g.progress[direction][square]
                    )

        # Encourage conversion rather than aimless king shuffling.
        if total <= 8 and abs(material) >= 70:
            if material > 0:
                hunters, targets, sign = k, enemy, 1
            else:
                hunters, targets, sign = ok, own, -1

            target_squares = []
            while targets:
                bit = targets & -targets
                targets ^= bit
                target_squares.append(bit.bit_length() - 1)

            while hunters:
                bit = hunters & -hunters
                hunters ^= bit
                square = bit.bit_length() - 1
                distance = min(g.distance[square][t] for t in target_squares)
                score += sign * 3 * (7 - distance)

        return score

    def search(self, position, depth, alpha, beta, ply):
        self.nodes += 1
        if (self.nodes & 127) == 0 and time.perf_counter() >= self.deadline:
            raise _Timeout

        if position in self.path:
            return 0

        m, k, om, ok, side = position
        if not (m | k):
            return -WIN + ply
        if not (om | ok):
            return WIN - ply

        original_alpha = alpha
        cached = self.tt.get(position)
        hash_move = -1

        if cached is not None:
            cached_depth, value, flag, hash_move = cached
            if value > WIN - 128:
                value -= ply
            elif value < -WIN + 128:
                value += ply

            if cached_depth >= depth:
                if flag == 0:
                    return value
                if flag == 1 and value >= beta:
                    return value
                if flag == 2 and value <= alpha:
                    return value

        moves, capturing = self.g.generate(position, captures_only=(depth <= 0))
        if not moves:
            if depth > 0:
                return -WIN + ply
            return self.evaluate(position, ply, quiet=True)

        killers = self.killers[ply]
        history = self.history[side]

        def ordering(entry):
            action = entry[1]
            return (
                entry[2]
                + (1000000 if action == hash_move else 0)
                + (8000 if action == killers[0] else 0)
                + (6000 if action == killers[1] else 0)
                + (history[action] if not capturing else 0)
            )

        if len(moves) > 1:
            moves.sort(key=ordering, reverse=True)

        next_depth = max(0, depth - 1)
        if capturing and len(moves) == 1 and depth > 0:
            next_depth = depth

        best_value = -INF
        best_action = moves[0][1]
        self.path.add(position)

        try:
            for index, (child, action, order) in enumerate(moves):
                if index == 0:
                    value = -self.search(
                        child, next_depth, -beta, -alpha, ply + 1
                    )
                else:
                    reduction = int(
                        depth >= 4
                        and index >= 4
                        and not capturing
                        and order < 1000
                        and action not in killers
                        and action != hash_move
                    )
                    value = -self.search(
                        child, max(0, next_depth - reduction),
                        -alpha - 1, -alpha, ply + 1
                    )
                    if reduction and value > alpha:
                        value = -self.search(
                            child, next_depth, -alpha - 1, -alpha, ply + 1
                        )
                    if alpha < value < beta:
                        value = -self.search(
                            child, next_depth, -beta, -alpha, ply + 1
                        )

                if value > best_value:
                    best_value = value
                    best_action = action

                if value > alpha:
                    alpha = value

                if alpha >= beta:
                    if not capturing:
                        history[action] = min(
                            4000, history[action] + depth * depth
                        )
                        if killers[0] != action:
                            killers[1] = killers[0]
                            killers[0] = action
                    break
        finally:
            self.path.remove(position)

        flag = (
            2 if best_value <= original_alpha
            else 1 if best_value >= beta
            else 0
        )
        stored_value = best_value
        if stored_value > WIN - 128:
            stored_value += ply
        elif stored_value < -WIN + 128:
            stored_value -= ply

        if cached is None or depth >= cached[0] or flag == 0:
            self.tt[position] = (depth, stored_value, flag, best_action)

        return best_value


def _remember_continuation(position, action, geometry, parity):
    """Recognize a subsequent call during an unfinished multi-jump."""
    global _FOLLOW
    _FOLLOW = None

    source, destination = action >> 5, action & 31
    sr, sc = geometry.coords[source]
    dr, dc = geometry.coords[destination]

    if abs(sr - dr) != 2:
        return

    m, k, om, ok, side = position
    source_bit = 1 << source
    landing = 1 << destination
    middle = 1 << (4 * ((sr + dr) // 2) + ((sc + dc) // 2) // 2)
    is_king = bool(k & source_bit)

    om &= ~middle
    ok &= ~middle
    if is_king:
        k = (k ^ source_bit) | landing
    else:
        m ^= source_bit
        if landing & geometry.crowns[side]:
            return
        m |= landing

    predicted = (m, k, om, ok, side)
    if geometry.capture_sources(predicted) & landing:
        _FOLLOW = (parity, predicted, destination)


def policy(my_men, my_kings, opp_men, opp_kings, color):
    start = time.perf_counter()
    deadline = start + 0.88

    first_square = None
    for group in (my_men, my_kings, opp_men, opp_kings):
        if len(group):
            first_square = group[0]
            break

    if first_square is None:
        raise ValueError("A terminal empty board has no legal move.")

    parity = (first_square[0] + first_square[1]) & 1
    geometry = _GEOMETRIES.get(parity)
    if geometry is None:
        geometry = _Geometry(parity)
        _GEOMETRIES[parity] = geometry

    side = 0 if color == "b" else 1
    position = (
        _bits(my_men), _bits(my_kings),
        _bits(opp_men), _bits(opp_kings), side
    )

    forced = -1
    if (
        _FOLLOW is not None
        and _FOLLOW[0] == parity
        and _FOLLOW[1] == position
    ):
        forced = _FOLLOW[2]

    root_moves, capturing = geometry.generate(position, forced=forced)
    if not root_moves and forced >= 0:
        root_moves, capturing = geometry.generate(position)

    if not root_moves:
        raise ValueError("No legal move exists in this terminal position.")

    def finish(action):
        _remember_continuation(position, action, geometry, parity)
        return (
            geometry.coords[action >> 5],
            geometry.coords[action & 31],
        )

    best_action = root_moves[0][1]
    if all(entry[1] == best_action for entry in root_moves):
        return finish(best_action)

    table = _TABLES.setdefault(parity, {})
    if len(table) > 80000:
        table.clear()

    engine = _Engine(geometry, table, deadline)
    cached = table.get(position)
    hash_move = cached[3] if cached is not None else -1

    root_moves.sort(
        key=lambda entry: (
            entry[1] == hash_move,
            -engine.evaluate(entry[0], 1),
            entry[2],
        ),
        reverse=True,
    )
    best_action = root_moves[0][1]
    engine.path.add(position)

    try:
        for depth in range(1, 65):
            if time.perf_counter() >= deadline:
                break

            alpha = -INF
            iteration_best = root_moves[0][1]
            scored = []

            for index, entry in enumerate(root_moves):
                if time.perf_counter() >= deadline:
                    raise _Timeout

                child, action, order = entry
                if index == 0:
                    value = -engine.search(
                        child, depth - 1, -INF, INF, 1
                    )
                else:
                    value = -engine.search(
                        child, depth - 1, -alpha - 1, -alpha, 1
                    )
                    if value > alpha:
                        value = -engine.search(
                            child, depth - 1, -INF, -alpha, 1
                        )

                scored.append((value, entry))
                if value > alpha:
                    alpha = value
                    iteration_best = action

            # Only commit a result after the whole iteration completes.
            best_action = iteration_best
            table[position] = (depth, alpha, 0, best_action)
            scored.sort(key=lambda item: item[0], reverse=True)
            root_moves = [entry for value, entry in scored]

            if abs(alpha) >= WIN - 100:
                break

    except _Timeout:
        pass

    return finish(best_action)
