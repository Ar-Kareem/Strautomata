
import math
import time

N = 6
FULL = (1 << 36) - 1
COL0 = sum(1 << (6 * r) for r in range(6))
COL5 = COL0 << 5
NOT_LEFT = FULL ^ COL0
NOT_RIGHT = FULL ^ COL5
MATE = 100000
INF = 1000000
MOBILITY = tuple(int(4 * math.sqrt(i)) for i in range(37))


class _Timeout(Exception):
    pass


class _Solved(Exception):
    pass


def _build_attack_tables():
    tables = []
    for square in range(36):
        row, col = divmod(square, 6)
        description = []
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            arms = []
            for sign in (-1, 1):
                arm = []
                r, c = row + sign * dr, col + sign * dc
                while 0 <= r < 6 and 0 <= c < 6:
                    arm.append(1 << (6 * r + c))
                    r += sign * dr
                    c += sign * dc
                arms.append(arm)

            cells = arms[0] + arms[1]
            mask = 0
            for bit in cells:
                mask |= bit

            lookup = {}
            for subset in range(1 << len(cells)):
                occupied = 0
                for i, bit in enumerate(cells):
                    if subset & (1 << i):
                        occupied |= bit
                attacks = 0
                for arm in arms:
                    for bit in arm:
                        if occupied & bit:
                            break
                        attacks |= bit
                lookup[occupied] = attacks
            description.extend((mask, lookup))
        tables.append(tuple(description))
    return tuple(tables)


ATTACK_TABLES = _build_attack_tables()


def _queen(square, occupied, tables=ATTACK_TABLES):
    m0, t0, m1, t1, m2, t2, m3, t3 = tables[square]
    return (
        t0[occupied & m0]
        | t1[occupied & m1]
        | t2[occupied & m2]
        | t3[occupied & m3]
    )


def _spread(bits, nr=NOT_RIGHT, nl=NOT_LEFT, full=FULL):
    horizontal = bits | ((bits & nr) << 1) | ((bits & nl) >> 1)
    return (horizontal | (horizontal << 6) | (horizontal >> 6)) & full


def _flood(seeds, allowed):
    reached = seeds
    while True:
        enlarged = reached | (_spread(reached) & allowed)
        if enlarged == reached:
            return reached
        reached = enlarged


def _moves(p, q, blocked):
    """Yield (new_p, new_blocked, source_bit, destination_bit, arrow_bit)."""
    occupied = p | q | blocked
    pieces = p
    queen = _queen
    while pieces:
        source = pieces & -pieces
        pieces ^= source
        destinations = queen(source.bit_length() - 1, occupied)
        remaining_p = p ^ source
        vacated = occupied ^ source
        while destinations:
            destination = destinations & -destinations
            destinations ^= destination
            new_p = remaining_p | destination
            arrows = queen(
                destination.bit_length() - 1, vacated | destination
            )
            while arrows:
                arrow = arrows & -arrows
                arrows ^= arrow
                yield new_p, blocked | arrow, source, destination, arrow


def _format(move):
    source, destination, arrow = move
    fr, fc = divmod(source.bit_length() - 1, 6)
    tr, tc = divmod(destination.bit_length() - 1, 6)
    ar, ac = divmod(arrow.bit_length() - 1, 6)
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def _solitaire(p, q, blocked, deadline, fallback):
    """Find a long legal continuation in completely independent territory."""
    capacity_cache = {}
    visited = set()
    answer = fallback
    best_length = 0
    ticks = 0

    def capacity(pieces, arrows):
        nonlocal ticks
        ticks += 1
        if ticks & 63 == 0 and time.perf_counter() >= deadline:
            raise _Timeout
        key = (pieces, arrows)
        value = capacity_cache.get(key)
        if value is None:
            reachable = _flood(pieces, FULL ^ (arrows | q))
            value = (reachable & ~pieces).bit_count()
            capacity_cache[key] = value
        return value

    target = capacity(p, blocked)

    def visit(pieces, arrows, depth, first_move, upper):
        nonlocal answer, best_length
        if time.perf_counter() >= deadline:
            raise _Timeout

        if depth > best_length:
            best_length = depth
            answer = first_move
            if best_length == target:
                raise _Solved

        if depth + upper <= best_length:
            return

        key = (pieces, arrows)
        if key in visited:
            return
        visited.add(key)

        candidates = []
        for record in _moves(pieces, q, arrows):
            np, nb, source, destination, arrow = record
            if (np, nb) in visited:
                continue
            cap = capacity(np, nb)
            if depth + 1 + cap <= best_length:
                continue
            occupied = np | q | nb
            freedom = _queen(
                destination.bit_length() - 1, occupied
            ).bit_count()
            freedom += (_spread(np) & (FULL ^ occupied)).bit_count()
            candidates.append((cap, freedom, record))

        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        for cap, _, record in candidates:
            if depth + 1 + cap <= best_length:
                continue
            np, nb, source, destination, arrow = record
            initial = first_move
            if initial is None:
                initial = (source, destination, arrow)
            visit(np, nb, depth + 1, initial, cap)

    try:
        visit(p, blocked, 0, None, target)
    except (_Timeout, _Solved):
        pass
    return answer


