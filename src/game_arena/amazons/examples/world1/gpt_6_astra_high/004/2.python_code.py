
import time
import heapq

N = 6
FULL = (1 << 36) - 1
NOT_LEFT = FULL ^ sum(1 << (6 * r) for r in range(6))
NOT_RIGHT = FULL ^ sum(1 << (6 * r + 5) for r in range(6))
WIN = 100000
INF = 10000000


def _build_attack_tables():
    result = []
    for s in range(36):
        r, c = divmod(s, 6)
        packed = []
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            rays = []
            for sign in (1, -1):
                ray = []
                rr, cc = r + sign * dr, c + sign * dc
                while 0 <= rr < 6 and 0 <= cc < 6:
                    ray.append(rr * 6 + cc)
                    rr += sign * dr
                    cc += sign * dc
                rays.append(ray)

            cells = rays[0] + rays[1]
            mask = sum(1 << x for x in cells)
            table = {}
            for subset in range(1 << len(cells)):
                occupied = 0
                for j, cell in enumerate(cells):
                    if subset & (1 << j):
                        occupied |= 1 << cell
                reachable = 0
                for ray in rays:
                    for cell in ray:
                        bit = 1 << cell
                        if occupied & bit:
                            break
                        reachable |= bit
                table[occupied] = reachable
            packed.extend((mask, table))
        result.append(tuple(packed))
    return result


LINES = _build_attack_tables()


def _attacks(square, occupied):
    a, ta, b, tb, c, tc, d, td = LINES[square]
    return (
        ta[occupied & a]
        | tb[occupied & b]
        | tc[occupied & c]
        | td[occupied & d]
    )


def _neighbors(bits):
    horizontal = (
        bits | ((bits & NOT_LEFT) >> 1) | ((bits & NOT_RIGHT) << 1)
    )
    return (horizontal | (horizontal << 6) | (horizontal >> 6)) & FULL


def _flood(seeds, allowed):
    reached = seeds
    while True:
        expanded = reached | (_neighbors(reached) & allowed)
        if expanded == reached:
            return reached
        reached = expanded


def _format_move(move):
    f, t, a = move
    return (
        f"{f // 6},{f % 6}:"
        f"{t // 6},{t % 6}:"
        f"{a // 6},{a % 6}"
    )


class _Timeout(Exception):
    pass


def _solo_plan(pieces, empty, deadline):
    """Try to attain the absolute survival upper bound, shooting backwards."""
    failed = set()
    path = []
    nodes = 0

    def dfs(men, free):
        nonlocal nodes
        nodes += 1
        if (nodes & 31) == 0 and time.perf_counter() >= deadline:
            raise _Timeout
        if not free:
            return True

        key = (men, free)
        if key in failed:
            return False
        if (_flood(men, free) & free) != free:
            failed.add(key)
            return False

        occupied = FULL ^ free
        choices = []
        remaining = men
        while remaining:
            fb = remaining & -remaining
            remaining ^= fb
            f = fb.bit_length() - 1
            destinations = _attacks(f, occupied)
            while destinations:
                tb = destinations & -destinations
                destinations ^= tb
                t = tb.bit_length() - 1
                new_free = free ^ tb
                new_men = men ^ fb ^ tb
                degree = _attacks(t, FULL ^ new_free).bit_count()
                choices.append((degree, f, t, new_men, new_free))

        # A Warnsdorff-style ordering is effective for filling small chambers.
        choices.sort()
        for _, f, t, new_men, new_free in choices:
            path.append((f, t, f))
            if dfs(new_men, new_free):
                return True
            path.pop()

        failed.add(key)
        return False

    try:
        if dfs(pieces, empty):
            return path[0] if path else None
    except _Timeout:
        pass
    return None


