
import time
from typing import Dict, List, Tuple

import numpy as np


# Physical edges on a 4x4 box board:
# horizontal: rows 0..4, columns 0..3
# vertical:   rows 0..3, columns 0..4
#
# Edge indices 0..19 are horizontal and 20..39 are vertical.

EDGE_COUNT = 40
FULL_MASK = (1 << EDGE_COUNT) - 1

EDGES: List[Tuple[str, int, int]] = []
EDGE_INDEX = {}

for r in range(5):
    for c in range(4):
        idx = len(EDGES)
        EDGES.append(("H", r, c))
        EDGE_INDEX[("H", r, c)] = idx

for r in range(4):
    for c in range(5):
        idx = len(EDGES)
        EDGES.append(("V", r, c))
        EDGE_INDEX[("V", r, c)] = idx


# The four-edge mask for every box.
BOX_MASKS: List[int] = []
EDGE_BOXES: List[List[int]] = [[] for _ in range(EDGE_COUNT)]

for r in range(4):
    for c in range(4):
        top = EDGE_INDEX[("H", r, c)]
        bottom = EDGE_INDEX[("H", r + 1, c)]
        left = EDGE_INDEX[("V", r, c)]
        right = EDGE_INDEX[("V", r, c + 1)]

        box_index = r * 4 + c
        mask = (
            (1 << top)
            | (1 << bottom)
            | (1 << left)
            | (1 << right)
        )
        BOX_MASKS.append(mask)

        EDGE_BOXES[top].append(box_index)
        EDGE_BOXES[bottom].append(box_index)
        EDGE_BOXES[left].append(box_index)
        EDGE_BOXES[right].append(box_index)


# For chain estimation: neighboring boxes joined by an internal edge.
BOX_NEIGHBORS: List[List[Tuple[int, int]]] = [[] for _ in range(16)]

for r in range(4):
    for c in range(4):
        b = r * 4 + c

        if r > 0:
            e = EDGE_INDEX[("H", r, c)]
            BOX_NEIGHBORS[b].append((e, (r - 1) * 4 + c))
        if r < 3:
            e = EDGE_INDEX[("H", r + 1, c)]
            BOX_NEIGHBORS[b].append((e, (r + 1) * 4 + c))
        if c > 0:
            e = EDGE_INDEX[("V", r, c)]
            BOX_NEIGHBORS[b].append((e, r * 4 + c - 1))
        if c < 3:
            e = EDGE_INDEX[("V", r, c + 1)]
            BOX_NEIGHBORS[b].append((e, r * 4 + c + 1))


class _SearchTimeout(Exception):
    pass


def _gain(mask: int, edge: int) -> int:
    """Number of boxes captured by drawing an empty edge."""
    result = 0
    for box in EDGE_BOXES[edge]:
        if (mask & BOX_MASKS[box]).bit_count() == 3:
            result += 1
    return result


def _occupied_sides(mask: int, box: int) -> int:
    return (mask & BOX_MASKS[box]).bit_count()


def _chain_cost(mask_after_move: int, edge: int) -> int:
    """
    Estimate how many low-degree boxes are exposed by a sacrifice.

    The starting boxes have three occupied sides. The traversal follows
    undrawn internal edges through boxes with at most two remaining sides.
    """
    starts = [
        box
        for box in EDGE_BOXES[edge]
        if _occupied_sides(mask_after_move, box) == 3
    ]

    if not starts:
        return 0

    visited = 0
    stack = starts[:]
    count = 0

    while stack:
        box = stack.pop()
        bit = 1 << box
        if visited & bit:
            continue

        # Boxes with two or fewer missing sides form chain-like regions.
        occupied = _occupied_sides(mask_after_move, box)
        if occupied < 2:
            continue

        visited |= bit
        count += 1

        for joining_edge, neighbor in BOX_NEIGHBORS[box]:
            if mask_after_move & (1 << joining_edge):
                continue
            if not (visited & (1 << neighbor)):
                if _occupied_sides(mask_after_move, neighbor) >= 2:
                    stack.append(neighbor)

    return max(1, count)


