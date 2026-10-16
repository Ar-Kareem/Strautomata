
from __future__ import annotations

import random
from collections import defaultdict, deque
from typing import List, Tuple

BOARD_N = 10

SHIP_LENGTHS = [5, 4, 3, 3, 2]

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < BOARD_N and 0 <= c < BOARD_N


def _grid_cells() -> List[Tuple[int, int]]:
    return [(r, c) for r in range(BOARD_N) for c in range(BOARD_N)]


def _get_hits(board: List[List[int]]) -> List[Tuple[int, int]]:
    hits = []
    for r in range(BOARD_N):
        row = board[r]
        for c in range(BOARD_N):
            if row[c] == 1:
                hits.append((r, c))
    return hits


def _get_misses(board: List[List[int]]) -> List[Tuple[int, int]]:
    out = []
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            if board[r][c] == -1:
                out.append((r, c))
    return out


def _find_hit_components(board: List[List[int]]) -> List[List[Tuple[int, int]]]:
    """
    Find connected components among hit cells (4-neighborhood).
    Used to focus probability in target mode.
    """
    hits = set(_get_hits(board))
    seen = set()
    comps = []

    for start in hits:
        if start in seen:
            continue
        q = deque([start])
        seen.add(start)
        comp = []
        while q:
            r, c = q.popleft()
            comp.append((r, c))
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if (nr, nc) in hits and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    q.append((nr, nc))
        comps.append(comp)
    return comps


def _orientation_from_cluster(cells: List[Tuple[int, int]]) -> str:
    """
    Determine likely orientation of a hit cluster:
    - "H" if all hits share same row
    - "V" if all share same col
    - "U" (unknown) otherwise
    """
    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}
    if len(rows) == 1:
        return "H"
    if len(cols) == 1:
        return "V"
    return "U"


def _cells_of_placement(start_r: int, start_c: int, length: int, orient: str) -> List[Tuple[int, int]]:
    if orient == "H":
        return [(start_r, start_c + i) for i in range(length)]
    else:
        return [(start_r + i, start_c) for i in range(length)]


def _placement_consistent(
    board: List[List[int]],
    cells: List[Tuple[int, int]],
    require_hits: set[Tuple[int, int]],
    forbid_misses: set[Tuple[int, int]],
) -> bool:
    # Forbid misses
    for (r, c) in cells:
        if (r, c) in forbid_misses:
            return False
    # Must cover all required hits
    for h in require_hits:
        if h not in cells:
            return False
    return True


def _remaining_ship_lengths(board: List[List[int]], total_hits: int) -> List[int]:
    """
    We don't know exactly which ships remain from just hit/miss,
    but we can infer an effective multiset by assuming any connected hits
    correspond to some subset of ships. A robust approach:
    use full lengths always; probability model naturally handles inconsistencies.

    However, we can slightly bias by removing lengths that are impossible
    given number of hits. Still keep it safe by not pruning aggressively.
    """
    # Conservative: keep all lengths.
    return SHIP_LENGTHS[:]


