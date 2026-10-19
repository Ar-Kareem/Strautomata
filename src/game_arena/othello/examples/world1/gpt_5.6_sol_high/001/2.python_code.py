
import time
import numpy as np


FULL = (1 << 64) - 1
A_FILE = sum(1 << (8 * r) for r in range(8))
H_FILE = sum(1 << (8 * r + 7) for r in range(8))
NOT_A = FULL ^ A_FILE
NOT_H = FULL ^ H_FILE

CORNERS = (
    (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)
)
EDGES = (
    A_FILE
    | H_FILE
    | sum(1 << c for c in range(8))
    | sum(1 << (56 + c) for c in range(8))
)

POSITION_WEIGHTS = (
    100, -25, 12, 6, 6, 12, -25, 100,
    -25, -45, -4, -3, -3, -4, -45, -25,
    12, -4, 8, 2, 2, 8, -4, 12,
    6, -3, 2, 1, 1, 2, -3, 6,
    6, -3, 2, 1, 1, 2, -3, 6,
    12, -4, 8, 2, 2, 8, -4, 12,
    -25, -45, -4, -3, -3, -4, -45, -25,
    100, -25, 12, 6, 6, 12, -25, 100,
)

_weight_groups = {}
for _i, _w in enumerate(POSITION_WEIGHTS):
    _weight_groups[_w] = _weight_groups.get(_w, 0) | (1 << _i)
WEIGHT_MASKS = tuple(_weight_groups.items())

CORNER_ADJACENCY = (
    (0, (1, 8, 9)),
    (7, (6, 14, 15)),
    (56, (48, 49, 57)),
    (63, (54, 55, 62)),
)

WIN_SCORE = 100000
INF = 1000000000

TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2

TT = {}
HISTORY = [0] * 64
KILLERS = [[0, 0] for _ in range(70)]

DEADLINE = 0.0
NODES = 0


class _SearchTimeout(Exception):
    pass


def _east(x):
    return ((x & NOT_H) << 1) & FULL


def _west(x):
    return (x & NOT_A) >> 1


def _south(x):
    return (x << 8) & FULL


def _north(x):
    return x >> 8


def _southeast(x):
    return ((x & NOT_H) << 9) & FULL


def _southwest(x):
    return ((x & NOT_A) << 7) & FULL


def _northeast(x):
    return (x & NOT_H) >> 7


def _northwest(x):
    return (x & NOT_A) >> 9


SHIFTS = (
    _east, _west, _south, _north,
    _southeast, _southwest, _northeast, _northwest,
)


def _legal_moves(player, opponent):
    empty = FULL ^ (player | opponent)
    moves = 0

    for shift in SHIFTS:
        line = shift(player) & opponent
        line |= shift(line) & opponent
        line |= shift(line) & opponent
        line |= shift(line) & opponent
        line |= shift(line) & opponent
        line |= shift(line) & opponent
        moves |= shift(line) & empty

    return moves


def _flips(move, player, opponent):
    result = 0

    for shift in SHIFTS:
        x = shift(move)
        captured = 0

        while x & opponent:
            captured |= x
            x = shift(x)

        if x & player:
            result |= captured

    return result


def _neighbors(bits):
    return (
        _east(bits) | _west(bits) | _south(bits) | _north(bits)
        | _southeast(bits) | _southwest(bits)
        | _northeast(bits) | _northwest(bits)
    )


def _stable_corner_edges(bits):
    stable = 0

    corner_directions = (
        (1 << 0, (_east, _south)),
        (1 << 7, (_west, _south)),
        (1 << 56, (_east, _north)),
        (1 << 63, (_west, _north)),
    )

    for corner, directions in corner_directions:
        if not (bits & corner):
            continue

        stable |= corner
        for shift in directions:
            x = shift(corner)
            while x and (x & bits):
                stable |= x
                x = shift(x)

    return stable


def _positional_score(player, opponent):
    score = 0

    for weight, mask in WEIGHT_MASKS:
        score += weight * (
            (player & mask).bit_count()
            - (opponent & mask).bit_count()
        )

    occupied = player | opponent

    # Once a corner is occupied, its neighboring squares cease to be
    # dangerous corner concessions, so replace their static penalties.
    for corner_index, adjacent in CORNER_ADJACENCY:
        corner = 1 << corner_index
        if not (occupied & corner):
            continue

        for index in adjacent:
            bit = 1 << index
            correction = 8 - POSITION_WEIGHTS[index]
            if player & bit:
                score += correction
            elif opponent & bit:
                score -= correction

    return score


