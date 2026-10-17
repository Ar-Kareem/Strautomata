
from time import perf_counter as _clock

_FULL = (1 << 64) - 1
_NOT_A = 0xFEFEFEFEFEFEFEFE
_NOT_H = 0x7F7F7F7F7F7F7F7F

_BITS = tuple(1 << s for s in range(64))
_ROWS = tuple(s >> 3 for s in range(64))
_COLS = tuple(s & 7 for s in range(64))
_SQUARES = tuple(_ROWS[s] ** 2 + _COLS[s] ** 2 for s in range(64))
_CENTRAL = tuple(
    14 - abs(2 * _ROWS[s] - 7) - abs(2 * _COLS[s] - 7)
    for s in range(64)
)

_WIN = 1000000
_INF = 2000000
_EXACT, _LOWER, _UPPER = 0, 1, 2


def _expand(bits):
    horizontal = (
        bits
        | ((bits << 1) & _NOT_A)
        | ((bits >> 1) & _NOT_H)
    )
    return (
        horizontal | (horizontal << 8) | (horizontal >> 8)
    ) & _FULL


_NEIGHBORS = tuple(_expand(b) ^ b for b in _BITS)


def _make_move_tables():
    tables = []
    axes = ((0, 1), (1, 0), (1, 1), (1, -1))

    for source in range(64):
        row, col = divmod(source, 8)
        source_tables = []

        for dr, dc in axes:
            line = _BITS[source]
            for sign in (-1, 1):
                rr, cc = row + sign * dr, col + sign * dc
                while 0 <= rr < 8 and 0 <= cc < 8:
                    line |= _BITS[rr * 8 + cc]
                    rr += sign * dr
                    cc += sign * dc

            distances = [()]
            for distance in range(1, 9):
                options = []
                for sign in (-1, 1):
                    rr = row + sign * dr * distance
                    cc = col + sign * dc * distance
                    if not (0 <= rr < 8 and 0 <= cc < 8):
                        continue

                    destination = rr * 8 + cc
                    between = 0
                    for step in range(1, distance):
                        r = row + sign * dr * step
                        c = col + sign * dc * step
                        between |= _BITS[r * 8 + c]

                    options.append((
                        _BITS[destination],
                        between,
                        (source << 6) | destination,
                    ))
                distances.append(tuple(options))

            source_tables.append((line, tuple(distances)))

        tables.append(tuple(source_tables))

    return tuple(tables)


_MOVE_TABLES = _make_move_tables()


def _legal_moves(me, opponent):
    occupied = me | opponent
    remaining = me
    moves = []

    while remaining:
        source_bit = remaining & -remaining
        remaining ^= source_bit
        source = source_bit.bit_length() - 1

        for line, distances in _MOVE_TABLES[source]:
            distance = (occupied & line).bit_count()
            for destination_bit, between, move in distances[distance]:
                if not (destination_bit & me) and not (between & opponent):
                    moves.append(move)

    return moves


def _pack_score(score, ply):
    if score > _WIN - 1000:
        return score + ply
    if score < -_WIN + 1000:
        return score - ply
    return score


def _unpack_score(score, ply):
    if score > _WIN - 1000:
        return score - ply
    if score < -_WIN + 1000:
        return score + ply
    return score


class _Timeout(Exception):
    pass


