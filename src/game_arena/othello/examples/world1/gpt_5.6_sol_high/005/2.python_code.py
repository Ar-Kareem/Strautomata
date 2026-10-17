
import time
import numpy as np

FULL = (1 << 64) - 1
A_FILE = sum(1 << (8 * r) for r in range(8))
H_FILE = sum(1 << (8 * r + 7) for r in range(8))
NOT_A = FULL ^ A_FILE
NOT_H = FULL ^ H_FILE

# (bit-index change, mask applied before shifting)
DIRECTIONS = (
    (1, NOT_H),
    (-1, NOT_A),
    (8, FULL),
    (-8, FULL),
    (9, NOT_H),
    (7, NOT_A),
    (-7, NOT_H),
    (-9, NOT_A),
)

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

WEIGHTS = (
    120, -30, 20, 5, 5, 20, -30, 120,
    -30, -45, -5, -5, -5, -5, -45, -30,
    20, -5, 15, 3, 3, 15, -5, 20,
    5, -5, 3, 3, 3, 3, -5, 5,
    5, -5, 3, 3, 3, 3, -5, 5,
    20, -5, 15, 3, 3, 15, -5, 20,
    -30, -45, -5, -5, -5, -5, -45, -30,
    120, -30, 20, 5, 5, 20, -30, 120,
)

CORNER_DATA = (
    (1 << 0, (1, 8, 9)),
    (1 << 7, (6, 14, 15)),
    (1 << 56, (48, 49, 57)),
    (1 << 63, (54, 55, 62)),
)

CORNER_ADJ_MASKS = tuple(
    (corner, sum(1 << i for i in indices), indices)
    for corner, indices in CORNER_DATA
)

# Fast byte-based positional-weight lookup.
WEIGHT_TABLE = []
for block in range(8):
    row = []
    base = block * 8
    for byte in range(256):
        total = 0
        for j in range(8):
            if byte & (1 << j):
                total += WEIGHTS[base + j]
        row.append(total)
    WEIGHT_TABLE.append(tuple(row))
WEIGHT_TABLE = tuple(WEIGHT_TABLE)

INF = 2_000_000
WIN_SCORE = 1_000_000

_TT = {}
_KILLERS = {}
_HISTORY = [0] * 64
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _legal_moves(player: int, opponent: int) -> int:
    empty = FULL ^ (player | opponent)
    moves = 0

    for direction, mask in DIRECTIONS:
        if direction > 0:
            x = ((player & mask) << direction) & opponent
            if not x:
                continue
            for _ in range(5):
                y = ((x & mask) << direction) & opponent
                if (y & ~x) == 0:
                    break
                x |= y
            moves |= ((x & mask) << direction) & empty
        else:
            shift = -direction
            x = ((player & mask) >> shift) & opponent
            if not x:
                continue
            for _ in range(5):
                y = ((x & mask) >> shift) & opponent
                if (y & ~x) == 0:
                    break
                x |= y
            moves |= ((x & mask) >> shift) & empty

    return moves & FULL


def _flips(move: int, player: int, opponent: int) -> int:
    result = 0

    for direction, mask in DIRECTIONS:
        captured = 0

        if direction > 0:
            x = ((move & mask) << direction) & FULL
            while x & opponent:
                captured |= x
                x = ((x & mask) << direction) & FULL
        else:
            shift = -direction
            x = (move & mask) >> shift
            while x & opponent:
                captured |= x
                x = (x & mask) >> shift

        if x & player:
            result |= captured

    return result


def _neighbors(bits: int) -> int:
    horizontal = ((bits & NOT_H) << 1) | ((bits & NOT_A) >> 1)
    vertical = ((bits << 8) & FULL) | (bits >> 8)
    diagonal = (
        ((bits & NOT_H) << 9)
        | ((bits & NOT_A) << 7)
        | ((bits & NOT_H) >> 7)
        | ((bits & NOT_A) >> 9)
    )
    return (horizontal | vertical | diagonal) & FULL


