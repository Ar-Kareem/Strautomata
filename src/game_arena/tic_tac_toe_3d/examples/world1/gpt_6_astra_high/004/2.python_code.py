
from itertools import permutations, product
from time import perf_counter


_FULL = (1 << 27) - 1
_CENTER = 1 << 13
_COORDS = tuple(product(range(3), repeat=3))

# Generate all 49 straight winning lines.
_line_set = set()
for direction in product((-1, 0, 1), repeat=3):
    if direction <= (0, 0, 0):
        continue
    dx, dy, dz = direction
    for x, y, z in _COORDS:
        ex, ey, ez = x + 2 * dx, y + 2 * dy, z + 2 * dz
        if 0 <= ex < 3 and 0 <= ey < 3 and 0 <= ez < 3:
            mask = 0
            for t in range(3):
                index = (x + t * dx) * 9 + (y + t * dy) * 3 + z + t * dz
                mask |= 1 << index
            _line_set.add(mask)

_LINES = tuple(sorted(_line_set))
_THROUGH = {
    1 << i: tuple(line for line in _LINES if line & (1 << i))
    for i in range(27)
}
_BASE = {bit: 20 * len(lines) for bit, lines in _THROUGH.items()}
_CORNERS = sum(
    1 << (9 * x + 3 * y + z)
    for x, y, z in product((0, 2), repeat=3)
)

# All rotations and reflections of the cube.
_symmetries = []
for axes in permutations(range(3)):
    for flips in product((False, True), repeat=3):
        mapping = []
        for xyz in _COORDS:
            v = [xyz[axes[t]] for t in range(3)]
            for t in range(3):
                if flips[t]:
                    v[t] = 2 - v[t]
            mapping.append(1 << (9 * v[0] + 3 * v[1] + v[2]))
        _symmetries.append(tuple(mapping))
_SYMMETRIES = tuple(_symmetries)


def _bits(mask):
    while mask:
        bit = mask & -mask
        yield bit
        mask ^= bit


def _coordinate(bit):
    index = bit.bit_length() - 1
    return index // 9, (index // 3) % 3, index % 3


def _analyze(me, opponent):
    wins = enemy_wins = forks = enemy_forks = 0
    attacks = enemy_attacks = 0
    single_difference = 0
    blank_lines = []

    for line in _LINES:
        a = line & me
        b = line & opponent
        if a:
            if b:
                continue
            missing = line ^ a
            if a & (a - 1):
                wins |= missing
            else:
                forks |= attacks & missing
                attacks |= missing
                single_difference += 1
        elif b:
            missing = line ^ b
            if b & (b - 1):
                enemy_wins |= missing
            else:
                enemy_forks |= enemy_attacks & missing
                enemy_attacks |= missing
                single_difference -= 1
        else:
            blank_lines.append(line)

    return (
        wins, enemy_wins, forks, enemy_forks,
        attacks, enemy_attacks, single_difference, blank_lines
    )


def _safe_moves(me, opponent, empty, attacks, enemy_forks):
    """
    Against an opponent fork, either create an immediate threat or
    neutralize every fork location.
    """
    defenses = empty
    for fork in _bits(enemy_forks):
        if not defenses:
            break

        choices = fork
        count = 0
        for line in _THROUGH[fork]:
            if line & me:
                continue
            stones = line & opponent
            if stones and not (stones & (stones - 1)):
                count += 1
                if count >= 3:
                    # A move elsewhere can destroy at most one of
                    # the independent lines passing through this cell.
                    choices = fork
                    break
                choices |= line & empty
        defenses &= choices

    return (attacks | defenses) & empty