class _Search:
    __slots__ = (
        "deadline", "features", "tt", "history",
        "killers", "nodes", "root_moves",
    )

    def __init__(self, deadline):
        self.deadline = deadline
        self.features = {}
        self.tt = {}
        self.history = [[0] * 4096 for _ in range(2)]
        self.killers = [[-1, -1] for _ in range(128)]
        self.nodes = 0
        self.root_moves = None

    def check_time(self):
        if _clock() >= self.deadline:
            raise _Timeout

    def shape(self, pieces):
        cached = self.features.get(pieces)
        if cached is not None:
            return cached

        if not pieces:
            result = (-10000, 0, 0, 0)
            self.features[pieces] = result
            return result

        groups = []
        remaining = pieces
        largest = 0

        while remaining:
            component = remaining & -remaining
            while True:
                grown = _expand(component) & pieces
                if grown == component:
                    break
                component = grown

            remaining ^= component
            groups.append(component)
            size = component.bit_count()
            if size > largest:
                largest = size

        count = len(groups)
        number = pieces.bit_count()

        if count == 1:
            result = (10000, 1, number, number)
            self.features[pieces] = result
            return result

        sum_row = 0
        sum_col = 0
        sum_squared = 0
        remaining = pieces
        while remaining:
            bit = remaining & -remaining
            remaining ^= bit
            square = bit.bit_length() - 1
            sum_row += _ROWS[square]
            sum_col += _COLS[square]
            sum_squared += _SQUARES[square]

        denominator = number * number
        variance_numerator = (
            number * sum_squared
            - sum_row * sum_row
            - sum_col * sum_col
        )
        center_numerator = (
            (2 * sum_row - 7 * number) ** 2
            + (2 * sum_col - 7 * number) ** 2
        )

        gap_cost = 0
        singleton_count = 0
        for component in groups:
            if component & (component - 1) == 0:
                singleton_count += 1

            other_groups = pieces ^ component
            reached = component
            distance = 0
            while not (reached & other_groups):
                reached = _expand(reached)
                distance += 1
            gap_cost += (distance - 1) ** 2

        contacts = (
            (pieces & (pieces >> 1) & _NOT_H).bit_count()
            + (pieces & (pieces >> 8)).bit_count()
            + (pieces & (pieces >> 9) & _NOT_H).bit_count()
            + (pieces & (pieces >> 7) & _NOT_A).bit_count()
        )

        score = (
            -70 * (count - 1)
            -16 * (number - largest)
            +120 * largest // number
            -18 * variance_numerator // denominator
            -3 * center_numerator // (4 * denominator)
            -10 * gap_cost
            -8 * singleton_count
            +12 * contacts // number
            +3 * number
        )

        result = (score, count, number, largest)
        self.features[pieces] = result
        return result

    def store(self, key, depth, flag, score, move, ply):
        old = self.tt.get(key)
        if old is None or old[0] <= depth:
            self.tt[key] = (
                depth, flag, _pack_score(score, ply), move
            )

    def search(self, me, opponent, depth, alpha, beta, ply):
        self.nodes += 1
        if self.nodes & 31 == 0:
            self.check_time()

        if not me:
            return -_WIN + ply
        if not opponent:
            return _WIN - ply

        mine = self.shape(me)
        theirs = self.shape(opponent)

        # At a child node, "opponent" made the preceding move.
        # Thus the preceding mover wins if both sides became connected.
        if theirs[1] == 1:
            return -_WIN + ply
        if mine[1] == 1:
            return _WIN - ply

        if depth <= 0:
            return mine[0] - theirs[0]

        key = (me, opponent)
        entry = self.tt.get(key)
        hash_move = -1
        if entry is not None:
            stored_depth, flag, stored_score, hash_move = entry
            if stored_depth >= depth:
                score = _unpack_score(stored_score, ply)
                if flag == _EXACT:
                    return score
                if flag == _LOWER and score >= beta:
                    return score
                if flag == _UPPER and score <= alpha:
                    return score

        moves = (
            self.root_moves if ply == 0
            else _legal_moves(me, opponent)
        )

        if not moves:
            # A blocked player passes in the internal game tree.
            return -self.search(
                opponent, me, depth - 1, -beta, -alpha, ply + 1
            )

        history = self.history[ply & 1]
        killer_one, killer_two = self.killers[ply]
        ranked = []

        for index, move in enumerate(moves):
            if index & 15 == 0:
                self.check_time()

            if move == hash_move:
                ranked.append((100000000, move))
                continue

            source = move >> 6
            destination = move & 63
            source_bit = _BITS[source]
            destination_bit = _BITS[destination]

            if depth >= 2:
                new_me = (me ^ source_bit) | destination_bit
                new_opponent = opponent & ~destination_bit
                child_mine = self.shape(new_me)

                if child_mine[1] == 1 or not new_opponent:
                    score = _WIN - ply - 1
                    self.store(
                        key, depth, _EXACT, score, move, ply
                    )
                    return score

                child_theirs = (
                    self.shape(new_opponent)
                    if new_opponent != opponent else theirs
                )

                if child_theirs[1] == 1:
                    positional = -_WIN
                else:
                    positional = child_mine[0] - child_theirs[0]

                priority = 8 * positional + history[move]
                if move == killer_one:
                    priority += 600
                elif move == killer_two:
                    priority += 400
            else:
                contacts_added = (
                    _NEIGHBORS[destination] & (me ^ source_bit)
                ).bit_count()
                contacts_removed = (
                    _NEIGHBORS[source] & me
                ).bit_count()

                priority = (
                    32 * (contacts_added - contacts_removed)
                    + 3 * (_CENTRAL[destination] - _CENTRAL[source])
                    + history[move]
                    + (6 if destination_bit & opponent else 0)
                )
                if move == killer_one:
                    priority += 1000
                elif move == killer_two:
                    priority += 800

            ranked.append((priority, move))

        ranked.sort(reverse=True)
        original_alpha = alpha
        best_score = -_INF
        best_move = ranked[0][1]

        for index, (_, move) in enumerate(ranked):
            if ply == 0 or index & 15 == 0:
                self.check_time()

            source_bit = _BITS[move >> 6]
            destination_bit = _BITS[move & 63]
            new_me = (me ^ source_bit) | destination_bit
            new_opponent = opponent & ~destination_bit

            if depth == 1:
                child_mine = self.shape(new_me)
                if child_mine[1] == 1 or not new_opponent:
                    score = _WIN - ply - 1
                    self.store(
                        key, depth, _EXACT, score, move, ply
                    )
                    return score

                child_theirs = (
                    self.shape(new_opponent)
                    if new_opponent != opponent else theirs
                )
                if child_theirs[1] == 1:
                    score = -_WIN + ply + 1
                else:
                    score = child_mine[0] - child_theirs[0]

            elif index == 0:
                score = -self.search(
                    new_opponent, new_me, depth - 1,
                    -beta, -alpha, ply + 1
                )
            else:
                reduction = 0
                if (
                    depth >= 3
                    and ply > 0
                    and index >= 6
                    and new_opponent == opponent
                    and move != killer_one
                    and move != killer_two
                    and theirs[1] > 2
                    and self.shape(new_me)[1] > 2
                ):
                    reduction = 1

                score = -self.search(
                    new_opponent, new_me,
                    depth - 1 - reduction,
                    -alpha - 1, -alpha, ply + 1
                )

                if reduction and score > alpha:
                    score = -self.search(
                        new_opponent, new_me, depth - 1,
                        -alpha - 1, -alpha, ply + 1
                    )

                if alpha < score < beta:
                    score = -self.search(
                        new_opponent, new_me, depth - 1,
                        -beta, -alpha, ply + 1
                    )

            if score > best_score:
                best_score = score
                best_move = move

            if score > alpha:
                alpha = score

            if alpha >= beta:
                if move != self.killers[ply][0]:
                    self.killers[ply][1] = self.killers[ply][0]
                    self.killers[ply][0] = move
                history[move] += depth * depth
                break

        if best_score <= original_alpha:
            flag = _UPPER
        elif best_score >= beta:
            flag = _LOWER
        else:
            flag = _EXACT

        self.store(
            key, depth, flag, best_score, best_move, ply
        )
        return best_score