def _evaluate(player, opponent, player_moves=None):
    occupied = player | opponent
    empty = FULL ^ occupied
    empties = empty.bit_count()

    if player_moves is None:
        player_moves = _legal_moves(player, opponent)
    opponent_moves = _legal_moves(opponent, player)

    player_count = player.bit_count()
    opponent_count = opponent.bit_count()
    disc_difference = player_count - opponent_count

    mobility_difference = (
        player_moves.bit_count() - opponent_moves.bit_count()
    )

    player_potential = (_neighbors(opponent) & empty).bit_count()
    opponent_potential = (_neighbors(player) & empty).bit_count()
    potential_difference = player_potential - opponent_potential

    empty_neighbors = _neighbors(empty)
    player_frontier = (player & empty_neighbors).bit_count()
    opponent_frontier = (opponent & empty_neighbors).bit_count()
    frontier_advantage = opponent_frontier - player_frontier

    corner_difference = (
        (player & CORNERS).bit_count()
        - (opponent & CORNERS).bit_count()
    )

    player_stable = _stable_corner_edges(player).bit_count()
    opponent_stable = _stable_corner_edges(opponent).bit_count()
    stable_difference = player_stable - opponent_stable

    positional = _positional_score(player, opponent)

    if empties > 40:
        disc_weight = -1
        mobility_weight = 13
    elif empties > 26:
        disc_weight = 0
        mobility_weight = 16
    elif empties > 16:
        disc_weight = 1
        mobility_weight = 18
    elif empties > 9:
        disc_weight = 3
        mobility_weight = 18
    else:
        disc_weight = 8
        mobility_weight = 12

    return (
        2 * positional
        + 165 * corner_difference
        + 24 * stable_difference
        + mobility_weight * mobility_difference
        + 3 * potential_difference
        + 5 * frontier_advantage
        + disc_weight * disc_difference
    )


def _terminal_score(player, opponent):
    difference = player.bit_count() - opponent.bit_count()

    if difference > 0:
        return WIN_SCORE + 100 * difference
    if difference < 0:
        return -WIN_SCORE + 100 * difference
    return 0


def _odd_region_mask(empty):
    unseen = empty
    odd_regions = 0

    while unseen:
        seed = unseen & -unseen
        region = seed
        frontier = seed

        while frontier:
            expanded = (
                _east(frontier) | _west(frontier)
                | _north(frontier) | _south(frontier)
            ) & unseen & ~region

            if not expanded:
                break

            region |= expanded
            frontier = expanded

        unseen &= ~region

        if region.bit_count() & 1:
            odd_regions |= region

    return odd_regions


def _check_time():
    global NODES
    NODES += 1

    if (NODES & 127) == 0 and time.perf_counter() >= DEADLINE:
        raise _SearchTimeout


def _store_tt(key, depth, value, flag, best_move):
    old = TT.get(key)

    if (
        old is None
        or depth > old[0]
        or (depth == old[0] and flag == TT_EXACT)
    ):
        TT[key] = (depth, value, flag, best_move)


def _ordered_children(
    player, opponent, moves, depth, ply, tt_move=0
):
    empty_count = 64 - (player | opponent).bit_count()
    odd_mask = 0

    if empty_count <= 16 and depth > 2:
        odd_mask = _odd_region_mask(FULL ^ (player | opponent))

    children = []
    bits = moves

    while bits:
        move = bits & -bits
        bits ^= move
        index = move.bit_length() - 1

        flipped = _flips(move, player, opponent)
        new_player = player | move | flipped
        new_opponent = opponent & ~flipped

        score = POSITION_WEIGHTS[index] * 25
        score += HISTORY[index]

        if move == tt_move:
            score += 2000000

        if ply < len(KILLERS):
            if move == KILLERS[ply][0]:
                score += 300000
            elif move == KILLERS[ply][1]:
                score += 150000

        if move & CORNERS:
            score += 500000
        elif move & EDGES:
            score += 140

        if move & odd_mask:
            score += 1200

        opponent_replies = _legal_moves(new_opponent, new_player)
        reply_count = opponent_replies.bit_count()

        score -= 30 * reply_count

        if opponent_replies & CORNERS:
            score -= 70000

        if not opponent_replies:
            score += 2500

        flip_count = flipped.bit_count()
        if empty_count > 20:
            score -= 4 * flip_count
        else:
            score += 4 * flip_count

        children.append(
            (score, move, new_player, new_opponent)
        )

    children.sort(key=lambda item: item[0], reverse=True)
    return children


