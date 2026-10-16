
import time

_FULL = (1 << 16) - 1
_MATE = 10000
_INF = 20000

_LINES = tuple(
    [sum(1 << (4 * r + c) for c in range(4)) for r in range(4)]
    + [sum(1 << (4 * r + c) for r in range(4)) for c in range(4)]
    + [
        sum(1 << (4 * i + i) for i in range(4)),
        sum(1 << (4 * i + 3 - i) for i in range(4)),
    ]
)

_TABLES = None


class _SearchTimeout(Exception):
    pass


def _build_tables():
    """Precompute compact descriptions of every possible player bitboard."""
    cell_lines = {}
    for cell in range(16):
        bit = 1 << cell
        cell_lines[bit] = sum(
            1 << j for j, line in enumerate(_LINES) if line & bit
        )

    # For each subset of winning lines, record their union and all cells
    # belonging to at least two of those lines.
    unions = [0] * 1024
    intersections = [0] * 1024
    for subset in range(1, 1024):
        bit = subset & -subset
        rest = subset ^ bit
        line = _LINES[bit.bit_length() - 1]
        unions[subset] = unions[rest] | line
        intersections[subset] = (
            intersections[rest] | (unions[rest] & line)
        )

    low = [0] * 65536
    high = [0] * 65536
    touched = [0] * 65536
    ones = [0] * 65536
    twos = [0] * 65536
    threes = [0] * 65536
    winning_moves = [0] * 65536

    for mask in range(1, 65536):
        rest = mask & (mask - 1)
        incident = cell_lines[mask ^ rest]

        old_low = low[rest]
        new_low = old_low ^ incident
        new_high = high[rest] ^ (old_low & incident)

        low[mask] = new_low
        high[mask] = new_high
        touched[mask] = touched[rest] | incident
        ones[mask] = new_low & ~new_high
        twos[mask] = new_high & ~new_low

        triple_lines = new_low & new_high
        threes[mask] = triple_lines
        winning_moves[mask] = unions[triple_lines] & (_FULL ^ mask)

    return touched, ones, twos, threes, winning_moves, intersections


def _coordinates(bit):
    return divmod(bit.bit_length() - 1, 4)