class _Engine:
    def __init__(self, me, opponent, walls, deadline):
        self.deadline = deadline
        self.root = (me, opponent, walls)
        blocked = walls.bit_count()
        self.king_weight = 8 + blocked // 3
        self.queen_weight = 12 - blocked // 5
        self.ranks = {}
        self.pv = {}
        self.tt = {}
        self.emergency = None
        self.emergency_score = -INF

    def check(self):
        if time.perf_counter() >= self.deadline:
            raise _Timeout

    def quick_evaluation(self, me, opponent, walls):
        occupied = me | opponent | walls
        empty = FULL ^ occupied

        union_me = union_opp = 0
        mobility_me = mobility_opp = 0

        pieces = me
        while pieces:
            bit = pieces & -pieces
            pieces ^= bit
            moves = _attacks(bit.bit_length() - 1, occupied)
            union_me |= moves
            mobility_me += moves.bit_count()

        pieces = opponent
        while pieces:
            bit = pieces & -pieces
            pieces ^= bit
            moves = _attacks(bit.bit_length() - 1, occupied)
            union_opp |= moves
            mobility_opp += moves.bit_count()

        # This position is evaluated immediately after "me" has moved.
        if not union_opp:
            return WIN, union_me, union_opp

        front_me, front_opp = me, opponent
        seen_me, seen_opp = me, opponent
        unclaimed = empty
        territory = 0

        while front_me or front_opp:
            front_me = (
                _neighbors(front_me) & empty & ~seen_me
                if front_me else 0
            )
            front_opp = (
                _neighbors(front_opp) & empty & ~seen_opp
                if front_opp else 0
            )
            territory += (
                (front_me & ~front_opp & unclaimed).bit_count()
                - (front_opp & ~front_me & unclaimed).bit_count()
            )
            unclaimed &= ~(front_me | front_opp)
            seen_me |= front_me
            seen_opp |= front_opp

        reach_difference = (
            (seen_me & empty).bit_count()
            - (seen_opp & empty).bit_count()
        )
        queen_near = union_me.bit_count() - union_opp.bit_count()

        score = (
            self.king_weight * territory
            + 20 * reach_difference
            + self.queen_weight * queen_near
            + mobility_me - mobility_opp
        )

        if not union_me:
            score -= 2000

        # In independent equal-sized territories, the player moving next
        # exhausts their moves first.
        if not (seen_me & seen_opp & empty):
            score += self.king_weight // 2

        return score, union_me, union_opp

    def refine(self, row, opponent):
        score, f, t, a, me, walls, union_me, union_opp = row
        if score >= WIN:
            return row

        occupied = me | opponent | walls
        empty = FULL ^ occupied
        frontier_me, frontier_opp = union_me, union_opp
        seen_me, seen_opp = union_me, union_opp
        unclaimed = empty & ~(union_me | union_opp)
        near_difference = union_me.bit_count() - union_opp.bit_count()
        queen_territory = near_difference

        while unclaimed and (frontier_me or frontier_opp):
            new_me = new_opp = 0
            frontier = frontier_me
            while frontier:
                bit = frontier & -frontier
                frontier ^= bit
                new_me |= _attacks(bit.bit_length() - 1, occupied)

            frontier = frontier_opp
            while frontier:
                bit = frontier & -frontier
                frontier ^= bit
                new_opp |= _attacks(bit.bit_length() - 1, occupied)

            new_me &= empty & ~seen_me
            new_opp &= empty & ~seen_opp
            queen_territory += (
                (new_me & ~new_opp & unclaimed).bit_count()
                - (new_opp & ~new_me & unclaimed).bit_count()
            )
            unclaimed &= ~(new_me | new_opp)
            seen_me |= new_me
            seen_opp |= new_opp
            frontier_me, frontier_opp = new_me, new_opp

        score += self.queen_weight * (queen_territory - near_difference)
        return (score, f, t, a, me, walls, union_me, union_opp)

    def rank_moves(self, me, opponent, walls, cutoff=INF):
        self.check()
        key = (me, opponent, walls)
        is_root = key == self.root
        occupied = me | opponent | walls
        exact_small = (FULL ^ occupied).bit_count() <= 8
        rows = []
        count = 0
        pieces = me

        while pieces:
            fb = pieces & -pieces
            pieces ^= fb
            f = fb.bit_length() - 1
            destinations = _attacks(f, occupied)

            while destinations:
                tb = destinations & -destinations
                destinations ^= tb
                t = tb.bit_length() - 1
                new_me = me ^ fb ^ tb

                # The origin is vacant; the landing square is occupied.
                moved_occupied = (occupied ^ fb) | tb
                arrows = _attacks(t, moved_occupied)

                while arrows:
                    ab = arrows & -arrows
                    arrows ^= ab
                    a = ab.bit_length() - 1
                    new_walls = walls | ab
                    value, ma, mb = self.quick_evaluation(
                        new_me, opponent, new_walls
                    )
                    row = (value, f, t, a, new_me, new_walls, ma, mb)
                    rows.append(row)

                    if is_root and value > self.emergency_score:
                        self.emergency_score = value
                        self.emergency = (f, t, a)

                    count += 1
                    if (count & 31) == 0:
                        self.check()

                    # A verified leaf refutation need not examine more moves.
                    if cutoff < INF and value >= cutoff + self.queen_weight:
                        refined = self.refine(row, opponent)
                        if refined[0] >= cutoff:
                            return [refined], False

                    if value >= WIN:
                        return [row], True

        if not rows:
            return [], True

        if not exact_small:
            shortlist = 48 if is_root else 20
            if len(rows) > shortlist:
                rows = heapq.nlargest(shortlist, rows)

        refined = []
        for i, row in enumerate(rows):
            if (i & 15) == 0:
                self.check()
            refined.append(self.refine(row, opponent))
        refined.sort(reverse=True)

        if not exact_small:
            refined = refined[:18 if is_root else 8]
        return refined, True

    def search(self, me, opponent, walls, depth, alpha, beta):
        self.check()
        key = (me, opponent, walls)
        original_alpha, original_beta = alpha, beta

        if depth > 1:
            entry = self.tt.get(key)
            if entry is not None and entry[0] >= depth:
                _, value, bound = entry
                if bound == 0:
                    return value
                if bound == 1:
                    alpha = max(alpha, value)
                else:
                    beta = min(beta, value)
                if alpha >= beta:
                    return value

        rows = self.ranks.get(key)
        if rows is None:
            rows, complete = self.rank_moves(
                me, opponent, walls, beta if depth == 1 else INF
            )
            if complete:
                self.ranks[key] = rows

        if not rows:
            return -WIN

        if rows[0][0] >= WIN:
            self.pv[key] = rows[0][1:4]
            return WIN - 1

        if depth == 1:
            self.pv[key] = rows[0][1:4]
            return rows[0][0]

        preferred = self.pv.get(key)
        if preferred is not None:
            for i, row in enumerate(rows):
                if row[1:4] == preferred:
                    if i:
                        rows = [row] + rows[:i] + rows[i + 1:]
                    break

        empties = (FULL ^ (me | opponent | walls)).bit_count()
        if empties <= 8 or key == self.root:
            width = len(rows)
        else:
            width = 8 if depth == 2 else 6

        best_value = -INF
        best_move = rows[0][1:4]
        for row in rows[:width]:
            value = -self.search(
                opponent, row[4], row[5],
                depth - 1, -beta, -alpha
            )

            # Prefer faster wins and postpone forced losses.
            if value > WIN // 2:
                value -= 1
            elif value < -WIN // 2:
                value += 1

            if value > best_value:
                best_value = value
                best_move = row[1:4]
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        self.pv[key] = best_move
        if best_value <= original_alpha:
            bound = -1
        elif best_value >= original_beta:
            bound = 1
        else:
            bound = 0
        self.tt[key] = (depth, best_value, bound)
        return best_value