def _negamax(player, opponent, depth, alpha, beta, ply):
    _check_time()

    key = (player, opponent)
    tt_entry = TT.get(key)
    tt_move = 0

    if tt_entry is not None:
        tt_depth, tt_value, tt_flag, tt_move = tt_entry

        if tt_depth >= depth:
            if tt_flag == TT_EXACT:
                return tt_value
            if tt_flag == TT_LOWER:
                alpha = max(alpha, tt_value)
            elif tt_flag == TT_UPPER:
                beta = min(beta, tt_value)

            if alpha >= beta:
                return tt_value

    moves = _legal_moves(player, opponent)

    if not moves:
        opponent_moves = _legal_moves(opponent, player)

        if not opponent_moves:
            value = _terminal_score(player, opponent)
            _store_tt(key, 127, value, TT_EXACT, 0)
            return value

        start_alpha = alpha
        start_beta = beta
        value = -_negamax(
            opponent, player, depth, -beta, -alpha, ply + 1
        )

        if value <= start_alpha:
            flag = TT_UPPER
        elif value >= start_beta:
            flag = TT_LOWER
        else:
            flag = TT_EXACT

        _store_tt(key, depth, value, flag, 0)
        return value

    if depth <= 0:
        return _evaluate(player, opponent, moves)

    start_alpha = alpha
    start_beta = beta
    best_value = -INF
    best_move = 0

    children = _ordered_children(
        player, opponent, moves, depth, ply, tt_move
    )

    for child_number, (
        _,
        move,
        new_player,
        new_opponent,
    ) in enumerate(children):
        if child_number == 0:
            value = -_negamax(
                new_opponent,
                new_player,
                depth - 1,
                -beta,
                -alpha,
                ply + 1,
            )
        else:
            value = -_negamax(
                new_opponent,
                new_player,
                depth - 1,
                -alpha - 1,
                -alpha,
                ply + 1,
            )

            if alpha < value < beta:
                value = -_negamax(
                    new_opponent,
                    new_player,
                    depth - 1,
                    -beta,
                    -alpha,
                    ply + 1,
                )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            index = move.bit_length() - 1
            HISTORY[index] = min(
                12000,
                HISTORY[index] + 4 * depth * depth,
            )

            if ply < len(KILLERS) and move != KILLERS[ply][0]:
                KILLERS[ply][1] = KILLERS[ply][0]
                KILLERS[ply][0] = move
            break

    if best_value <= start_alpha:
        flag = TT_UPPER
    elif best_value >= start_beta:
        flag = TT_LOWER
    else:
        flag = TT_EXACT

    _store_tt(key, depth, best_value, flag, best_move)
    return best_value


def _root_search(player, opponent, depth, preferred_move):
    moves = _legal_moves(player, opponent)
    children = _ordered_children(
        player, opponent, moves, depth, 0, preferred_move
    )

    alpha = -INF
    beta = INF
    best_value = -INF
    best_move = children[0][1]

    for child_number, (
        _,
        move,
        new_player,
        new_opponent,
    ) in enumerate(children):
        if child_number == 0:
            value = -_negamax(
                new_opponent,
                new_player,
                depth - 1,
                -beta,
                -alpha,
                1,
            )
        else:
            value = -_negamax(
                new_opponent,
                new_player,
                depth - 1,
                -alpha - 1,
                -alpha,
                1,
            )

            if alpha < value < beta:
                value = -_negamax(
                    new_opponent,
                    new_player,
                    depth - 1,
                    -beta,
                    -alpha,
                    1,
                )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

    _store_tt(
        (player, opponent),
        depth,
        best_value,
        TT_EXACT,
        best_move,
    )
    return best_value, best_move


def _array_to_bitboard(array):
    board = 0
    flat = array.ravel()

    for index in range(64):
        if int(flat[index]):
            board |= 1 << index

    return board


def _move_to_string(move):
    index = move.bit_length() - 1
    row, column = divmod(index, 8)
    return chr(ord("a") + column) + str(row + 1)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global DEADLINE, NODES, KILLERS

    player = _array_to_bitboard(you)
    enemy = _array_to_bitboard(opponent)
    legal = _legal_moves(player, enemy)

    if not legal:
        return "pass"

    if legal & (legal - 1) == 0:
        return _move_to_string(legal)

    if len(TT) > 350000:
        TT.clear()

    for i in range(64):
        if HISTORY[i] > 6000:
            HISTORY[i] //= 2

    KILLERS = [[0, 0] for _ in range(70)]
    NODES = 0
    DEADLINE = time.perf_counter() + 0.92

    empties = 64 - (player | enemy).bit_count()

    # Establish a strong legal fallback before any timed search.
    fallback_children = _ordered_children(
        player, enemy, legal, 1, 0, 0
    )
    best_move = fallback_children[0][1]

    if empties <= 12:
        targets = [min(4, empties), min(7, empties), empties]
        targets = sorted(set(d for d in targets if d > 0))
    elif empties <= 20:
        targets = list(range(3, empties + 1, 2))
        if targets[-1] != empties:
            targets.append(empties)
    else:
        targets = list(range(2, empties + 1))

    for depth in targets:
        try:
            _, candidate = _root_search(
                player, enemy, depth, best_move
            )
            best_move = candidate

            if depth >= empties:
                break
        except _SearchTimeout:
            break

    return _move_to_string(best_move)
