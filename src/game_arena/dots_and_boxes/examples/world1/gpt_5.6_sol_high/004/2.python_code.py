
import time
import random
import numpy as np


# ---------------------------------------------------------------------------
# Board geometry
#
# Horizontal indices:
#   0 .. 19  -> (row, col), row 0..4, col 0..3
#
# Vertical indices:
#   20 .. 39 -> (row, col), row 0..3, col 0..4
# ---------------------------------------------------------------------------

NUM_EDGES = 40
ALL_EDGES_MASK = (1 << NUM_EDGES) - 1

BOX_MASKS = []
EDGE_BOXES = [[] for _ in range(NUM_EDGES)]


def _h_index(row: int, col: int) -> int:
    return row * 4 + col


def _v_index(row: int, col: int) -> int:
    return 20 + row * 5 + col


for _r in range(4):
    for _c in range(4):
        _box_index = _r * 4 + _c
        _edges = (
            _h_index(_r, _c),
            _h_index(_r + 1, _c),
            _v_index(_r, _c),
            _v_index(_r, _c + 1),
        )

        _box_mask = 0
        for _edge in _edges:
            _box_mask |= 1 << _edge
            EDGE_BOXES[_edge].append(_box_index)

        BOX_MASKS.append(_box_mask)

EDGE_BOXES = tuple(tuple(x) for x in EDGE_BOXES)
BOX_MASKS = tuple(BOX_MASKS)


# Per-call search data.
_deadline = 0.0
_nodes = 0
_tt = {}
_eval_cache = {}
_forced_cache = {}


class _SearchTimeout(Exception):
    pass


def _mask_from_arrays(horizontal: np.ndarray, vertical: np.ndarray) -> int:
    mask = 0

    for row in range(5):
        for col in range(4):
            if horizontal[row, col] != 0:
                mask |= 1 << _h_index(row, col)

    for row in range(4):
        for col in range(5):
            if vertical[row, col] != 0:
                mask |= 1 << _v_index(row, col)

    return mask


def _move_string(edge: int) -> str:
    if edge < 20:
        row, col = divmod(edge, 4)
        return f"{row},{col},H"

    edge -= 20
    row, col = divmod(edge, 5)
    return f"{row},{col},V"


def _available_edges(mask: int):
    remaining = ALL_EDGES_MASK ^ mask
    while remaining:
        bit = remaining & -remaining
        yield bit.bit_length() - 1
        remaining ^= bit


def _move_information(mask: int, edge: int):
    """
    Return:
      captures: boxes completed immediately
      danger:   boxes changed from two sides to three sides
      load:     total number of already occupied sides around this edge
    """
    bit = 1 << edge
    captures = 0
    danger = 0
    load = 0

    for box in EDGE_BOXES[edge]:
        box_mask = BOX_MASKS[box]
        sides = (mask & box_mask).bit_count()
        load += sides

        if (mask & box_mask) == (box_mask ^ bit):
            captures += 1
        elif sides == 2:
            danger += 1

    return captures, danger, load


def _classify_moves(mask: int):
    captures = []
    safe = []
    dangerous = []

    for edge in _available_edges(mask):
        made, danger, load = _move_information(mask, edge)
        item = (edge, made, danger, load)

        if made:
            captures.append(item)
        elif danger == 0:
            safe.append(item)
        else:
            dangerous.append(item)

    return captures, safe, dangerous


def _ordered_moves(mask: int, captures_only: bool = False):
    moves = []

    for edge in _available_edges(mask):
        made, danger, load = _move_information(mask, edge)

        if captures_only and made == 0:
            continue

        if made:
            # Captures first, especially double captures.
            order = (3, made, -danger, load)
        elif danger == 0:
            # Safe moves before sacrifices.
            order = (2, load, len(EDGE_BOXES[edge]), -edge)
        else:
            # Prefer opening one box rather than two.
            order = (1, -danger, -load, -edge)

        moves.append((order, edge, made))

    moves.sort(reverse=True)
    return [(edge, made) for _, edge, made in moves]


def _forced_capture_gain(mask: int) -> int:
    """
    Estimate how many boxes the next player can collect immediately if they
    greedily continue every available capture.
    """
    cached = _forced_cache.get(mask)
    if cached is not None:
        return cached

    original = mask
    gain = 0

    while True:
        best_edge = -1
        best_made = 0
        best_danger = 10

        for edge in _available_edges(mask):
            made, danger, _ = _move_information(mask, edge)
            if made > best_made or (
                made == best_made and made > 0 and danger < best_danger
            ):
                best_edge = edge
                best_made = made
                best_danger = danger

        if best_edge < 0:
            break

        mask |= 1 << best_edge
        gain += best_made

    _forced_cache[original] = gain
    return gain


