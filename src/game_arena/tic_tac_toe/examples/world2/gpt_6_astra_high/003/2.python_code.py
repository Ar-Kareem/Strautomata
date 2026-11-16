
from itertools import permutations
from time import perf_counter

FULL = (1 << 16) - 1
ALL_LINES = (1 << 10) - 1
MATE = 10000
INF = 20000

LINES = tuple(
    [0xF << (4 * r) for r in range(4)]
    + [0x1111 << c for c in range(4)]
    + [0x8421, 0x1248]
)

_TABLES = None
_TT = {}


class _SearchTimeout(Exception):
    pass


def _coordinates(move):
    index = move.bit_length() - 1
    return index // 4, index % 4


def _immediate_moves(stones, empty):
    result = 0
    for line in LINES:
        occupied = line & stones
        if occupied.bit_count() == 3:
            result |= line ^ occupied
    return result & empty


def _fallback(ours, theirs, candidates):
    """Choose a legal, tactically sensible move without any search."""
    weights = (1, 6, 35, 250, 10000)
    best_move = candidates & -candidates
    best_score = -1

    while candidates:
        move = candidates & -candidates
        candidates ^= move
        score = 0

        for line in LINES:
            if not (line & move):
                continue
            if not (line & theirs):
                score += weights[(line & ours).bit_count()]
            if not (line & ours):
                score += weights[(line & theirs).bit_count()]

        if score > best_score:
            best_score = score
            best_move = move

    return best_move


def _build_tables():
    global _TABLES
    if _TABLES is not None:
        return _TABLES

    # For each subset of winning lines, record its union and the cells
    # belonging to at least two selected lines.
    unions = [0] * 1024
    intersections = [0] * 1024

    for subset in range(1, 1024):
        bit = subset & -subset
        previous = subset ^ bit
        line = LINES[bit.bit_length() - 1]
        unions[subset] = unions[previous] | line
        intersections[subset] = (
            intersections[previous] | (unions[previous] & line)
        )

    membership = [
        sum(1 << j for j, line in enumerate(LINES) if line & (1 << i))
        for i in range(16)
    ]

    blocked = [0] * 65536
    singles = [0] * 65536
    doubles = [0] * 65536
    triples = [0] * 65536
    winning = [0] * 65536

    for stones in range(1, 65536):
        bit = stones & -stones
        previous = stones ^ bit
        changed = membership[bit.bit_length() - 1]
        unchanged = ALL_LINES ^ changed

        blocked[stones] = blocked[previous] | changed
        singles[stones] = (
            (singles[previous] & unchanged)
            | (changed & ~blocked[previous])
        )
        doubles[stones] = (
            (doubles[previous] & unchanged)
            | (changed & singles[previous])
        )
        triples[stones] = (
            (triples[previous] & unchanged)
            | (changed & doubles[previous])
        )
        winning[stones] = unions[triples[stones]] & (FULL ^ stones)

    _TABLES = (
        blocked, singles, doubles, winning, unions, intersections
    )
    return _TABLES


def _root_representatives(ours, theirs, empty):
    """Keep one move from each symmetry-equivalent root orbit."""
    symmetries = []

    # These transformations preserve rows, columns, and both diagonals.
    for permutation in permutations(range(4)):
        if any(
            permutation[3 - i] != 3 - permutation[i]
            for i in range(4)
        ):
            continue

        for reflect in (False, True):
            for transpose in (False, True):
                mapping = []
                transformed_ours = 0
                transformed_theirs = 0

                for i in range(16):
                    r, c = divmod(i, 4)
                    rr = permutation[r]
                    cc = permutation[c]
                    if reflect:
                        cc = 3 - cc
                    if transpose:
                        rr, cc = cc, rr

                    target = 1 << (4 * rr + cc)
                    mapping.append(target)

                    if ours & (1 << i):
                        transformed_ours |= target
                    if theirs & (1 << i):
                        transformed_theirs |= target

                if (
                    transformed_ours == ours
                    and transformed_theirs == theirs
                ):
                    symmetries.append(mapping)

    representatives = 0
    remaining = empty

    while remaining:
        move = remaining & -remaining
        representatives |= move
        index = move.bit_length() - 1

        orbit = 0
        for mapping in symmetries:
            orbit |= mapping[index]

        remaining &= ~orbit

    return representatives


