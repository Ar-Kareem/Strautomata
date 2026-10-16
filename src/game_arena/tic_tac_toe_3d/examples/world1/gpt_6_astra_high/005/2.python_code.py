
from itertools import product, permutations
from time import perf_counter


SIZE = 27
FULL = (1 << SIZE) - 1
MATE = 30000
INF = 100000
EXACT, LOWER, UPPER = 0, 1, 2


def _build_geometry():
    coordinates = tuple(product(range(3), repeat=3))
    lines = set()

    for x, y, z in coordinates:
        for dx, dy, dz in product((-1, 0, 1), repeat=3):
            if dx == dy == dz == 0:
                continue
            ex, ey, ez = x + 2 * dx, y + 2 * dy, z + 2 * dz
            if not (0 <= ex < 3 and 0 <= ey < 3 and 0 <= ez < 3):
                continue

            mask = 0
            for step in range(3):
                i = x + step * dx
                j = y + step * dy
                k = z + step * dz
                mask |= 1 << (9 * i + 3 * j + k)
            lines.add(mask)

    lines = tuple(sorted(lines))
    weights = tuple(
        sum(bool(line & (1 << cell)) for line in lines)
        for cell in range(SIZE)
    )

    symmetries = []
    for order in permutations(range(3)):
        for flips in product((False, True), repeat=3):
            mapping = []
            for xyz in coordinates:
                transformed = [
                    2 - xyz[order[d]] if flips[d] else xyz[order[d]]
                    for d in range(3)
                ]
                i, j, k = transformed
                mapping.append(1 << (9 * i + 3 * j + k))
            symmetries.append(tuple(mapping))

    return lines, weights, tuple(symmetries)


LINES, WEIGHTS, SYMMETRIES = _build_geometry()


def _coordinate(bit):
    cell = bit.bit_length() - 1
    return cell // 9, (cell // 3) % 3, cell % 3


def _inspect(a, b):
    """
    a and b are the current player's and opponent's bitboards.

    links_a[m] contains the winning threats created by playing m
    on lines that currently contain exactly one a piece.
    """
    wins_a = wins_b = forks_a = forks_b = attacks_a = 0
    links_a = [0] * SIZE
    links_b = [0] * SIZE
    singles_a = singles_b = 0
    live = False

    for line in LINES:
        x = line & a
        y = line & b

        if x and y:
            continue
        live = True
        if not x and not y:
            continue

        holes = line ^ (x or y)
        if not holes:
            # Already completed lines cannot occur during normal search.
            continue

        u = holes & -holes
        v = holes ^ u

        if not v:
            if x:
                wins_a |= u
            else:
                wins_b |= u
            continue

        iu = u.bit_length() - 1
        iv = v.bit_length() - 1

        if x:
            singles_a += 1
            attacks_a |= holes
            if links_a[iu]:
                forks_a |= u
            if links_a[iv]:
                forks_a |= v
            links_a[iu] |= v
            links_a[iv] |= u
        else:
            singles_b += 1
            if links_b[iu]:
                forks_b |= u
            if links_b[iv]:
                forks_b |= v
            links_b[iu] |= v
            links_b[iv] |= u

    return (
        wins_a, wins_b, forks_a, forks_b, attacks_a,
        links_a, links_b, singles_a - singles_b, live
    )


def _safe_moves(empty, opponent_forks, attacks, links_a, links_b):
    """
    Called when neither player has an immediate win and the current
    player has no immediate fork.

    Excluded moves lose to an opponent fork on the next turn.
    """
    if not opponent_forks:
        return empty

    defenses = empty
    remaining = opponent_forks

    while remaining:
        fork = remaining & -remaining
        remaining ^= fork
        neighbors = links_b[fork.bit_length() - 1]

        rest = neighbors & (neighbors - 1)
        if rest & (rest - 1):
            # Three or more threats: only occupying the fork square works.
            defenses &= fork
        else:
            # Two threats: occupying either partner also breaks the fork.
            defenses &= fork | neighbors

    # A threat can force a reply instead of directly defending every fork.
    candidates = (defenses | attacks) & empty
    forcing = candidates & attacks

    while forcing:
        move = forcing & -forcing
        forcing ^= move

        # No current-player fork exists, so this reply is a single bit.
        reply = links_a[move.bit_length() - 1]
        reply_threats = links_b[reply.bit_length() - 1] & ~move

        if reply_threats & (reply_threats - 1):
            # The forced reply itself gives the opponent a winning fork.
            candidates &= ~move

    return candidates