def _probability_heatmap(board: List[List[int]], target_mode: bool) -> List[List[int]]:
    """
    Build heatmap by enumerating all placements for all ships that are consistent
    with the board's known hits/misses.
    In target_mode, restrict to placements that include at least one known hit and
    (if possible) align with a hit component orientation.
    """
    forbid_misses = set(_get_misses(board))
    hits = set(_get_hits(board))
    heat = [[0 for _ in range(BOARD_N)] for _ in range(BOARD_N)]

    if not hits:
        require_hits = set()
        hit_components = []
        orient_hint = "U"
    else:
        # In target mode, focus on the largest hit component (most likely current ship).
        hit_components = _find_hit_components(board)
        largest = max(hit_components, key=len)
        orient_hint = _orientation_from_cluster(largest)

        if target_mode:
            # Require at least one hit from the chosen component.
            # Also, ensure all hits in that component that are forced into a line are covered.
            require_hits = set(largest)
            # But if component orientation is unknown, we can't require all hits for line-consistency.
            if orient_hint == "U":
                # Require only the "most central" hit (reduces overrestriction)
                # by selecting a median cell from the component.
                sorted_comp = sorted(largest)
                require_hits = {sorted_comp[len(sorted_comp) // 2]}
        else:
            require_hits = set()

    remaining_lengths = _remaining_ship_lengths(board, total_hits=len(hits))

    # Enumerate placements
    for length in remaining_lengths:
        for r in range(BOARD_N):
            for c in range(BOARD_N):
                # Horizontal
                if c + length <= BOARD_N:
                    if target_mode:
                        # Orientation restriction from hint if known
                        if orient_hint == "V":
                            pass
                        else:
                            cells = _cells_of_placement(r, c, length, "H")
                            if target_mode:
                                if hits and not any(cell in hits for cell in cells):
                                    continue
                            if _placement_consistent(board, cells, require_hits, forbid_misses):
                                for (rr, cc) in cells:
                                    if board[rr][cc] == 0:
                                        heat[rr][cc] += 1
                    else:
                        cells = _cells_of_placement(r, c, length, "H")
                        if _placement_consistent(board, cells, require_hits, forbid_misses):
                            for (rr, cc) in cells:
                                if board[rr][cc] == 0:
                                    heat[rr][cc] += 1

                # Vertical
                if r + length <= BOARD_N:
                    if target_mode:
                        if orient_hint == "H":
                            pass
                        else:
                            cells = _cells_of_placement(r, c, length, "V")
                            if target_mode:
                                if hits and not any(cell in hits for cell in cells):
                                    continue
                            if _placement_consistent(board, cells, require_hits, forbid_misses):
                                for (rr, cc) in cells:
                                    if board[rr][cc] == 0:
                                        heat[rr][cc] += 1
                    else:
                        cells = _cells_of_placement(r, c, length, "V")
                        if _placement_consistent(board, cells, require_hits, forbid_misses):
                            for (rr, cc) in cells:
                                if board[rr][cc] == 0:
                                    heat[rr][cc] += 1

    return heat


def _choose_best_unknown(board: List[List[int]], heat: List[List[int]]) -> Tuple[int, int]:
    best = -1
    candidates = []
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            if board[r][c] == 0:
                v = heat[r][c]
                if v > best:
                    best = v
                    candidates = [(r, c)]
                elif v == best:
                    candidates.append((r, c))
    if not candidates:
        # Fallback: pick any unknown
        for r in range(BOARD_N):
            for c in range(BOARD_N):
                if board[r][c] == 0:
                    return r, c
        # Should never happen if move legality checked externally
        return 0, 0
    # Small randomness to break ties
    return random.choice(candidates)


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Battleship move policy on a 10x10 board.
    board values: 0 unknown, -1 miss, 1 hit.
    Returns (row, col) for a cell with board[row][col] == 0.
    """
    hits = _get_hits(board)
    # If we have any hits, target mode; else hunt mode.
    target_mode = len(hits) > 0

    heat = _probability_heatmap(board, target_mode=target_mode)

    # In target mode, we can also strongly prefer cells adjacent to any hit
    # if heat is flat; but heat should already capture this. We'll apply a gentle
    # adjacency boost by adding 1 to unknown neighbors of hits.
    if target_mode:
        boost = [[0 for _ in range(BOARD_N)] for _ in range(BOARD_N)]
        hitset = set(hits)
        for (r, c) in hitset:
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if _in_bounds(nr, nc) and board[nr][nc] == 0:
                    boost[nr][nc] += 1
        for r in range(BOARD_N):
            for c in range(BOARD_N):
                heat[r][c] += boost[r][c]

    move = _choose_best_unknown(board, heat)
    r, c = move
    # Ensure legality strictly
    if board[r][c] != 0:
        # Find first legal
        for rr in range(BOARD_N):
            for cc in range(BOARD_N):
                if board[rr][cc] == 0:
                    return rr, cc
    return move
