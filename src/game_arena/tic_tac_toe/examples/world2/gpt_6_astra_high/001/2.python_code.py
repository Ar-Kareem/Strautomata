
from array import array
from time import perf_counter


_ALL = (1 << 16) - 1
_LINES = (
    0x000F, 0x00F0, 0x0F00, 0xF000,
    0x1111, 0x2222, 0x4444, 0x8888,
    0x8421, 0x1248,
)

_PREFERRED = (5, 6, 9, 10, 0, 3, 12, 15, 1, 2, 4, 7, 8, 11, 13, 14)
_PRIORITY = [0] * 16
for _rank, _square in enumerate(_PREFERRED):
    _PRIORITY[_square] = 16 - _rank

_TABLES = None
_TT = {}
_MATE = 100000
_INF = 1000000
_EXACT, _LOWER, _UPPER = 0, 1, 2
_SOLVED = 32


class _SearchTimeout(Exception):
    pass


def _make_symmetries():
    mappings = []
    for reflect in range(2):
        for rotation in range(4):
            mapping = []
            for square in range(16):
                r, c = divmod(square, 4)
                if reflect:
                    c = 3 - c
                for _ in range(rotation):
                    r, c = c, 3 - r
                mapping.append(1 << (4 * r + c))
            mappings.append(tuple(mapping))
    return tuple(mappings)


_SYMMETRIES = _make_symmetries()


def _transform(bits, mapping):
    result = 0
    while bits:
        bit = bits & -bits
        bits ^= bit
        result |= mapping[bit.bit_length() - 1]
    return result


def _immediate_moves(player, empty):
    result = 0
    for line in _LINES:
        missing = line & ~player
        if missing and not (missing & (missing - 1)):
            result |= missing & empty
    return result


def _quick_evaluation(player, opponent):
    weights = (0, 3, 20, 150, _MATE)
    value = 0
    for line in _LINES:
        if not (line & opponent):
            value += weights[(line & player).bit_count()]
        if not (line & player):
            value -= weights[(line & opponent).bit_count()]
    return value


def _initialize_tables():
    global _TABLES
    if _TABLES is not None:
        return _TABLES

    # For each bitboard, record which lines contain 0, 1, or 2 marks.
    zero = array("H", [0]) * 65536
    one = array("H", [0]) * 65536
    two = array("H", [0]) * 65536
    threats = array("H", [0]) * 65536

    covers = {}
    for square in range(16):
        bit = 1 << square
        covers[bit] = sum(
            1 << i for i, line in enumerate(_LINES) if line & bit
        )

    zero[0] = 1023
    for mask in range(1, 65536):
        bit = mask & -mask
        previous = mask ^ bit
        cover = covers[bit]
        outside = 1023 ^ cover
        z = zero[previous]
        o = one[previous]
        zero[mask] = z & outside
        one[mask] = (o & outside) | (z & cover)
        two[mask] = (two[previous] & outside) | (o & cover)

    # threats[player] contains squares completing a four-in-a-row.
    # Filtering it by the actual empty squares removes blocked threats.
    for line in _LINES:
        outside = _ALL ^ line
        missing_bits = line
        while missing_bits:
            missing = missing_bits & -missing_bits
            missing_bits ^= missing
            triple = line ^ missing
            subset = outside
            while True:
                index = triple | subset
                threats[index] |= missing
                if subset == 0:
                    break
                subset = (subset - 1) & outside

    # Union of the board squares covered by any specified set of lines.
    live = array("H", [0]) * 1024
    for mask in range(1, 1024):
        bit = mask & -mask
        live[mask] = live[mask ^ bit] | _LINES[bit.bit_length() - 1]

    _TABLES = zero, one, two, threats, live
    return _TABLES


