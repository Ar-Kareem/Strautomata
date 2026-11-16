
from time import perf_counter

_GEOMETRY = {}
_TRANSPOSITIONS = {0: {}, 1: {}}


class _Timeout(Exception):
    pass


def _make_lookup(values):
    tables = []
    for block in range(4):
        table = [0] * 256
        offset = block * 8
        for mask in range(1, 256):
            bit = mask & -mask
            table[mask] = (
                table[mask ^ bit]
                + values[offset + bit.bit_length() - 1]
            )
        tables.append(table)
    return tuple(tables)


def _geometry(parity):
    cached = _GEOMETRY.get(parity)
    if cached is not None:
        return cached

    squares = [
        (r, c)
        for r in range(8)
        for c in range(8)
        if ((r + c) & 1) == parity
    ]
    indices = {square: i for i, square in enumerate(squares)}

    steps = [{}, {}]
    jumps = [{}, {}]

    for i, (r, c) in enumerate(squares):
        source = 1 << i
        for up, dr in ((0, -1), (1, 1)):
            for dc in (-1, 1):
                middle = (r + dr, c + dc)
                if middle not in indices:
                    continue

                j = indices[middle]
                delta = abs(j - i)
                steps[up][delta] = steps[up].get(delta, 0) | source

                target = (r + 2 * dr, c + 2 * dc)
                if target in indices:
                    k = indices[target]
                    group = (delta, abs(k - i))
                    jumps[up][group] = (
                        jumps[up].get(group, 0) | source
                    )

    advancement = (0, 0, 3, 7, 12, 20, 32, 0)
    column_bonus = (0, 1, 3, 4, 4, 3, 1, 0)
    man_values = [[], []]
    king_values = []

    for r, c in squares:
        for up in (0, 1):
            progress = r if up else 7 - r
            value = 100 + advancement[progress] + column_bonus[c]
            if 2 <= r <= 5 and 2 <= c <= 5:
                value += 4
            if progress == 0:
                value += 6
            if c in (0, 7) and progress < 5:
                value += 2
            man_values[up].append(value)

        king_values.append(
            180
            + 2 * min(r, 7 - r)
            + 2 * min(c, 7 - c)
            + (3 if 2 <= r <= 5 and 2 <= c <= 5 else 0)
        )

    distances = tuple(
        tuple(
            max(abs(r1 - r2), abs(c1 - c2))
            for r2, c2 in squares
        )
        for r1, c1 in squares
    )

    result = {
        "squares": squares,
        "steps": tuple(
            tuple((mask, delta) for delta, mask in group.items())
            for group in steps
        ),
        "jumps": tuple(
            tuple(
                (mask, middle, target)
                for (middle, target), mask in group.items()
            )
            for group in jumps
        ),
        "step_masks": tuple(
            tuple(group.get(delta, 0) for delta in (3, 4, 5))
            for group in steps
        ),
        "man_lookup": tuple(_make_lookup(v) for v in man_values),
        "king_lookup": _make_lookup(king_values),
        "man_bit_values": tuple(
            {1 << i: value for i, value in enumerate(values)}
            for values in man_values
        ),
        "king_bit_values": {
            1 << i: value for i, value in enumerate(king_values)
        },
        "distances": distances,
    }
    _GEOMETRY[parity] = result
    return result


