
from __future__ import annotations

from time import perf_counter
import random


SHIP_LENGTHS = [5, 4, 3, 3, 2]
UNIQUE_LENGTHS = sorted(set(SHIP_LENGTHS))

# Precompute all placements for each ship length.
# Each placement is (mask, cells_tuple, orientation)
# orientation: 0 = horizontal, 1 = vertical
PLACEMENTS: dict[int, list[tuple[int, tuple[int, ...], int]]] = {L: [] for L in UNIQUE_LENGTHS}
COVER_BY_LEN_CELL: dict[int, list[list[int]]] = {L: [[] for _ in range(100)] for L in UNIQUE_LENGTHS}

for L in UNIQUE_LENGTHS:
    # Horizontal
    for r in range(10):
        for c in range(11 - L):
            cells = tuple(r * 10 + (c + k) for k in range(L))
            mask = 0
            for idx in cells:
                mask |= 1 << idx
            PLACEMENTS[L].append((mask, cells, 0))
            for idx in cells:
                COVER_BY_LEN_CELL[L][idx].append(mask)

    # Vertical
    for r in range(11 - L):
        for c in range(10):
            cells = tuple((r + k) * 10 + c for k in range(L))
            mask = 0
            for idx in cells:
                mask |= 1 << idx
            PLACEMENTS[L].append((mask, cells, 1))
            for idx in cells:
                COVER_BY_LEN_CELL[L][idx].append(mask)


def _neighbors(idx: int):
    r, c = divmod(idx, 10)
    if r > 0:
        yield idx - 10
    if r < 9:
        yield idx + 10
    if c > 0:
        yield idx - 1
    if c < 9:
        yield idx + 1


