
import time
from itertools import permutations

_FULL = (1 << 16) - 1
_MATE = 10000
_INF = 20000

_LINES = (
    0x000F, 0x00F0, 0x0F00, 0xF000,
    0x1111, 0x2222, 0x4444, 0x8888,
    0x8421, 0x1248,
)

_POSITION = (
    4, 1, 1, 4,
    1, 5, 5, 1,
    1, 5, 5, 1,
    4, 1, 1, 4,
)

_TABLES = None
_TT = {}


class _SearchTimeout(Exception):
    pass


def _coordinates(bit):
    index = bit.bit_length() - 1
    return index // 4, index % 4


def _get_tables():
    global _TABLES

    if _TABLES is not None:
        return _TABLES

    incidence = [0] * 16
    for line_index, line in enumerate(_LINES):
        for square in range(16):
            if line & (1 << square):
                incidence[square] |= 1 << line_index

    # Union of selected lines, and squares on at least two selected lines.
    unions = [0] * 1024
    multiple = [0] * 1024
    for selected in range(1, 1024):
        bit = selected & -selected
        previous = selected ^ bit
        line = _LINES[bit.bit_length() - 1]
        unions[selected] = unions[previous] | line
        multiple[selected] = (
            multiple[previous] | (unions[previous] & line)
        )

    opened = [0] * 65536
    ones = [0] * 65536
    twos = [0] * 65536
    threats = [0] * 65536
    opened[0] = 1023

    for stones in range(1, 65536):
        bit = stones & -stones
        previous = stones ^ bit
        touched = incidence[bit.bit_length() - 1]
        untouched = 1023 ^ touched

        old_open = opened[previous]
        old_one = ones[previous]
        old_two = twos[previous]

        opened[stones] = old_open & untouched
        ones[stones] = (
            (old_one & untouched) | (old_open & touched)
        )
        twos[stones] = (
            (old_two & untouched) | (old_one & touched)
        )
        threats[stones] = (
            threats[previous] | unions[old_two & touched]
        ) & (_FULL ^ stones)

    # These 32 transformations preserve all ten winning lines.
    symmetries = []
    for permutation in permutations(range(4)):
        if any(
            permutation[3 - i] != 3 - permutation[i]
            for i in range(4)
        ):
            continue
        for reflected in (False, True):
            for transposed in (False, True):
                mapping = []
                for r in range(4):
                    for c in range(4):
                        nr = permutation[r]
                        nc = permutation[c]
                        if reflected:
                            nc = 3 - nc
                        if transposed:
                            nr, nc = nc, nr
                        mapping.append(1 << (4 * nr + nc))
                symmetries.append(tuple(mapping))

    _TABLES = (
        opened, ones, twos, threats,
        multiple, incidence, tuple(symmetries),
    )
    return _TABLES


