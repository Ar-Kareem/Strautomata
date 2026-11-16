
import time
import math

N = 6
FULL = (1 << 36) - 1
BITS = tuple(1 << i for i in range(36))
LEFT = sum(BITS[r * 6] for r in range(6))
RIGHT = sum(BITS[r * 6 + 5] for r in range(6))
FREEDOM = tuple(math.sqrt(i) for i in range(37))
WIN = 100000.0
INF = 10000000.0


def _build_tables():
    attack_tables = []
    keep = [[-1] * 36 for _ in range(36)]

    for s in range(36):
        r, c = divmod(s, 6)
        entries = []

        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            rays = []
            for sign in (-1, 1):
                ray = []
                rr, cc = r + sign * dr, c + sign * dc
                while 0 <= rr < 6 and 0 <= cc < 6:
                    ray.append(rr * 6 + cc)
                    rr += sign * dr
                    cc += sign * dc
                rays.append(ray)

            squares = rays[0] + rays[1]
            mask = 0
            subsets = [0]
            for x in squares:
                bit = BITS[x]
                mask |= bit
                subsets += [v | bit for v in subsets]

            table = {}
            for occupied in subsets:
                attacks = 0
                for ray in rays:
                    for x in ray:
                        bit = BITS[x]
                        if occupied & bit:
                            break
                        attacks |= bit
                table[occupied] = attacks

            entries.extend((mask, table))

            for ray in rays:
                cut = 0
                for x in reversed(ray):
                    cut |= BITS[x]
                    keep[s][x] = ~cut

        attack_tables.append(tuple(entries))

    return tuple(attack_tables), tuple(tuple(row) for row in keep)


ATTACK_TABLES, KEEP = _build_tables()


def _attack(s, occupied):
    m0, t0, m1, t1, m2, t2, m3, t3 = ATTACK_TABLES[s]
    return (t0[occupied & m0] | t1[occupied & m1] |
            t2[occupied & m2] | t3[occupied & m3])


def _neighbors(x):
    horizontal = x | ((x & ~RIGHT) << 1) | ((x & ~LEFT) >> 1)
    return (horizontal | (horizontal << 6) | (horizontal >> 6)) & FULL


def _flood(seeds, allowed):
    reached = seeds
    while True:
        new = _neighbors(reached) & allowed
        if new == reached:
            return reached
        reached = new


def _indices(mask):
    result = []
    while mask:
        bit = mask & -mask
        mask ^= bit
        result.append(bit.bit_length() - 1)
    return result


def _format(move):
    f, t, a = move
    fr, fc = divmod(f, 6)
    tr, tc = divmod(t, 6)
    ar, ac = divmod(a, 6)
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


class _Timeout(Exception):
    pass