def policy(board: list[list[int]]) -> tuple[int, int]:
    global _TABLES

    deadline = time.perf_counter() + 0.86

    me = 0
    opponent = 0
    for r in range(4):
        for c in range(4):
            value = board[r][c]
            if value == 1:
                me |= 1 << (4 * r + c)
            elif value == -1:
                opponent |= 1 << (4 * r + c)

    empty = _FULL ^ (me | opponent)

    # A full board has no legal action; arena calls are expected to be
    # nonterminal.
    if not empty:
        return (0, 0)

    if not (me | opponent):
        return (1, 1)

    if not (empty & (empty - 1)):
        return _coordinates(empty)

    # Handle the most common forced moves without initializing tables.
    immediate = 0
    enemy_immediate = 0
    for line in _LINES:
        if not (line & opponent) and (line & me).bit_count() == 3:
            immediate |= line & empty
        if not (line & me) and (line & opponent).bit_count() == 3:
            enemy_immediate |= line & empty

    if immediate:
        return _coordinates(immediate & -immediate)

    if enemy_immediate and not (
        enemy_immediate & (enemy_immediate - 1)
    ):
        return _coordinates(enemy_immediate)

    if _TABLES is None:
        _TABLES = _build_tables()

    touched, ones, twos, threes, wins, intersections = _TABLES

    def evaluate(p, o):
        p_open = ~touched[o]
        o_open = ~touched[p]
        return (
            4 * (
                (ones[p] & p_open).bit_count()
                - (ones[o] & o_open).bit_count()
            )
            + 22 * (
                (twos[p] & p_open).bit_count()
                - (twos[o] & o_open).bit_count()
            )
            + 140 * (
                (threes[p] & p_open).bit_count()
                - (threes[o] & o_open).bit_count()
            )
        )

    def best_static(mask):
        best_bit = mask & -mask
        best_value = -_INF
        while mask:
            bit = mask & -mask
            mask ^= bit
            value = evaluate(me | bit, opponent)
            if value > best_value:
                best_value = value
                best_bit = bit
        return best_bit

    # If there are multiple immediate enemy wins, block one rather than
    # making an unrelated move, even though perfect defense is impossible.
    if enemy_immediate:
        return _coordinates(best_static(enemy_immediate))

    # Two open two-mark lines crossing at an empty cell create a fork.
    root_forks = intersections[twos[me] & ~touched[opponent]] & empty
    if root_forks:
        return _coordinates(best_static(root_forks))

    tt = {}
    history = {1 << i: 0 for i in range(16)}
    killers = [0] * 18
    nodes = 0

    def ordered_moves(p, o, available, tt_move, ply, enemy_forks):
        ranked = []
        remaining = available
        killer = killers[ply]

        while remaining:
            bit = remaining & -remaining
            remaining ^= bit

            new_p = p | bit
            after = available ^ bit
            forcing = bool(wins[new_p] & after)

            # Without a forcing threat, allowing an enemy fork loses
            # in four plies. Other moves cannot lose sooner here.
            if enemy_forks and not forcing:
                surviving_forks = (
                    intersections[twos[o] & ~touched[new_p]] & after
                )
                if surviving_forks:
                    continue

            score = evaluate(new_p, o)
            score += min(history[bit], 4096)
            if forcing:
                score += 8192
            if bit == killer:
                score += 2048
            if bit == tt_move:
                score += 1000000

            ranked.append((score, bit))

        ranked.sort(reverse=True)
        return [bit for _, bit in ranked]

    def search(p, o, depth, alpha, beta, ply):
        nonlocal nodes
        nodes += 1
        if (nodes & 255) == 0 and time.perf_counter() >= deadline:
            raise _SearchTimeout

        available = _FULL ^ (p | o)
        count = available.bit_count()

        if not available:
            return 0

        own_win = wins[p] & available
        if own_win:
            return _MATE + count

        enemy_win = wins[o] & available
        if enemy_win & (enemy_win - 1):
            return -(_MATE + count - 1)

        # With at most two empty cells and no immediate win or double
        # threat, neither player can force a win.
        if count <= 2:
            return 0

        if (touched[p] & touched[o]) == 1023:
            return 0

        forks = intersections[twos[p] & ~touched[o]] & available
        if forks and (not enemy_win or (forks & enemy_win)):
            return _MATE + count - 2

        key = (p << 16) | o
        entry = tt.get(key)
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

        original_alpha = alpha

        if enemy_win:
            # Forced blocks do not consume the ordinary search horizon.
            moves = [enemy_win]
            child_depth = depth
        else:
            enemy_forks = (
                intersections[twos[o] & ~touched[p]] & available
            )

            # Quiescence: stop only when immediate threats and fork
            # defenses have all been resolved.
            if depth <= 0 and not enemy_forks:
                return evaluate(p, o)

            moves = ordered_moves(
                p, o, available, tt_move, ply, enemy_forks
            )
            child_depth = max(0, depth - 1)

            if not moves:
                score = -(_MATE + count - 3)
                tt[key] = (
                    99, score, 0, available & -available
                )
                return score

        best_score = -_INF
        best_move = moves[0]

        for index, bit in enumerate(moves):
            if index == 0:
                score = -search(
                    o, p | bit, child_depth, -beta, -alpha, ply + 1
                )
            else:
                # Principal-variation search: test alternatives with a
                # narrow window before paying for a full re-search.
                score = -search(
                    o, p | bit, child_depth,
                    -alpha - 1, -alpha, ply + 1
                )
                if alpha < score < beta:
                    score = -search(
                        o, p | bit, child_depth,
                        -beta, -alpha, ply + 1
                    )

            if score > best_score:
                best_score = score
                best_move = bit

            if score > alpha:
                alpha = score

            if alpha >= beta:
                killers[ply] = bit
                history[bit] += (depth + 1) * (depth + 1)
                break

        if best_score <= original_alpha:
            flag = 2  # Upper bound.
        elif best_score >= beta:
            flag = 1  # Lower bound.
        else:
            flag = 0  # Exact for this search depth.

        tt[key] = (depth, best_score, flag, best_move)
        return best_score

    enemy_forks = (
        intersections[twos[opponent] & ~touched[me]] & empty
    )
    candidates = ordered_moves(
        me, opponent, empty, 0, 0, enemy_forks
    )

    if not candidates:
        return _coordinates(best_static(empty))

    best_move = candidates[0]

    # A sole safe move needs no further search.
    if len(candidates) == 1:
        return _coordinates(best_move)

    root_key = (me << 16) | opponent

    for depth in range(1, empty.bit_count() + 1):
        if time.perf_counter() >= deadline:
            break

        try:
            value = search(me, opponent, depth, -_INF, _INF, 0)
        except _SearchTimeout:
            break

        entry = tt.get(root_key)
        if entry is not None and (entry[3] & empty):
            best_move = entry[3]

        # Mate scores represent proven tactical results, not heuristics.
        if abs(value) >= _MATE:
            break

    # Retain only a move from a completed iteration, or the legal fallback.
    if not (best_move & empty):
        best_move = empty & -empty

    return _coordinates(best_move)
