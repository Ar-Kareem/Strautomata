
import itertools
import time


_FULL = (1 << 27) - 1
_CENTER = 1 << 13
_CORNERS = sum(
    1 << (9 * x + 3 * y + z)
    for x in (0, 2)
    for y in (0, 2)
    for z in (0, 2)
)
_MATE = 1_000_000
_INF = 2_000_000
_Q_LIMIT = -3


def _build_geometry():
    lines = set()
    coordinates = list(itertools.product(range(3), repeat=3))

    for direction in itertools.product((-1, 0, 1), repeat=3):
        if direction == (0, 0, 0):
            continue
        if next(v for v in direction if v != 0) != 1:
            continue

        for start in coordinates:
            end = tuple(start[a] + 2 * direction[a] for a in range(3))
            if not all(0 <= v < 3 for v in end):
                continue

            mask = 0
            for step in range(3):
                x, y, z = (
                    start[a] + step * direction[a] for a in range(3)
                )
                mask |= 1 << (9 * x + 3 * y + z)
            lines.add(mask)

    lines = tuple(sorted(lines))
    weights = tuple(
        sum(bool(line & (1 << i)) for line in lines)
        for i in range(27)
    )

    transformations = []
    for permutation in itertools.permutations(range(3)):
        for flips in itertools.product((False, True), repeat=3):
            mapping = []
            for coordinate in coordinates:
                transformed = [
                    coordinate[permutation[a]] for a in range(3)
                ]
                for a in range(3):
                    if flips[a]:
                        transformed[a] = 2 - transformed[a]
                x, y, z = transformed
                mapping.append(1 << (9 * x + 3 * y + z))
            transformations.append(tuple(mapping))

    return lines, weights, tuple(transformations)


_LINES, _WEIGHTS, _TRANSFORMS = _build_geometry()


def _coordinates(bit):
    index = bit.bit_length() - 1
    return index // 9, (index // 3) % 3, index % 3


def _pick(mask):
    best = mask & -mask
    best_weight = -1
    while mask:
        bit = mask & -mask
        mask ^= bit
        weight = _WEIGHTS[bit.bit_length() - 1]
        if weight > best_weight:
            best_weight = weight
            best = bit
    return best


def _transform(mask, mapping):
    result = 0
    while mask:
        bit = mask & -mask
        mask ^= bit
        result |= mapping[bit.bit_length() - 1]
    return result


def _features(me, opponent):
    """
    threats[i] contains the winning squares created by playing at i
    on currently open lines containing exactly one friendly stone.
    """
    my_wins = 0
    opponent_wins = 0
    my_threats = [0] * 27
    opponent_threats = [0] * 27
    score = 0

    for line in _LINES:
        mine = line & me
        theirs = line & opponent

        if mine:
            if theirs:
                continue
            vacancies = line ^ mine
            if not vacancies:
                continue
            if vacancies & (vacancies - 1):
                first = vacancies & -vacancies
                second = vacancies ^ first
                my_threats[first.bit_length() - 1] |= second
                my_threats[second.bit_length() - 1] |= first
                score += 16
            else:
                my_wins |= vacancies
                score += 100

        elif theirs:
            vacancies = line ^ theirs
            if not vacancies:
                continue
            if vacancies & (vacancies - 1):
                first = vacancies & -vacancies
                second = vacancies ^ first
                opponent_threats[first.bit_length() - 1] |= second
                opponent_threats[second.bit_length() - 1] |= first
                score -= 16
            else:
                opponent_wins |= vacancies
                score -= 100

    score += 18 * (
        int(bool(me & _CENTER)) - int(bool(opponent & _CENTER))
    )
    score += 5 * (
        (me & _CORNERS).bit_count()
        - (opponent & _CORNERS).bit_count()
    )
    score += 2 * (me.bit_count() - opponent.bit_count())
    score += 6  # Small initiative bonus.

    return my_wins, opponent_wins, my_threats, opponent_threats, score


