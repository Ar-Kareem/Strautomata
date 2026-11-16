
import time
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import numpy as np


# Edge numbering:
#   0..19  : horizontal edges, index = row * 4 + col
#   20..39 : vertical edges,   index = 20 + row * 5 + col
NUM_EDGES = 40
ALL_EDGES_MASK = (1 << NUM_EDGES) - 1

EDGE_ACTIONS: List[str] = []
EDGE_BOXES: List[List[int]] = [[] for _ in range(NUM_EDGES)]
EDGE_CENTER_SCORE: List[float] = [0.0] * NUM_EDGES
BOX_MASKS: List[int] = [0] * 16


def _h_index(row: int, col: int) -> int:
    return row * 4 + col


def _v_index(row: int, col: int) -> int:
    return 20 + row * 5 + col


# Build edge action strings.
for r in range(5):
    for c in range(4):
        EDGE_ACTIONS.append(f"{r},{c},H")

for r in range(4):
    for c in range(5):
        EDGE_ACTIONS.append(f"{r},{c},V")


# Build box masks and edge-to-box adjacency.
for r in range(4):
    for c in range(4):
        box = r * 4 + c
        edges = (
            _h_index(r, c),
            _h_index(r + 1, c),
            _v_index(r, c),
            _v_index(r, c + 1),
        )
        mask = 0
        for edge in edges:
            mask |= 1 << edge
            EDGE_BOXES[edge].append(box)
        BOX_MASKS[box] = mask


# Small centrality bonus used only to break otherwise similar opening choices.
for r in range(5):
    for c in range(4):
        edge = _h_index(r, c)
        x = float(r)
        y = c + 0.5
        EDGE_CENTER_SCORE[edge] = -0.01 * (
            abs(x - 2.0) + abs(y - 2.0)
        )

for r in range(4):
    for c in range(5):
        edge = _v_index(r, c)
        x = r + 0.5
        y = float(c)
        EDGE_CENTER_SCORE[edge] = -0.01 * (
            abs(x - 2.0) + abs(y - 2.0)
        )


# Search globals, reset for every call to policy.
_DEADLINE = 0.0
_NODES = 0
_TT: Dict[Tuple[int, int], Tuple[float, int]] = {}
_EVAL_CACHE: Dict[int, float] = {}
_LOONY_CACHE: Dict[int, Optional[float]] = {}

INF = 1.0e9
TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2


class _SearchTimeout(Exception):
    pass


def _check_time() -> None:
    global _NODES
    _NODES += 1
    if (_NODES & 255) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout


def _gain(mask: int, edge: int) -> int:
    """Number of boxes completed by drawing edge."""
    bit = 1 << edge
    result = 0
    for box in EDGE_BOXES[edge]:
        other_sides = BOX_MASKS[box] ^ bit
        if (mask & other_sides) == other_sides:
            result += 1
    return result


def _created_threes(mask: int, edge: int) -> int:
    """Number of adjacent boxes changed from two sides to three sides."""
    result = 0
    for box in EDGE_BOXES[edge]:
        if (mask & BOX_MASKS[box]).bit_count() == 2:
            result += 1
    return result


def _side_transition_counts(mask: int, edge: int) -> Tuple[int, int]:
    """Return adjacent boxes changed to one side and to two sides."""
    new_ones = 0
    new_twos = 0
    for box in EDGE_BOXES[edge]:
        sides = (mask & BOX_MASKS[box]).bit_count()
        if sides == 0:
            new_ones += 1
        elif sides == 1:
            new_twos += 1
    return new_ones, new_twos


def _quick_harvest(mask: int) -> int:
    """
    Estimate how many boxes the player to move can collect by repeatedly
    taking an available capture. Used for move ordering and leaf estimates.
    """
    total = 0

    while True:
        remaining = ALL_EDGES_MASK ^ mask
        best_edge = -1
        best_key = (-1, -1)

        while remaining:
            bit = remaining & -remaining
            edge = bit.bit_length() - 1
            remaining ^= bit

            gain = _gain(mask, edge)
            if gain:
                next_mask = mask | bit

                # Prefer moves that also expose further captures.
                followups = 0
                next_remaining = ALL_EDGES_MASK ^ next_mask
                while next_remaining:
                    bit2 = next_remaining & -next_remaining
                    edge2 = bit2.bit_length() - 1
                    next_remaining ^= bit2
                    if _gain(next_mask, edge2):
                        followups += 1

                key = (gain, followups)
                if key > best_key:
                    best_key = key
                    best_edge = edge

        if best_edge < 0:
            return total

        gained = _gain(mask, best_edge)
        total += gained
        mask |= 1 << best_edge