def _ordered_moves(mask: int) -> List[int]:
    """
    Order moves for both alpha-beta efficiency and rollout quality.

    Priority:
      1. Captures, especially double captures.
      2. Safe moves that do not create a three-sided box.
      3. Sacrifices exposing the shortest estimated chain.
    """
    ranked = []
    free = FULL_MASK & ~mask

    while free:
        bit = free & -free
        free ^= bit
        edge = bit.bit_length() - 1

        gain = _gain(mask, edge)
        tie = (edge * 17 + ((mask >> (edge % 13)) & 31)) % 43

        if gain:
            # Captures are normally strongest and improve move ordering.
            ranked.append(((4, gain, tie), edge))
            continue

        adjacent_counts = [
            _occupied_sides(mask, box) for box in EDGE_BOXES[edge]
        ]

        # A non-capturing edge is unsafe when it changes a box from
        # two occupied sides to three occupied sides.
        unsafe = any(count == 2 for count in adjacent_counts)

        if not unsafe:
            # Prefer edges that do not prematurely turn boxes into
            # two-sided chain seeds.
            seeds_created = sum(count == 1 for count in adjacent_counts)
            untouched = sum(count == 0 for count in adjacent_counts)
            interior = len(EDGE_BOXES[edge])
            key = (3, -seeds_created, untouched, interior, tie)
            ranked.append((key, edge))
        else:
            cost = _chain_cost(mask | bit, edge)
            exposed = sum(count == 2 for count in adjacent_counts)
            key = (2, -cost, -exposed, tie)
            ranked.append((key, edge))

    ranked.sort(reverse=True)
    return [edge for _, edge in ranked]


def _rollout(mask: int, cache: Dict[int, int]) -> int:
    """
    Fast deterministic play to the end.

    The returned value is the future box margin for the player whose turn it
    is at `mask`. Capturing preserves the turn; a non-capture negates the
    next player's value.
    """
    cached = cache.get(mask)
    if cached is not None:
        return cached

    if mask == FULL_MASK:
        return 0

    moves = _ordered_moves(mask)
    if not moves:
        return 0

    edge = moves[0]
    new_mask = mask | (1 << edge)
    gain = _gain(mask, edge)

    if gain:
        value = gain + _rollout(new_mask, cache)
    else:
        value = -_rollout(new_mask, cache)

    # Bound memory usage during large opening searches.
    if len(cache) < 50000:
        cache[mask] = value

    return value


def _search(
    mask: int,
    depth: int,
    alpha: int,
    beta: int,
    deadline: float,
    nodes: List[int],
    table: Dict[Tuple[int, int], int],
    rollout_cache: Dict[int, int],
) -> int:
    """
    Alpha-beta search with Dots-and-Boxes turn handling.

    Depth is reduced only when a move passes the turn. Capturing sequences
    are therefore searched as tactical extensions at no depth cost.
    """
    nodes[0] += 1
    if (nodes[0] & 127) == 0 and time.perf_counter() >= deadline:
        raise _SearchTimeout

    if mask == FULL_MASK:
        return 0

    key = (mask, depth)
    cached = table.get(key)
    if cached is not None:
        return cached

    moves = _ordered_moves(mask)
    if not moves:
        return 0

    if depth == 0:
        # Quiescence: finish tactical capture sequences before evaluating.
        capture_moves = [edge for edge in moves if _gain(mask, edge) > 0]
        if not capture_moves:
            value = _rollout(mask, rollout_cache)
            table[key] = value
            return value
        moves = capture_moves

    best = -100
    cutoff = False

    for edge in moves:
        bit = 1 << edge
        new_mask = mask | bit
        gain = _gain(mask, edge)

        if gain:
            # Same player moves again.
            value = gain + _search(
                new_mask,
                depth,
                alpha - gain,
                beta - gain,
                deadline,
                nodes,
                table,
                rollout_cache,
            )
        else:
            # Turn passes, so perspective changes.
            value = -_search(
                new_mask,
                depth - 1,
                -beta,
                -alpha,
                deadline,
                nodes,
                table,
                rollout_cache,
            )

        if value > best:
            best = value
        if value > alpha:
            alpha = value
        if alpha >= beta:
            cutoff = True
            break

    # Only cache exact values. A beta-cutoff supplies a bound, not
    # necessarily the exact minimax value.
    if not cutoff:
        table[key] = best

    return best


