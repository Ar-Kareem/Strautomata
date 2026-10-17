
# battleship_policy.py
from __future__ import annotations

from typing import List, Tuple
import random
import zlib

Board = List[List[int]]  # 10x10 with values {0 unknown, -1 miss, 1 hit}


SHIP_SIZES = (5, 4, 3, 3, 2)
N = 10


def _stable_seed(board: Board) -> int:
    """
    Stable (cross-run) seed based on board contents.
    """
    # Pack into bytes cheaply; values are in {-1,0,1} so shift by +1 to {0,1,2}
    b = bytearray()
    for r in range(N):
        row = board[r]
        for c in range(N):
            b.append(row[c] + 1)
    return zlib.adler32(b) & 0xFFFFFFFF


def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def _unknown_cells(board: Board) -> List[Tuple[int, int]]:
    cells = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                cells.append((r, c))
    return cells


def _hit_cells(board: Board) -> List[Tuple[int, int]]:
    cells = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1:
                cells.append((r, c))
    return cells


def _neighbors4(r: int, c: int):
    yield r - 1, c
    yield r + 1, c
    yield r, c - 1
    yield r, c + 1


def _heatmap_from_placements(board: Board, require_hit: bool) -> List[List[float]]:
    """
    Compute per-cell probability mass by summing over all ship placements that:
      - do NOT overlap known misses (-1)
      - if require_hit=True: include at least one known hit (1)
    We ignore inter-ship non-overlap dependencies; this is the classic fast approximation.
    """
    heat = [[0.0 for _ in range(N)] for _ in range(N)]
    hits_exist = any(board[r][c] == 1 for r in range(N) for c in range(N))

    for L in SHIP_SIZES:
        # Two orientations: horizontal (0,1), vertical (1,0)
        for dr, dc in ((0, 1), (1, 0)):
            max_r = N - (L - 1) * dr
            max_c = N - (L - 1) * dc
            for r0 in range(max_r):
                for c0 in range(max_c):
                    cells = []
                    invalid = False
                    hit_count = 0
                    for k in range(L):
                        r = r0 + dr * k
                        c = c0 + dc * k
                        v = board[r][c]
                        if v == -1:
                            invalid = True
                            break
                        if v == 1:
                            hit_count += 1
                        cells.append((r, c))
                    if invalid:
                        continue
                    if require_hit and hit_count == 0:
                        continue

                    # Weight placements that explain more hits much more strongly.
                    # This drives extension shots in target mode.
                    weight = 1.0
                    if hit_count > 0:
                        # Exponential emphasis; tuned to be strong but not overflow.
                        weight *= (6.0 ** hit_count)

                    # If there are hits on the board and we are in target mode, slightly
                    # de-emphasize placements that contain no hits (already filtered).
                    # In hunt mode, no extra weighting.

                    for (r, c) in cells:
                        if board[r][c] == 0:
                            heat[r][c] += weight
                        # If board[r][c] == 1 we don't add because it's not a legal move anyway.

    # If require_hit=True but no hits exist, heat will be all zeros; caller handles that.
    return heat


def _best_cells_from_heat(board: Board, heat: List[List[float]], rng: random.Random) -> Tuple[int, int] | None:
    best = -1.0
    best_cells: List[Tuple[int, int]] = []
    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue
            score = heat[r][c]
            if score > best + 1e-12:
                best = score
                best_cells = [(r, c)]
            elif abs(score - best) <= 1e-12 and best >= 0.0:
                best_cells.append((r, c))
    if not best_cells:
        return None
    # If all scores are 0, this is still a valid tie; caller may prefer other fallbacks.
    return rng.choice(best_cells)


def _neighbor_target_fallback(board: Board, rng: random.Random) -> Tuple[int, int] | None:
    """
    If we have hits but the placement-based heatmap is uninformative, shoot near hits.
    Scores unknown neighbors by adjacency to hits and line-continuation potential.
    """
    hits = _hit_cells(board)
    if not hits:
        return None

    candidates = {}
    for hr, hc in hits:
        for nr, nc in _neighbors4(hr, hc):
            if not _in_bounds(nr, nc) or board[nr][nc] != 0:
                continue
            # Base score: adjacent to a hit
            score = 10.0

            # Add for being adjacent to multiple hits
            adj_hits = 0
            for ar, ac in _neighbors4(nr, nc):
                if _in_bounds(ar, ac) and board[ar][ac] == 1:
                    adj_hits += 1
            score += 4.0 * adj_hits

            # Line continuation bonuses:
            # If candidate is in line with hits (two-step), boost.
            # Horizontal
            if _in_bounds(nr, nc - 1) and _in_bounds(nr, nc - 2):
                if board[nr][nc - 1] == 1 and board[nr][nc - 2] == 1:
                    score += 8.0
            if _in_bounds(nr, nc + 1) and _in_bounds(nr, nc + 2):
                if board[nr][nc + 1] == 1 and board[nr][nc + 2] == 1:
                    score += 8.0
            # Vertical
            if _in_bounds(nr - 1, nc) and _in_bounds(nr - 2, nc):
                if board[nr - 1][nc] == 1 and board[nr - 2][nc] == 1:
                    score += 8.0
            if _in_bounds(nr + 1, nc) and _in_bounds(nr + 2, nc):
                if board[nr + 1][nc] == 1 and board[nr + 2][nc] == 1:
                    score += 8.0

            # Keep max score if multiple hits propose same candidate
            prev = candidates.get((nr, nc), -1e18)
            if score > prev:
                candidates[(nr, nc)] = score

    if not candidates:
        return None

    best = max(candidates.values())
    best_cells = [cell for cell, sc in candidates.items() if abs(sc - best) < 1e-12]
    return rng.choice(best_cells)


def policy(board: Board) -> Tuple[int, int]:
    """
    Return a legal (row, col) move where board[row][col] == 0.
    """
    rng = random.Random(_stable_seed(board))

    # Ensure we always can return something legal.
    unknown = _unknown_cells(board)
    if not unknown:
        return (0, 0)

    hits = _hit_cells(board)

    # TARGET MODE: use hit-conditioned placement heatmap
    if hits:
        heat_t = _heatmap_from_placements(board, require_hit=True)
        move = _best_cells_from_heat(board, heat_t, rng)

        # If the heatmap is entirely zero (can happen in weird constrained states),
        # fall back to neighbor targeting.
        if move is not None:
            r, c = move
            # Check if all candidate scores are zero by verifying this cell score.
            if heat_t[r][c] > 0.0:
                return move

        move2 = _neighbor_target_fallback(board, rng)
        if move2 is not None:
            return move2
        # Fall through to hunt if no neighbors exist

    # HUNT MODE: global placement heatmap + parity preference
    heat = _heatmap_from_placements(board, require_hit=False)

    # Prefer checkerboard parity when there are plenty of unknowns left.
    # If parity cells are exhausted, fall back to all.
    parity_cells = [(r, c) for (r, c) in unknown if (r + c) % 2 == 0]
    if parity_cells:
        # Choose best by heat among parity cells
        best = -1.0
        best_cells: List[Tuple[int, int]] = []
        for r, c in parity_cells:
            sc = heat[r][c]
            if sc > best + 1e-12:
                best = sc
                best_cells = [(r, c)]
            elif abs(sc - best) <= 1e-12:
                best_cells.append((r, c))
        if best_cells:
            return rng.choice(best_cells)

    move = _best_cells_from_heat(board, heat, rng)
    if move is not None:
        return move

    # Absolute last resort: any unknown cell.
    return rng.choice(unknown)