def _tactics(my_threats, opponent_threats, empty):
    forks = 0
    forcing = 0
    opponent_forks = 0
    defenses = empty

    remaining = empty
    while remaining:
        bit = remaining & -remaining
        remaining ^= bit
        index = bit.bit_length() - 1

        mine = my_threats[index]
        theirs = opponent_threats[index]

        if mine:
            forcing |= bit
            if mine & (mine - 1):
                forks |= bit

        if theirs & (theirs - 1):
            opponent_forks |= bit

            # To stop a two-threat fork, occupy its square or either
            # supporting endpoint. Three or more threats require
            # occupying the fork square itself.
            if theirs.bit_count() == 2:
                defenses &= bit | theirs
            else:
                defenses &= bit

    return forks, forcing, opponent_forks, defenses


class _SearchTimeout(Exception):
    pass


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    started = time.perf_counter()
    deadline = started + 0.88

    me = 0
    opponent = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                bit = 1 << (9 * i + 3 * j + k)
                if board[i][j][k] == 1:
                    me |= bit
                elif board[i][j][k] == -1:
                    opponent |= bit

    empty = _FULL ^ (me | opponent)
    if not empty:
        # No legal action exists on a full board; normally never called.
        return (0, 0, 0)

    fallback = _pick(empty)

    # If called after a completed game, still return an empty square.
    if any(
        (me & line) == line or (opponent & line) == line
        for line in _LINES
    ):
        return _coordinates(fallback)

    if (me | opponent).bit_count() <= 1 and empty & _CENTER:
        return (1, 1, 1)

    wins, enemy_wins, mt, ot, _ = _features(me, opponent)

    if wins:
        return _coordinates(_pick(wins))

    if enemy_wins:
        # With multiple distinct winning squares, defeat is immediate
        # regardless of the move; blocking one is still legal.
        return _coordinates(_pick(enemy_wins))

    forks, forcing, enemy_forks, defenses = _tactics(mt, ot, empty)
    if forks:
        return _coordinates(_pick(forks))

    candidates = empty
    if enemy_forks:
        candidates = forcing | defenses
        if not candidates:
            return _coordinates(_pick(enemy_forks))

    def initial_rank(bit):
        index = bit.bit_length() - 1
        return (
            100_000 * bool(mt[index])
            + 4_000 * ot[index].bit_count()
            + 20 * _WEIGHTS[index]
        )

    root_moves = []
    remaining = candidates
    while remaining:
        bit = remaining & -remaining
        remaining ^= bit
        root_moves.append(bit)
    root_moves.sort(key=initial_rank, reverse=True)

    # Search one representative from each symmetry orbit that preserves
    # both players' current stones.
    stabilizers = [
        mapping
        for mapping in _TRANSFORMS
        if _transform(me, mapping) == me
        and _transform(opponent, mapping) == opponent
    ]
    representatives = []
    seen = 0
    for bit in root_moves:
        if bit & seen:
            continue
        representatives.append(bit)
        index = bit.bit_length() - 1
        for mapping in stabilizers:
            seen |= mapping[index]
    root_moves = representatives

    best_move = root_moves[0]
    if len(root_moves) == 1:
        return _coordinates(best_move)

    # Entries: (searched depth, score, bound type, preferred move).
    # Bound types: 0 exact, 1 lower bound, 2 upper bound.
    table = {}
    history = [0] * 27
    killers = [[0, 0] for _ in range(28)]
    nodes = 0

    def search(p, o, depth, alpha, beta, ply):
        nonlocal nodes
        nodes += 1
        if (nodes & 63) == 0 and time.perf_counter() >= deadline:
            raise _SearchTimeout

        free = _FULL ^ (p | o)
        if not free:
            return 0

        key = p | (o << 27)
        original_alpha = alpha
        entry = table.get(key)
        tt_move = 0

        if entry is not None:
            stored_depth, stored_score, flag, tt_move = entry
            if stored_depth >= depth:
                if flag == 0:
                    return stored_score
                if flag == 1 and stored_score >= beta:
                    return stored_score
                if flag == 2 and stored_score <= alpha:
                    return stored_score

        pw, ow, pt, other_t, evaluation = _features(p, o)

        if pw:
            value = _MATE - ply - 1
            table[key] = (99, value, 0, pw & -pw)
            return value

        if ow:
            if ow & (ow - 1):
                value = -_MATE + ply + 2
                table[key] = (99, value, 0, ow & -ow)
                return value

            index = ow.bit_length() - 1
            threats = pt[index]
            if threats & (threats - 1):
                value = _MATE - ply - 3
                table[key] = (99, value, 0, ow)
                return value

            # A mandatory reply consumes no discretionary search depth.
            value = -search(o, p | ow, depth, -beta, -alpha, ply + 1)
            flag = (
                2 if value <= original_alpha
                else 1 if value >= beta
                else 0
            )
            table[key] = (depth, value, flag, ow)
            return value

        pf, checks, of, defensive = _tactics(pt, other_t, free)

        if pf:
            value = _MATE - ply - 3
            table[key] = (99, value, 0, pf & -pf)
            return value

        moves = free
        if of:
            moves = checks | defensive
            if not moves:
                value = -_MATE + ply + 4
                table[key] = (99, value, 0, free & -free)
                return value
            evaluation -= 80 * of.bit_count()

        if depth <= _Q_LIMIT:
            table[key] = (depth, evaluation, 0, 0)
            return evaluation

        chosen = 0
        if depth <= 0 and not of:
            # Quiescence: consider forcing continuations beyond the
            # nominal horizon, while retaining the quiet evaluation.
            best = evaluation
            if best >= beta:
                table[key] = (depth, best, 1, 0)
                return best
            if best > alpha:
                alpha = best
            moves = checks
        else:
            best = -_INF

        ordered = []
        remaining_moves = moves
        killer_one, killer_two = killers[ply]
        while remaining_moves:
            bit = remaining_moves & -remaining_moves
            remaining_moves ^= bit
            index = bit.bit_length() - 1
            rank = (
                10_000_000 * (bit == tt_move)
                + 100_000 * bool(pt[index])
                + 4_000 * other_t[index].bit_count()
                + 3_000 * (bit == killer_one)
                + 2_000 * (bit == killer_two)
                + min(history[index], 2_000)
                + 20 * _WEIGHTS[index]
            )
            ordered.append((rank, bit))
        ordered.sort(reverse=True)

        for move_number, (_, bit) in enumerate(ordered):
            if move_number == 0 or depth <= 0:
                value = -search(
                    o, p | bit, depth - 1, -beta, -alpha, ply + 1
                )
            else:
                # Principal variation search.
                value = -search(
                    o, p | bit, depth - 1,
                    -alpha - 1, -alpha, ply + 1
                )
                if alpha < value < beta:
                    value = -search(
                        o, p | bit, depth - 1,
                        -beta, -alpha, ply + 1
                    )

            if value > best:
                best = value
                chosen = bit
            if value > alpha:
                alpha = value

            if alpha >= beta:
                index = bit.bit_length() - 1
                if depth > 0 and not pt[index]:
                    history[index] += depth * depth
                    if killers[ply][0] != bit:
                        killers[ply][1] = killers[ply][0]
                        killers[ply][0] = bit
                break

        flag = (
            2 if best <= original_alpha
            else 1 if best >= beta
            else 0
        )
        table[key] = (depth, best, flag, chosen)
        return best

    previous_scores = {bit: 0 for bit in root_moves}

    try:
        for depth in range(1, empty.bit_count() + 1):
            root_moves.sort(
                key=lambda bit: (
                    bit == best_move,
                    previous_scores.get(bit, -_INF),
                ),
                reverse=True,
            )

            alpha = -_INF
            iteration_best = -_INF
            current_scores = {}

            for move_number, bit in enumerate(root_moves):
                if time.perf_counter() >= deadline:
                    raise _SearchTimeout

                if move_number == 0:
                    value = -search(
                        opponent, me | bit, depth - 1,
                        -_INF, _INF, 1
                    )
                else:
                    value = -search(
                        opponent, me | bit, depth - 1,
                        -alpha - 1, -alpha, 1
                    )
                    if value > alpha:
                        value = -search(
                            opponent, me | bit, depth - 1,
                            -_INF, -alpha, 1
                        )

                current_scores[bit] = value

                # The previous best is searched first. Updating after
                # each completed improvement gives a safe anytime result.
                if value > iteration_best:
                    iteration_best = value
                    best_move = bit

                if value > alpha:
                    alpha = value

                if value >= _MATE - 64:
                    return _coordinates(bit)

            previous_scores = current_scores

            # Every root alternative has been proved losing.
            if iteration_best <= -_MATE + 64:
                break

    except _SearchTimeout:
        pass

    if not (best_move & empty):
        best_move = fallback
    return _coordinates(best_move)