def _fallback_move(mask: int) -> int:
    captures, safe, dangerous = _classify_moves(mask)

    if captures:
        captures.sort(key=lambda x: (x[1], -x[2], x[3], -x[0]), reverse=True)
        return captures[0][0]

    if safe:
        safe.sort(
            key=lambda x: (x[3], len(EDGE_BOXES[x[0]]), -x[0]),
            reverse=True,
        )
        return safe[0][0]

    if dangerous:
        best_edge = dangerous[0][0]
        best_key = None

        for edge, _, danger, load in dangerous:
            concession = _forced_capture_gain(mask | (1 << edge))
            key = (concession, danger, load, edge)
            if best_key is None or key < best_key:
                best_key = key
                best_edge = edge

        return best_edge

    return -1


def _greedy_value(mask: int) -> int:
    """
    Fast full-game estimate from the perspective of the player to move.
    This is used as the leaf evaluation for the alpha-beta search.
    """
    cached = _eval_cache.get(mask)
    if cached is not None:
        return cached

    original = mask
    player = 1
    score = 0

    while mask != ALL_EDGES_MASK:
        captures, safe, dangerous = _classify_moves(mask)

        if captures:
            captures.sort(
                key=lambda x: (x[1], -x[2], x[3], -x[0]),
                reverse=True,
            )
            edge, made, _, _ = captures[0]
            mask |= 1 << edge
            score += player * made
            continue

        if safe:
            safe.sort(
                key=lambda x: (x[3], len(EDGE_BOXES[x[0]]), -x[0]),
                reverse=True,
            )
            edge = safe[0][0]
        else:
            edge = dangerous[0][0]
            best_key = None

            for candidate, _, danger, load in dangerous:
                concession = _forced_capture_gain(mask | (1 << candidate))
                key = (concession, danger, load, candidate)

                if best_key is None or key < best_key:
                    best_key = key
                    edge = candidate

        mask |= 1 << edge
        player = -player

    _eval_cache[original] = score
    return score


def _search(mask: int, depth: int, alpha: int, beta: int) -> int:
    """
    Negamax-like alpha-beta search.

    Capturing moves retain the same perspective and do not consume a
    turn-passing depth unit. Non-capturing moves pass the turn and negate the
    child value.
    """
    global _nodes

    _nodes += 1
    if (_nodes & 63) == 0 and time.perf_counter() >= _deadline:
        raise _SearchTimeout

    if mask == ALL_EDGES_MASK:
        return 0

    key = (mask, depth)
    alpha_original = alpha
    beta_original = beta

    entry = _tt.get(key)
    if entry is not None:
        value, flag = entry

        if flag == 0:
            return value
        if flag == 1:
            alpha = max(alpha, value)
        else:
            beta = min(beta, value)

        if alpha >= beta:
            return value

    captures_only = False

    if depth <= 0:
        has_capture = False
        for edge in _available_edges(mask):
            made, _, _ = _move_information(mask, edge)
            if made:
                has_capture = True
                break

        if not has_capture:
            value = _greedy_value(mask)
            _tt[key] = (value, 0)
            return value

        captures_only = True

    moves = _ordered_moves(mask, captures_only=captures_only)

    if not moves:
        return 0

    best = -17

    for edge, made in moves:
        child = mask | (1 << edge)

        if made:
            value = made + _search(
                child,
                depth,
                alpha - made,
                beta - made,
            )
        else:
            value = -_search(
                child,
                depth - 1,
                -beta,
                -alpha,
            )

        if value > best:
            best = value
        if value > alpha:
            alpha = value
        if alpha >= beta:
            break

    if best <= alpha_original:
        flag = 2  # Upper bound
    elif best >= beta_original:
        flag = 1  # Lower bound
    else:
        flag = 0  # Exact for this depth

    _tt[key] = (best, flag)
    return best


def _root_search(mask: int, depth: int):
    moves = _ordered_moves(mask)
    if not moves:
        return -1, 0

    best_edge = moves[0][0]
    best_value = -17
    alpha = -17
    beta = 17

    for edge, made in moves:
        if time.perf_counter() >= _deadline:
            raise _SearchTimeout

        child = mask | (1 << edge)

        if made:
            value = made + _search(
                child,
                depth,
                alpha - made,
                beta - made,
            )
        else:
            value = -_search(
                child,
                depth - 1,
                -beta,
                -alpha,
            )

        if value > best_value:
            best_value = value
            best_edge = edge

        if value > alpha:
            alpha = value

    return best_edge, best_value