def _orthogonal_neighbors(bits: int) -> int:
    return (
        ((bits & NOT_H) << 1)
        | ((bits & NOT_A) >> 1)
        | ((bits << 8) & FULL)
        | (bits >> 8)
    ) & FULL


def _odd_region_mask(empty: int) -> int:
    remaining = empty
    odd_regions = 0

    while remaining:
        seed = remaining & -remaining
        region = seed

        while True:
            expanded = region | (_orthogonal_neighbors(region) & empty)
            if expanded == region:
                break
            region = expanded

        if region.bit_count() & 1:
            odd_regions |= region
        remaining &= ~region

    return odd_regions


def _weighted_sum(bits: int) -> int:
    return (
        WEIGHT_TABLE[0][bits & 255]
        + WEIGHT_TABLE[1][(bits >> 8) & 255]
        + WEIGHT_TABLE[2][(bits >> 16) & 255]
        + WEIGHT_TABLE[3][(bits >> 24) & 255]
        + WEIGHT_TABLE[4][(bits >> 32) & 255]
        + WEIGHT_TABLE[5][(bits >> 40) & 255]
        + WEIGHT_TABLE[6][(bits >> 48) & 255]
        + WEIGHT_TABLE[7][(bits >> 56) & 255]
    )


def _stable_edge_bits(bits: int) -> int:
    stable = 0

    # Each tuple is (corner index, two directions along its edges).
    for corner, step1, step2 in (
        (0, 1, 8),
        (7, -1, 8),
        (56, 1, -8),
        (63, -1, -8),
    ):
        corner_bit = 1 << corner
        if not (bits & corner_bit):
            continue

        stable |= corner_bit
        for step in (step1, step2):
            index = corner
            for _ in range(7):
                index += step
                bit = 1 << index
                if bits & bit:
                    stable |= bit
                else:
                    break

    return stable


def _percentage_difference(a: int, b: int) -> int:
    total = a + b
    if total == 0:
        return 0
    return int(100.0 * (a - b) / total)


