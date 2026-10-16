
import math
import time
import heapq

N = 6
FULL = (1 << 36) - 1
BITS = tuple(1 << i for i in range(36))
COL0 = sum(1 << (6 * r) for r in range(6))
COL5 = COL0 << 5
NOT_COL0 = FULL ^ COL0
NOT_COL5 = FULL ^ COL5
SQRT = tuple(math.sqrt(i) for i in range(37))
WIN = 100000.0
INF = 1000000000.0


def _near(x):
    h = ((x & NOT_COL0) >> 1) | ((x & NOT_COL5) << 1)
    z = x | h
    return (h | (z << 6) | (z >> 6)) & FULL


ADJ = tuple(_near(b) for b in BITS)


def _build_lines():
    result = []
    for square in range(36):
        r, c = divmod(square, 6)
        entry = []
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            rays = []
            mask = 0
            for sign in (1, -1):
                ray = []
                rr, cc = r + sign * dr, c + sign * dc
                while 0 <= rr < 6 and 0 <= cc < 6:
                    bit = BITS[6 * rr + cc]
                    ray.append(bit)
                    mask |= bit
                    rr += sign * dr
                    cc += sign * dc
                rays.append(ray)

            table = {}
            subset = mask
            while True:
                attacks = 0
                for ray in rays:
                    for bit in ray:
                        if subset & bit:
                            break
                        attacks |= bit
                table[subset] = attacks
                if subset == 0:
                    break
                subset = (subset - 1) & mask
            entry.extend((mask, table))
        result.append(tuple(entry))
    return tuple(result)


LINES = _build_lines()


def _moves(square, occupied):
    m0, t0, m1, t1, m2, t2, m3, t3 = LINES[square]
    return (t0[occupied & m0] | t1[occupied & m1] |
            t2[occupied & m2] | t3[occupied & m3])


def _flood(seeds, allowed):
    reached = seeds
    while True:
        enlarged = reached | (_near(reached) & allowed)
        if enlarged == reached:
            return reached
        reached = enlarged


def _king_race(p, o, empty):
    fa, fb = p, o
    seen_a, seen_b = p, o
    left = empty
    territory = ties = 0

    while left:
        fa = _near(fa) & empty & ~seen_a
        fb = _near(fb) & empty & ~seen_b
        if not (fa | fb):
            break
        seen_a |= fa
        seen_b |= fb

        a, b = fa & left, fb & left
        territory += (a & ~b).bit_count() - (b & ~a).bit_count()
        ties += (a & b).bit_count()
        left &= ~(fa | fb)

    return territory, ties


def _queen_race(p, o, occupied, empty, fa, fb):
    seen_a, seen_b = p | fa, o | fb
    left = empty
    territory = ties = 0

    while left and (fa | fb):
        a, b = fa & left, fb & left
        territory += (a & ~b).bit_count() - (b & ~a).bit_count()
        ties += (a & b).bit_count()
        left &= ~(fa | fb)
        if not left:
            break

        na = nb = 0
        x = fa
        while x:
            bit = x & -x
            x ^= bit
            na |= _moves(bit.bit_length() - 1, occupied)
        x = fb
        while x:
            bit = x & -x
            x ^= bit
            nb |= _moves(bit.bit_length() - 1, occupied)

        fa = na & ~seen_a
        fb = nb & ~seen_b
        seen_a |= fa
        seen_b |= fb

    return territory, ties


def _evaluate(p, o, occupied, empty, weights, precise, terminal):
    # This evaluates a position immediately after p has moved.
    if not (_near(o) & empty):
        return terminal

    qa = qb = 0
    ma = mb = 0.0
    la = lb = 0.0

    x = p
    while x:
        bit = x & -x
        x ^= bit
        square = bit.bit_length() - 1
        attacks = _moves(square, occupied)
        qa |= attacks
        ma += SQRT[attacks.bit_count()]
        la += SQRT[(ADJ[square] & empty).bit_count()]

    x = o
    while x:
        bit = x & -x
        x ^= bit
        square = bit.bit_length() - 1
        attacks = _moves(square, occupied)
        qb |= attacks
        mb += SQRT[attacks.bit_count()]
        lb += SQRT[(ADJ[square] & empty).bit_count()]

    if not qa:
        # Not a formal loss: an opponent move could release this player.
        return -120.0

    kt, kties = _king_race(p, o, empty)
    kw, qw, mw = weights
    value = kw * kt + mw * (ma - mb) + 0.16 * (la - lb)

    if precise:
        qt, qties = _queen_race(p, o, occupied, empty, qa, qb)
        value += qw * qt - 0.08 * (kw * kties + qw * qties)
    else:
        approximate_qt = qa.bit_count() - qb.bit_count() + 0.12 * kt
        value += qw * approximate_qt
        value -= 0.08 * kw * kties
        value -= 0.05 * qw * (qa & qb).bit_count()

    return value