def _iterative_tactical_search(mask: int, remaining: int) -> int:
    best_edge = _fallback_move(mask)

    for depth in range(1, remaining + 1):
        try:
            edge, _ = _root_search(mask, depth)
        except _SearchTimeout:
            break

        if edge >= 0:
            best_edge = edge

        # With at least as much turn-passing depth as remaining edges, the
        # search is necessarily terminal and therefore exact.
        if depth >= remaining:
            break

        if time.perf_counter() >= _deadline:
            break

    return best_edge


def _random_rollout(mask: int, rng: random.Random) -> int:
    """
    Randomized but tactically informed rollout. The return value is the future
    box differential for the player who is to move at the supplied state.
    """
    player = 1
    score = 0

    while mask != ALL_EDGES_MASK:
        captures, safe, dangerous = _classify_moves(mask)

        if captures:
            best_made = max(item[1] for item in captures)
            choices = [item for item in captures if item[1] == best_made]

            minimum_danger = min(item[2] for item in choices)
            choices = [item for item in choices if item[2] == minimum_danger]

            edge, made, _, _ = rng.choice(choices)
            mask |= 1 << edge
            score += player * made
            continue

        if safe:
            # Mostly random play avoids label bias, with a mild preference for
            # moves interacting with already developed boxes.
            if len(safe) == 1 or rng.random() < 0.28:
                maximum_load = max(item[3] for item in safe)
                choices = [item for item in safe if item[3] == maximum_load]
                edge = rng.choice(choices)[0]
            else:
                edge = rng.choice(safe)[0]
        else:
            best_gain = 100
            choices = []

            for item in dangerous:
                edge = item[0]
                gain = _forced_capture_gain(mask | (1 << edge))

                if gain < best_gain:
                    best_gain = gain
                    choices = [item]
                elif gain == best_gain:
                    choices.append(item)

            minimum_danger = min(item[2] for item in choices)
            choices = [item for item in choices if item[2] == minimum_danger]
            edge = rng.choice(choices)[0]

        mask |= 1 << edge
        player = -player

    return score


def _monte_carlo_safe_move(mask: int, safe_moves) -> int:
    candidates = [item[0] for item in safe_moves]

    if len(candidates) == 1:
        return candidates[0]

    totals = [0.0] * len(candidates)
    counts = [0] * len(candidates)

    seed = (
        (mask ^ (mask >> 17) ^ (mask << 11) ^ 0x9E3779B97F4A7C15)
        & ((1 << 64) - 1)
    )
    rng = random.Random(seed)

    rounds = 0

    while rounds < 10000:
        for i, edge in enumerate(candidates):
            if time.perf_counter() >= _deadline:
                break

            # The root move is safe and therefore passes the turn. A rollout
            # value for the opponent must consequently be negated.
            child = mask | (1 << edge)
            value = -_random_rollout(child, rng)

            totals[i] += value
            counts[i] += 1

        rounds += 1

        if time.perf_counter() >= _deadline:
            break

    best_edge = candidates[0]
    best_key = None

    for i, edge in enumerate(candidates):
        if counts[i]:
            average = totals[i] / counts[i]
        else:
            average = -100.0

        _, _, load = _move_information(mask, edge)
        key = (average, load, len(EDGE_BOXES[edge]), -edge)

        if best_key is None or key > best_key:
            best_key = key
            best_edge = edge

    return best_edge


def policy(
    horizontal: np.ndarray,
    vertical: np.ndarray,
    capture: np.ndarray,
) -> str:
    """
    Return a legal Dots and Boxes move in 'row,col,dir' format.
    """
    global _deadline, _nodes, _tt, _eval_cache, _forced_cache

    start = time.perf_counter()
    _deadline = start + 0.80
    _nodes = 0
    _tt = {}
    _eval_cache = {}
    _forced_cache = {}

    mask = _mask_from_arrays(horizontal, vertical)
    remaining = NUM_EDGES - mask.bit_count()

    # Guaranteed legal fallback, independent of all strategic calculations.
    fallback = _fallback_move(mask)

    if fallback < 0:
        # A valid game should never call the policy on a full board. This
        # defensive branch preserves the required string return type.
        return "0,0,H"

    captures, safe, _ = _classify_moves(mask)

    try:
        # Capturing positions, sacrifice positions, and compact endgames need
        # tactical calculation because chain control and double-crosses matter.
        if captures or not safe or remaining <= 20:
            chosen = _iterative_tactical_search(mask, remaining)
        else:
            # During the broad safe phase, simulations distinguish otherwise
            # similar non-conceding edges more efficiently than shallow search.
            chosen = _monte_carlo_safe_move(mask, safe)
    except Exception:
        # Search timing or any unexpected numerical issue must never prevent a
        # legal move from being returned.
        chosen = fallback

    if chosen < 0 or (mask & (1 << chosen)):
        chosen = fallback

    return _move_string(chosen)
