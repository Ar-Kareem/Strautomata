
import math
import time

N = 36
FULL = (1 << N) - 1
BIT = tuple(1 << i for i in range(N))
NOT_LEFT = FULL ^ sum(BIT[6 * r] for r in range(6))
NOT_RIGHT = FULL ^ sum(BIT[6 * r + 5] for r in range(6))
MOBILITY = tuple(math.sqrt(i) for i in range(37))

MATE = 100000
INF = 1000000


def _expand(x):
    horizontal = ((x & NOT_LEFT) >> 1) | ((x & NOT_RIGHT) << 1)
    middle = x | horizontal
    return horizontal | (middle << 6) | (middle >> 6)


def _build_attack_tables():
    tables = []
    axes = ((0, 1), (1, 0), (1, 1), (1, -1))

    for square in range(36):
        r, c = divmod(square, 6)
        entry = []

        for dr, dc in axes:
            rays = []
            for sign in (1, -1):
                ray = []
                rr, cc = r + sign * dr, c + sign * dc
                while 0 <= rr < 6 and 0 <= cc < 6:
                    ray.append(rr * 6 + cc)
                    rr += sign * dr
                    cc += sign * dc
                rays.append(ray)

            squares = rays[0] + rays[1]
            mask = sum(BIT[s] for s in squares)
            lookup = {}

            for pattern in range(1 << len(squares)):
                occupied = 0
                for j, s in enumerate(squares):
                    if pattern & (1 << j):
                        occupied |= BIT[s]

                attacks = 0
                for ray in rays:
                    for s in ray:
                        if occupied & BIT[s]:
                            break
                        attacks |= BIT[s]

                lookup[occupied] = attacks

            entry.extend((mask, lookup))

        tables.append(tuple(entry))

    return tuple(tables)


LINES = _build_attack_tables()


def _attacks(square, occupied):
    m0, t0, m1, t1, m2, t2, m3, t3 = LINES[square]
    return (
        t0[occupied & m0]
        | t1[occupied & m1]
        | t2[occupied & m2]
        | t3[occupied & m3]
    )


def _flood(seeds, allowed):
    reached = seeds
    while True:
        enlarged = reached | (_expand(reached) & allowed)
        if enlarged == reached:
            return reached
        reached = enlarged


def _king_information(me, opponent, empty):
    seen_me, seen_op = me, opponent
    front_me, front_op = me, opponent
    territory = ties = 0

    while front_me or front_op:
        front_me = _expand(front_me) & empty & ~seen_me
        front_op = _expand(front_op) & empty & ~seen_op
        seen_me |= front_me
        seen_op |= front_op

        territory += (
            (front_me & ~seen_op).bit_count()
            - (front_op & ~seen_me).bit_count()
        )
        ties += (front_me & front_op).bit_count()

    return territory, ties, seen_me & empty, seen_op & empty


def _encode(source, destination, arrow):
    return (source << 12) | (destination << 6) | arrow


def _format_move(move):
    source = move >> 12
    destination = (move >> 6) & 63
    arrow = move & 63
    return (
        f"{source // 6},{source % 6}:"
        f"{destination // 6},{destination % 6}:"
        f"{arrow // 6},{arrow % 6}"
    )


def _first_legal(me, walls):
    occupied = me | walls
    pieces = me

    while pieces:
        source_bit = pieces & -pieces
        pieces -= source_bit
        source = source_bit.bit_length() - 1
        destinations = _attacks(source, occupied)

        if destinations:
            destination = (destinations & -destinations).bit_length() - 1
            # Shooting back to the vacated source is always legal.
            return _encode(source, destination, source)

    return None


