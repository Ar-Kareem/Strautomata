
import time
import heapq
from functools import lru_cache


N = 6
SQ = 36
ALL = (1 << SQ) - 1
INF = 10 ** 9
MATE = 10 ** 7

_DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),             (0, 1),
    (1, -1),  (1, 0),    (1, 1),
)

RAYS = []
KING = []
CENTER = []

for r in range(N):
    for c in range(N):
        rays = []
        kmask = 0
        for dr, dc in _DIRS:
            ray = []
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                kmask |= 1 << (rr * N + cc)
            while 0 <= rr < N and 0 <= cc < N:
                ray.append(rr * N + cc)
                rr += dr
                cc += dc
            rays.append(tuple(ray))
        RAYS.append(tuple(rays))
        KING.append(kmask)

        # Higher near the center; used only as a small tie-breaker.
        CENTER.append(10 - abs(2 * r - 5) - abs(2 * c - 5))

RAYS = tuple(RAYS)
KING = tuple(KING)
CENTER = tuple(CENTER)


class _SearchTimeout(Exception):
    pass


def _bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


@lru_cache(maxsize=80000)
def _reach(square, occupied):
    """Bit mask of all queen-reachable empty squares."""
    result = 0
    for ray in RAYS[square]:
        for target in ray:
            bit = 1 << target
            if occupied & bit:
                break
            result |= bit
    return result


def _mobility_data(pieces, occupied):
    total = 0
    union = 0
    active = 0
    quality = 0

    for square in _bits(pieces):
        moves = _reach(square, occupied)
        count = moves.bit_count()
        total += count
        union |= moves
        if count:
            active += 1
        # Rewards both raw mobility and avoiding nearly trapped amazons.
        quality += count + 2 * min(count, 8)

    return total, union, active, quality


def _has_move(pieces, occupied):
    for square in _bits(pieces):
        if _reach(square, occupied):
            return True
    return False


def _queen_distances(sources, occupied):
    unreachable = 99
    dist = [unreachable] * SQ
    frontier = sources
    seen = sources
    depth = 0

    for square in _bits(sources):
        dist[square] = 0

    while frontier:
        nxt = 0
        f = frontier
        while f:
            bit = f & -f
            square = bit.bit_length() - 1
            f ^= bit
            nxt |= _reach(square, occupied)

        nxt &= ~seen
        nxt &= ALL
        if not nxt:
            break

        depth += 1
        for square in _bits(nxt):
            dist[square] = depth

        seen |= nxt
        frontier = nxt

    return dist


def _king_distances(sources, occupied):
    unreachable = 99
    dist = [unreachable] * SQ
    frontier = sources
    seen = sources
    free = ALL & ~occupied
    depth = 0

    for square in _bits(sources):
        dist[square] = 0

    while frontier:
        nxt = 0
        f = frontier
        while f:
            bit = f & -f
            square = bit.bit_length() - 1
            f ^= bit
            nxt |= KING[square]

        nxt &= free
        nxt &= ~seen
        if not nxt:
            break

        depth += 1
        for square in _bits(nxt):
            dist[square] = depth

        seen |= nxt
        frontier = nxt

    return dist


@lru_cache(maxsize=30000)
def _quick_abs(p1, p2, arrows):
    """Cheap ordering evaluation, positive for player 1."""
    occupied = p1 | p2 | arrows
    m1, u1, a1, q1 = _mobility_data(p1, occupied)
    m2, u2, a2, q2 = _mobility_data(p2, occupied)

    direct_control = (
        (u1 & ~u2).bit_count() -
        (u2 & ~u1).bit_count()
    )

    center_score = 0
    for square in _bits(p1):
        center_score += CENTER[square]
    for square in _bits(p2):
        center_score -= CENTER[square]

    return (
        12 * (q1 - q2)
        + 16 * direct_control
        + 30 * (a1 - a2)
        + 2 * center_score
        + 2 * (m1 - m2)
    )