def _pick(mask, links_a=None, links_b=None):
    best_bit = mask & -mask
    best_score = (-INF, -INF)

    while mask:
        bit = mask & -mask
        mask ^= bit
        cell = bit.bit_length() - 1

        score = 2 * WEIGHTS[cell]
        if links_a is not None:
            score += 8 * links_a[cell].bit_count()
        if links_b is not None:
            score += 6 * links_b[cell].bit_count()

        ranking = (score, -cell)
        if ranking > best_score:
            best_score = ranking
            best_bit = bit

    return best_bit


def _root_representatives(a, b, empty):
    stabilizers = []

    for mapping in SYMMETRIES:
        transformed_a = transformed_b = 0
        bits = a
        while bits:
            bit = bits & -bits
            bits ^= bit
            transformed_a |= mapping[bit.bit_length() - 1]
        if transformed_a != a:
            continue

        bits = b
        while bits:
            bit = bits & -bits
            bits ^= bit
            transformed_b |= mapping[bit.bit_length() - 1]
        if transformed_b == b:
            stabilizers.append(mapping)

    if len(stabilizers) <= 1:
        return empty

    representatives = 0
    bits = empty
    while bits:
        bit = bits & -bits
        bits ^= bit
        cell = bit.bit_length() - 1
        if all(mapping[cell] >= bit for mapping in stabilizers):
            representatives |= bit

    return representatives