def policy(board: list[list[int]]) -> tuple[int, int]:
    deadline = time.perf_counter() + 0.88

    player = 0
    opponent = 0
    for r in range(4):
        for c in range(4):
            if board[r][c] == 1:
                player |= 1 << (4 * r + c)
            elif board[r][c] == -1:
                opponent |= 1 << (4 * r + c)

    empty = _FULL ^ (player | opponent)

    # No legal action exists on a full board; games normally never call
    # the policy in this terminal state.
    if not empty:
        return (0, 0)

    fallback = empty & -empty
    if empty == _FULL:
        return (1, 1)

    (
        opened, ones, twos, threats,
        multiple, incidence, symmetries,
    ) = _get_tables()

    winning = threats[player] & empty
    if winning:
        return _coordinates(winning & -winning)

    danger = threats[opponent] & empty
    if danger:
        # A single threat has exactly one possible saving move.
        # With multiple threats, blocking one is the best practical try.
        candidates = []
        remaining = danger
        while remaining:
            bit = remaining & -remaining
            remaining ^= bit
            attack = (threats[player | bit] & (empty ^ bit)).bit_count()
            candidates.append((attack, _POSITION[bit.bit_length() - 1], bit))
        return _coordinates(max(candidates)[2])

    forks = multiple[twos[player] & opened[opponent]] & empty
    if forks:
        return _coordinates(forks & -forks)

    tt = _TT
    if len(tt) > 350000:
        tt.clear()

    history = [0] * 32
    killers = [0] * 17
    nodes = 0

    def ordered_moves(p, q, vacant, left, hash_move):
        own_open = opened[q]
        enemy_open = opened[p]
        own_one = ones[p] & own_open
        own_two = twos[p] & own_open
        enemy_one = ones[q] & enemy_open
        enemy_two = twos[q] & enemy_open
        untouched = own_open & enemy_open
        offset = (left & 1) * 16
        killer = killers[left]

        ranked = []
        while vacant:
            bit = vacant & -vacant
            vacant ^= bit
            square = bit.bit_length() - 1
            touched = incidence[square]

            score = (
                history[offset + square]
                + 20000 * bool(own_two & touched)
                + 1600 * (enemy_two & touched).bit_count()
                + 220 * (own_one & touched).bit_count()
                + 40 * (enemy_one & touched).bit_count()
                + 6 * (untouched & touched).bit_count()
                + _POSITION[square]
            )
            if bit == killer:
                score += 100000
            if bit == hash_move:
                score += 1000000
            ranked.append((score, bit))

        ranked.sort(reverse=True)
        return [bit for _, bit in ranked]

    def evaluate(p, q, vacant, open_p, open_q):
        value = 3 * (
            (ones[p] & open_q).bit_count()
            - (ones[q] & open_p).bit_count()
        )
        value += 20 * (
            (twos[p] & open_q).bit_count()
            - (twos[q] & open_p).bit_count()
        )
        value += 2 * (
            (multiple[open_q] & vacant).bit_count()
            - (multiple[open_p] & vacant).bit_count()
        )
        return value

    def search(p, q, left, depth, alpha, beta):
        nonlocal nodes
        nodes += 1
        if (nodes & 511) == 0:
            if time.perf_counter() >= deadline:
                raise _SearchTimeout

        vacant = _FULL ^ (p | q)

        if threats[p] & vacant:
            return _MATE + left - 1

        forced = threats[q] & vacant
        if forced & (forced - 1):
            return -_MATE - left + 2

        if left <= 2:
            return 0

        open_p = opened[p]
        open_q = opened[q]
        if not (open_p | open_q):
            return 0

        if not forced:
            if multiple[twos[p] & open_q] & vacant:
                return _MATE + left - 3

        key = p | (q << 16)
        entry = tt.get(key)
        hash_move = 0
        if entry is not None:
            stored_depth, stored_value, bound, hash_move = entry
            if stored_depth >= depth:
                if bound == 0:
                    return stored_value
                if bound == 1 and stored_value >= beta:
                    return stored_value
                if bound == 2 and stored_value <= alpha:
                    return stored_value

        # Do not stop at a forced block or an impending opponent fork.
        if depth == 0 and not forced:
            enemy_forks = multiple[twos[q] & open_p] & vacant
            if not enemy_forks:
                return evaluate(p, q, vacant, open_p, open_q)

        original_alpha = alpha
        next_depth = max(0, depth - 1)

        if forced:
            best_move = forced
            best_value = -search(
                q, p | forced, left - 1, next_depth, -beta, -alpha
            )
        else:
            moves = ordered_moves(p, q, vacant, left, hash_move)
            best_value = -_INF
            best_move = moves[0]

            for index, bit in enumerate(moves):
                if index == 0:
                    value = -search(
                        q, p | bit, left - 1, next_depth,
                        -beta, -alpha,
                    )
                else:
                    # Principal-variation search.
                    value = -search(
                        q, p | bit, left - 1, next_depth,
                        -alpha - 1, -alpha,
                    )
                    if alpha < value < beta:
                        value = -search(
                            q, p | bit, left - 1, next_depth,
                            -beta, -alpha,
                        )

                if value > best_value:
                    best_value = value
                    best_move = bit

                if value > alpha:
                    alpha = value

                if alpha >= beta:
                    killers[left] = bit
                    h = (left & 1) * 16 + bit.bit_length() - 1
                    history[h] = min(
                        8192, history[h] + 8 * depth * depth + 8
                    )
                    break

        if best_value <= original_alpha:
            bound = 2
        elif best_value >= beta:
            bound = 1
        else:
            bound = 0

        if (
            entry is None
            or depth >= entry[0]
            or bound == 0
        ):
            tt[key] = (depth, best_value, bound, best_move)

        return best_value

    left = empty.bit_count()
    root_key = player | (opponent << 16)
    root_entry = tt.get(root_key)
    hash_move = root_entry[3] if root_entry is not None else 0
    moves = ordered_moves(player, opponent, empty, left, hash_move)

    # Search only one representative of each symmetry-equivalent move.
    stabilizers = []
    for mapping in symmetries:
        mapped_player = 0
        mapped_opponent = 0

        stones = player
        while stones:
            bit = stones & -stones
            stones ^= bit
            mapped_player |= mapping[bit.bit_length() - 1]

        if mapped_player != player:
            continue

        stones = opponent
        while stones:
            bit = stones & -stones
            stones ^= bit
            mapped_opponent |= mapping[bit.bit_length() - 1]

        if mapped_opponent == opponent:
            stabilizers.append(mapping)

    representatives = []
    seen = 0
    for bit in moves:
        if seen & bit:
            continue
        representatives.append(bit)
        square = bit.bit_length() - 1
        for mapping in stabilizers:
            seen |= mapping[square]
    moves = representatives

    best_move = moves[0] if moves else fallback
    if len(moves) == 1:
        return _coordinates(best_move)

    for depth in range(1, left + 1):
        if time.perf_counter() >= deadline:
            break

        current_best = best_move
        root_value = -_INF
        results = {}

        try:
            for index, bit in enumerate(moves):
                if index == 0:
                    value = -search(
                        opponent, player | bit, left - 1,
                        depth - 1, -_INF, _INF,
                    )
                else:
                    value = -search(
                        opponent, player | bit, left - 1,
                        depth - 1, -root_value - 1, -root_value,
                    )
                    if value > root_value:
                        value = -search(
                            opponent, player | bit, left - 1,
                            depth - 1, -_INF, -root_value,
                        )

                results[bit] = value
                if value > root_value:
                    root_value = value
                    current_best = bit

                # A proven win is sufficient; no need to spend more time.
                if value >= _MATE:
                    return _coordinates(bit)

        except _SearchTimeout:
            break

        best_move = current_best
        tt[root_key] = (depth, root_value, 0, best_move)

        if root_value <= -_MATE:
            break

        moves.sort(key=lambda bit: results[bit], reverse=True)

    if not (best_move & empty):
        best_move = fallback
    return _coordinates(best_move)
