
import random
from collections import deque
from typing import List, Tuple

# Standard Battleship fleet (lengths)
FLEET = (5, 4, 3, 3, 2)


def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 10 and 0 <= c < 10


def _neighbors4(r: int, c: int):
    if r > 0:
        yield r - 1, c
    if r < 9:
        yield r + 1, c
    if c > 0:
        yield r, c - 1
    if c < 9:
        yield r, c + 1


def _board_seed(board: List[List[int]]) -> int:
    # Deterministic seed from board contents (stable across runs)
    x = 1469598103934665603  # FNV offset basis (64-bit)
    for r in range(10):
        row = board[r]
        for c in range(10):
            v = row[c] + 2  # map {-1,0,1} to {1,2,3}
            x ^= (v + (r * 11 + c) * 1315423911) & 0xFFFFFFFFFFFFFFFF
            x = (x * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return x & 0xFFFFFFFF


def _unknown_cells(board: List[List[int]]) -> List[Tuple[int, int]]:
    return [(r, c) for r in range(10) for c in range(10) if board[r][c] == 0]


def _hit_cells(board: List[List[int]]) -> List[Tuple[int, int]]:
    return [(r, c) for r in range(10) for c in range(10) if board[r][c] == 1]


def _hit_components(board: List[List[int]]) -> List[List[Tuple[int, int]]]:
    """4-neighbor connected components of hits."""
    seen = [[False] * 10 for _ in range(10)]
    comps: List[List[Tuple[int, int]]] = []
    for r in range(10):
        for c in range(10):
            if board[r][c] != 1 or seen[r][c]:
                continue
            q = deque([(r, c)])
            seen[r][c] = True
            comp = []
            while q:
                rr, cc = q.popleft()
                comp.append((rr, cc))
                for nr, nc in _neighbors4(rr, cc):
                    if not seen[nr][nc] and board[nr][nc] == 1:
                        seen[nr][nc] = True
                        q.append((nr, nc))
            comps.append(comp)
    return comps


def _is_linear_component(comp: List[Tuple[int, int]]) -> Tuple[bool, str]:
    """Return (is_linear, orientation in {'h','v','?'})."""
    if len(comp) <= 1:
        return True, "?"
    rows = {r for r, _ in comp}
    cols = {c for _, c in comp}
    if len(rows) == 1:
        return True, "h"
    if len(cols) == 1:
        return True, "v"
    return False, "?"


def _add_heat_for_all_placements(board: List[List[int]], heat: List[List[int]]) -> None:
    """Base hunt heatmap: count placements that don't cross misses."""
    for L in FLEET:
        # horizontal
        for r in range(10):
            for c0 in range(0, 10 - L + 1):
                ok = True
                for k in range(L):
                    if board[r][c0 + k] == -1:
                        ok = False
                        break
                if not ok:
                    continue
                for k in range(L):
                    c = c0 + k
                    if board[r][c] == 0:
                        heat[r][c] += 1

        # vertical
        for c in range(10):
            for r0 in range(0, 10 - L + 1):
                ok = True
                for k in range(L):
                    if board[r0 + k][c] == -1:
                        ok = False
                        break
                if not ok:
                    continue
                for k in range(L):
                    r = r0 + k
                    if board[r][c] == 0:
                        heat[r][c] += 1


def _add_heat_for_hit_components(board: List[List[int]], heat: List[List[int]], comps: List[List[Tuple[int, int]]]) -> None:
    """
    Target-mode heat:
    - Big bonuses to adjacent unknowns
    - Very big bonuses to ends of linear components
    - Placement-consistency bonuses for placements that cover the component
    """
    ADJ_BONUS = 60
    END_BONUS = 220
    PLACEMENT_BONUS = 8  # per placement per cell, modest but adds up

    # Adjacent-to-hit bonus
    for comp in comps:
        for r, c in comp:
            for nr, nc in _neighbors4(r, c):
                if board[nr][nc] == 0:
                    heat[nr][nc] += ADJ_BONUS

    for comp in comps:
        linear, orient = _is_linear_component(comp)
        comp_set = set(comp)

        # If component isn't linear (can happen when two ships touch orthogonally),
        # we avoid forcing a single-ship model and rely mainly on adjacency bonus.
        if not linear:
            continue

        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        min_r, max_r = min(rs), max(rs)
        min_c, max_c = min(cs), max(cs)
        size = len(comp)

        # End bonuses for likely continuation cells
        if orient == "h":
            r0 = rs[0]
            lc = min_c - 1
            rc = max_c + 1
            if _in_bounds(r0, lc) and board[r0][lc] == 0:
                heat[r0][lc] += END_BONUS
            if _in_bounds(r0, rc) and board[r0][rc] == 0:
                heat[r0][rc] += END_BONUS
        elif orient == "v":
            c0 = cs[0]
            ur = min_r - 1
            dr = max_r + 1
            if _in_bounds(ur, c0) and board[ur][c0] == 0:
                heat[ur][c0] += END_BONUS
            if _in_bounds(dr, c0) and board[dr][c0] == 0:
                heat[dr][c0] += END_BONUS

        # Placement-consistency heat: count placements that cover this component
        span = (max_c - min_c + 1) if orient == "h" else (max_r - min_r + 1) if orient == "v" else 1

        for L in FLEET:
            if L < span or L < size:
                continue

            if orient in ("h", "?"):
                # Component must fit within a horizontal placement on row r0.
                # If orient == "?" (single hit), allow both directions.
                if orient == "h":
                    r0 = rs[0]
                    start_min = max(0, max_c - L + 1)
                    start_max = min(min_c, 10 - L)
                    for c0 in range(start_min, start_max + 1):
                        # build placement and validate
                        ok = True
                        for k in range(L):
                            if board[r0][c0 + k] == -1:
                                ok = False
                                break
                        if not ok:
                            continue
                        # Must include all component cells (guaranteed by range selection for linear comp)
                        for k in range(L):
                            rr, cc = r0, c0 + k
                            if board[rr][cc] == 0:
                                heat[rr][cc] += PLACEMENT_BONUS
                else:
                    # Single hit case: try horizontal placements that include it.
                    (r0, c_hit) = comp[0]
                    start_min = max(0, c_hit - L + 1)
                    start_max = min(c_hit, 10 - L)
                    for c0 in range(start_min, start_max + 1):
                        ok = True
                        for k in range(L):
                            if board[r0][c0 + k] == -1:
                                ok = False
                                break
                        if not ok:
                            continue
                        # Must include the hit cell
                        if not (c0 <= c_hit < c0 + L):
                            continue
                        for k in range(L):
                            rr, cc = r0, c0 + k
                            if board[rr][cc] == 0:
                                heat[rr][cc] += PLACEMENT_BONUS

            if orient in ("v", "?"):
                if orient == "v":
                    c0 = cs[0]
                    start_min = max(0, max_r - L + 1)
                    start_max = min(min_r, 10 - L)
                    for r0 in range(start_min, start_max + 1):
                        ok = True
                        for k in range(L):
                            if board[r0 + k][c0] == -1:
                                ok = False
                                break
                        if not ok:
                            continue
                        for k in range(L):
                            rr, cc = r0 + k, c0
                            if board[rr][cc] == 0:
                                heat[rr][cc] += PLACEMENT_BONUS
                else:
                    (r_hit, c0) = comp[0]
                    start_min = max(0, r_hit - L + 1)
                    start_max = min(r_hit, 10 - L)
                    for r0 in range(start_min, start_max + 1):
                        ok = True
                        for k in range(L):
                            if board[r0 + k][c0] == -1:
                                ok = False
                                break
                        if not ok:
                            continue
                        if not (r0 <= r_hit < r0 + L):
                            continue
                        for k in range(L):
                            rr, cc = r0 + k, c0
                            if board[rr][cc] == 0:
                                heat[rr][cc] += PLACEMENT_BONUS


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Return a legal shot (row, col) where board[row][col] == 0.
    Uses probabilistic hunt + hit-focused target behavior.
    """
    # Safety: if malformed board, fall back to (0,0) if possible.
    if not isinstance(board, list) or len(board) != 10:
        return (0, 0)
    for r in range(10):
        if not isinstance(board[r], list) or len(board[r]) != 10:
            return (0, 0)

    unknowns = _unknown_cells(board)
    if not unknowns:
        # No legal moves exist; return something legal-looking.
        return (0, 0)

    hits = _hit_cells(board)
    comps = _hit_components(board) if hits else []

    heat = [[0] * 10 for _ in range(10)]

    # Base hunt model always contributes
    _add_heat_for_all_placements(board, heat)

    # Target model: heavily biases finishing when hits exist
    if comps:
        _add_heat_for_hit_components(board, heat, comps)
    else:
        # Parity preference in pure hunt mode (min ship length is 2).
        # Boost one color moderately; do not forbid the other color.
        for r in range(10):
            for c in range(10):
                if board[r][c] == 0 and ((r + c) & 1) == 0:
                    heat[r][c] += 2

    # Choose max-heat among unknown cells; deterministic randomized tie-break.
    seed = _board_seed(board)
    rng = random.Random(seed)
    rng.shuffle(unknowns)

    best = unknowns[0]
    best_score = heat[best[0]][best[1]]

    for (r, c) in unknowns[1:]:
        s = heat[r][c]
        if s > best_score:
            best_score = s
            best = (r, c)

    # Final legality check (must be unknown)
    if board[best[0]][best[1]] != 0:
        # Fallback: first legal unknown
        for r, c in unknowns:
            if board[r][c] == 0:
                return (r, c)
        return (0, 0)

    return best