def policy(board: list[list[int]]) -> tuple[int, int]:
    deadline = perf_counter() + 0.88

    ours = 0
    theirs = 0
    for r in range(4):
        for c in range(4):
            if board[r][c] == 1:
                ours |= 1 << (4 * r + c)
            elif board[r][c] == -1:
                theirs |= 1 << (4 * r + c)

    empty = FULL ^ (ours | theirs)

    # No legal action exists on a full board; normal arena calls are
    # nonterminal and therefore never enter this branch.
    if not empty:
        return (0, 0)

    wins = _immediate_moves(ours, empty)
    if wins:
        return _coordinates(wins & -wins)

    threats = _immediate_moves(theirs, empty)
    if threats:
        # One threat requires this block. Multiple threats are already
        # a forced loss, but blocking one remains a legal practical try.
        return _coordinates(_fallback(ours, theirs, threats))

    if empty == FULL:
        return (1, 1)

    best_move = _fallback(ours, theirs, empty)

    blocked, singles, doubles, winning, unions, intersections = (
        _build_tables()
    )

    forks = intersections[doubles[ours] & ~blocked[theirs]] & empty
    if forks:
        return _coordinates(_fallback(ours, theirs, forks))

    if perf_counter() >= deadline:
        return _coordinates(best_move)

    if len(_TT) > 180000:
        _TT.clear()
    tt = _TT

    root_empty_count = empty.bit_count()
    root_moves = _root_representatives(ours, theirs, empty)
    root_key = ours | (theirs << 16)

    history = [0] * 16
    killer_one = [0] * 17
    killer_two = [0] * 17
    nodes = 0

    def evaluate(p, q, free):
        p_open = ALL_LINES ^ blocked[q]
        q_open = ALL_LINES ^ blocked[p]

        p_one = singles[p] & p_open
        q_one = singles[q] & q_open
        p_two = doubles[p] & p_open
        q_two = doubles[q] & q_open

        score = (
            3 * (p_one.bit_count() - q_one.bit_count())
            + 20 * (p_two.bit_count() - q_two.bit_count())
            + p_open.bit_count() - q_open.bit_count()
        )

        # Reward two-stone lines connected to other live lines through
        # empty intersections: these are useful future fork locations.
        p_connections = unions[p_two] & intersections[p_open] & free
        q_connections = unions[q_two] & intersections[q_open] & free
        score += 2 * (
            p_connections.bit_count() - q_connections.bit_count()
        )
        return score

    def search(p, q, depth, alpha, beta):
        nonlocal nodes
        nodes += 1
        if (nodes & 255) == 0 and perf_counter() >= deadline:
            raise _SearchTimeout

        free = FULL ^ (p | q)
        count = free.bit_count()
        if not count:
            return 0

        depth = max(depth, 0)
        if count <= 6:
            depth = max(depth, count)

        key = p | (q << 16)
        entry = tt.get(key)
        hash_move = 0

        if entry is not None:
            stored_depth, value, flag, hash_move = entry
            if stored_depth >= depth:
                if flag == 0:
                    return value
                if flag == 1 and value >= beta:
                    return value
                if flag == 2 and value <= alpha:
                    return value

        if winning[p] & free:
            return MATE + count

        forced = winning[q] & free
        if forced and (forced & (forced - 1)):
            return -MATE - count + 1

        if (blocked[p] & blocked[q]) == ALL_LINES:
            return 0

        p_forks = intersections[doubles[p] & ~blocked[q]] & free
        if p_forks and (not forced or (p_forks & forced)):
            return MATE + count - 2

        # Quiescence: do not stop while blocking a win or defending
        # against an opponent's available fork.
        if depth == 0 and not forced:
            q_forks = intersections[doubles[q] & ~blocked[p]] & free
            if not q_forks:
                value = evaluate(p, q, free)
                tt[key] = (0, value, 0, 0)
                return value

        original_alpha = alpha

        if forced:
            moves = [forced]
        else:
            candidates = root_moves if count == root_empty_count else free
            ordered = []

            while candidates:
                move = candidates & -candidates
                candidates ^= move
                index = move.bit_length() - 1

                next_p = p | move
                next_free = free ^ move
                attack = winning[next_p] & next_free

                priority = (
                    16 * evaluate(next_p, q, next_free) + history[index]
                )
                if attack:
                    priority += 30000
                if move == killer_one[count]:
                    priority += 8000
                elif move == killer_two[count]:
                    priority += 4000

                # Put moves allowing an immediate opponent fork last.
                reply_forks = (
                    intersections[doubles[q] & ~blocked[next_p]]
                    & next_free
                )
                if reply_forks and (
                    not attack or (reply_forks & attack)
                ):
                    priority -= 200000

                if move == hash_move:
                    priority += 1000000

                ordered.append((priority, move))

            ordered.sort(reverse=True)
            moves = [move for _, move in ordered]

        best_value = -INF
        local_best = moves[0]
        first = True

        for move in moves:
            if first:
                value = -search(q, p | move, depth - 1, -beta, -alpha)
                first = False
            else:
                # Principal-variation search.
                value = -search(
                    q, p | move, depth - 1, -alpha - 1, -alpha
                )
                if alpha < value < beta:
                    value = -search(
                        q, p | move, depth - 1, -beta, -alpha
                    )

            if value > best_value:
                best_value = value
                local_best = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                if move != killer_one[count]:
                    killer_two[count] = killer_one[count]
                    killer_one[count] = move

                index = move.bit_length() - 1
                bonus = min(128, (depth + 1) ** 2)
                history[index] += (
                    bonus - history[index] * bonus // 16384
                )
                break

        if best_value <= original_alpha:
            flag = 2  # Upper bound.
        elif best_value >= beta:
            flag = 1  # Lower bound.
        else:
            flag = 0  # Exact at this search depth.

        tt[key] = (depth, best_value, flag, local_best)
        return best_value

    previous_score = 0
    first_depth = root_empty_count if root_empty_count <= 8 else 1

    try:
        for depth in range(first_depth, root_empty_count + 1):
            if perf_counter() >= deadline:
                break

            if depth >= 3 and depth != first_depth:
                low, high = previous_score - 40, previous_score + 40
            else:
                low, high = -INF, INF

            score = search(ours, theirs, depth, low, high)

            if score <= low or score >= high:
                if perf_counter() >= deadline:
                    break
                score = search(ours, theirs, depth, -INF, INF)

            entry = tt.get(root_key)
            if entry is not None:
                candidate = entry[3]
                if candidate and (candidate & empty):
                    best_move = candidate

            previous_score = score
            if abs(score) >= MATE or depth >= root_empty_count:
                break

    except _SearchTimeout:
        pass

    # Retain the last completed iteration's legal move on timeout.
    if not (best_move & empty):
        best_move = empty & -empty

    return _coordinates(best_move)
