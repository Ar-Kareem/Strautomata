
import time
import numpy as np

FULL = (1 << 64) - 1
FILE_A = sum(1 << (r * 8) for r in range(8))
FILE_H = sum(1 << (r * 8 + 7) for r in range(8))
NOT_A = FULL ^ FILE_A
NOT_H = FULL ^ FILE_H

# (bit displacement, mask applied before displacement)
DIRECTIONS = (
    (-9, NOT_A), (-8, FULL), (-7, NOT_H),
    (-1, NOT_A),             (1, NOT_H),
    (7, NOT_A),  (8, FULL),  (9, NOT_H),
)

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)
EDGES = (
    0xFF
    | (0xFF << 56)
    | FILE_A
    | FILE_H
)

POSITION_WEIGHTS = (
    120, -25, 20, 5, 5, 20, -25, 120,
    -25, -45, -5, -5, -5, -5, -45, -25,
    20, -5, 15, 3, 3, 15, -5, 20,
    5, -5, 3, 3, 3, 3, -5, 5,
    5, -5, 3, 3, 3, 3, -5, 5,
    20, -5, 15, 3, 3, 15, -5, 20,
    -25, -45, -5, -5, -5, -5, -45, -25,
    120, -25, 20, 5, 5, 20, -25, 120,
)

CORNER_ADJACENCY = (
    (0, (1, 8, 9)),
    (7, (6, 14, 15)),
    (56, (48, 49, 57)),
    (63, (54, 55, 62)),
)

# Rays used for conservative, guaranteed-stable edge-disc detection.
EDGE_RAYS = (
    (0, 1, 2, 3, 4, 5, 6, 7),
    (0, 8, 16, 24, 32, 40, 48, 56),
    (7, 6, 5, 4, 3, 2, 1, 0),
    (7, 15, 23, 31, 39, 47, 55, 63),
    (56, 57, 58, 59, 60, 61, 62, 63),
    (56, 48, 40, 32, 24, 16, 8, 0),
    (63, 62, 61, 60, 59, 58, 57, 56),
    (63, 55, 47, 39, 31, 23, 15, 7),
)

# Fast byte-based positional evaluation tables.
POSITION_TABLE = []
for row in range(8):
    table = [0] * 256
    base = row * 8
    for pattern in range(256):
        value = 0
        bits = pattern
        while bits:
            bit = bits & -bits
            col = bit.bit_length() - 1
            value += POSITION_WEIGHTS[base + col]
            bits ^= bit
        table[pattern] = value
    POSITION_TABLE.append(table)

INF = 1_000_000_000
WIN_VALUE = 1_000_000

_deadline = 0.0
_nodes = 0
_tt = {}
_history = [0] * 64
_killers = [0] * 65


class SearchTimeout(Exception):
    pass


def _shift(bits, displacement, mask):
    bits &= mask
    if displacement > 0:
        return (bits << displacement) & FULL
    return bits >> (-displacement)


def _legal(player, opponent):
    empty = FULL ^ (player | opponent)
    result = 0

    for displacement, mask in DIRECTIONS:
        line = _shift(player, displacement, mask) & opponent
        line |= _shift(line, displacement, mask) & opponent
        line |= _shift(line, displacement, mask) & opponent
        line |= _shift(line, displacement, mask) & opponent
        line |= _shift(line, displacement, mask) & opponent
        line |= _shift(line, displacement, mask) & opponent
        result |= _shift(line, displacement, mask) & empty

    return result


def _make_move(player, opponent, move):
    flipped = 0

    for displacement, mask in DIRECTIONS:
        line = _shift(move, displacement, mask) & opponent
        captured = 0

        while line:
            captured |= line
            beyond = _shift(line, displacement, mask)
            if beyond & player:
                flipped |= captured
                break
            line = beyond & opponent

    return player | move | flipped, opponent & ~flipped


def _neighbors(bits):
    result = 0
    for displacement, mask in DIRECTIONS:
        result |= _shift(bits, displacement, mask)
    return result


def _orthogonal_neighbors(bits):
    return (
        _shift(bits, -8, FULL)
        | _shift(bits, 8, FULL)
        | _shift(bits, -1, NOT_A)
        | _shift(bits, 1, NOT_H)
    )


