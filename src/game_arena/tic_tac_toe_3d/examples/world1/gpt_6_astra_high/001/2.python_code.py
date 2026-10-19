
import time


_BITS = tuple(1 << i for i in range(27))
_COORDS = tuple(
    (x, y, z)
    for x in range(3)
    for y in range(3)
    for z in range(3)
)
_ALL = (1 << 27) - 1

_LINES = []
_INCIDENT = [[] for _ in range(27)]

# Generate every straight winning line, using one orientation per direction.
for dx in (-1, 0, 1):
    for dy in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if dx == dy == dz == 0:
                continue
            if dx < 0 or (dx == 0 and dy < 0):
                continue
            if dx == 0 and dy == 0 and dz < 0:
                continue

            for x, y, z in _COORDS:
                ex, ey, ez = x + 2 * dx, y + 2 * dy, z + 2 * dz
                if not (0 <= ex < 3 and 0 <= ey < 3 and 0 <= ez < 3):
                    continue

                cells = tuple(
                    (x + t * dx) * 9
                    + (y + t * dy) * 3
                    + z + t * dz
                    for t in range(3)
                )
                mask = sum(_BITS[i] for i in cells)
                _LINES.append((mask, cells))
                for i in cells:
                    others = [j for j in cells if j != i]
                    _INCIDENT[i].append((mask, others[0], others[1]))

_LINES = tuple(_LINES)
_INCIDENT = tuple(tuple(items) for items in _INCIDENT)
_WEIGHTS = tuple(len(items) for items in _INCIDENT)


