
import time
import numpy as np


# ---------------------------------------------------------------------------
# Bitboard constants
# ---------------------------------------------------------------------------

FULL = (1 << 64) - 1

A_FILE = sum(1 << (r * 8) for r in range(8))
H_FILE = sum(1 << (r * 8 + 7) for r in range(8))
NOT_A = FULL ^ A_FILE
NOT_H = FULL ^ H_FILE

TOP_EDGE = sum(1 << c for c in range(8))
BOTTOM_EDGE = sum(1 << (56 + c) for c in range(8))
LEFT_EDGE = A_FILE
RIGHT_EDGE = H_FILE
EDGE_MASK = TOP_EDGE | BOTTOM_EDGE | LEFT_EDGE | RIGHT_EDGE

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

# (shift amount, mask applied before shifting)
DIRECTIONS = (
    (1, NOT_H),    # east
    (-1, NOT_A),   # west
    (8, FULL),     # south
    (-8, FULL),    # north
    (9, NOT_H),    # south-east
    (7, NOT_A),    # south-west
    (-7, NOT_H),   # north-east
    (-9, NOT_A),   # north-west
)

# Positional values. Corner-neighbor penalties are corrected dynamically
# after the associated corner is occupied.
POSITION_VALUES = (
    120, -30,  20,   5,   5,  20, -30, 120,
    -30, -55,  -5,  -5,  -5,  -5, -55, -30,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -30, -55,  -5,  -5,  -5,  -5, -55, -30,
    120, -30,  20,   5,   5,  20, -30, 120,
)

_groups = {}
for _index, _weight in enumerate(POSITION_VALUES):
    _groups[_weight] = _groups.get(_weight, 0) | (1 << _index)
POSITION_GROUPS = tuple(_groups.items())
del _groups, _index, _weight

# For each corner: corner bit, orthogonally adjacent C-squares, diagonal X-square.
CORNER_ADJACENCY = (
    (1 << 0,  (1 << 1) | (1 << 8),   1 << 9),
    (1 << 7,  (1 << 6) | (1 << 15),  1 << 14),
    (1 << 56, (1 << 48) | (1 << 57), 1 << 49),
    (1 << 63, (1 << 55) | (1 << 62), 1 << 54),
)

CORNER_RAYS = (
    (
        tuple(range(0, 8)),
        tuple(range(0, 64, 8)),
    ),
    (
        tuple(range(7, -1, -1)),
        tuple(range(7, 64, 8)),
    ),
    (
        tuple(range(56, 64)),
        tuple(range(56, -1, -8)),
    ),
    (
        tuple(range(63, 55, -1)),
        tuple(range(63, 6, -8)),
    ),
)

INF = 10_000_000
EXACT = 0
LOWER = 1
UPPER = 2

# Persistent table can reuse analysis from earlier calls in the same game.
# key -> (depth, score, bound type, best move bit)
_TT = {}

_deadline = 0.0
_nodes = 0


# ---------------------------------------------------------------------------
# Bitboard operations
# ---------------------------------------------------------------------------

def _shift(bits, amount, mask):
    if amount > 0:
        return ((bits & mask) << amount) & FULL
    return (bits & mask) >> (-amount)


def _legal_moves(player, enemy):
    empty = FULL ^ (player | enemy)
    result = 0

    for amount, mask in DIRECTIONS:
        if amount > 0:
            captured = (((player & mask) << amount) & FULL) & enemy
            for _ in range(5):
                captured |= ((((captured & mask) << amount) & FULL) & enemy)
            result |= (((captured & mask) << amount) & FULL) & empty
        else:
            shift = -amount
            captured = ((player & mask) >> shift) & enemy
            for _ in range(5):
                captured |= (((captured & mask) >> shift) & enemy)
            result |= ((captured & mask) >> shift) & empty

    return result


def _flips_for_move(player, enemy, move):
    flips = 0

    for amount, mask in DIRECTIONS:
        line = 0
        current = _shift(move, amount, mask) & enemy

        while current:
            line |= current
            following = _shift(current, amount, mask)

            if following & player:
                flips |= line
                break
            if not (following & enemy):
                break
            current = following & enemy

    return flips


def _neighbors(bits):
    return (
        (((bits & NOT_H) << 1) & FULL)
        | ((bits & NOT_A) >> 1)
        | ((bits << 8) & FULL)
        | (bits >> 8)
        | (((bits & NOT_H) << 9) & FULL)
        | (((bits & NOT_A) << 7) & FULL)
        | ((bits & NOT_H) >> 7)
        | ((bits & NOT_A) >> 9)
    )