def _encode(f, t, a):
    return f | (t << 6) | (a << 12)


def _format(move):
    f = move & 63
    t = (move >> 6) & 63
    a = (move >> 12) & 63
    return (
        f"{f // 6},{f % 6}:"
        f"{t // 6},{t % 6}:"
        f"{a // 6},{a % 6}"
    )


class _Timeout(Exception):
    pass


class _Engine:
    def __init__(self, deadline, fallback):
        self.deadline = deadline
        self.answer = fallback
        self.ranks = {}
        self.tt = {}

    def check(self):
        if time.perf_counter() >= self.deadline:
            raise _Timeout

    def rank(self, p, o, walls, root=False):
        self.check()
        key = (p, o, walls)
        cached = self.ranks.get(key)
        if cached is not None:
            return cached

        occupied = p | o | walls
        empty = FULL ^ occupied
        count = empty.bit_count()

        if not (_near(p) & empty):
            self.ranks[key] = []
            return []

        if count <= 10:
            keep = 100000
        elif root:
            keep = 80 if count < 18 else 64
        else:
            keep = 36 if count < 16 else 26

        openness = min(1.0, (count - 1) / 28.0)
        weights = (
            1.55 - 0.80 * openness,
            0.65 + 0.45 * openness,
            0.25 + 0.35 * openness,
        )
        terminal = WIN - walls.bit_count() - 1
        heap = []
        generated = 0
        best_fast = -INF

        pieces = p
        while pieces:
            fbit = pieces & -pieces
            pieces ^= fbit
            f = fbit.bit_length() - 1
            destinations = _moves(f, occupied)
            vacated = occupied ^ fbit

            while destinations:
                tbit = destinations & -destinations
                destinations ^= tbit
                t = tbit.bit_length() - 1
                new_p = p ^ fbit ^ tbit
                after_move = vacated | tbit
                arrows = _moves(t, after_move)

                while arrows:
                    abit = arrows & -arrows
                    arrows ^= abit
                    a = abit.bit_length() - 1
                    new_walls = walls | abit
                    new_occupied = after_move | abit
                    new_empty = FULL ^ new_occupied
                    move = _encode(f, t, a)

                    score = _evaluate(
                        new_p, o, new_occupied, new_empty,
                        weights, False, terminal
                    )

                    if root and score > best_fast:
                        best_fast = score
                        self.answer = move

                    item = (score, move, new_p, new_walls)
                    if score > WIN / 2:
                        result = [item]
                        self.ranks[key] = result
                        return result

                    if len(heap) < keep:
                        heapq.heappush(heap, item)
                    elif score >= heap[0][0]:
                        heapq.heappushpop(heap, item)

                    generated += 1
                    if generated & 31 == 0:
                        self.check()

        refined = []
        for i, (_, move, new_p, new_walls) in enumerate(heap):
            if i & 7 == 0:
                self.check()
            occ = new_p | o | new_walls
            score = _evaluate(
                new_p, o, occ, FULL ^ occ, weights, True, terminal
            )
            refined.append((score, move, new_p, new_walls))

        refined.sort(reverse=True)
        self.ranks[key] = refined
        return refined

    @staticmethod
    def width(empty_count):
        if empty_count <= 10:
            return 100000
        if empty_count < 14:
            return 16
        if empty_count < 20:
            return 10
        return 7

    def search(self, p, o, walls, depth, alpha, beta):
        self.check()
        key = (p, o, walls)
        original_alpha = alpha
        original_beta = beta
        entry = self.tt.get(key)
        preferred = None

        if entry is not None:
            old_depth, value, flag, preferred = entry
            if old_depth >= depth:
                if flag == 0:
                    return value
                if flag == 1:
                    alpha = max(alpha, value)
                else:
                    beta = min(beta, value)
                if alpha >= beta:
                    return value

        ranked = self.rank(p, o, walls)
        if not ranked:
            return -WIN + walls.bit_count()

        if ranked[0][0] > WIN / 2:
            value, move = ranked[0][:2]
            self.tt[key] = (100, value, 0, move)
            return value

        if depth <= 1:
            value, move = ranked[0][:2]
            self.tt[key] = (1, value, 0, move)
            return value

        count = 36 - (p | o | walls).bit_count()
        selected = ranked[:self.width(count)]

        if preferred is not None:
            for item in ranked:
                if item[1] == preferred:
                    selected = [item] + [
                        other for other in selected
                        if other[1] != preferred
                    ]
                    break

        best_value = -INF
        best_move = selected[0][1]

        for _, move, new_p, new_walls in selected:
            value = -self.search(
                o, new_p, new_walls, depth - 1, -beta, -alpha
            )
            if value > best_value:
                best_value, best_move = value, move
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        if best_value <= original_alpha:
            flag = 2
        elif best_value >= original_beta:
            flag = 1
        else:
            flag = 0
        self.tt[key] = (depth, best_value, flag, best_move)
        return best_value

    def competitive(self, p, o, walls):
        ranked = self.rank(p, o, walls, root=True)
        if not ranked:
            return
        self.answer = ranked[0][1]
        if ranked[0][0] > WIN / 2:
            return

        count = 36 - (p | o | walls).bit_count()
        root_width = 100000 if count <= 10 else (26 if count < 18 else 20)
        candidates = ranked[:root_width]

        for depth in range(2, count + 1):
            self.check()
            previous_best = self.answer
            candidates.sort(
                key=lambda item: (item[1] == previous_best, item[0]),
                reverse=True
            )

            alpha = -INF
            completed = []
            for item in candidates:
                _, move, new_p, new_walls = item
                value = -self.search(
                    o, new_p, new_walls, depth - 1, -INF, -alpha
                )
                completed.append((value, move, new_p, new_walls))

                if value > alpha:
                    alpha = value
                    # The previous iteration's best is searched first,
                    # so a partial iteration still gives a useful answer.
                    self.answer = move

                if alpha > WIN / 2:
                    return

            candidates = completed
            if alpha < -WIN / 2:
                return

    def solo(self, p, empty):
        """Maximize remaining moves in permanently uncontested regions."""
        memo = {}

        def solve(pieces, free, root=False):
            self.check()
            key = (pieces, free)
            known = memo.get(key)
            if known is not None:
                return known

            goal = free.bit_count()
            if not (_near(pieces) & free):
                memo[key] = 0
                return 0

            occupied = FULL ^ free
            choices = []
            duplicates = set()
            generated = 0
            root_order = None

            sources = pieces
            while sources:
                fbit = sources & -sources
                sources ^= fbit
                f = fbit.bit_length() - 1
                destinations = _moves(f, occupied)

                while destinations:
                    tbit = destinations & -destinations
                    destinations ^= tbit
                    t = tbit.bit_length() - 1
                    new_p = pieces ^ fbit ^ tbit
                    after_move = (occupied ^ fbit) | tbit
                    arrows = _moves(t, after_move)

                    while arrows:
                        abit = arrows & -arrows
                        arrows ^= abit
                        a = abit.bit_length() - 1

                        new_free = (free | fbit) & ~(tbit | abit)
                        reachable = _flood(new_p, new_p | new_free)
                        new_free &= reachable
                        state = (new_p, new_free)

                        generated += 1
                        if generated & 31 == 0:
                            self.check()
                        if state in duplicates:
                            continue
                        duplicates.add(state)

                        upper = 1 + new_free.bit_count()
                        degree = (ADJ[t] & new_free).bit_count()
                        move = _encode(f, t, a)
                        order = (upper, int(abit == fbit), -degree, move)
                        choices.append((order, move, new_p, new_free))

                        if root and (root_order is None or order > root_order):
                            root_order = order
                            self.answer = move

            choices.sort(reverse=True)
            best = 0

            for order, move, new_p, new_free in choices:
                if order[0] <= best:
                    continue
                value = 1 + solve(new_p, new_free)
                if value > best:
                    best = value
                    if root:
                        self.answer = move
                if best == goal:
                    break

            memo[key] = best
            return best

        solve(p, empty, root=True)


def policy(board) -> str:
    deadline = time.perf_counter() + 0.90

    p = o = walls = 0
    for r in range(6):
        for c in range(6):
            value = int(board[r][c])
            bit = BITS[6 * r + c]
            if value == 1:
                p |= bit
            elif value == 2:
                o |= bit
            elif value == -1:
                walls |= bit

    occupied = p | o | walls
    empty = FULL ^ occupied

    # Moving and shooting back to the source is always legal
    # whenever this queen move is legal.
    fallback = None
    sources = p
    while sources:
        fbit = sources & -sources
        sources ^= fbit
        f = fbit.bit_length() - 1
        targets = _moves(f, occupied)
        if targets:
            t = (targets & -targets).bit_length() - 1
            fallback = _encode(f, t, f)
            break

    if fallback is None:
        # No legal action exists in a terminal position.
        return "0,0:0,0:0,0"

    engine = _Engine(deadline, fallback)

    try:
        region = _flood(p, FULL ^ walls)
        if not (region & o):
            if _near(o) & empty:
                engine.solo(p, region & empty)
            # Otherwise the opponent is already immobile in a
            # separate region, and the fallback wins immediately.
        else:
            engine.competitive(p, o, walls)
    except _Timeout:
        pass

    return _format(engine.answer)