def _evaluate(player: int, opponent: int, player_moves: int = None) -> int:
    occupied = player | opponent
    empty = FULL ^ occupied
    empties = empty.bit_count()

    if player_moves is None:
        player_moves = _legal_moves(player, opponent)
    opponent_moves = _legal_moves(opponent, player)

    positional = _weighted_sum(player) - _weighted_sum(opponent)

    # Once a corner is occupied, its adjacent squares cease to be dangerous.
    for corner, _, indices in CORNER_ADJ_MASKS:
        if occupied & corner:
            for index in indices:
                bit = 1 << index
                adjustment = 15 - WEIGHTS[index]
                if player & bit:
                    positional += adjustment
                elif opponent & bit:
                    positional -= adjustment

    player_corners = (player & CORNERS).bit_count()
    opponent_corners = (opponent & CORNERS).bit_count()
    corner_difference = player_corners - opponent_corners

    # Penalize discs next to a corner while that corner is still empty.
    corner_closeness = 0
    for corner, adjacent, _ in CORNER_ADJ_MASKS:
        if not (occupied & corner):
            corner_closeness += (
                (player & adjacent).bit_count()
                - (opponent & adjacent).bit_count()
            )

    player_mobility = player_moves.bit_count()
    opponent_mobility = opponent_moves.bit_count()
    mobility = _percentage_difference(player_mobility, opponent_mobility)

    player_potential = (_neighbors(opponent) & empty).bit_count()
    opponent_potential = (_neighbors(player) & empty).bit_count()
    potential = _percentage_difference(player_potential, opponent_potential)

    empty_neighbors = _neighbors(empty)
    player_frontier = (player & empty_neighbors).bit_count()
    opponent_frontier = (opponent & empty_neighbors).bit_count()
    frontier = _percentage_difference(player_frontier, opponent_frontier)

    player_discs = player.bit_count()
    opponent_discs = opponent.bit_count()
    disc_difference = _percentage_difference(player_discs, opponent_discs)

    stable_difference = (
        _stable_edge_bits(player).bit_count()
        - _stable_edge_bits(opponent).bit_count()
    )

    score = (
        2 * positional
        + 8 * mobility
        + 2 * potential
        - 4 * frontier
        + 650 * corner_difference
        - 90 * corner_closeness
        + 110 * stable_difference
    )

    if empties > 40:
        score -= disc_difference
    elif empties > 18:
        score += disc_difference
    else:
        score += (2 + (20 - empties) // 2) * disc_difference
        score += 15 if (empties & 1) else -15

    return int(score)


def _terminal_score(player: int, opponent: int) -> int:
    difference = player.bit_count() - opponent.bit_count()
    if difference > 0:
        return WIN_SCORE + 100 * difference
    if difference < 0:
        return -WIN_SCORE + 100 * difference
    return 0


def _check_time() -> None:
    global _NODES
    _NODES += 1
    if (_NODES & 127) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout


def _ordered_moves(
    player: int,
    opponent: int,
    moves: int,
    tt_move: int,
    depth: int,
):
    empty = FULL ^ (player | opponent)
    empties = empty.bit_count()
    odd_mask = _odd_region_mask(empty) if empties <= 18 else 0
    killers = _KILLERS.get(depth, ())
    result = []

    remaining = moves
    while remaining:
        move = remaining & -remaining
        remaining ^= move

        flipped = _flips(move, player, opponent)
        new_player = player | move | flipped
        new_opponent = opponent & ~flipped
        opponent_moves = _legal_moves(new_opponent, new_player)

        index = move.bit_length() - 1
        move_weight = WEIGHTS[index]

        for corner, adjacent, _ in CORNER_ADJ_MASKS:
            if (move & adjacent) and (player & corner):
                move_weight = max(move_weight, 15)

        score = 30 * move_weight
        score += _HISTORY[index]

        if move == tt_move:
            score += 1_000_000
        if move & CORNERS:
            score += 100_000
        if move in killers:
            score += 20_000
        if not opponent_moves:
            score += 16_000

        score -= 700 * opponent_moves.bit_count()
        score -= 30_000 * (opponent_moves & CORNERS).bit_count()

        if odd_mask & move:
            score += 2_500

        # Fewer flips are often preferable, especially near the end.
        score -= (15 if empties > 20 else 25) * flipped.bit_count()

        result.append(
            (score, move, flipped, new_player, new_opponent)
        )

    result.sort(key=lambda item: item[0], reverse=True)
    return result


def _store_tt(key, depth: int, value: int, flag: int, best_move: int) -> None:
    old = _TT.get(key)
    if old is None or depth >= old[0]:
        if len(_TT) < 400_000 or old is not None:
            _TT[key] = (depth, value, flag, best_move)


def _negamax(
    player: int,
    opponent: int,
    depth: int,
    alpha: int,
    beta: int,
) -> int:
    _check_time()

    key = (player, opponent)
    entry = _TT.get(key)
    tt_move = 0

    if entry is not None:
        stored_depth, stored_value, flag, tt_move = entry
        if stored_depth >= depth:
            if flag == 0:
                return stored_value
            if flag == 1:
                if stored_value >= beta:
                    return stored_value
                alpha = max(alpha, stored_value)
            else:
                if stored_value <= alpha:
                    return stored_value
                beta = min(beta, stored_value)
            if alpha >= beta:
                return stored_value

    search_alpha = alpha
    search_beta = beta

    moves = _legal_moves(player, opponent)

    if not moves:
        opponent_moves = _legal_moves(opponent, player)
        if not opponent_moves:
            return _terminal_score(player, opponent)

        value = -_negamax(opponent, player, depth, -beta, -alpha)
        _store_tt(key, depth, value, 0, 0)
        return value

    if depth <= 0:
        return _evaluate(player, opponent, moves)

    ordered = _ordered_moves(
        player, opponent, moves, tt_move, depth
    )

    best_value = -INF
    best_move = 0
    first = True

    for _, move, _, new_player, new_opponent in ordered:
        if first:
            value = -_negamax(
                new_opponent,
                new_player,
                depth - 1,
                -beta,
                -alpha,
            )
            first = False
        else:
            value = -_negamax(
                new_opponent,
                new_player,
                depth - 1,
                -alpha - 1,
                -alpha,
            )
            if alpha < value < beta:
                value = -_negamax(
                    new_opponent,
                    new_player,
                    depth - 1,
                    -beta,
                    -alpha,
                )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            index = move.bit_length() - 1
            _HISTORY[index] += depth * depth

            previous = _KILLERS.get(depth, ())
            if move not in previous:
                _KILLERS[depth] = (move,) + previous[:1]
            break

    if best_value <= search_alpha:
        flag = 2  # Upper bound
    elif best_value >= search_beta:
        flag = 1  # Lower bound
    else:
        flag = 0  # Exact

    _store_tt(key, depth, best_value, flag, best_move)
    return best_value


def _root_search(
    player: int,
    opponent: int,
    depth: int,
    previous_best: int,
):
    if time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout

    moves = _legal_moves(player, opponent)
    ordered = _ordered_moves(
        player, opponent, moves, previous_best, depth
    )

    alpha = -INF
    beta = INF
    best_value = -INF
    best_move = ordered[0][1]
    first = True

    for _, move, _, new_player, new_opponent in ordered:
        if time.perf_counter() >= _DEADLINE:
            raise _SearchTimeout

        if first:
            value = -_negamax(
                new_opponent,
                new_player,
                depth - 1,
                -beta,
                -alpha,
            )
            first = False
        else:
            value = -_negamax(
                new_opponent,
                new_player,
                depth - 1,
                -alpha - 1,
                -alpha,
            )
            if alpha < value < beta:
                value = -_negamax(
                    new_opponent,
                    new_player,
                    depth - 1,
                    -beta,
                    -alpha,
                )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

    _store_tt(
        (player, opponent), depth, best_value, 0, best_move
    )
    return best_value, best_move


def _array_to_bits(board: np.ndarray) -> int:
    flat = np.asarray(board).reshape(-1)
    bits = 0
    for index in range(64):
        if int(flat[index]):
            bits |= 1 << index
    return bits


def _move_to_string(move: int) -> str:
    index = move.bit_length() - 1
    row, column = divmod(index, 8)
    return chr(ord("a") + column) + str(row + 1)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _TT, _KILLERS, _HISTORY, _DEADLINE, _NODES

    player = _array_to_bits(you)
    enemy = _array_to_bits(opponent)
    legal = _legal_moves(player, enemy)

    if not legal:
        return "pass"

    if legal & (legal - 1) == 0:
        return _move_to_string(legal)

    _TT = {}
    _KILLERS = {}
    _HISTORY = [0] * 64
    _NODES = 0

    # Leave a safety margin below the one-second limit.
    _DEADLINE = time.perf_counter() + 0.93

    # Always maintain a legal fallback.
    fallback = legal & -legal
    best_move = max(
        (1 << i for i in range(64) if legal & (1 << i)),
        key=lambda move: (
            1 if move & CORNERS else 0,
            WEIGHTS[move.bit_length() - 1],
        ),
    )
    if not best_move:
        best_move = fallback

    empties = (FULL ^ (player | enemy)).bit_count()

    try:
        for depth in range(1, empties + 1):
            _, completed_move = _root_search(
                player, enemy, depth, best_move
            )
            best_move = completed_move

            # Searching as many plies as there are empty squares is exact.
            if depth >= empties:
                break
    except _SearchTimeout:
        pass
    except Exception:
        # The preselected move remains legal under any unexpected failure.
        pass

    return _move_to_string(best_move)