def policy(board) -> str:
    started = time.perf_counter()
    deadline = started + 0.89

    p = q = blocked = 0
    for r in range(6):
        for c in range(6):
            value = int(board[r][c])
            bit = BITS[r * 6 + c]
            if value == 1:
                p |= bit
            elif value == 2:
                q |= bit
            elif value != 0:
                blocked |= bit

    occupied = p | q | blocked
    fallback = None
    for f in _indices(p):
        destinations = _attack(f, occupied)
        if destinations:
            t = (destinations & -destinations).bit_length() - 1
            # Shooting back to the source is always legal.
            fallback = (f, t, f)
            break

    if fallback is None:
        # No legal action exists in a terminal position.
        return "0,0:0,0:0,0"

    def check():
        if time.perf_counter() >= deadline:
            raise _Timeout

    opponent_mobile = False
    for s in _indices(q):
        if _attack(s, occupied):
            opponent_mobile = True
            break
    if not opponent_mobile:
        return _format(fallback)

    empty = FULL ^ occupied
    own_region = _flood(p, FULL ^ blocked)

    # With no shared connected component, only survival length matters.
    if not (own_region & q):
        solo_empty = empty & own_region
        memo = {}
        best_move = [fallback]
        active_move = [fallback]
        longest = [-1]

        def record(length):
            if length > longest[0]:
                longest[0] = length
                best_move[0] = active_move[0]

        def survive(pieces, spaces, depth):
            check()
            record(depth)
            if not spaces:
                return 0

            key = (pieces, spaces)
            cached = memo.get(key)
            if cached is not None:
                record(depth + cached)
                return cached

            upper = spaces.bit_count()
            occ = FULL ^ spaces
            options = []

            for f in _indices(pieces):
                fb = BITS[f]
                destinations = _attack(f, occ)
                while destinations:
                    tb = destinations & -destinations
                    destinations ^= tb
                    t = tb.bit_length() - 1
                    np = (pieces ^ fb) | tb
                    interim = (spaces ^ tb) | fb
                    arrows = _attack(t, FULL ^ interim)

                    while arrows:
                        ab = arrows & -arrows
                        arrows ^= ab
                        a = ab.bit_length() - 1
                        ne = interim ^ ab
                        ne &= _flood(np, np | ne)
                        capacity = 1 + ne.bit_count()
                        arrow_degree = (
                            _neighbors(ab) & interim
                        ).bit_count() - 1
                        landing_degree = (
                            _neighbors(tb) & ne
                        ).bit_count()
                        priority = (
                            100 * capacity - 4 * arrow_degree
                            + landing_degree
                        )
                        options.append(
                            (priority, f, t, a, np, ne, capacity)
                        )
                    check()

            if not options:
                memo[key] = 0
                return 0

            options.sort(reverse=True)
            if depth == 0:
                best_move[0] = options[0][1:4]

            best = 0
            for _, f, t, a, np, ne, capacity in options:
                if capacity <= best:
                    continue
                if depth == 0:
                    active_move[0] = (f, t, a)
                value = 1 + survive(np, ne, depth + 1)
                if value > best:
                    best = value
                    record(depth + best)
                    if best == upper:
                        break

            memo[key] = best
            return best

        try:
            survive(p, solo_empty, 0)
        except _Timeout:
            pass
        return _format(best_move[0])

    eval_cache = {}
    order_cache = {}
    transposition = {}

    def evaluate(us, them, walls):
        key = (us, them, walls)
        cached = eval_cache.get(key)
        if cached is not None:
            return cached
        check()

        occ = us | them | walls
        free = FULL ^ occ
        ua = va = 0
        mobility = 0
        freedom = 0.0

        for s in _indices(us):
            attacks = _attack(s, occ)
            count = attacks.bit_count()
            ua |= attacks
            mobility += count
            freedom += FREEDOM[count]

        for s in _indices(them):
            attacks = _attack(s, occ)
            count = attacks.bit_count()
            va |= attacks
            mobility -= count
            freedom -= FREEDOM[count]

        if not ua:
            value = -WIN
        elif not va:
            value = WIN
        else:
            remaining_count = free.bit_count()

            # Evaluate separated positions in units of available moves.
            if remaining_count <= 16:
                region = _flood(us, FULL ^ walls)
                if not (region & them):
                    other_region = _flood(them, FULL ^ walls)
                    difference = (
                        (region & free).bit_count()
                        - (other_region & free).bit_count()
                    )
                    value = 20.0 * (difference - 0.5) + 0.02 * mobility
                    eval_cache[key] = value
                    return value

            queen_territory = ua.bit_count() - va.bit_count()
            queen_ties = (ua & va).bit_count()
            unclaimed = free & ~(ua | va)
            seen_u, seen_v = ua, va
            front_u, front_v = ua, va

            while unclaimed and (front_u or front_v):
                next_u = next_v = 0
                while front_u:
                    bit = front_u & -front_u
                    front_u ^= bit
                    next_u |= _attack(bit.bit_length() - 1, occ)
                while front_v:
                    bit = front_v & -front_v
                    front_v ^= bit
                    next_v |= _attack(bit.bit_length() - 1, occ)

                next_u &= ~seen_u
                next_v &= ~seen_v
                reached_u = next_u & unclaimed
                reached_v = next_v & unclaimed
                queen_territory += (
                    reached_u.bit_count() - reached_v.bit_count()
                )
                queen_ties += (reached_u & reached_v).bit_count()
                unclaimed &= ~(next_u | next_v)
                seen_u |= next_u
                seen_v |= next_v
                front_u, front_v = next_u, next_v

            front_u = _neighbors(us) & free
            front_v = _neighbors(them) & free
            king_territory = front_u.bit_count() - front_v.bit_count()
            seen_u, seen_v = front_u, front_v
            unclaimed = free & ~(front_u | front_v)

            while unclaimed and (front_u or front_v):
                front_u = _neighbors(front_u) & free & ~seen_u
                front_v = _neighbors(front_v) & free & ~seen_v
                king_territory += (
                    (front_u & unclaimed).bit_count()
                    - (front_v & unclaimed).bit_count()
                )
                unclaimed &= ~(front_u | front_v)
                seen_u |= front_u
                seen_v |= front_v

            phase = remaining_count / 36.0
            value = (
                (2.0 + 0.8 * phase) * queen_territory
                + (1.8 - 0.8 * phase) * king_territory
                + 0.11 * mobility
                + 0.50 * freedom
                + 0.16 * (ua.bit_count() - va.bit_count())
                + 0.08 * queen_ties
                - 1.0
            )

        eval_cache[key] = value
        return value

    def generate(us, them, walls):
        """Generate every legal move with inexpensive exact mobility scores."""
        occ = us | them | walls
        ours = _indices(us)
        theirs = _indices(them)
        moves = []

        for f in ours:
            fb = BITS[f]
            destinations = _attack(f, occ)
            stationary = [s for s in ours if s != f]

            while destinations:
                tb = destinations & -destinations
                destinations ^= tb
                t = tb.bit_length() - 1
                interim_occ = (occ ^ fb) | tb

                our_attacks = [
                    (_attack(s, interim_occ), KEEP[s])
                    for s in stationary
                ]
                our_attacks.append((_attack(t, interim_occ), KEEP[t]))
                their_attacks = [
                    (_attack(s, interim_occ), KEEP[s])
                    for s in theirs
                ]
                arrows = _attack(t, interim_occ)

                while arrows:
                    ab = arrows & -arrows
                    arrows ^= ab
                    a = ab.bit_length() - 1
                    our_union = their_union = 0
                    mob = 0
                    freedom = 0.0

                    for attacks, keep in our_attacks:
                        surviving = attacks & keep[a]
                        count = surviving.bit_count()
                        our_union |= surviving
                        mob += count
                        freedom += FREEDOM[count]

                    for attacks, keep in their_attacks:
                        surviving = attacks & keep[a]
                        count = surviving.bit_count()
                        their_union |= surviving
                        mob -= count
                        freedom -= FREEDOM[count]

                    if not their_union:
                        score = WIN
                    elif not our_union:
                        score = -WIN
                    else:
                        score = (
                            2.0 * (
                                our_union.bit_count()
                                - their_union.bit_count()
                            )
                            + 0.13 * mob + 0.80 * freedom
                        )
                    moves.append((score, f, t, a))

                check()

        moves.sort(reverse=True)
        return moves

    def diverse(moves, limit, per_landing=3):
        if len(moves) <= limit:
            return moves
        selected = []
        deferred = []
        counts = {}
        for move in moves:
            landing = (move[1], move[2])
            count = counts.get(landing, 0)
            if count < per_landing:
                selected.append(move)
                counts[landing] = count + 1
                if len(selected) == limit:
                    return selected
            else:
                deferred.append(move)
        selected.extend(deferred[:limit - len(selected)])
        return selected

    def ordered(us, them, walls):
        key = (us, them, walls)
        cached = order_cache.get(key)
        if cached is not None:
            return cached

        candidates = generate(us, them, walls)
        spaces = 36 - (us | them | walls).bit_count()
        if spaces > 7:
            candidates = diverse(candidates, 24)

        ranked = []
        for _, f, t, a in candidates:
            np = (us ^ BITS[f]) | BITS[t]
            nb = walls | BITS[a]
            score = -evaluate(them, np, nb)
            ranked.append((score, f, t, a))
        ranked.sort(reverse=True)
        order_cache[key] = ranked
        return ranked

    def search(us, them, walls, depth, alpha, beta):
        check()
        key = (us, them, walls)
        original_alpha = alpha
        entry = transposition.get(key)
        preferred = None

        if entry is not None:
            old_depth, value, flag, preferred = entry
            if old_depth >= depth:
                if flag == 0:
                    return value
                if flag == 1 and value >= beta:
                    return value
                if flag == -1 and value <= alpha:
                    return value

        static = evaluate(us, them, walls)
        if depth == 0 or abs(static) >= WIN:
            return static

        moves = ordered(us, them, walls)
        if not moves:
            return -WIN

        if depth == 1:
            value = moves[0][0]
            transposition[key] = (depth, value, 0, moves[0][1:4])
            return value

        spaces = 36 - (us | them | walls).bit_count()
        if spaces <= 7:
            candidates = moves
        else:
            width = 8 if depth >= 4 else 10
            candidates = moves[:width]

        if preferred is not None:
            preferred_entry = None
            for move in moves:
                if move[1:4] == preferred:
                    preferred_entry = move
                    break
            if preferred_entry is not None:
                candidates = [preferred_entry] + [
                    move for move in candidates
                    if move[1:4] != preferred
                ]

        best = -INF
        best_action = candidates[0][1:4]

        for _, f, t, a in candidates:
            np = (us ^ BITS[f]) | BITS[t]
            nb = walls | BITS[a]
            value = -search(them, np, nb, depth - 1, -beta, -alpha)

            if value > best:
                best = value
                best_action = (f, t, a)
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        if best <= original_alpha:
            flag = -1
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        transposition[key] = (depth, best, flag, best_action)
        return best

    best_move = fallback

    try:
        initial = generate(p, q, blocked)
        root_scores = []
        root_best_score = -INF
        root_evaluation_deadline = started + 0.24

        for index, (_, f, t, a) in enumerate(initial):
            np = (p ^ BITS[f]) | BITS[t]
            nb = blocked | BITS[a]
            score = -evaluate(q, np, nb)
            root_scores.append((score, f, t, a))

            if score > root_best_score:
                root_best_score = score
                best_move = (f, t, a)
            if score >= WIN:
                return _format(best_move)

            if (index >= 95 and
                    time.perf_counter() >= root_evaluation_deadline):
                break

        root_scores.sort(reverse=True)
        spaces = empty.bit_count()
        if spaces > 7:
            roots = diverse(root_scores, 28)
        else:
            roots = root_scores

        for depth in range(2, min(spaces + 1, 16)):
            check()
            roots.sort(
                key=lambda move: (
                    move[1:4] == best_move, move[0]
                ),
                reverse=True
            )
            alpha = -INF
            iteration_best = best_move
            completed_scores = []

            for _, f, t, a in roots:
                np = (p ^ BITS[f]) | BITS[t]
                nb = blocked | BITS[a]
                value = -search(q, np, nb, depth - 1, -INF, -alpha)
                completed_scores.append((value, f, t, a))

                if value > alpha:
                    alpha = value
                    iteration_best = (f, t, a)
                    # The previous principal move is searched first, so
                    # completed partial iterations also give a useful move.
                    best_move = iteration_best

                if value >= WIN:
                    return _format(iteration_best)

            completed_scores.sort(reverse=True)
            roots = completed_scores
            best_move = iteration_best

            if abs(alpha) >= WIN:
                break

    except _Timeout:
        pass

    return _format(best_move)