def policy(board) -> str:
    start = time.perf_counter()
    deadline = start + 0.90

    p = q = blocked = 0
    for r in range(6):
        for c in range(6):
            value = int(board[r][c])
            bit = 1 << (6 * r + c)
            if value == 1:
                p |= bit
            elif value == 2:
                q |= bit
            elif value == -1:
                blocked |= bit

    occupied = p | q | blocked
    empty = FULL ^ occupied

    # Establish a legal answer before doing any expensive work.
    fallback = None
    pieces = p
    while pieces:
        source = pieces & -pieces
        pieces ^= source
        destinations = _queen(source.bit_length() - 1, occupied)
        if destinations:
            destination = destinations & -destinations
            # The reverse shot to the vacated source is always legal.
            fallback = (source, destination, source)
            break

    if fallback is None:
        # No legal move exists in this terminal case; the arena should not
        # request a move here. Still return a correctly formatted string.
        return "0,0:0,0:0,0"

    if not (_spread(q) & empty):
        return _format(fallback)

    # Connectivity here treats amazons as traversable and only arrows as
    # barriers, so this test cannot incorrectly declare a temporary blockade
    # to be a permanent separation.
    if not (_flood(p, FULL ^ blocked) & q):
        return _format(_solitaire(p, q, blocked, deadline, fallback))

    evaluation_cache = {}
    transpositions = {}
    ticks = 0
    answer = fallback

    def evaluate(mine, theirs, arrows):
        nonlocal ticks
        ticks += 1
        if ticks & 63 == 0 and time.perf_counter() >= deadline:
            raise _Timeout

        key = (mine, theirs, arrows)
        cached = evaluation_cache.get(key)
        if cached is not None:
            return cached

        occ = mine | theirs | arrows
        vacant = FULL ^ occ
        frontier1 = _spread(mine) & vacant
        frontier2 = _spread(theirs) & vacant

        if not frontier1:
            evaluation_cache[key] = -MATE
            return -MATE
        if not frontier2:
            # Move and shoot back to the source to preserve the blockade.
            evaluation_cache[key] = MATE
            return MATE

        queen1 = queen2 = 0
        mobility = 0
        pieces1 = mine
        while pieces1:
            bit = pieces1 & -pieces1
            pieces1 ^= bit
            attacks = _queen(bit.bit_length() - 1, occ)
            queen1 |= attacks
            mobility += MOBILITY[attacks.bit_count()]

        pieces2 = theirs
        while pieces2:
            bit = pieces2 & -pieces2
            pieces2 ^= bit
            attacks = _queen(bit.bit_length() - 1, occ)
            queen2 |= attacks
            mobility -= MOBILITY[attacks.bit_count()]

        seen1, seen2 = mine, theirs
        king_territory = 0
        proximity = 3 * (
            frontier1.bit_count() - frontier2.bit_count()
        )
        layer = 1

        while frontier1 or frontier2:
            king_territory += (
                frontier1 & ~(seen2 | frontier2)
            ).bit_count()
            king_territory -= (
                frontier2 & ~(seen1 | frontier1)
            ).bit_count()

            if layer == 2:
                proximity += (
                    frontier1.bit_count() - frontier2.bit_count()
                )

            seen1 |= frontier1
            seen2 |= frontier2
            frontier1 = _spread(frontier1) & vacant & ~seen1
            frontier2 = _spread(frontier2) & vacant & ~seen2
            layer += 1

        reachable1 = seen1 & vacant
        reachable2 = seen2 & vacant
        exclusive1 = reachable1 & ~reachable2
        exclusive2 = reachable2 & ~reachable1
        capacity_difference = (
            exclusive1.bit_count() - exclusive2.bit_count()
        )

        queen_territory = (
            (queen1 | exclusive1).bit_count()
            - (queen2 | exclusive2).bit_count()
        )

        # Resolve two-queen-move races using reverse visibility from the
        # relatively few squares not already reached in one move.
        unresolved = (
            reachable1 & reachable2 & ~(queen1 | queen2)
        )
        while unresolved:
            bit = unresolved & -unresolved
            unresolved ^= bit
            attacks = _queen(bit.bit_length() - 1, occ)
            queen_territory += bool(attacks & queen1) - bool(attacks & queen2)

        if vacant.bit_count() > 18:
            king_weight, queen_weight = 5, 5
        else:
            king_weight, queen_weight = 7, 3

        score = (
            king_weight * king_territory
            + queen_weight * queen_territory
            + 8 * capacity_difference
            + proximity
            + mobility
            - 1
        )
        evaluation_cache[key] = score
        return score

    def store(key, depth, value, original_alpha, beta, move):
        if value <= original_alpha:
            flag = -1
        elif value >= beta:
            flag = 1
        else:
            flag = 0
        transpositions[key] = (depth, value, flag, move)

    def search(mine, theirs, arrows, depth, alpha, beta):
        if time.perf_counter() >= deadline:
            raise _Timeout

        if depth <= 0:
            return evaluate(mine, theirs, arrows)

        vacant = FULL ^ (mine | theirs | arrows)
        if not (_spread(mine) & vacant):
            return -MATE
        if not (_spread(theirs) & vacant):
            return MATE

        key = (mine, theirs, arrows)
        original_alpha = alpha
        entry = transpositions.get(key)
        preferred = None

        if entry is not None:
            old_depth, old_value, flag, preferred = entry
            if old_depth >= depth:
                if flag == 0:
                    return old_value
                if flag == 1:
                    alpha = max(alpha, old_value)
                else:
                    beta = min(beta, old_value)
                if alpha >= beta:
                    return old_value

        best = -INF
        best_move = None

        def same_as_preferred(record):
            return (
                preferred is not None
                and record[0] == preferred[0]
                and record[1] == preferred[1]
            )

        if preferred is not None:
            np, nb = preferred[0], preferred[1]
            if depth == 1:
                value = -evaluate(theirs, np, nb)
            else:
                value = -search(
                    theirs, np, nb, depth - 1, -beta, -alpha
                )
            best, best_move = value, preferred
            alpha = max(alpha, value)
            if alpha >= beta or best == MATE:
                store(key, depth, best, original_alpha, beta, best_move)
                return best

        if depth == 1:
            # Full-width final ply, with alpha-beta cutoffs.
            for record in _moves(mine, theirs, arrows):
                if same_as_preferred(record):
                    continue
                np, nb = record[0], record[1]
                value = -evaluate(theirs, np, nb)
                if value > best:
                    best, best_move = value, record
                alpha = max(alpha, value)
                if alpha >= beta or best == MATE:
                    break
            store(key, depth, best, original_alpha, beta, best_move)
            return best

        ordered = []
        for record in _moves(mine, theirs, arrows):
            if same_as_preferred(record):
                continue
            np, nb = record[0], record[1]
            value = -evaluate(theirs, np, nb)
            if value == MATE:
                store(key, depth, MATE, original_alpha, beta, record)
                return MATE
            ordered.append((value, record))

        ordered.sort(key=lambda item: item[0], reverse=True)

        remaining = vacant.bit_count()
        if remaining <= 8:
            width = len(ordered)
        elif remaining <= 10:
            width = 20
        elif remaining <= 16:
            width = 12
        else:
            width = 8

        if preferred is not None and remaining > 8:
            width = max(0, width - 1)

        for _, record in ordered[:width]:
            np, nb = record[0], record[1]
            value = -search(
                theirs, np, nb, depth - 1, -beta, -alpha
            )
            if value > best:
                best, best_move = value, record
            alpha = max(alpha, value)
            if alpha >= beta or best == MATE:
                break

        store(key, depth, best, original_alpha, beta, best_move)
        return best

    try:
        ranked = []
        best_static = -INF
        for record in _moves(p, q, blocked):
            np, nb, source, destination, arrow = record
            value = -evaluate(q, np, nb)
            ranked.append((value, record))
            if value > best_static:
                best_static = value
                answer = (source, destination, arrow)
            if value == MATE:
                return _format(answer)

        ranked.sort(key=lambda item: item[0], reverse=True)
        empty_count = empty.bit_count()

        # Preserve some different landing squares rather than selecting
        # only near-identical arrow variations.
        if empty_count > 8:
            limit = 24 if empty_count > 18 else 32
            base = max(1, limit - 8)
            selected = ranked[:base]
            selected_states = {
                (item[1][0], item[1][1]) for item in selected
            }
            destinations = {
                (item[1][2], item[1][3]) for item in selected
            }

            for item in ranked[base:]:
                if len(selected) >= limit:
                    break
                record = item[1]
                destination_key = (record[2], record[3])
                if destination_key not in destinations:
                    selected.append(item)
                    destinations.add(destination_key)
                    selected_states.add((record[0], record[1]))

            if len(selected) < limit:
                for item in ranked[base:]:
                    if len(selected) >= limit:
                        break
                    record = item[1]
                    state = (record[0], record[1])
                    if state not in selected_states:
                        selected.append(item)
                        selected_states.add(state)

            selected.sort(key=lambda item: item[0], reverse=True)
            ranked = selected

        for depth in range(2, min(empty_count, 18) + 1):
            if time.perf_counter() >= deadline:
                break

            alpha = -INF
            results = []
            for index, (_, record) in enumerate(ranked):
                np, nb, source, destination, arrow = record
                value = -search(q, np, nb, depth - 1, -INF, -alpha)
                results.append((value, record))

                if value > alpha:
                    alpha = value
                    answer = (source, destination, arrow)

                if alpha == MATE:
                    results.extend(ranked[index + 1:])
                    break

            results.sort(key=lambda item: item[0], reverse=True)
            ranked = results

    except _Timeout:
        pass

    return _format(answer)