def _edge_to_string(edge: int) -> str:
    orientation, row, col = EDGES[edge]
    return f"{row},{col},{orientation}"


def policy(
    horizontal: np.ndarray,
    vertical: np.ndarray,
    capture: np.ndarray,
) -> str:
    """
    Select a legal move for a 4x4 Dots and Boxes board.
    """
    del capture  # Existing scores do not change future margin optimization.

    mask = 0
    legal_edges: List[int] = []

    for edge, (orientation, row, col) in enumerate(EDGES):
        if orientation == "H":
            occupied = horizontal[row, col] != 0
        else:
            occupied = vertical[row, col] != 0

        if occupied:
            mask |= 1 << edge
        else:
            legal_edges.append(edge)

    # The engine should not request a move after the physical board is full.
    # The additional scan handles literal 5x5 representations defensively.
    if not legal_edges:
        for r in range(5):
            for c in range(5):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
                if vertical[r, c] == 0:
                    return f"{r},{c},V"
        return "0,0,H"

    # Establish an unquestionably legal fallback before doing any search.
    fallback_edge = legal_edges[0]
    rollout_cache: Dict[int, int] = {}

    try:
        # Improve the fallback by playing every root candidate against the
        # fast terminal policy.
        best_fallback_value = -100
        for edge in _ordered_moves(mask):
            new_mask = mask | (1 << edge)
            gain = _gain(mask, edge)

            if gain:
                value = gain + _rollout(new_mask, rollout_cache)
            else:
                value = -_rollout(new_mask, rollout_cache)

            if value > best_fallback_value:
                best_fallback_value = value
                fallback_edge = edge
    except Exception:
        return _edge_to_string(fallback_edge)

    best_edge = fallback_edge
    remaining = len(legal_edges)
    deadline = time.perf_counter() + 0.88

    # Iterative deepening ensures that interruption always leaves a complete
    # result from the previous iteration.
    for depth in range(1, remaining + 1):
        if time.perf_counter() >= deadline:
            break

        table: Dict[Tuple[int, int], int] = {}
        nodes = [0]

        try:
            root_alpha = -17
            root_beta = 17
            iteration_best = None
            iteration_value = -100

            for edge in _ordered_moves(mask):
                if time.perf_counter() >= deadline:
                    raise _SearchTimeout

                new_mask = mask | (1 << edge)
                gain = _gain(mask, edge)

                if gain:
                    value = gain + _search(
                        new_mask,
                        depth,
                        root_alpha - gain,
                        root_beta - gain,
                        deadline,
                        nodes,
                        table,
                        rollout_cache,
                    )
                else:
                    value = -_search(
                        new_mask,
                        depth - 1,
                        -root_beta,
                        -root_alpha,
                        deadline,
                        nodes,
                        table,
                        rollout_cache,
                    )

                if value > iteration_value:
                    iteration_value = value
                    iteration_best = edge

                if value > root_alpha:
                    root_alpha = value

            if iteration_best is not None:
                best_edge = iteration_best

            # At this depth every possible turn-passing move has been
            # searched, so the result is exact.
            if depth >= remaining:
                break

        except _SearchTimeout:
            break
        except Exception:
            break

    return _edge_to_string(best_edge)