@lru_cache(maxsize=None)
def _abstract_loony_value(
    components: Tuple[Tuple[int, int], ...]
) -> float:
    """
    Exact controlled-value recursion for independent chains and loops.

    A component is (size, handout):
      handout=2 for a chain
      handout=4 for a loop

    The returned score is the future box differential for the player who
    must open a component.
    """
    if not components:
        return 0.0

    best = -INF

    for i, (size, handout) in enumerate(components):
        rest = components[:i] + components[i + 1:]
        rest_value = _abstract_loony_value(rest)

        # The opponent takes the whole component, then must open the rest.
        opponent_takes_all = -float(size) - rest_value
        opponent_choice = opponent_takes_all

        # Alternatively the opponent may leave the standard handout and
        # preserve control of the remaining components.
        if (handout == 2 and size >= 3) or (
            handout == 4 and size >= 4
        ):
            keep_control = (
                float(2 * handout - size) + rest_value
            )
            opponent_choice = min(opponent_choice, keep_control)

        # The opener chooses which component to sacrifice.
        best = max(best, opponent_choice)

    return best


def _loony_value(mask: int) -> Optional[float]:
    """
    Recognize a standard chain/loop endgame and return its exact abstract
    value. Returns None if the position is not in standard loony form.
    """
    cached = _LOONY_CACHE.get(mask, "missing")
    if cached != "missing":
        return cached

    remaining_boxes: List[int] = []

    for box, box_mask in enumerate(BOX_MASKS):
        sides = (mask & box_mask).bit_count()

        if sides == 4:
            continue

        # Standard loony components have exactly two undrawn sides per box.
        if sides != 2:
            _LOONY_CACHE[mask] = None
            return None

        remaining_boxes.append(box)

    if not remaining_boxes:
        _LOONY_CACHE[mask] = 0.0
        return 0.0

    remaining_set = set(remaining_boxes)
    visited = set()
    components: List[Tuple[int, int]] = []

    for start in remaining_boxes:
        if start in visited:
            continue

        stack = [start]
        visited.add(start)
        component: List[int] = []
        has_open_boundary = False

        while stack:
            box = stack.pop()
            component.append(box)
            r, c = divmod(box, 4)

            # Empty boundary sides make this a chain rather than a loop.
            if r == 0 and not (mask & (1 << _h_index(0, c))):
                has_open_boundary = True
            if r == 3 and not (mask & (1 << _h_index(4, c))):
                has_open_boundary = True
            if c == 0 and not (mask & (1 << _v_index(r, 0))):
                has_open_boundary = True
            if c == 3 and not (mask & (1 << _v_index(r, 4))):
                has_open_boundary = True

            neighbours: List[Tuple[int, int]] = []

            if r > 0:
                neighbours.append(
                    ((r - 1) * 4 + c, _h_index(r, c))
                )
            if r < 3:
                neighbours.append(
                    ((r + 1) * 4 + c, _h_index(r + 1, c))
                )
            if c > 0:
                neighbours.append(
                    (r * 4 + c - 1, _v_index(r, c))
                )
            if c < 3:
                neighbours.append(
                    (r * 4 + c + 1, _v_index(r, c + 1))
                )

            for neighbour, shared_edge in neighbours:
                if (
                    neighbour in remaining_set
                    and not (mask & (1 << shared_edge))
                    and neighbour not in visited
                ):
                    visited.add(neighbour)
                    stack.append(neighbour)

        handout = 2 if has_open_boundary else 4
        components.append((len(component), handout))

    key = tuple(sorted(components))
    value = _abstract_loony_value(key)
    _LOONY_CACHE[mask] = value
    return value