def _hit_components(board: list[list[int]]):
    visited = set()
    comps = []

    for r in range(10):
        for c in range(10):
            if board[r][c] != 1:
                continue
            start = r * 10 + c
            if start in visited:
                continue

            stack = [start]
            visited.add(start)
            cells = []

            while stack:
                cur = stack.pop()
                cells.append(cur)
                for nb in _neighbors(cur):
                    rr, cc = divmod(nb, 10)
                    if board[rr][cc] == 1 and nb not in visited:
                        visited.add(nb)
                        stack.append(nb)

            rows = {idx // 10 for idx in cells}
            cols = {idx % 10 for idx in cells}
            is_line = len(rows) == 1 or len(cols) == 1
            orient = 0 if len(rows) == 1 else (1 if len(cols) == 1 else -1)

            mask = 0
            for idx in cells:
                mask |= 1 << idx

            comps.append(
                {
                    "cells": cells,
                    "mask": mask,
                    "size": len(cells),
                    "is_line": is_line,
                    "orient": orient,
                }
            )

    return comps


def _random_fill(rem: list[int], occupied: int, valid_by_len: dict[int, list[int]], rng: random.Random, deadline: float):
    if not rem:
        return occupied

    ordered = sorted(rem, reverse=True)

    # Fast random greedy attempts first
    for _ in range(12):
        if perf_counter() >= deadline:
            return None
        occ = occupied
        seq = ordered[:]
        # Small randomization among same-size choices / order
        rng.shuffle(seq)
        seq.sort(reverse=True)

        ok = True
        for L in seq:
            feasible = [p for p in valid_by_len[L] if (p & occ) == 0]
            if not feasible:
                ok = False
                break
            occ |= rng.choice(feasible)

        if ok:
            return occ

    # Exact backtracking fallback
    def exact_fill(rem2: list[int], occ2: int):
        if perf_counter() >= deadline:
            return None
        if not rem2:
            return occ2

        best_i = -1
        best_feasible = None

        for i, L in enumerate(rem2):
            feasible = [p for p in valid_by_len[L] if (p & occ2) == 0]
            if not feasible:
                return None
            if best_feasible is None or len(feasible) < len(best_feasible):
                best_i = i
                best_feasible = feasible

        rng.shuffle(best_feasible)
        for p in best_feasible:
            res = exact_fill(rem2[:best_i] + rem2[best_i + 1 :], occ2 | p)
            if res is not None:
                return res
        return None

    return exact_fill(rem, occupied)


def _sample_fleet(hit_mask: int, miss_mask: int, valid_by_len: dict[int, list[int]], rng: random.Random, deadline: float):
    rem = SHIP_LENGTHS[:]

    def rec(rem2: list[int], occupied: int, covered_hits: int):
        if perf_counter() >= deadline:
            return None

        uncovered = hit_mask & ~covered_hits
        if uncovered == 0:
            return _random_fill(rem2, occupied, valid_by_len, rng, deadline)

        # Choose the most constrained uncovered hit cell.
        best_options = None
        u = uncovered
        while u:
            hbit = u & -u
            cell = hbit.bit_length() - 1

            options = []
            for i, L in enumerate(rem2):
                for p in COVER_BY_LEN_CELL[L][cell]:
                    if (p & miss_mask) or (p & occupied):
                        continue
                    options.append((i, p, (p & uncovered).bit_count()))

            if not options:
                return None

            if best_options is None or len(options) < len(best_options):
                best_options = options
                if len(best_options) == 1:
                    break

            u ^= hbit

        best_options.sort(key=lambda x: (-x[2], rng.random()))

        for i, p, _ in best_options:
            new_rem = rem2[:i] + rem2[i + 1 :]
            res = rec(new_rem, occupied | p, covered_hits | (p & hit_mask))
            if res is not None:
                return res

        return None

    return rec(rem, 0, 0)


def policy(board: list[list[int]]) -> tuple[int, int]:
    # Build masks
    hit_mask = 0
    miss_mask = 0
    unknown = []

    for r in range(10):
        row = board[r]
        for c in range(10):
            v = row[c]
            idx = r * 10 + c
            if v == 1:
                hit_mask |= 1 << idx
            elif v == -1:
                miss_mask |= 1 << idx
            else:
                unknown.append(idx)

    # Safe fallback in case the board is somehow full.
    if not unknown:
        return (0, 0)

    hit_count = hit_mask.bit_count()
    comps = _hit_components(board)

    # Deterministic seed from board state.
    seed = 1469598103934665603
    for r in range(10):
        for c in range(10):
            seed ^= (board[r][c] + 2) & 0xFF
            seed = (seed * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    rng = random.Random(seed)

    # Pre-filter placements that do not cross known misses.
    valid_by_len: dict[int, list[int]] = {}
    for L in UNIQUE_LENGTHS:
        valid_by_len[L] = [mask for (mask, _cells, _orient) in PLACEMENTS[L] if (mask & miss_mask) == 0]

    scores = [0.0] * 100

    # Placement-based heatmap.
    # Heavily weight placements that include hits.
    hit_weight = {0: 1.0, 1: 25.0, 2: 220.0, 3: 1600.0, 4: 7000.0, 5: 20000.0}

    for L in SHIP_LENGTHS:
        for mask, cells, orient in PLACEMENTS[L]:
            if mask & miss_mask:
                continue

            hmask = mask & hit_mask
            h = hmask.bit_count()
            w = hit_weight.get(h, 40000.0)

            if h and comps:
                # Reward placements that fully explain linear hit components.
                for comp in comps:
                    inter = mask & comp["mask"]
                    if not inter:
                        continue

                    if comp["is_line"] and comp["size"] >= 2:
                        if orient == comp["orient"] and inter == comp["mask"]:
                            w *= 4.0
                        else:
                            # Still possible if ships touch, but much less likely.
                            w *= 0.12

            for idx in cells:
                rr, cc = divmod(idx, 10)
                if board[rr][cc] == 0:
                    scores[idx] += w

    # Local endpoint / neighbor bonuses from hit components.
    if hit_count > 0:
        for comp in comps:
            cells = comp["cells"]

            if comp["is_line"] and comp["size"] >= 2:
                if comp["orient"] == 0:
                    row = cells[0] // 10
                    cols = sorted(idx % 10 for idx in cells)
                    left_c = cols[0] - 1
                    right_c = cols[-1] + 1

                    if left_c >= 0 and board[row][left_c] == 0:
                        scores[row * 10 + left_c] += 500.0 * comp["size"]
                    if right_c < 10 and board[row][right_c] == 0:
                        scores[row * 10 + right_c] += 500.0 * comp["size"]
                else:
                    col = cells[0] % 10
                    rows = sorted(idx // 10 for idx in cells)
                    up_r = rows[0] - 1
                    down_r = rows[-1] + 1

                    if up_r >= 0 and board[up_r][col] == 0:
                        scores[up_r * 10 + col] += 500.0 * comp["size"]
                    if down_r < 10 and board[down_r][col] == 0:
                        scores[down_r * 10 + col] += 500.0 * comp["size"]
            else:
                bonus = 140.0 if comp["size"] == 1 else 90.0
                for idx in cells:
                    for nb in _neighbors(idx):
                        rr, cc = divmod(nb, 10)
                        if board[rr][cc] == 0:
                            scores[nb] += bonus

    # Monte Carlo full-fleet sampling when hits exist.
    # This helps avoid overcommitting to already-complete ships.
    if hit_count > 0:
        budget = 0.18 + 0.05 * min(hit_count, 4)
        deadline = perf_counter() + budget
        max_success = 60 + 25 * hit_count

        mc_counts = [0] * 100
        successes = 0

        while successes < max_success and perf_counter() < deadline:
            fleet = _sample_fleet(hit_mask, miss_mask, valid_by_len, rng, deadline)
            if fleet is None:
                break

            occ_unknown = fleet & ~(hit_mask | miss_mask)
            x = occ_unknown
            while x:
                b = x & -x
                idx = b.bit_length() - 1
                mc_counts[idx] += 1
                x ^= b
            successes += 1

        if successes > 0:
            scale = 4500.0 if successes >= 20 else 2500.0
            inv = 1.0 / successes
            for idx in unknown:
                scores[idx] += scale * mc_counts[idx] * inv

    # Tiny positional tie-breaker: prefer cells with more open neighbors and slightly toward center.
    for idx in unknown:
        r, c = divmod(idx, 10)
        open_nbs = 0
        for nb in _neighbors(idx):
            rr, cc = divmod(nb, 10)
            if board[rr][cc] == 0:
                open_nbs += 1
        center_bonus = (4.5 - abs(r - 4.5)) + (4.5 - abs(c - 4.5))
        scores[idx] += 0.003 * open_nbs + 0.001 * center_bonus

    # Hunt-mode parity restriction when there are no hits.
    candidates = unknown
    if hit_count == 0 and len(unknown) > 20:
        parity_cells = [idx for idx in unknown if ((idx // 10 + idx % 10) & 1) == 0]
        if parity_cells:
            candidates = parity_cells

    # Choose best legal move.
    best_idx = None
    best_score = None
    for idx in candidates:
        s = scores[idx]
        if best_score is None or s > best_score:
            best_score = s
            best_idx = idx

    # Safety fallback if something odd happens.
    if best_idx is None:
        best_idx = unknown[0]

    return divmod(best_idx, 10)