def policy(my_men, my_kings, opp_men, opp_kings, color):
    started = perf_counter()
    deadline = started + 0.88

    my_men = [(int(r), int(c)) for r, c in my_men]
    my_kings = [(int(r), int(c)) for r, c in my_kings]
    opp_men = [(int(r), int(c)) for r, c in opp_men]
    opp_kings = [(int(r), int(c)) for r, c in opp_kings]

    occupied_squares = my_men + my_kings + opp_men + opp_kings
    parity = (
        (occupied_squares[0][0] + occupied_squares[0][1]) & 1
        if occupied_squares else 1
    )
    geometry = _geometry(parity)

    def pack(pieces):
        board = 0
        for r, c in pieces:
            board |= 1 << (4 * r + c // 2)
        return board

    root = (
        pack(my_men),
        pack(my_kings),
        pack(opp_men),
        pack(opp_kings),
        int(color == "w"),
    )

    down_steps, up_steps = geometry["steps"]
    down_jumps, up_jumps = geometry["jumps"]
    dm3, dm4, dm5 = geometry["step_masks"][0]
    um3, um4, um5 = geometry["step_masks"][1]
    man_lookup = geometry["man_lookup"]
    king_lookup = geometry["king_lookup"]
    man_values = geometry["man_bit_values"]
    king_values = geometry["king_bit_values"]
    distances = geometry["distances"]

    tt = _TRANSPOSITIONS[parity]
    if len(tt) > 110000:
        tt.clear()

    history = [{}, {}]
    killers = [[None, None] for _ in range(96)]
    path = set()
    nodes = 0
    INF = 32000
    MATE = 30000

    def generate(mm, mk, om, ok, up):
        enemy = om | ok
        empty = ~(mm | mk | enemy)
        upward = mk | (mm if up else 0)
        downward = mk | (mm if not up else 0)
        moves = []
        append = moves.append

        if upward:
            for mask, middle, target in up_jumps:
                sources = (
                    upward & mask
                    & (enemy >> middle)
                    & (empty >> target)
                )
                while sources:
                    bit = sources & -sources
                    sources ^= bit
                    append((bit, bit << target, bit << middle))

        if downward:
            for mask, middle, target in down_jumps:
                sources = (
                    downward & mask
                    & (enemy << middle)
                    & (empty << target)
                )
                while sources:
                    bit = sources & -sources
                    sources ^= bit
                    append((bit, bit >> target, bit >> middle))

        if moves:
            return moves

        if upward:
            for mask, delta in up_steps:
                sources = upward & mask & (empty >> delta)
                while sources:
                    bit = sources & -sources
                    sources ^= bit
                    append((bit, bit << delta, 0))

        if downward:
            for mask, delta in down_steps:
                sources = downward & mask & (empty << delta)
                while sources:
                    bit = sources & -sources
                    sources ^= bit
                    append((bit, bit >> delta, 0))

        return moves

    def play(mm, mk, om, ok, up, move):
        source, target, captured = move
        if source & mk:
            new_men = mm
            new_kings = (mk ^ source) | target
        else:
            new_men = mm ^ source
            crown = 0xF0000000 if up else 0xF
            if target & crown:
                new_kings = mk | target
            else:
                new_men |= target
                new_kings = mk

        return (
            om & ~captured,
            ok & ~captured,
            new_men,
            new_kings,
            1 - up,
        )

    def table_sum(board, tables):
        return (
            tables[0][board & 255]
            + tables[1][(board >> 8) & 255]
            + tables[2][(board >> 16) & 255]
            + tables[3][board >> 24]
        )

    def pursuit(kings, enemies):
        targets = []
        while enemies:
            bit = enemies & -enemies
            enemies ^= bit
            targets.append(bit.bit_length() - 1)

        total_distance = 0
        number = kings.bit_count()
        while kings:
            bit = kings & -kings
            kings ^= bit
            row = distances[bit.bit_length() - 1]
            nearest = 8
            for target in targets:
                distance = row[target]
                if distance < nearest:
                    nearest = distance
            total_distance += nearest

        return 6 * total_distance // number

    def evaluate(mm, mk, om, ok, up):
        nm = mm.bit_count()
        nk = mk.bit_count()
        no = om.bit_count()
        ko = ok.bit_count()
        total = nm + nk + no + ko
        king_extra = max(0, 16 - total)

        score = (
            table_sum(mm, man_lookup[up])
            - table_sum(om, man_lookup[1 - up])
        )
        if mk:
            score += table_sum(mk, king_lookup)
        if ok:
            score -= table_sum(ok, king_lookup)
        score += king_extra * (nk - ko)

        material = 100 * (nm - no) + (180 + king_extra) * (nk - ko)
        if material >= 0:
            score += material * 4 // (total + 6)
        else:
            score -= (-material) * 4 // (total + 6)

        if mm or om:
            mine = mm | mk
            theirs = om | ok

            if up:
                supported_mine = (
                    ((mine & um3) << 3)
                    | ((mine & um4) << 4)
                    | ((mine & um5) << 5)
                )
                supported_theirs = (
                    ((theirs & dm3) >> 3)
                    | ((theirs & dm4) >> 4)
                    | ((theirs & dm5) >> 5)
                )
            else:
                supported_mine = (
                    ((mine & dm3) >> 3)
                    | ((mine & dm4) >> 4)
                    | ((mine & dm5) >> 5)
                )
                supported_theirs = (
                    ((theirs & um3) << 3)
                    | ((theirs & um4) << 4)
                    | ((theirs & um5) << 5)
                )

            score += 3 * (
                (mm & supported_mine).bit_count()
                - (om & supported_theirs).bit_count()
            )

        if total <= 8:
            if material > 60 and mk and (om | ok):
                score -= pursuit(mk, om | ok)
            elif material < -60 and ok and (mm | mk):
                score += pursuit(ok, mm | mk)

        return score

    def order_moves(moves, mm, mk, ok, up, preferred, ply):
        if len(moves) < 2:
            return

        hist = history[up]
        killer1, killer2 = killers[ply]
        men_pst = man_values[up]
        crown = 0xF0000000 if up else 0xF

        def priority(move):
            if move == preferred:
                return 1000000000

            source, target, captured = move
            is_king = bool(source & mk)
            promotes = not is_king and bool(target & crown)

            if is_king:
                delta = king_values[target] - king_values[source]
            elif promotes:
                delta = king_values[target] - men_pst[source]
            else:
                delta = men_pst[target] - men_pst[source]

            value = 16 * delta + hist.get(move, 0)
            if captured:
                value += 150000
                if captured & ok:
                    value += 25000
            else:
                if move == killer1:
                    value += 200000
                elif move == killer2:
                    value += 190000

            if promotes:
                value += 50000
            return value

        moves.sort(key=priority, reverse=True)

    def search(mm, mk, om, ok, up, depth, alpha, beta, ply):
        nonlocal nodes
        nodes += 1
        if (nodes & 127) == 0 and perf_counter() >= deadline:
            raise _Timeout

        if not (mm | mk):
            return -MATE + ply
        if not (om | ok):
            return MATE - ply
        if ply >= 94:
            return evaluate(mm, mk, om, ok, up)

        key = (mm, mk, om, ok, up)
        if key in path:
            return 0

        original_alpha = alpha
        entry = tt.get(key)
        preferred = None
        if entry is not None:
            stored_depth, value, bound, preferred = entry
            if value > 29000:
                value -= ply
            elif value < -29000:
                value += ply

            if stored_depth >= depth:
                if bound == 0:
                    return value
                if bound == 1 and value >= beta:
                    return value
                if bound == 2 and value <= alpha:
                    return value

        moves = generate(mm, mk, om, ok, up)
        if not moves:
            return -MATE + ply

        capturing = bool(moves[0][2])

        if depth == 0 and not capturing:
            value = evaluate(mm, mk, om, ok, up)
            if entry is None or entry[0] == 0:
                tt[key] = (0, value, 0, None)
            return value

        order_moves(moves, mm, mk, ok, up, preferred, ply)
        path.add(key)

        next_depth = max(0, depth - 1)
        if capturing and len(moves) == 1 and depth > 0:
            next_depth = depth

        best_value = -INF
        best_move = moves[0]
        crown = 0xF0000000 if up else 0xF

        for index, move in enumerate(moves):
            child = play(mm, mk, om, ok, up, move)
            promotes = bool((move[0] & mm) and (move[1] & crown))

            reduce = (
                depth >= 5
                and ply > 0
                and index >= 4
                and not capturing
                and not promotes
                and move != preferred
                and move not in killers[ply]
            )

            if reduce:
                value = -search(
                    *child, next_depth - 1,
                    -alpha - 1, -alpha, ply + 1
                )
                if value > alpha:
                    value = -search(
                        *child, next_depth,
                        -alpha - 1, -alpha, ply + 1
                    )
                    if alpha < value < beta:
                        value = -search(
                            *child, next_depth,
                            -beta, -alpha, ply + 1
                        )
            elif index == 0 or depth < 3:
                value = -search(
                    *child, next_depth, -beta, -alpha, ply + 1
                )
            else:
                value = -search(
                    *child, next_depth,
                    -alpha - 1, -alpha, ply + 1
                )
                if alpha < value < beta:
                    value = -search(
                        *child, next_depth, -beta, -alpha, ply + 1
                    )

            if value > best_value:
                best_value = value
                best_move = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                if not capturing:
                    pair = killers[ply]
                    if pair[0] != move:
                        pair[1] = pair[0]
                        pair[0] = move
                    hist = history[up]
                    hist[move] = min(
                        100000,
                        hist.get(move, 0) + depth * depth * 8
                    )
                break

        path.remove(key)

        if best_value <= original_alpha:
            bound = 2
        elif best_value >= beta:
            bound = 1
        else:
            bound = 0

        stored_value = best_value
        if stored_value > 29000:
            stored_value += ply
        elif stored_value < -29000:
            stored_value -= ply

        if entry is None or depth >= entry[0]:
            tt[key] = (depth, stored_value, bound, best_move)

        return best_value

    legal_moves = generate(*root)

    # The arena invokes the policy only when a legal move exists.
    chosen = legal_moves[0]

    if len(legal_moves) > 1:
        previous = tt.get(root)
        preferred = previous[3] if previous is not None else None
        order_moves(
            legal_moves, root[0], root[1], root[3],
            root[4], preferred, 0
        )
        chosen = legal_moves[0]
        last_score = 0

        try:
            for depth in range(1, 65):
                if perf_counter() >= deadline:
                    break

                if depth >= 4:
                    alpha = max(-INF, last_score - 45)
                    beta = min(INF, last_score + 45)
                else:
                    alpha, beta = -INF, INF

                score = search(*root, depth, alpha, beta, 0)

                if score <= alpha or score >= beta:
                    score = search(*root, depth, -INF, INF, 0)

                result = tt.get(root)
                if result is not None and result[3] in legal_moves:
                    chosen = result[3]

                last_score = score
                if abs(score) > 29000:
                    break

        except _Timeout:
            pass

    source, target, _ = chosen
    squares = geometry["squares"]
    return (
        squares[source.bit_length() - 1],
        squares[target.bit_length() - 1],
    )