def policy(board: list[list[int]]) -> tuple[int, int]:
    global _TT

    started = perf_counter()
    deadline = started + 0.86

    player = 0
    opponent = 0
    for r in range(4):
        for c in range(4):
            bit = 1 << (4 * r + c)
            if board[r][c] == 1:
                player |= bit
            elif board[r][c] == -1:
                opponent |= bit

    empty = _ALL ^ (player | opponent)

    # A full board has no legal action; normal game calls never reach this.
    if not empty:
        return (0, 0)

    def coordinates(bit):
        return divmod(bit.bit_length() - 1, 4)

    wins = _immediate_moves(player, empty)
    if wins:
        return coordinates(wins & -wins)

    legal = [1 << i for i in _PREFERRED if empty & (1 << i)]
    opposing_wins = _immediate_moves(opponent, empty)

    if opposing_wins:
        # A single threat must be blocked. If already lost to a double
        # threat, still block one and present the strongest counterplay.
        choices = [bit for bit in legal if bit & opposing_wins]
        move = max(
            choices,
            key=lambda bit: _quick_evaluation(player | bit, opponent),
        )
        return coordinates(move)

    if not (player | opponent):
        return (1, 1)

    fallback = max(
        legal,
        key=lambda bit: _quick_evaluation(player | bit, opponent),
    )

    # With no opposing immediate win, a double threat wins in three plies.
    if player.bit_count() >= 4:
        for bit in legal:
            threats_after = _immediate_moves(player | bit, empty ^ bit)
            if threats_after & (threats_after - 1):
                return coordinates(bit)

    remaining = empty.bit_count()
    if remaining <= 3:
        return coordinates(fallback)

    zero, one, two, threats, live = _initialize_tables()

    if len(_TT) > 200000:
        _TT = {}
    tt = _TT

    if perf_counter() >= deadline:
        return coordinates(fallback)

    killers = [[0, 0] for _ in range(17)]
    history = [[0] * 16 for _ in range(2)]
    symmetry_cache = {}
    nodes = 0
    clock = perf_counter

    def evaluate(p, o):
        p_open = zero[o]
        o_open = zero[p]
        return (
            3 * (
                (one[p] & p_open).bit_count()
                - (one[o] & o_open).bit_count()
            )
            + 20 * (
                (two[p] & p_open).bit_count()
                - (two[o] & o_open).bit_count()
            )
        )

    def search(p, o, depth, alpha, beta, n, ply):
        nonlocal nodes
        nodes += 1
        if (nodes & 127) == 0 and clock() >= deadline:
            raise _SearchTimeout

        if n == 0:
            return 0

        key = p | (o << 16)
        entry = tt.get(key)
        hash_move = 0

        if entry is not None:
            old_depth, value, flag, hash_move = entry
            if old_depth >= depth:
                if flag == _EXACT:
                    return value
                if flag == _LOWER and value >= beta:
                    return value
                if flag == _UPPER and value <= alpha:
                    return value

        available = _ALL ^ (p | o)
        winning = threats[p] & available
        if winning:
            move = winning & -winning
            value = _MATE + n - 1
            tt[key] = (_SOLVED, value, _EXACT, move)
            return value

        must_block = threats[o] & available
        if must_block & (must_block - 1):
            value = -_MATE - n + 2
            tt[key] = (
                _SOLVED, value, _EXACT, must_block & -must_block
            )
            return value

        original_alpha = alpha

        if must_block:
            # Forced replies do not consume the nominal search depth.
            move = must_block
            value = -search(
                o, p | move, depth, -beta, -alpha, n - 1, ply + 1
            )
            flag = (
                _UPPER if value <= original_alpha
                else _LOWER if value >= beta
                else _EXACT
            )
            stored_depth = depth
            if flag == _EXACT and (
                abs(value) >= _MATE or depth >= n
            ):
                stored_depth = _SOLVED
            tt[key] = (stored_depth, value, flag, move)
            return value

        open_lines = zero[p] | zero[o]
        if not open_lines:
            move = available & -available
            tt[key] = (_SOLVED, 0, _EXACT, move)
            return 0

        if n <= 2:
            move = available & -available
            tt[key] = (_SOLVED, 0, _EXACT, move)
            return 0

        if depth == 0 and p.bit_count() < 4 and o.bit_count() < 4:
            value = evaluate(p, o)
            tt[key] = (0, value, _EXACT, 0)
            return value

        # Squares on permanently blocked lines are interchangeable passes.
        move_mask = available & live[open_lines]
        dead = available & ~move_mask
        if dead:
            representative = (
                hash_move if hash_move & dead else dead & -dead
            )
            move_mask |= representative

        candidates = []
        fork_defense = _ALL
        can_opponent_fork = o.bit_count() >= 4
        bits = move_mask

        while bits:
            move = bits & -bits
            bits ^= move
            after_empty = available ^ move
            checks = threats[p | move] & after_empty

            if checks & (checks - 1):
                value = _MATE + n - 3
                tt[key] = (_SOLVED, value, _EXACT, move)
                return value

            candidates.append((move, bool(checks)))

            if can_opponent_fork:
                opposing_checks = threats[o | move] & after_empty
                if opposing_checks & (opposing_checks - 1):
                    # Stop this fork by taking its origin, or, when it
                    # has exactly two endpoints, by taking an endpoint.
                    defense = move
                    if opposing_checks.bit_count() == 2:
                        defense |= opposing_checks
                    fork_defense &= defense

        if n <= 3:
            move = candidates[0][0]
            tt[key] = (_SOLVED, 0, _EXACT, move)
            return 0

        safe = [
            (move, checking)
            for move, checking in candidates
            if checking or (move & fork_defense)
        ]

        if not safe:
            value = -_MATE - n + 4
            move = candidates[0][0]
            tt[key] = (_SOLVED, value, _EXACT, move)
            return value

        # Resolve immediate fork danger even beyond the nominal horizon.
        if depth == 0 and fork_defense == _ALL:
            value = evaluate(p, o)
            tt[key] = (0, value, _EXACT, 0)
            return value

        ordered = []
        killer1, killer2 = killers[ply]
        hist = history[ply & 1]

        for move, checking in safe:
            square = move.bit_length() - 1
            ordering = (
                8 * evaluate(p | move, o)
                + _PRIORITY[square]
                + (hist[square] >> 2)
            )
            if checking:
                ordering += 10000
            if move == killer1:
                ordering += 160
            elif move == killer2:
                ordering += 80
            if move == hash_move:
                ordering += 1000000
            ordered.append((ordering, move))

        ordered.sort(reverse=True)

        invariant_symmetries = ()
        if n >= 12 or ply == 0:
            invariant_symmetries = symmetry_cache.get(key)
            if invariant_symmetries is None:
                invariant_symmetries = tuple(
                    mapping
                    for mapping in _SYMMETRIES[1:]
                    if _transform(p, mapping) == p
                    and _transform(o, mapping) == o
                )
                symmetry_cache[key] = invariant_symmetries

        seen = 0
        best_value = -_INF
        best_move = ordered[0][1]
        next_depth = max(0, depth - 1)
        first = True

        for _, move in ordered:
            if seen & move:
                continue

            if invariant_symmetries:
                square = move.bit_length() - 1
                seen |= move
                for mapping in invariant_symmetries:
                    seen |= mapping[square]

            if first:
                value = -search(
                    o, p | move, next_depth,
                    -beta, -alpha, n - 1, ply + 1,
                )
                first = False
            else:
                # Principal-variation search: most later moves need only
                # a narrow-window test.
                value = -search(
                    o, p | move, next_depth,
                    -alpha - 1, -alpha, n - 1, ply + 1,
                )
                if alpha < value < beta:
                    value = -search(
                        o, p | move, next_depth,
                        -beta, -alpha, n - 1, ply + 1,
                    )

            if value > best_value:
                best_value = value
                best_move = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                square = move.bit_length() - 1
                hist[square] = min(
                    2048, hist[square] + max(1, depth * depth)
                )
                if move != killers[ply][0]:
                    killers[ply][1] = killers[ply][0]
                    killers[ply][0] = move
                break

        flag = (
            _UPPER if best_value <= original_alpha
            else _LOWER if best_value >= beta
            else _EXACT
        )
        stored_depth = depth
        if flag == _EXACT and (
            abs(best_value) >= _MATE or depth >= n
        ):
            stored_depth = _SOLVED

        tt[key] = (stored_depth, best_value, flag, best_move)
        return best_value

    chosen = fallback
    previous_score = 0
    root_key = player | (opponent << 16)

    for depth in range(1, remaining + 1):
        if clock() >= deadline:
            break

        try:
            if depth == 1:
                score = search(
                    player, opponent, depth,
                    -_INF, _INF, remaining, 0,
                )
            else:
                low = previous_score - 64
                high = previous_score + 64
                score = search(
                    player, opponent, depth,
                    low, high, remaining, 0,
                )
                if score <= low or score >= high:
                    score = search(
                        player, opponent, depth,
                        -_INF, _INF, remaining, 0,
                    )

            root_entry = tt.get(root_key)
            if root_entry is not None:
                move = root_entry[3]
                if move and (move & empty):
                    chosen = move

            previous_score = score

            if abs(score) >= _MATE:
                break
            if (
                root_entry is not None
                and root_entry[0] >= remaining
                and root_entry[2] == _EXACT
            ):
                break

        except _SearchTimeout:
            break

    # Only a move from a completed search iteration can replace fallback.
    chosen &= empty
    if not chosen:
        chosen = fallback
    return coordinates(chosen & -chosen)