@lru_cache(maxsize=20000)
def _rich_abs(p1, p2, arrows):
    """Territory and mobility evaluation, positive for player 1."""
    occupied = p1 | p2 | arrows
    empty = ALL & ~occupied

    qd1 = _queen_distances(p1, occupied)
    qd2 = _queen_distances(p2, occupied)
    kd1 = _king_distances(p1, occupied)
    kd2 = _king_distances(p2, occupied)

    queen_control = 0
    king_control = 0
    potential = 0

    e = empty
    while e:
        bit = e & -e
        square = bit.bit_length() - 1
        e ^= bit

        d1 = qd1[square]
        d2 = qd2[square]

        if d1 < d2:
            queen_control += 3 if d2 == 99 else 1
        elif d2 < d1:
            queen_control -= 3 if d1 == 99 else 1

        k1 = kd1[square]
        k2 = kd2[square]
        if k1 < k2:
            king_control += 1
        elif k2 < k1:
            king_control -= 1

        if d1 != 99:
            potential += 20 // (d1 + 1)
        if d2 != 99:
            potential -= 20 // (d2 + 1)

    m1, u1, a1, qual1 = _mobility_data(p1, occupied)
    m2, u2, a2, qual2 = _mobility_data(p2, occupied)

    direct_control = (
        (u1 & ~u2).bit_count() -
        (u2 & ~u1).bit_count()
    )

    center_score = 0
    for square in _bits(p1):
        center_score += CENTER[square]
    for square in _bits(p2):
        center_score -= CENTER[square]

    return (
        90 * queen_control
        + 22 * king_control
        + 3 * potential
        + 7 * (qual1 - qual2)
        + 8 * (m1 - m2)
        + 28 * (a1 - a2)
        + 4 * direct_control
        + 2 * center_score
    )


def _children(p1, p2, arrows, side):
    occupied = p1 | p2 | arrows
    pieces = p1 if side == 1 else p2

    for origin in _bits(pieces):
        origin_bit = 1 << origin
        destinations = _reach(origin, occupied)

        while destinations:
            to_bit = destinations & -destinations
            to = to_bit.bit_length() - 1
            destinations ^= to_bit

            occupied_after_move = (occupied ^ origin_bit) | to_bit
            arrow_targets = _reach(to, occupied_after_move)

            if side == 1:
                np1 = (p1 ^ origin_bit) | to_bit
                np2 = p2
            else:
                np1 = p1
                np2 = (p2 ^ origin_bit) | to_bit

            while arrow_targets:
                arrow_bit = arrow_targets & -arrow_targets
                arrow = arrow_bit.bit_length() - 1
                arrow_targets ^= arrow_bit

                yield (
                    (origin, to, arrow),
                    np1,
                    np2,
                    arrows | arrow_bit,
                )


def _rank_children(p1, p2, arrows, side, limit, deadline):
    """Generate all moves but retain only the best ordering candidates."""
    heap = []
    serial = 0
    opponent = 2 if side == 1 else 1
    sign = 1 if side == 1 else -1

    for move, np1, np2, narrows in _children(p1, p2, arrows, side):
        serial += 1
        if (serial & 31) == 0 and time.perf_counter() >= deadline:
            raise _SearchTimeout

        occupied = np1 | np2 | narrows
        opponent_pieces = np2 if opponent == 2 else np1

        if not _has_move(opponent_pieces, occupied):
            score = MATE
        else:
            score = sign * _quick_abs(np1, np2, narrows)

        item = (score, serial, move, np1, np2, narrows)

        if len(heap) < limit:
            heapq.heappush(heap, item)
        elif item[:2] > heap[0][:2]:
            heapq.heapreplace(heap, item)

    heap.sort(reverse=True)
    return heap, serial