def _diverse_take(items, limit):
    """Keep the strongest moves while allowing different destinations."""
    if len(items) <= limit:
        return items

    prefix = max(1, limit // 2)
    chosen = items[:prefix]
    used = {item[1] for item in chosen}
    destination_counts = {}

    for item in chosen:
        key = item[1] >> 6
        destination_counts[key] = destination_counts.get(key, 0) + 1

    for item in items[prefix:]:
        key = item[1] >> 6
        if destination_counts.get(key, 0) < 3:
            chosen.append(item)
            used.add(item[1])
            destination_counts[key] = destination_counts.get(key, 0) + 1
            if len(chosen) == limit:
                break

    if len(chosen) < limit:
        for item in items[prefix:]:
            if item[1] not in used:
                chosen.append(item)
                used.add(item[1])
                if len(chosen) == limit:
                    break

    chosen.sort(key=lambda item: item[0], reverse=True)
    return chosen


class _Timeout(Exception):
    pass


class _Engine:
    def __init__(self, deadline, fallback):
        self.deadline = deadline
        self.best_move = fallback
        self.ticks = 0
        self.evaluations = {}
        self.orders = {}
        self.transpositions = {}
        self.solo_cache = {}
        self.solo_longest = -1

    def _check(self):
        self.ticks += 1
        if (self.ticks & 31) == 0:
            if time.perf_counter() >= self.deadline:
                raise _Timeout

    def _quick(self, me, opponent, blocked):
        occupied = me | opponent | blocked
        empty = FULL ^ occupied
        count = empty.bit_count()

        if not (_expand(me) & empty):
            return -MATE - count
        if not (_expand(opponent) & empty):
            return MATE + count - 1

        territory, ties, reach_me, reach_op = _king_information(
            me, opponent, empty
        )
        exclusive = (
            (reach_me & ~reach_op).bit_count()
            - (reach_op & ~reach_me).bit_count()
        )

        union_me = union_op = 0
        mobility = 0.0

        pieces = me
        while pieces:
            b = pieces & -pieces
            pieces -= b
            attacks = _attacks(b.bit_length() - 1, occupied)
            union_me |= attacks
            mobility += MOBILITY[attacks.bit_count()]

        pieces = opponent
        while pieces:
            b = pieces & -pieces
            pieces -= b
            attacks = _attacks(b.bit_length() - 1, occupied)
            union_op |= attacks
            mobility -= MOBILITY[attacks.bit_count()]

        return (
            4.0 * territory
            + 9.0 * exclusive
            + 2.0 * (union_me.bit_count() - union_op.bit_count())
            + 0.7 * mobility
            + 0.25 * ties
            - 1.5
        )

    def _evaluate(self, me, opponent, blocked):
        key = (me, opponent, blocked)
        cached = self.evaluations.get(key)
        if cached is not None:
            return cached

        occupied = me | opponent | blocked
        empty = FULL ^ occupied
        count = empty.bit_count()

        if not (_expand(me) & empty):
            value = -MATE - count
            self.evaluations[key] = value
            return value

        if not (_expand(opponent) & empty):
            value = MATE + count - 1
            self.evaluations[key] = value
            return value

        king, king_ties, reach_me, reach_op = _king_information(
            me, opponent, empty
        )
        exclusive = (
            (reach_me & ~reach_op).bit_count()
            - (reach_op & ~reach_me).bit_count()
        )

        target_me = me | reach_me
        target_op = opponent | reach_op
        seen_me, seen_op = me, opponent
        front_me, front_op = me, opponent

        queen = queen_ties = 0
        proximity = mobility = 0.0
        weight = 0.5
        layer = 0

        while seen_me != target_me or seen_op != target_op:
            next_me = next_op = 0

            if seen_me != target_me:
                pieces = front_me
                while pieces:
                    b = pieces & -pieces
                    pieces -= b
                    attacks = _attacks(b.bit_length() - 1, occupied)
                    next_me |= attacks
                    if layer == 0:
                        mobility += MOBILITY[attacks.bit_count()]

            if seen_op != target_op:
                pieces = front_op
                while pieces:
                    b = pieces & -pieces
                    pieces -= b
                    attacks = _attacks(b.bit_length() - 1, occupied)
                    next_op |= attacks
                    if layer == 0:
                        mobility -= MOBILITY[attacks.bit_count()]

            next_me &= ~seen_me
            next_op &= ~seen_op
            seen_me |= next_me
            seen_op |= next_op

            queen += (
                (next_me & ~seen_op).bit_count()
                - (next_op & ~seen_me).bit_count()
            )
            queen_ties += (next_me & next_op).bit_count()
            proximity += weight * (
                next_me.bit_count() - next_op.bit_count()
            )

            front_me, front_op = next_me, next_op
            weight *= 0.5
            layer += 1

        queen_weight = 2.0 + count / 10.0
        king_weight = 7.5 - queen_weight

        value = (
            queen_weight * (queen + 0.12 * queen_ties)
            + king_weight * (king + 0.04 * king_ties)
            + 8.0 * exclusive
            + 2.0 * proximity
            + 0.65 * mobility
            - 1.5
        )

        self.evaluations[key] = value
        return value

    def _rank(self, me, opponent, blocked, root=False):
        key = (me, opponent, blocked)
        cached = self.orders.get(key)
        if cached is not None:
            return cached

        occupied = me | opponent | blocked
        remaining = (FULL ^ occupied).bit_count()
        exhaustive = remaining <= 9 or (root and remaining <= 11)
        evaluate_all = root or exhaustive
        width = 24 if root else (12 if remaining > 17 else 16)

        candidates = []
        root_best = -INF
        pieces = me

        while pieces:
            source_bit = pieces & -pieces
            pieces -= source_bit
            source = source_bit.bit_length() - 1
            destinations = _attacks(source, occupied)

            while destinations:
                destination_bit = destinations & -destinations
                destinations -= destination_bit
                destination = destination_bit.bit_length() - 1

                moved = me ^ source_bit ^ destination_bit
                moved_occupied = occupied ^ source_bit ^ destination_bit
                arrows = _attacks(destination, moved_occupied)

                while arrows:
                    arrow_bit = arrows & -arrows
                    arrows -= arrow_bit
                    arrow = arrow_bit.bit_length() - 1
                    new_blocked = blocked | arrow_bit
                    move = _encode(source, destination, arrow)

                    if evaluate_all:
                        score = -self._evaluate(
                            opponent, moved, new_blocked
                        )
                    else:
                        score = -self._quick(
                            opponent, moved, new_blocked
                        )

                    candidate = (score, move, moved, new_blocked)
                    candidates.append(candidate)

                    if root and score > root_best:
                        root_best = score
                        self.best_move = move

                    # This is a direct win: the opponent cannot move.
                    if score >= MATE:
                        result = [candidate]
                        self.orders[key] = result
                        return result

                    self._check()

        if not candidates:
            self.orders[key] = []
            return []

        candidates.sort(key=lambda item: item[0], reverse=True)

        if not evaluate_all:
            pool = _diverse_take(candidates, max(32, 2 * width + 8))
            candidates = []

            for _, move, moved, new_blocked in pool:
                score = -self._evaluate(opponent, moved, new_blocked)
                candidates.append((score, move, moved, new_blocked))
                self._check()

            candidates.sort(key=lambda item: item[0], reverse=True)

        if not exhaustive:
            candidates = _diverse_take(candidates, width)

        self.orders[key] = candidates
        return candidates

    def _search(self, me, opponent, blocked, depth, alpha, beta):
        self._check()
        key = (me, opponent, blocked)

        static = self._evaluate(me, opponent, blocked)
        if depth == 0 or abs(static) >= MATE:
            return static

        preferred = None
        entry = self.transpositions.get(key)

        if entry is not None:
            old_depth, flag, value, preferred = entry
            if old_depth >= depth:
                if flag == 0:
                    return value
                if flag == 1:
                    alpha = max(alpha, value)
                else:
                    beta = min(beta, value)
                if alpha >= beta:
                    return value

        original_alpha, original_beta = alpha, beta
        actions = self._rank(me, opponent, blocked)

        if not actions:
            return -MATE - (FULL ^ (me | opponent | blocked)).bit_count()

        if depth == 1:
            value, move = actions[0][0], actions[0][1]
            self.transpositions[key] = (depth, 0, value, move)
            return value

        if preferred is not None and actions[0][1] != preferred:
            for i, item in enumerate(actions):
                if item[1] == preferred:
                    actions = [item] + actions[:i] + actions[i + 1:]
                    break

        best = -INF
        best_move = actions[0][1]

        for _, move, moved, new_blocked in actions:
            value = -self._search(
                opponent, moved, new_blocked,
                depth - 1, -beta, -alpha
            )

            if value > best:
                best = value
                best_move = move
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        if best <= original_alpha:
            flag = -1
        elif best >= original_beta:
            flag = 1
        else:
            flag = 0

        self.transpositions[key] = (depth, flag, best, best_move)
        return best

    def play_connected(self, me, opponent, blocked):
        actions = self._rank(me, opponent, blocked, root=True)
        if not actions:
            return

        self.best_move = actions[0][1]
        if actions[0][0] >= MATE:
            return

        remaining = (FULL ^ (me | opponent | blocked)).bit_count()

        for depth in range(2, remaining + 1):
            if time.perf_counter() >= self.deadline:
                raise _Timeout

            alpha = -INF
            iteration_best = actions[0][1]
            scored = []

            # The previous iteration's winner is searched first.
            for item in actions:
                _, move, moved, new_blocked = item
                value = -self._search(
                    opponent, moved, new_blocked,
                    depth - 1, -INF, -alpha
                )
                scored.append((value, item))

                if value > alpha:
                    alpha = value
                    iteration_best = move
                    self.best_move = move

            self.best_move = iteration_best
            scored.sort(key=lambda pair: pair[0], reverse=True)
            actions = [item for _, item in scored]

            if remaining <= 9 and abs(alpha) >= MATE:
                return

            # Spend deeper-search time on the most promising root moves.
            if remaining > 12:
                limit = 18 if depth == 2 else 12
                actions = actions[:limit]

    def _record_solo(self, length, first_move):
        if first_move is not None and length > self.solo_longest:
            self.solo_longest = length
            self.best_move = first_move

    def _solo(self, me, walls, ply=0, first_move=None, upper=None):
        """Maximize our remaining moves when neither side can interact."""
        self._check()
        key = (me, walls)
        cached = self.solo_cache.get(key)

        if cached is not None:
            self._record_solo(ply + cached, first_move)
            return cached

        occupied = me | walls
        empty = FULL ^ occupied

        if not (_expand(me) & empty):
            self._record_solo(ply, first_move)
            self.solo_cache[key] = 0
            return 0

        if upper is None:
            upper = (_flood(me, FULL ^ walls) & ~me).bit_count()

        candidates = []
        pieces = me

        while pieces:
            source_bit = pieces & -pieces
            pieces -= source_bit
            source = source_bit.bit_length() - 1
            destinations = _attacks(source, occupied)

            while destinations:
                destination_bit = destinations & -destinations
                destinations -= destination_bit
                destination = destination_bit.bit_length() - 1
                moved = me ^ source_bit ^ destination_bit
                moved_occupied = occupied ^ source_bit ^ destination_bit
                arrows = _attacks(destination, moved_occupied)

                while arrows:
                    arrow_bit = arrows & -arrows
                    arrows -= arrow_bit
                    arrow = arrow_bit.bit_length() - 1
                    new_walls = walls | arrow_bit
                    new_empty = FULL ^ (moved | new_walls)

                    reachable = _flood(moved, FULL ^ new_walls) & ~moved
                    bound = reachable.bit_count()
                    freedom = (_expand(moved) & new_empty).bit_count()
                    mobility = _attacks(
                        destination, moved | new_walls
                    ).bit_count()

                    ordering = (
                        100.0 * bound
                        + freedom
                        + 0.02 * mobility
                        + (0.05 if arrow == source else 0.0)
                    )

                    candidates.append((
                        ordering,
                        _encode(source, destination, arrow),
                        moved,
                        new_walls,
                        bound,
                    ))
                    self._check()

        candidates.sort(key=lambda item: item[0], reverse=True)

        if ply == 0 and candidates:
            self.best_move = candidates[0][1]

        best = 0

        for _, move, moved, new_walls, bound in candidates:
            if 1 + bound <= best:
                continue

            initial_move = move if ply == 0 else first_move
            value = 1 + self._solo(
                moved, new_walls, ply + 1, initial_move, bound
            )
            self._record_solo(ply + value, initial_move)

            if value > best:
                best = value
            if best == upper:
                break

        self.solo_cache[key] = best
        return best


def policy(board) -> str:
    start = time.perf_counter()
    me = opponent = blocked = 0

    for r in range(6):
        for c in range(6):
            value = int(board[r][c])
            bit = BIT[6 * r + c]
            if value == 1:
                me |= bit
            elif value == 2:
                opponent |= bit
            elif value == -1:
                blocked |= bit

    fallback = _first_legal(me, opponent | blocked)

    # No legal string exists for a terminal position; avoid raising an
    # exception if the caller nevertheless supplies one.
    if fallback is None:
        return "0,0:0,0:0,0"

    empty = FULL ^ (me | opponent | blocked)

    # The fallback replaces its source with an arrow, so it cannot
    # release an already immobilized opponent.
    if not (_expand(opponent) & empty):
        return _format_move(fallback)

    engine = _Engine(start + 0.88, fallback)

    try:
        # Include amazons in connectivity: this separation test remains
        # valid even after either side vacates its current squares.
        connected_to_us = _flood(me, FULL ^ blocked)

        if not (connected_to_us & opponent):
            engine._solo(me, blocked | opponent)
        else:
            engine.play_connected(me, opponent, blocked)
    except _Timeout:
        pass

    return _format_move(engine.best_move)