def _heuristic(mask: int) -> float:
    """
    Static evaluation from the perspective of the player to move.
    It is called only at stable positions without immediate captures.
    """
    cached = _EVAL_CACHE.get(mask)
    if cached is not None:
        return cached

    loony = _loony_value(mask)
    if loony is not None:
        _EVAL_CACHE[mask] = loony
        return loony

    remaining = ALL_EDGES_MASK ^ mask
    safe_count = 0
    degree_two_boxes = 0
    remaining_boxes = 0

    for box_mask in BOX_MASKS:
        sides = (mask & box_mask).bit_count()
        if sides < 4:
            remaining_boxes += 1
        if sides == 2:
            degree_two_boxes += 1

    scan = remaining
    while scan:
        bit = scan & -scan
        edge = bit.bit_length() - 1
        scan ^= bit

        if _gain(mask, edge) == 0 and _created_threes(mask, edge) == 0:
            safe_count += 1

    if safe_count:
        # If safe moves simply alternate, making the last safe move is
        # valuable because the opponent must open the first chain.
        initiative = 1.0 if (safe_count & 1) else -1.0
        magnitude = min(
            2.0,
            0.30 + 0.035 * degree_two_boxes
            + 0.015 * remaining_boxes,
        )
        value = initiative * magnitude
        _EVAL_CACHE[mask] = value
        return value

    # No safe edge exists. Estimate the least costly component to open.
    minimum_gift = 100
    scan = remaining
    while scan:
        bit = scan & -scan
        edge = bit.bit_length() - 1
        scan ^= bit
        gift = _quick_harvest(mask | bit)
        if gift < minimum_gift:
            minimum_gift = gift

    if minimum_gift == 100:
        value = 0.0
    else:
        value = -float(minimum_gift)

    _EVAL_CACHE[mask] = value
    return value


def _move_score(
    mask: int,
    edge: int,
    gain: int,
    detailed: bool = False,
) -> float:
    """Move-ordering score; larger moves are searched first."""
    next_mask = mask | (1 << edge)

    if gain:
        score = 1000.0 + 100.0 * gain
        if detailed:
            score += 4.0 * _quick_harvest(next_mask)
        return score

    created = _created_threes(mask, edge)

    if created == 0:
        new_ones, new_twos = _side_transition_counts(mask, edge)

        # Preserve safety by avoiding second sides where possible. In the
        # very early game, spreading first sides over interior boxes is useful.
        return (
            100.0
            + 2.0 * new_ones
            - 12.0 * new_twos
            + 0.5 * len(EDGE_BOXES[edge])
            + EDGE_CENTER_SCORE[edge]
        )

    score = -20.0 * created
    if detailed:
        score -= 5.0 * _quick_harvest(next_mask)
    return score


def _ordered_moves(
    mask: int,
    captures_only_at_quiescence: bool,
) -> List[Tuple[int, int]]:
    """
    Generate moves with tactical ordering.

    If captures are available, safe remote moves are omitted inside the
    search because voluntarily passing while leaving a free box is dominated.
    Dangerous noncapturing moves remain, since they include hard-hearted
    handouts.
    """
    remaining = ALL_EDGES_MASK ^ mask
    moves: List[Tuple[int, int, float]] = []
    captures_exist = False

    scan = remaining
    info: List[Tuple[int, int, int]] = []

    while scan:
        bit = scan & -scan
        edge = bit.bit_length() - 1
        scan ^= bit

        gain = _gain(mask, edge)
        created = 0 if gain else _created_threes(mask, edge)
        if gain:
            captures_exist = True
        info.append((edge, gain, created))

    for edge, gain, created in info:
        if captures_exist:
            if gain:
                pass
            elif captures_only_at_quiescence:
                continue
            elif created == 0:
                # Ignore unrelated safe passes, but retain handouts.
                continue

        score = _move_score(mask, edge, gain, detailed=False)
        moves.append((edge, gain, score))

    moves.sort(key=lambda item: item[2], reverse=True)
    return [(edge, gain) for edge, gain, _ in moves]