class _SearchTimeout(Exception):
    pass


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    start = perf_counter()
    deadline = start + 0.90

    me = opponent = 0
    for index, (i, j, k) in enumerate(_COORDS):
        value = board[i][j][k]
        if value == 1:
            me |= 1 << index
        elif value == -1:
            opponent |= 1 << index

    empty = _FULL ^ (me | opponent)
    if not empty:
        # No legal action exists on a full board.
        return (0, 0, 0)
    if empty == _FULL:
        return (1, 1, 1)

    stats = _analyze(me, opponent)
    wins, enemy_wins, forks, enemy_forks, attacks, enemy_attacks, _, _ = stats

    if wins:
        return _coordinate(wins & -wins)
    if enemy_wins:
        # A single threat has a unique defense. With multiple threats,
        # blocking one is still a legal best-effort action.
        choice = max(
            _bits(enemy_wins),
            key=lambda b: (bool(b & forks), _BASE[b])
        )
        return _coordinate(choice)
    if forks:
        return _coordinate(max(_bits(forks), key=_BASE.__getitem__))

    candidates = empty
    if enemy_forks:
        safe = _safe_moves(me, opponent, empty, attacks, enemy_forks)
        if safe:
            candidates = safe
        else:
            return _coordinate(max(
                _bits(empty),
                key=lambda b: (bool(b & enemy_forks), _BASE[b])
            ))

    if not (candidates & (candidates - 1)):
        return _coordinate(candidates)

    MATE = 100000
    INF = 1000000
    EXACT, LOWER, UPPER = 0, 1, 2

    table = {}
    symmetry_cache = {}
    history = [[0] * 27 for _ in range(2)]
    killers = [[0, 0] for _ in range(32)]
    nodes = 0

    def representatives(p, q):
        key = (p, q)
        cached = symmetry_cache.get(key)
        if cached is not None:
            return cached

        pi = [b.bit_length() - 1 for b in _bits(p)]
        qi = [b.bit_length() - 1 for b in _bits(q)]
        group = []
        for mapping in _SYMMETRIES:
            if sum(mapping[i] for i in pi) != p:
                continue
            if sum(mapping[i] for i in qi) == q:
                group.append(mapping)

        available = _FULL ^ (p | q)
        if len(group) <= 1:
            symmetry_cache[key] = available
            return available

        seen = result = 0
        for bit in _bits(available):
            if seen & bit:
                continue
            result |= bit
            index = bit.bit_length() - 1
            for mapping in group:
                seen |= mapping[index]

        symmetry_cache[key] = result
        return result

    def ordered_moves(mask, attack_mask, enemy_attack_mask, ply, tt_move=0):
        h = history[ply & 1]
        killer1, killer2 = killers[ply]
        scored = []
        for bit in _bits(mask):
            score = _BASE[bit] + h[bit.bit_length() - 1]
            if bit & attack_mask:
                score += 10000
            if bit & enemy_attack_mask:
                score += 250
            if bit == killer1:
                score += 24000
            elif bit == killer2:
                score += 16000
            if bit == tt_move:
                score += 1000000
            scored.append((score, bit))
        scored.sort(reverse=True)
        return [bit for _, bit in scored]

    def search(p, q, depth, alpha, beta, ply):
        nonlocal nodes
        nodes += 1
        if (nodes & 127) == 0 and perf_counter() >= deadline:
            raise _SearchTimeout

        available = _FULL ^ (p | q)
        if not available:
            return 0

        remaining = available.bit_count()
        if remaining <= 6:
            depth = max(depth, remaining)

        key = (p, q)
        entry = table.get(key)
        tt_move = 0
        if entry is not None:
            stored_depth, flag, value, tt_move = entry
            if stored_depth >= depth:
                if flag == EXACT:
                    return value
                if flag == LOWER and value >= beta:
                    return value
                if flag == UPPER and value <= alpha:
                    return value

        (
            win, enemy_win, fork, enemy_fork,
            attack, enemy_attack, difference, blank_lines
        ) = _analyze(p, q)

        if win:
            value = MATE - ply - 1
            table[key] = (64, EXACT, value, win & -win)
            return value

        if enemy_win:
            if enemy_win & (enemy_win - 1):
                value = -MATE + ply + 2
                table[key] = (64, EXACT, value, enemy_win & -enemy_win)
                return value
            if fork & enemy_win:
                value = MATE - ply - 3
                table[key] = (64, EXACT, value, enemy_win)
                return value
            moves_mask = enemy_win
        else:
            if fork:
                value = MATE - ply - 3
                table[key] = (64, EXACT, value, fork & -fork)
                return value

            if not attack and not enemy_attack and not blank_lines:
                table[key] = (64, EXACT, 0, 0)
                return 0

            moves_mask = available
            if enemy_fork:
                moves_mask = _safe_moves(
                    p, q, available, attack, enemy_fork
                )
                if not moves_mask:
                    value = -MATE + ply + 4
                    table[key] = (64, EXACT, value, available & -available)
                    return value
            elif depth <= 0:
                # Quiet-position evaluation: live lines and their
                # intersections with potential future threats.
                value = 24 * difference + 5
                value += 5 * (bool(p & _CENTER) - bool(q & _CENTER))
                value += 2 * (
                    (p & _CORNERS).bit_count()
                    - (q & _CORNERS).bit_count()
                )
                for line in blank_lines:
                    a = (line & attack).bit_count()
                    b = (line & enemy_attack).bit_count()
                    value += 3 * (a * a - b * b)

                table[key] = (0, EXACT, value, 0)
                return value

        # Symmetry reduction is especially valuable near the opening.
        if remaining >= 23 and moves_mask & (moves_mask - 1):
            moves_mask &= representatives(p, q)

        if moves_mask & (moves_mask - 1):
            moves = ordered_moves(
                moves_mask, attack, enemy_attack, ply, tt_move
            )
            child_depth = max(0, depth - 1)
        else:
            moves = [moves_mask]
            # Forced moves do not consume the strategic search depth.
            child_depth = depth

        original_alpha = alpha
        best_value = -INF
        best_move = moves[0]

        for number, move in enumerate(moves):
            if number == 0:
                value = -search(
                    q, p | move, child_depth, -beta, -alpha, ply + 1
                )
            else:
                value = -search(
                    q, p | move, child_depth,
                    -alpha - 1, -alpha, ply + 1
                )
                if alpha < value < beta:
                    value = -search(
                        q, p | move, child_depth,
                        -beta, -alpha, ply + 1
                    )

            if value > best_value:
                best_value, best_move = value, move
            if value > alpha:
                alpha = value

            if alpha >= beta:
                if killers[ply][0] != move:
                    killers[ply][1] = killers[ply][0]
                    killers[ply][0] = move
                index = move.bit_length() - 1
                h = history[ply & 1]
                h[index] = min(6000, h[index] + (depth + 1) ** 2)
                break

        if best_value <= original_alpha:
            flag = UPPER
        elif best_value >= beta:
            flag = LOWER
        else:
            flag = EXACT
        table[key] = (depth, flag, best_value, best_move)
        return best_value

    candidates &= representatives(me, opponent)
    root_moves = ordered_moves(candidates, attacks, enemy_attacks, 0)
    best_move = root_moves[0]
    completed_iteration = False
    remaining = empty.bit_count()

    for depth in range(1, remaining + 1):
        iteration_best = root_moves[0]
        iteration_value = -INF
        alpha = -INF
        results = []

        try:
            for number, move in enumerate(root_moves):
                if perf_counter() >= deadline:
                    raise _SearchTimeout

                if number == 0:
                    value = -search(
                        opponent, me | move, depth - 1,
                        -INF, INF, 1
                    )
                else:
                    value = -search(
                        opponent, me | move, depth - 1,
                        -alpha - 1, -alpha, 1
                    )
                    if value > alpha:
                        value = -search(
                            opponent, me | move, depth - 1,
                            -INF, -alpha, 1
                        )

                results.append((value, move))
                if value > iteration_value:
                    iteration_value = value
                    iteration_best = move
                    if not completed_iteration:
                        best_move = move
                alpha = max(alpha, value)

                # A demonstrated forced win is sufficient.
                if value >= MATE - 100:
                    return _coordinate(move)

        except _SearchTimeout:
            break

        best_move = iteration_best
        completed_iteration = True
        results.sort(key=lambda item: item[0], reverse=True)
        root_moves = [move for _, move in results]

        if iteration_value <= -MATE + 100:
            break
        if remaining <= 7:
            # Every child was searched to the end.
            break

    return _coordinate(best_move)