def _format_move(move):
    origin, to, arrow = move
    fr, fc = divmod(origin, N)
    tr, tc = divmod(to, N)
    ar, ac = divmod(arrow, N)
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def policy(board) -> str:
    start = time.perf_counter()
    deadline = start + 0.90

    p1 = 0
    p2 = 0
    arrows = 0

    for r in range(N):
        for c in range(N):
            value = int(board[r, c])
            bit = 1 << (r * N + c)
            if value == 1:
                p1 |= bit
            elif value == 2:
                p2 |= bit
            elif value == -1:
                arrows |= bit

    # Establish a legal fallback before doing any strategic work.
    generator = _children(p1, p2, arrows, 1)
    try:
        first = next(generator)
    except StopIteration:
        # The environment promises not to call policy in terminal states.
        return ""

    fallback_move = first[0]
    best_move = fallback_move

    try:
        # Rank a broad set of root moves with the cheap evaluator.
        root_keep = 280
        heap = []
        serial = 0
        total_root_moves = 0

        def add_root(child):
            nonlocal serial, total_root_moves
            move, np1, np2, narrows = child
            serial += 1
            total_root_moves += 1

            occupied = np1 | np2 | narrows
            if not _has_move(np2, occupied):
                score = MATE
            else:
                score = _quick_abs(np1, np2, narrows)

            item = (score, serial, move, np1, np2, narrows)
            if len(heap) < root_keep:
                heapq.heappush(heap, item)
            elif item[:2] > heap[0][:2]:
                heapq.heapreplace(heap, item)

        add_root(first)
        for child in generator:
            add_root(child)

        selected = sorted(heap, reverse=True)
        if selected:
            best_move = selected[0][2]

        # Any move that leaves the opponent immobile wins immediately.
        if selected and selected[0][0] >= MATE:
            return _format_move(selected[0][2])

        # More expensive territorial evaluation of the best quick candidates.
        empty_count = (ALL & ~(p1 | p2 | arrows)).bit_count()
        if total_root_moves <= 80 or empty_count <= 10:
            static_cap = min(len(selected), 260)
        else:
            static_cap = min(len(selected), 180)

        static_end = min(start + 0.34, deadline - 0.38)
        root_entries = []

        for i, item in enumerate(selected[:static_cap]):
            if i > 0 and time.perf_counter() >= static_end:
                break

            quick_score, _, move, np1, np2, narrows = item
            occupied = np1 | np2 | narrows

            if not _has_move(np2, occupied):
                rich_score = MATE - 1
            else:
                rich_score = _rich_abs(np1, np2, narrows)

            root_entries.append(
                (rich_score, quick_score, move, np1, np2, narrows)
            )

        if not root_entries:
            return _format_move(best_move)

        root_entries.sort(key=lambda x: (x[0], x[1]), reverse=True)
        best_move = root_entries[0][2]

        # Selective iterative deepening.
        if empty_count <= 9 and total_root_moves <= root_keep:
            configs = []
            max_depth = min(7, max(2, empty_count))
            for depth in range(2, max_depth + 1):
                configs.append(
                    (depth, len(root_entries), {d: 100000 for d in range(1, depth)})
                )
        elif total_root_moves <= 35:
            configs = [
                (2, len(root_entries), {1: 90}),
                (3, min(len(root_entries), 35), {2: 60, 1: 50}),
                (4, min(len(root_entries), 26), {3: 35, 2: 28, 1: 24}),
            ]
        else:
            configs = [
                (2, min(len(root_entries), 52), {1: 40}),
                (3, min(len(root_entries), 28), {2: 24, 1: 18}),
                (4, min(len(root_entries), 17), {3: 16, 2: 14, 1: 12}),
            ]

        preferred = best_move

        for depth, root_limit, limits in configs:
            if time.perf_counter() >= deadline - 0.07:
                break

            tt = {}

            def negamax(cp1, cp2, carrows, side, remaining,
                        alpha, beta, ply):
                if time.perf_counter() >= deadline:
                    raise _SearchTimeout

                occupied = cp1 | cp2 | carrows
                pieces = cp1 if side == 1 else cp2

                if not _has_move(pieces, occupied):
                    return -MATE + ply

                if remaining == 0:
                    value = _rich_abs(cp1, cp2, carrows)
                    return value if side == 1 else -value

                key = (cp1, cp2, carrows, side, remaining)
                cached = tt.get(key)
                if cached is not None:
                    return cached

                limit = limits.get(remaining, 100000)
                ranked, count = _rank_children(
                    cp1, cp2, carrows, side, limit, deadline
                )

                if count == 0:
                    return -MATE + ply

                best_value = -INF
                cutoff = False
                next_side = 2 if side == 1 else 1

                for _, _, _, np1, np2, narrows in ranked:
                    value = -negamax(
                        np1, np2, narrows, next_side,
                        remaining - 1, -beta, -alpha, ply + 1
                    )

                    if value > best_value:
                        best_value = value
                    if value > alpha:
                        alpha = value
                    if alpha >= beta:
                        cutoff = True
                        break

                # Only exact, fully searched nodes are cached.
                if not cutoff:
                    tt[key] = best_value

                return best_value

            ordered = root_entries[:root_limit]

            # Always retain the best result from the previous completed depth.
            preferred_entry = None
            for entry in root_entries:
                if entry[2] == preferred:
                    preferred_entry = entry
                    break

            if preferred_entry is not None:
                ordered = [e for e in ordered if e[2] != preferred]
                ordered.insert(0, preferred_entry)
                ordered = ordered[:root_limit]

            iteration_best_move = None
            iteration_best_value = -INF
            alpha = -INF

            try:
                for _, _, move, np1, np2, narrows in ordered:
                    if time.perf_counter() >= deadline:
                        raise _SearchTimeout

                    value = -negamax(
                        np1, np2, narrows, 2, depth - 1,
                        -INF, -alpha, 1
                    )

                    if value > iteration_best_value:
                        iteration_best_value = value
                        iteration_best_move = move
                    if value > alpha:
                        alpha = value

                if iteration_best_move is not None:
                    best_move = iteration_best_move
                    preferred = iteration_best_move

                    if iteration_best_value >= MATE - 100:
                        break

            except _SearchTimeout:
                break

    except Exception:
        # The legal fallback is retained if time pressure or any unexpected
        # condition interrupts strategic evaluation.
        pass

    return _format_move(best_move)