def _odd_region_mask(empty):
    """Return empty squares belonging to odd-sized 4-connected regions."""
    remaining = empty
    odd = 0

    while remaining:
        seed = remaining & -remaining
        region = seed
        frontier = seed

        while frontier:
            expanded = (
                (((frontier & NOT_H) << 1) & FULL)
                | ((frontier & NOT_A) >> 1)
                | ((frontier << 8) & FULL)
                | (frontier >> 8)
            ) & remaining & ~region

            if not expanded:
                break
            region |= expanded
            frontier = expanded

        if region.bit_count() & 1:
            odd |= region
        remaining &= ~region

    return odd


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def _stable_edge_bits(discs, occupied):
    stable = 0

    for corner_number, corner_bit in enumerate((1 << 0, 1 << 7, 1 << 56, 1 << 63)):
        if not (discs & corner_bit):
            continue

        for ray in CORNER_RAYS[corner_number]:
            for square in ray:
                bit = 1 << square
                if discs & bit:
                    stable |= bit
                else:
                    break

    # Once an edge has no empty cells, every disc on that edge is stable.
    for edge in (TOP_EDGE, BOTTOM_EDGE, LEFT_EDGE, RIGHT_EDGE):
        if (occupied & edge) == edge:
            stable |= discs & edge

    return stable


def _positional_difference(player, enemy):
    value = 0
    for weight, mask in POSITION_GROUPS:
        value += weight * (
            (player & mask).bit_count() - (enemy & mask).bit_count()
        )

    occupied = player | enemy

    # C- and X-squares cease being dangerous after their corner is occupied.
    for corner, c_squares, x_square in CORNER_ADJACENCY:
        if occupied & corner:
            value += 35 * (
                (player & c_squares).bit_count()
                - (enemy & c_squares).bit_count()
            )
            value += 60 * (
                (player & x_square).bit_count()
                - (enemy & x_square).bit_count()
            )

    return value


def _ratio_difference(a, b):
    total = a + b
    if total == 0:
        return 0
    return (100 * (a - b)) // total


def _evaluate(player, enemy, player_moves=None):
    occupied = player | enemy
    empty = FULL ^ occupied
    empties = empty.bit_count()

    if player_moves is None:
        player_moves = _legal_moves(player, enemy)
    enemy_moves = _legal_moves(enemy, player)

    my_mobility = player_moves.bit_count()
    enemy_mobility = enemy_moves.bit_count()
    mobility = _ratio_difference(my_mobility, enemy_mobility)

    potential_player = (empty & _neighbors(enemy)).bit_count()
    potential_enemy = (empty & _neighbors(player)).bit_count()
    potential = _ratio_difference(potential_player, potential_enemy)

    player_frontier = (player & _neighbors(empty)).bit_count()
    enemy_frontier = (enemy & _neighbors(empty)).bit_count()
    # Fewer frontier discs are preferable.
    frontier = _ratio_difference(enemy_frontier, player_frontier)

    corner_difference = (
        (player & CORNERS).bit_count() - (enemy & CORNERS).bit_count()
    )

    stable_player = _stable_edge_bits(player, occupied)
    stable_enemy = _stable_edge_bits(enemy, occupied)
    stable_difference = (
        stable_player.bit_count() - stable_enemy.bit_count()
    )

    disc_difference = player.bit_count() - enemy.bit_count()
    positional = _positional_difference(player, enemy)

    score = 3 * positional
    score += 1000 * corner_difference
    score += 120 * stable_difference

    if empties > 44:
        score += 6 * mobility
        score += 2 * potential
        score += 3 * frontier
        score -= 2 * disc_difference
    elif empties > 20:
        score += 8 * mobility
        score += 2 * potential
        score += 4 * frontier
        score += disc_difference
    else:
        score += 9 * mobility
        score += potential
        score += 3 * frontier
        score += (4 + 3 * (20 - empties)) * disc_difference

        # Coarse move-parity term from the current side's perspective.
        if empties & 1:
            score += 30
        else:
            score -= 30

    return score


def _terminal_score(player, enemy):
    difference = player.bit_count() - enemy.bit_count()
    if difference > 0:
        return 1_000_000 + 1000 * difference
    if difference < 0:
        return -1_000_000 + 1000 * difference
    return 0


# ---------------------------------------------------------------------------
# Search and move ordering
# ---------------------------------------------------------------------------

class _SearchTimeout(Exception):
    pass


def _ordered_moves(player, enemy, moves, tt_move, depth):
    empty = FULL ^ (player | enemy)
    empties = empty.bit_count()

    odd_regions = 0
    if empties <= 18 and depth >= 2:
        odd_regions = _odd_region_mask(empty)

    candidates = []
    remaining = moves

    while remaining:
        move = remaining & -remaining
        remaining ^= move

        flips = _flips_for_move(player, enemy, move)
        new_player = player | move | flips
        new_enemy = enemy ^ flips

        square = move.bit_length() - 1
        order_score = 10 * POSITION_VALUES[square]

        if move & CORNERS:
            order_score += 100_000
        elif move & EDGE_MASK:
            order_score += 150

        if move == tt_move:
            order_score += 1_000_000

        if move & odd_regions:
            order_score += 400

        flip_count = flips.bit_count()
        if empties > 30:
            order_score -= 8 * flip_count
        else:
            order_score += 8 * flip_count

        # At meaningful depths, prefer moves that constrain the opponent.
        if depth >= 2:
            opponent_moves = _legal_moves(new_enemy, new_player)
            order_score -= 120 * opponent_moves.bit_count()
            if opponent_moves & CORNERS:
                order_score -= 30_000 * (opponent_moves & CORNERS).bit_count()

        candidates.append(
            (order_score, move, flips, new_player, new_enemy)
        )

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates


def _negamax(player, enemy, depth, alpha, beta):
    global _nodes

    _nodes += 1
    if (_nodes & 255) == 0 and time.perf_counter() >= _deadline:
        raise _SearchTimeout

    key = player | (enemy << 64)
    alpha_original = alpha
    beta_original = beta

    entry = _TT.get(key)
    tt_move = 0

    if entry is not None:
        stored_depth, stored_score, bound_type, tt_move = entry

        if stored_depth >= depth:
            if bound_type == EXACT:
                return stored_score
            if bound_type == LOWER and stored_score >= beta:
                return stored_score
            if bound_type == UPPER and stored_score <= alpha:
                return stored_score

    moves = _legal_moves(player, enemy)

    if not moves:
        enemy_moves = _legal_moves(enemy, player)
        if not enemy_moves:
            score = _terminal_score(player, enemy)
            _TT[key] = (100, score, EXACT, 0)
            return score

        # Passing does not consume a placement depth.
        score = -_negamax(enemy, player, depth, -beta, -alpha)
        _TT[key] = (depth, score, EXACT, 0)
        return score

    if depth <= 0:
        return _evaluate(player, enemy, moves)

    candidates = _ordered_moves(player, enemy, moves, tt_move, depth)

    best_score = -INF
    best_move = candidates[0][1]

    for index, (_, move, flips, new_player, new_enemy) in enumerate(candidates):
        # Child is viewed from the opponent's perspective.
        if index == 0:
            score = -_negamax(
                new_enemy, new_player, depth - 1, -beta, -alpha
            )
        else:
            # Principal variation search: first try a zero-width window.
            score = -_negamax(
                new_enemy, new_player, depth - 1, -alpha - 1, -alpha
            )
            if alpha < score < beta:
                score = -_negamax(
                    new_enemy, new_player, depth - 1, -beta, -alpha
                )

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    if best_score <= alpha_original:
        bound_type = UPPER
    elif best_score >= beta_original:
        bound_type = LOWER
    else:
        bound_type = EXACT

    old_entry = _TT.get(key)
    if old_entry is None or depth >= old_entry[0]:
        _TT[key] = (depth, best_score, bound_type, best_move)

    return best_score


# ---------------------------------------------------------------------------
# Required API
# ---------------------------------------------------------------------------

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _deadline, _nodes

    start = time.perf_counter()
    _deadline = start + 0.92
    _nodes = 0

    player = 0
    enemy = 0

    you_flat = np.asarray(you).reshape(-1)
    opponent_flat = np.asarray(opponent).reshape(-1)

    for index in range(64):
        bit = 1 << index
        if int(you_flat[index]):
            player |= bit
        elif int(opponent_flat[index]):
            enemy |= bit

    moves = _legal_moves(player, enemy)

    if not moves:
        return "pass"

    # Limit persistent memory while retaining useful game-tree reuse.
    if len(_TT) > 400_000:
        _TT.clear()

    # Immediate legal fallback, replaced by a stronger heuristic fallback below.
    best_move = moves & -moves

    try:
        initial_order = _ordered_moves(player, enemy, moves, 0, 2)
        if initial_order:
            best_move = initial_order[0][1]
    except Exception:
        pass

    empties = 64 - (player | enemy).bit_count()

    if empties <= 12:
        requested_depths = [1, min(3, empties), empties]
        depths = []
        for depth in requested_depths:
            if depth >= 1 and depth not in depths:
                depths.append(depth)
    else:
        depths = range(1, empties + 1)

    root_key = player | (enemy << 64)

    try:
        for depth in depths:
            if time.perf_counter() >= _deadline:
                break

            _negamax(player, enemy, depth, -INF, INF)

            root_entry = _TT.get(root_key)
            if root_entry is not None:
                candidate = root_entry[3]
                if candidate and (candidate & moves):
                    best_move = candidate

            # Searching every remaining empty square gives an exact result.
            if depth >= empties:
                break

    except _SearchTimeout:
        pass
    except Exception:
        # The already selected move remains legal under any unexpected failure.
        pass

    # Defensive legality check before formatting.
    if not (best_move & moves):
        best_move = moves & -moves

    square = best_move.bit_length() - 1
    row, column = divmod(square, 8)
    return chr(ord("a") + column) + str(row + 1)