class _SearchTimeout(Exception):
    pass


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    deadline = perf_counter() + 0.90

    a = b = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                bit = 1 << (9 * i + 3 * j + k)
                value = board[i][j][k]
                if value == 1:
                    a |= bit
                elif value == -1:
                    b |= bit

    empty = FULL & ~(a | b)

    # A full terminal board has no legal action; normal arena calls
    # always contain at least one empty cell.
    if not empty:
        return (0, 0, 0)

    if not (a | b):
        return (1, 1, 1)

    wa, wb, fa, fb, attacks, la, lb, _, live = _inspect(a, b)

    if wa:
        return _coordinate(_pick(wa, la, lb))

    if wb:
        # With one threat this is mandatory. With multiple threats,
        # block one while maximizing remaining counterplay.
        return _coordinate(_pick(wb, la, lb))

    if fa:
        return _coordinate(_pick(fa, la, lb))

    candidates = _safe_moves(empty, fb, attacks, la, lb)
    if not candidates:
        # All moves lose against perfect play. Prefer making the opponent
        # find a fork rather than forcing them to play it as a block.
        choices = (empty & ~attacks) or empty
        return _coordinate(_pick(choices, la, lb))

    if not live:
        return _coordinate(_pick(candidates))

    root_reps = _root_representatives(a, b, empty)
    root_candidates = candidates & root_reps
    best_move = _pick(root_candidates, la, lb)

    if not (root_candidates & (root_candidates - 1)):
        return _coordinate(best_move)

    table = {}
    history = [[0] * SIZE for _ in range(2)]
    killers = [[0, 0] for _ in range(SIZE + 2)]
    nodes = 0
    partial_move = best_move

    def search(us, them, depth, alpha, beta, ply):
        nonlocal nodes, partial_move

        nodes += 1
        if (nodes & 63) == 0 and perf_counter() >= deadline:
            raise _SearchTimeout

        key = us | (them << SIZE)
        entry = table.get(key)
        tt_move = 0

        if entry is not None:
            stored_depth, stored_value, bound, tt_move = entry
            if stored_depth >= depth:
                if bound == EXACT:
                    return stored_value
                if bound == LOWER and stored_value >= beta:
                    return stored_value
                if bound == UPPER and stored_value <= alpha:
                    return stored_value

        free = FULL & ~(us | them)
        if not free:
            return 0

        w1, w2, f1, f2, attack, l1, l2, line_balance, alive = _inspect(
            us, them
        )

        if w1:
            value = MATE - ply - 1
            table[key] = (99, value, EXACT, w1 & -w1)
            return value

        if w2:
            move = w2 & -w2
            if w2 & (w2 - 1):
                value = -MATE + ply + 2
                table[key] = (99, value, EXACT, move)
                return value
            if f1 & move:
                value = MATE - ply - 3
                table[key] = (99, value, EXACT, move)
                return value
            moves = move
        elif f1:
            value = MATE - ply - 3
            table[key] = (99, value, EXACT, f1 & -f1)
            return value
        else:
            moves = _safe_moves(free, f2, attack, l1, l2)
            if not moves:
                value = -MATE + ply + 4
                table[key] = (99, value, EXACT, free & -free)
                return value

        if not alive:
            table[key] = (99, 0, EXACT, free & -free)
            return 0

        if ply == 0:
            moves &= root_reps

        # Extend forced blocks and fork evasions beyond the nominal
        # horizon. Also extend positions with only one viable move.
        if (
            depth == 0
            and not w2
            and not f2
            and moves & (moves - 1)
        ):
            value = 24 * line_balance + 8
            bits = us
            while bits:
                bit = bits & -bits
                bits ^= bit
                value += 2 * WEIGHTS[bit.bit_length() - 1]
            bits = them
            while bits:
                bit = bits & -bits
                bits ^= bit
                value -= 2 * WEIGHTS[bit.bit_length() - 1]

            table[key] = (0, value, EXACT, 0)
            return value

        ordered = []
        bits = moves
        hist = history[ply & 1]
        killer1, killer2 = killers[ply]

        while bits:
            move = bits & -bits
            bits ^= move
            cell = move.bit_length() - 1

            priority = 24 * WEIGHTS[cell]
            priority += 256 * l2[cell].bit_count()
            priority += min(hist[cell], 2048)
            if move & attack:
                priority += 4000
            if move == killer1:
                priority += 1500
            elif move == killer2:
                priority += 1000
            if move == tt_move:
                priority += 1000000

            ordered.append((priority, -cell, move))

        ordered.sort(reverse=True)

        original_alpha = alpha
        best_value = -INF
        chosen = ordered[0][2]
        next_depth = max(0, depth - 1)

        for move_number, (_, _, move) in enumerate(ordered):
            if move_number and depth >= 2:
                value = -search(
                    them, us | move, next_depth,
                    -alpha - 1, -alpha, ply + 1
                )
                if alpha < value < beta:
                    value = -search(
                        them, us | move, next_depth,
                        -beta, -alpha, ply + 1
                    )
            else:
                value = -search(
                    them, us | move, next_depth,
                    -beta, -alpha, ply + 1
                )

            if value > best_value:
                best_value = value
                chosen = move
                if ply == 0:
                    partial_move = move

            # A proven root win is sufficient; no need to spend the
            # remaining budget distinguishing winning continuations.
            if ply == 0 and value >= MATE - 32:
                table[key] = (depth, value, LOWER, move)
                return value

            if value > alpha:
                alpha = value

            if alpha >= beta:
                cell = move.bit_length() - 1
                hist[cell] += depth * depth + 1
                if not (move & attack) and move != killers[ply][0]:
                    killers[ply][1] = killers[ply][0]
                    killers[ply][0] = move
                break

            # Immediate wins and three-ply fork wins were already
            # handled, so five plies is the fastest remaining win.
            if best_value >= MATE - ply - 5:
                break

        if best_value <= original_alpha:
            bound = UPPER
        elif best_value >= beta:
            bound = LOWER
        else:
            bound = EXACT

        table[key] = (depth, best_value, bound, chosen)
        return best_value

    root_key = a | (b << SIZE)
    completed_iteration = False

    for depth in range(1, empty.bit_count() + 1):
        try:
            value = search(a, b, depth, -INF, INF, 0)
        except _SearchTimeout:
            if not completed_iteration:
                best_move = partial_move
            break

        entry = table.get(root_key)
        if entry is not None and entry[3] & empty:
            best_move = entry[3]
        completed_iteration = True

        if abs(value) >= MATE - 32:
            break
        if entry is not None and entry[0] == 99:
            break
        if perf_counter() >= deadline:
            break

    # Preserve legality even if an incomplete iteration supplied no move.
    if not (best_move & empty):
        best_move = empty & -empty

    return _coordinate(best_move)