def _format_move(move):
    source = move >> 6
    destination = move & 63
    return (
        f"{source >> 3},{source & 7}:"
        f"{destination >> 3},{destination & 7}"
    )


def policy(board) -> str:
    started = _clock()
    me = 0
    opponent = 0

    for row in range(8):
        for col in range(8):
            value = board[row][col]
            bit = _BITS[row * 8 + col]
            if value == 1:
                me |= bit
            elif value == -1:
                opponent |= bit

    moves = _legal_moves(me, opponent)

    # The arena calls the policy on positions requiring a legal move.
    # Save a generated legal move before doing any timed search.
    best_move = moves[0]

    engine = _Search(started + 0.88)
    engine.root_moves = moves
    opponent_shape = engine.shape(opponent)
    best_score = -_INF

    # Complete a cheap one-ply search first, ensuring a useful fallback.
    for move in moves:
        source_bit = _BITS[move >> 6]
        destination_bit = _BITS[move & 63]
        new_me = (me ^ source_bit) | destination_bit
        new_opponent = opponent & ~destination_bit
        mine = engine.shape(new_me)

        if mine[1] == 1 or not new_opponent:
            return _format_move(move)

        theirs = (
            engine.shape(new_opponent)
            if new_opponent != opponent else opponent_shape
        )
        if theirs[1] == 1:
            score = -_WIN + 1
        else:
            score = mine[0] - theirs[0]

        if score > best_score:
            best_score = score
            best_move = move

    root_key = (me, opponent)
    engine.tt[root_key] = (1, _EXACT, best_score, best_move)

    for depth in range(2, 64):
        try:
            engine.check_time()
            score = engine.search(
                me, opponent, depth, -_INF, _INF, 0
            )
            entry = engine.tt.get(root_key)
            if entry is not None:
                best_move = entry[3]

            if score >= _WIN - 128:
                break
        except _Timeout:
            break

    return _format_move(best_move)