def policy(board) -> str:
    start = time.perf_counter()
    deadline = start + 0.90

    me = opponent = walls = 0
    for r in range(6):
        for c in range(6):
            value = int(board[r][c])
            bit = 1 << (6 * r + c)
            if value == 1:
                me |= bit
            elif value == 2:
                opponent |= bit
            elif value != 0:
                walls |= bit

    occupied = me | opponent | walls
    empty = FULL ^ occupied

    # Shooting back to the origin is always legal after a legal queen move.
    fallback = None
    pieces = me
    while pieces:
        bit = pieces & -pieces
        pieces ^= bit
        f = bit.bit_length() - 1
        destinations = _attacks(f, occupied)
        if destinations:
            t = (destinations & -destinations).bit_length() - 1
            fallback = (f, t, f)
            break

    if fallback is None:
        # No legal action exists in a terminal position. Keep the API robust;
        # the arena specifies that such positions will not be queried.
        f = (me & -me).bit_length() - 1 if me else 0
        return _format_move((f, f, f))

    # When components are truly disconnected, maximizing one's own lifespan
    # is optimal, irrespective of the opponent's choices.
    connected_to_me = _flood(me, FULL ^ walls)
    if not (connected_to_me & opponent):
        local_empty = connected_to_me & empty
        solo = _solo_plan(
            me, local_empty,
            min(deadline - 0.05, time.perf_counter() + 0.13)
        )
        if solo is not None:
            return _format_move(solo)

    engine = _Engine(me, opponent, walls, deadline)
    best_move = fallback
    initialized = False

    try:
        rows, _ = engine.rank_moves(me, opponent, walls)
        if rows:
            engine.ranks[engine.root] = rows
            best_move = rows[0][1:4]
            engine.pv[engine.root] = best_move
            initialized = True

            if rows[0][0] >= WIN:
                return _format_move(best_move)

            for depth in range(2, min(18, empty.bit_count() + 1) + 1):
                value = engine.search(
                    me, opponent, walls, depth, -INF, INF
                )
                best_move = engine.pv.get(engine.root, best_move)
                if value >= WIN - 36:
                    break
                if empty.bit_count() <= 8 and value <= -WIN + 36:
                    break

    except _Timeout:
        if not initialized and engine.emergency is not None:
            best_move = engine.emergency

    return _format_move(best_move)