def _search(mask: int, depth: int, alpha: float, beta: float) -> float:
    """
    Negamax-style search where depth counts noncapturing turn changes.
    Capturing sequences are extended automatically.
    """
    _check_time()

    if mask == ALL_EDGES_MASK:
        return 0.0

    original_alpha = alpha
    original_beta = beta
    key = (mask, depth)

    entry = _TT.get(key)
    if entry is not None:
        value, flag = entry
        if flag == TT_EXACT:
            return value
        if flag == TT_LOWER:
            alpha = max(alpha, value)
        else:
            beta = min(beta, value)
        if alpha >= beta:
            return value

    # Determine whether an immediate capture exists.
    remaining = ALL_EDGES_MASK ^ mask
    captures_exist = False
    scan = remaining
    while scan:
        bit = scan & -scan
        edge = bit.bit_length() - 1
        scan ^= bit
        if _gain(mask, edge):
            captures_exist = True
            break

    if not captures_exist:
        loony = _loony_value(mask)
        if loony is not None:
            _TT[key] = (loony, TT_EXACT)
            return loony

        if depth <= 0:
            value = _heuristic(mask)
            _TT[key] = (value, TT_EXACT)
            return value

    # At depth zero, continue immediate captures but do not begin a new
    # noncapturing sacrifice.
    moves = _ordered_moves(
        mask,
        captures_only_at_quiescence=(depth <= 0),
    )

    if not moves:
        value = _heuristic(mask)
        _TT[key] = (value, TT_EXACT)
        return value

    best = -INF

    for edge, gain in moves:
        child = mask | (1 << edge)

        if gain:
            # A capture keeps the turn.
            value = float(gain) + _search(
                child,
                depth,
                alpha - gain,
                beta - gain,
            )
        else:
            if depth <= 0:
                continue

            # A noncapture passes the turn.
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

    if best == -INF:
        best = _heuristic(mask)

    if best <= original_alpha:
        flag = TT_UPPER
    elif best >= original_beta:
        flag = TT_LOWER
    else:
        flag = TT_EXACT

    _TT[key] = (best, flag)
    return best


def _root_search(
    mask: int,
    depth: int,
    root_order: List[int],
) -> Tuple[float, int]:
    """Search all legal root moves and return (value, best_edge)."""
    legal = [edge for edge in root_order if not (mask & (1 << edge))]
    alpha = -INF
    best_value = -INF
    best_edge = legal[0]

    for edge in legal:
        if time.perf_counter() >= _DEADLINE:
            raise _SearchTimeout

        gain = _gain(mask, edge)
        child = mask | (1 << edge)

        if gain:
            value = float(gain) + _search(
                child,
                depth,
                alpha - gain,
                INF,
            )
        else:
            value = -_search(
                child,
                depth - 1,
                -INF,
                -alpha,
            )

        if value > best_value:
            best_value = value
            best_edge = edge

        if value > alpha:
            alpha = value

    return best_value, best_edge


def policy(
    horizontal: np.ndarray,
    vertical: np.ndarray,
    capture: np.ndarray,
) -> str:
    """
    Return a legal move for a 4x4 Dots and Boxes board.
    """
    del capture  # Future tactics are determined by occupied edges.

    global _DEADLINE, _NODES, _TT, _EVAL_CACHE, _LOONY_CACHE

    occupied = 0
    legal_edges: List[int] = []

    # Only the geometrically valid 5x4 horizontal entries are edges.
    for r in range(5):
        for c in range(4):
            edge = _h_index(r, c)
            if int(horizontal[r, c]) != 0:
                occupied |= 1 << edge
            else:
                legal_edges.append(edge)

    # Only the geometrically valid 4x5 vertical entries are edges.
    for r in range(4):
        for c in range(5):
            edge = _v_index(r, c)
            if int(vertical[r, c]) != 0:
                occupied |= 1 << edge
            else:
                legal_edges.append(edge)

    # Normally policy is never called after the game is over.
    if not legal_edges:
        return "0,0,H"

    # Establish a strong legal fallback before doing any timed work.
    ranked = sorted(
        legal_edges,
        key=lambda edge: _move_score(
            occupied,
            edge,
            _gain(occupied, edge),
            detailed=True,
        ),
        reverse=True,
    )
    best_edge = ranked[0]

    try:
        _NODES = 0
        _TT = {}
        _EVAL_CACHE = {}
        _LOONY_CACHE = {}
        _DEADLINE = time.perf_counter() + 0.86

        remaining_edges = len(legal_edges)

        # Iterative deepening ensures that an interrupted iteration never
        # destroys the best result from the previous completed iteration.
        root_order = ranked[:]
        maximum_depth = min(remaining_edges, 24)

        for depth in range(1, maximum_depth + 1):
            _, iteration_best = _root_search(
                occupied,
                depth,
                root_order,
            )
            best_edge = iteration_best

            # Search the previous principal move first on the next iteration.
            root_order = [best_edge] + [
                edge for edge in root_order if edge != best_edge
            ]

            if time.perf_counter() >= _DEADLINE:
                break

    except _SearchTimeout:
        pass
    except Exception:
        # The preselected fallback is guaranteed to be an empty valid edge.
        pass

    return EDGE_ACTIONS[best_edge]