class _SearchTimeout(Exception):
    pass


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    deadline = time.perf_counter() + 0.90

    bits = _BITS
    incident = _INCIDENT
    weights = _WEIGHTS
    own = opponent = 0
    positional = 0

    for i, (x, y, z) in enumerate(_COORDS):
        value = board[x][y][z]
        if value == 1:
            own |= bits[i]
            positional += weights[i]
        elif value == -1:
            opponent |= bits[i]
            positional -= weights[i]

    empty = _ALL ^ (own | opponent)
    if not empty:
        return (0, 0, 0)

    if not (own | opponent):
        return (1, 1, 1)

    # graph[i] contains the possible winning replies created by playing i.
    # Each edge represents a line with one friendly stone and two empties.
    ga = [0] * 27
    gb = [0] * 27
    own_wins = opponent_wins = 0

    for mask, _ in _LINES:
        a = own & mask
        b = opponent & mask

        if not b:
            count = a.bit_count()
            if count == 2:
                own_wins |= mask ^ a
            elif count == 1:
                holes = mask ^ a
                u = holes & -holes
                v = holes ^ u
                ga[u.bit_length() - 1] |= v
                ga[v.bit_length() - 1] |= u

        if not a:
            count = b.bit_count()
            if count == 2:
                opponent_wins |= mask ^ b
            elif count == 1:
                holes = mask ^ b
                u = holes & -holes
                v = holes ^ u
                gb[u.bit_length() - 1] |= v
                gb[v.bit_length() - 1] |= u

    def indices(mask):
        while mask:
            bit = mask & -mask
            mask ^= bit
            yield bit.bit_length() - 1

    if own_wins:
        i = max(indices(own_wins), key=lambda j: weights[j])
        return _COORDS[i]

    if opponent_wins:
        # A single threat must be blocked. With multiple threats, block one
        # while creating as much counterplay as possible.
        i = max(
            indices(opponent_wins),
            key=lambda j: (ga[j].bit_count(), weights[j]),
        )
        return _COORDS[i]

    for i in indices(empty):
        if ga[i] & (ga[i] - 1):
            return _COORDS[i]

    def rank_move(i, ag, bg, occupied):
        score = 4 * weights[i] + 65 * bg[i].bit_count()
        attack = ag[i]
        if attack:
            score += 220
            reply = attack.bit_length() - 1
            if bg[reply] & ~bits[i]:
                score -= 120

        # Empty lines can create new fork opportunities.
        for mask, u, v in incident[i]:
            if not (mask & occupied):
                score += 8
                if ag[u]:
                    score += 55
                if ag[v]:
                    score += 55
                if bg[u]:
                    score += 35
                if bg[v]:
                    score += 35
        return score

    def advance(ag, bg, occupied, i):
        """Update the graphs and return them in next-player order."""
        bit = bits[i]
        clear = _ALL ^ bit
        na = ag.copy()
        nb = bg.copy()

        neighbors = ag[i]
        while neighbors:
            b = neighbors & -neighbors
            neighbors ^= b
            na[b.bit_length() - 1] &= clear
        na[i] = 0

        neighbors = bg[i]
        while neighbors:
            b = neighbors & -neighbors
            neighbors ^= b
            nb[b.bit_length() - 1] &= clear
        nb[i] = 0

        for mask, u, v in incident[i]:
            if not (mask & occupied):
                na[u] |= bits[v]
                na[v] |= bits[u]

        return nb, na

    # Establish a tactically sensible legal fallback before searching.
    attacks = 0
    defenses = empty
    for i in indices(empty):
        if ga[i]:
            attacks |= bits[i]
        links = gb[i]
        if links & (links - 1):
            allowed = bits[i]
            if links.bit_count() == 2:
                allowed |= links
            defenses &= allowed

    candidates = attacks | defenses
    for i in indices(attacks):
        reply = ga[i].bit_length() - 1
        counter = gb[reply] & ~bits[i]
        if counter & (counter - 1):
            candidates &= ~bits[i]

    occupied = own | opponent
    best_move = max(
        indices(candidates or empty),
        key=lambda i: rank_move(i, ga, gb, occupied),
    )

    MATE = 100000
    INF = 1000000
    EXACT, LOWER, UPPER = 0, 1, 2

    table = {}
    killers = [[-1, -1] for _ in range(28)]
    history = [[0] * 27 for _ in range(2)]
    nodes = 0
    root_progress = best_move

    def search(a, b, ag, bg, empties, pending,
               depth, alpha, beta, ply, pos):
        nonlocal nodes, root_progress

        nodes += 1
        if nodes & 63 == 0 and time.perf_counter() >= deadline:
            raise _SearchTimeout

        if not empties:
            return 0

        key = (a << 27) | b
        original_alpha = alpha
        cached = table.get(key)
        tt_move = -1

        if cached is not None:
            old_depth, value, flag, tt_move = cached
            if old_depth >= depth:
                if flag == EXACT:
                    return value
                if flag == LOWER and value >= beta:
                    return value
                if flag == UPPER and value <= alpha:
                    return value

        best_value = -INF
        best_i = -1

        if pending:
            if pending & (pending - 1):
                value = -MATE + ply + 2
                table[key] = (99, value, EXACT, -1)
                return value

            i = pending.bit_length() - 1
            threats = ag[i]
            if threats & (threats - 1):
                value = MATE - ply - 3
                table[key] = (99, value, EXACT, i)
                return value

            moves = [i]
            next_depth = depth  # Forced blocks do not consume search depth.

        else:
            attack_mask = 0
            defense_mask = empties
            danger = False
            a_activity = b_activity = 0

            remaining = empties
            while remaining:
                bit = remaining & -remaining
                remaining ^= bit
                i = bit.bit_length() - 1

                links = ag[i]
                if links:
                    if links & (links - 1):
                        value = MATE - ply - 3
                        table[key] = (99, value, EXACT, i)
                        return value
                    attack_mask |= bit
                    a_activity += 1

                links = bg[i]
                if links:
                    b_activity += 1
                    if links & (links - 1):
                        danger = True
                        allowed = bit
                        if links.bit_count() == 2:
                            allowed |= links
                        defense_mask &= allowed

            move_mask = attack_mask | defense_mask

            # An attack is losing if its mandatory reply makes an enemy fork.
            remaining = attack_mask
            while remaining:
                bit = remaining & -remaining
                remaining ^= bit
                i = bit.bit_length() - 1
                reply = ag[i].bit_length() - 1
                counter = bg[reply] & ~bit
                if counter & (counter - 1):
                    move_mask &= ~bit

            if not move_mask:
                value = -MATE + ply + 4
                i = (empties & -empties).bit_length() - 1
                table[key] = (99, value, EXACT, i)
                return value

            if depth <= 0 and not danger:
                # Quiescence: examine a few additional forcing attacks.
                stand_pat = 12 * (a_activity - b_activity) + pos + 3
                if depth <= -2:
                    table[key] = (depth, stand_pat, EXACT, -1)
                    return stand_pat
                if stand_pat >= beta:
                    table[key] = (depth, stand_pat, LOWER, -1)
                    return stand_pat

                best_value = stand_pat
                if stand_pat > alpha:
                    alpha = stand_pat
                move_mask &= attack_mask

                if not move_mask:
                    flag = UPPER if stand_pat <= original_alpha else EXACT
                    table[key] = (depth, stand_pat, flag, -1)
                    return stand_pat

            occupied_here = _ALL ^ empties
            side_history = history[ply & 1]
            killer1, killer2 = killers[ply]
            ranked = []

            for i in indices(move_mask):
                score = rank_move(i, ag, bg, occupied_here)
                score += min(80, side_history[i] // 8)
                if i == killer1:
                    score += 100
                elif i == killer2:
                    score += 60
                if i == tt_move:
                    score += 1000000
                ranked.append((score, i))

            ranked.sort(reverse=True)
            moves = [i for _, i in ranked]
            next_depth = max(-2, depth - 1)

        occupied_here = _ALL ^ empties
        searched = 0

        for i in moves:
            bit = bits[i]
            child_ag, child_bg = advance(ag, bg, occupied_here, i)
            child_empty = empties ^ bit
            child_pending = ag[i]
            child_pos = -pos - weights[i]

            if searched and depth >= 2:
                value = -search(
                    b, a | bit, child_ag, child_bg,
                    child_empty, child_pending, next_depth,
                    -alpha - 1, -alpha, ply + 1, child_pos,
                )
                if alpha < value < beta:
                    value = -search(
                        b, a | bit, child_ag, child_bg,
                        child_empty, child_pending, next_depth,
                        -beta, -alpha, ply + 1, child_pos,
                    )
            else:
                value = -search(
                    b, a | bit, child_ag, child_bg,
                    child_empty, child_pending, next_depth,
                    -beta, -alpha, ply + 1, child_pos,
                )

            searched += 1

            if value > best_value:
                best_value = value
                best_i = i
                if ply == 0:
                    root_progress = i

            if value > alpha:
                alpha = value

            if alpha >= beta:
                if depth > 0:
                    if killers[ply][0] != i:
                        killers[ply][1] = killers[ply][0]
                        killers[ply][0] = i
                    history[ply & 1][i] += depth * depth
                break

        if best_value <= original_alpha:
            flag = UPPER
        elif best_value >= beta:
            flag = LOWER
        else:
            flag = EXACT

        table[key] = (depth, best_value, flag, best_i)
        return best_value

    root_key = (own << 27) | opponent
    completed_iteration = False

    for depth in range(1, empty.bit_count() + 1):
        if time.perf_counter() >= deadline:
            break

        root_progress = best_move
        try:
            value = search(
                own, opponent, ga, gb, empty, 0,
                depth, -INF, INF, 0, positional,
            )
        except _SearchTimeout:
            if not completed_iteration:
                best_move = root_progress
            break

        entry = table.get(root_key)
        if entry is not None:
            move = entry[3]
            if 0 <= move < 27 and empty & bits[move]:
                best_move = move

        completed_iteration = True
        if abs(value) >= MATE - 100:
            break

    # Final legality guard, including interrupted-search cases.
    if not (0 <= best_move < 27 and empty & bits[best_move]):
        best_move = (empty & -empty).bit_length() - 1

    return _COORDS[best_move]