def _normalized_difference(a, b):
    total = a + b
    if total == 0:
        return 0

    numerator = 100 * (a - b)
    if numerator >= 0:
        return numerator // total
    return -((-numerator) // total)


def _position_score(bits):
    return sum(
        POSITION_TABLE[row][(bits >> (row * 8)) & 0xFF]
        for row in range(8)
    )


def _stable_edge_bits(bits):
    stable = 0

    for ray in EDGE_RAYS:
        corner_bit = 1 << ray[0]
        if not (bits & corner_bit):
            continue

        for index in ray:
            bit = 1 << index
            if bits & bit:
                stable |= bit
            else:
                break

    return stable


def _evaluate(player, opponent, player_moves):
    occupied = player | opponent
    empty = FULL ^ occupied
    empties = empty.bit_count()

    opponent_moves = _legal(opponent, player)
    player_mobility = player_moves.bit_count()
    opponent_mobility = opponent_moves.bit_count()
    mobility = _normalized_difference(player_mobility, opponent_mobility)

    empty_neighbors = _neighbors(empty)
    player_frontier = (player & empty_neighbors).bit_count()
    opponent_frontier = (opponent & empty_neighbors).bit_count()
    # Positive means the opponent has more exposed frontier discs.
    frontier = _normalized_difference(opponent_frontier, player_frontier)

    player_potential = (empty & _neighbors(opponent)).bit_count()
    opponent_potential = (empty & _neighbors(player)).bit_count()
    potential = _normalized_difference(player_potential, opponent_potential)

    player_count = player.bit_count()
    opponent_count = opponent.bit_count()
    disc_difference = _normalized_difference(player_count, opponent_count)

    positional = _position_score(player) - _position_score(opponent)

    # Once a corner is occupied, its adjacent squares are no longer dangerous
    # corner concessions, so replace their static values with a small bonus.
    for corner_index, adjacent in CORNER_ADJACENCY:
        corner_bit = 1 << corner_index
        if occupied & corner_bit:
            for square in adjacent:
                bit = 1 << square
                replacement_delta = 10 - POSITION_WEIGHTS[square]
                if player & bit:
                    positional += replacement_delta
                elif opponent & bit:
                    positional -= replacement_delta

    corner_difference = (player & CORNERS).bit_count() - (
        opponent & CORNERS
    ).bit_count()

    player_stable = _stable_edge_bits(player).bit_count()
    opponent_stable = _stable_edge_bits(opponent).bit_count()
    stable_difference = player_stable - opponent_stable

    if empties > 44:
        return (
            4 * positional
            + 5 * mobility
            + 2 * potential
            + 3 * frontier
            + 800 * corner_difference
            + 25 * stable_difference
        )

    if empties > 24:
        return (
            3 * positional
            + 7 * mobility
            + 2 * potential
            + 4 * frontier
            + 900 * corner_difference
            + 35 * stable_difference
        )

    if empties > 12:
        return (
            2 * positional
            + 8 * mobility
            + potential
            + 3 * frontier
            + 1000 * corner_difference
            + 55 * stable_difference
            + 3 * disc_difference
        )

    parity = 20 if empties & 1 else -20
    return (
        positional
        + 6 * mobility
        + 2 * frontier
        + 1100 * corner_difference
        + 70 * stable_difference
        + (20 - empties) * 4 * disc_difference
        + parity
    )


def _odd_region_mask(empty):
    remaining = empty
    odd_squares = 0

    while remaining:
        seed = remaining & -remaining
        component = seed
        frontier = seed

        while frontier:
            expansion = _orthogonal_neighbors(frontier) & remaining & ~component
            if not expansion:
                break
            component |= expansion
            frontier = expansion

        remaining &= ~component
        if component.bit_count() & 1:
            odd_squares |= component

    return odd_squares


def _ordered_moves(player, opponent, moves, tt_move, empties, depth):
    odd_squares = _odd_region_mask(FULL ^ (player | opponent)) if empties <= 14 else 0
    ordered = []

    bits = moves
    while bits:
        move = bits & -bits
        bits ^= move
        index = move.bit_length() - 1

        new_player, new_opponent = _make_move(player, opponent, move)
        opponent_moves = _legal(new_opponent, new_player)
        opponent_mobility = opponent_moves.bit_count()
        flipped_count = (new_player & opponent).bit_count()

        score = POSITION_WEIGHTS[index] * 100
        score -= opponent_mobility * 1800
        score += _history[index]

        if move == tt_move:
            score += 10_000_000
        if move & CORNERS:
            score += 2_000_000
        if opponent_moves & CORNERS:
            score -= 400_000
        if move & EDGES:
            score += 3000
        if move & odd_squares:
            score += 8000
        if depth < len(_killers) and move == _killers[depth]:
            score += 150_000

        if empties > 20:
            score -= 20 * flipped_count
        else:
            score += 30 * flipped_count

        ordered.append((score, move, new_player, new_opponent))

    ordered.sort(key=lambda item: item[0], reverse=True)
    return ordered


def _terminal_value(player, opponent):
    difference = player.bit_count() - opponent.bit_count()
    if difference > 0:
        return WIN_VALUE + 100 * difference
    if difference < 0:
        return -WIN_VALUE + 100 * difference
    return 0


def _negamax(player, opponent, depth, alpha, beta):
    global _nodes

    _nodes += 1
    if (_nodes & 255) == 0 and time.perf_counter() >= _deadline:
        raise SearchTimeout

    key = player | (opponent << 64)
    original_alpha = alpha
    original_beta = beta

    entry = _tt.get(key)
    tt_move = 0

    if entry is not None:
        stored_depth, stored_value, flag, tt_move = entry
        if stored_depth >= depth:
            if flag == 0:  # Exact
                return stored_value
            if flag == 1:  # Lower bound
                alpha = max(alpha, stored_value)
            else:          # Upper bound
                beta = min(beta, stored_value)

            if alpha >= beta:
                return stored_value

    moves = _legal(player, opponent)

    if not moves:
        opponent_moves = _legal(opponent, player)
        if not opponent_moves:
            value = _terminal_value(player, opponent)
            _tt[key] = (100, value, 0, 0)
            return value

        value = -_negamax(opponent, player, depth, -beta, -alpha)

        if value <= original_alpha:
            flag = 2
        elif value >= original_beta:
            flag = 1
        else:
            flag = 0
        _tt[key] = (depth, value, flag, 0)
        return value

    if depth <= 0:
        value = _evaluate(player, opponent, moves)
        _tt[key] = (0, value, 0, tt_move)
        return value

    empties = 64 - (player | opponent).bit_count()
    ordered = _ordered_moves(
        player, opponent, moves, tt_move, empties, depth
    )

    best_value = -INF
    best_move = ordered[0][1]

    for move_number, (_, move, new_player, new_opponent) in enumerate(ordered):
        child_depth = depth - 1

        if move_number == 0:
            value = -_negamax(
                new_opponent, new_player, child_depth, -beta, -alpha
            )
        else:
            use_reduction = (
                depth >= 6
                and move_number >= 6
                and empties > 18
                and not (move & CORNERS)
            )

            if use_reduction:
                value = -_negamax(
                    new_opponent,
                    new_player,
                    child_depth - 1,
                    -alpha - 1,
                    -alpha,
                )
                if value > alpha:
                    value = -_negamax(
                        new_opponent,
                        new_player,
                        child_depth,
                        -alpha - 1,
                        -alpha,
                    )
            else:
                value = -_negamax(
                    new_opponent,
                    new_player,
                    child_depth,
                    -alpha - 1,
                    -alpha,
                )

            if alpha < value < beta:
                value = -_negamax(
                    new_opponent, new_player, child_depth, -beta, -alpha
                )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            index = move.bit_length() - 1
            _history[index] = min(
                100_000, _history[index] + 100 * depth * depth
            )
            if depth < len(_killers):
                _killers[depth] = move
            break

    if best_value <= original_alpha:
        flag = 2  # Upper bound
    elif best_value >= original_beta:
        flag = 1  # Lower bound
    else:
        flag = 0  # Exact

    _tt[key] = (depth, best_value, flag, best_move)
    return best_value


def _array_to_bitboard(board):
    result = 0
    for row in range(8):
        for col in range(8):
            if board[row][col]:
                result |= 1 << (row * 8 + col)
    return result


def _move_to_string(move):
    index = move.bit_length() - 1
    row, col = divmod(index, 8)
    return chr(ord("a") + col) + str(row + 1)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _deadline, _nodes, _tt, _history, _killers

    player = _array_to_bitboard(you)
    enemy = _array_to_bitboard(opponent)
    legal_moves = _legal(player, enemy)

    if not legal_moves:
        return "pass"

    # Establish a legal fallback before any time-limited work.
    fallback = legal_moves & -legal_moves
    fallback_score = -INF
    remaining = legal_moves

    while remaining:
        move = remaining & -remaining
        remaining ^= move
        index = move.bit_length() - 1

        score = POSITION_WEIGHTS[index]
        if move & CORNERS:
            score += 10000
        elif move & EDGES:
            score += 20

        if score > fallback_score:
            fallback_score = score
            fallback = move

    best_move = fallback
    empties = 64 - (player | enemy).bit_count()

    _tt = {}
    _history = [0] * 64
    _killers = [0] * 65
    _nodes = 0
    _deadline = time.perf_counter() + 0.93

    try:
        # Iterative deepening gives a fully searched move at every completed
        # depth and progressively improves transposition-table move ordering.
        for depth in range(1, empties + 1):
            _negamax(player, enemy, depth, -INF, INF)

            root_entry = _tt.get(player | (enemy << 64))
            if root_entry is not None:
                candidate = root_entry[3]
                if candidate & legal_moves:
                    best_move = candidate

            # Searching one ply per empty square solves the position exactly,
            # including pass sequences.
            if depth >= empties:
                break

            if time.perf_counter() >= _deadline:
                break

    except SearchTimeout:
        pass

    # Final legality guard.
    if not (best_move & legal_moves):
        best_move = legal_moves & -legal_moves

    return _move_to_string(best_move)
