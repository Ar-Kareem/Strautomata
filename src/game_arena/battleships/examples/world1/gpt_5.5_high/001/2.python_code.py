
from __future__ import annotations

N = 10
SHIP_LENGTHS = (5, 4, 3, 3, 2)
_UNIQUE_LENGTHS = tuple(sorted(set(SHIP_LENGTHS)))

# Precompute every straight placement for each ship length.
_PLACEMENTS = {}
for _L in _UNIQUE_LENGTHS:
    arr = []
    for r in range(N):
        for c in range(N - _L + 1):
            arr.append((tuple((r, c + i) for i in range(_L)), "H"))
    for r in range(N - _L + 1):
        for c in range(N):
            arr.append((tuple((r + i, c) for i in range(_L)), "V"))
    _PLACEMENTS[_L] = arr


def _fallback(board):
    """Always return some legal unknown cell if one exists."""
    for r in range(N):
        for c in range(N):
            try:
                if board[r][c] == 0:
                    return (r, c)
            except Exception:
                pass
    return (0, 0)


def _center_value(r, c):
    # Larger is better; center cells have the highest value.
    dr = 2 * r - (N - 1)
    dc = 2 * c - (N - 1)
    return -(dr * dr + dc * dc)


def _get_components(board):
    """Return orthogonally connected hit components and a component-id grid."""
    comp_id = [[-1 for _ in range(N)] for _ in range(N)]
    comps = []

    for r in range(N):
        for c in range(N):
            if board[r][c] != 1 or comp_id[r][c] != -1:
                continue

            cid = len(comps)
            stack = [(r, c)]
            comp_id[r][c] = cid
            cells = []

            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < N and 0 <= nc < N:
                        if board[nr][nc] == 1 and comp_id[nr][nc] == -1:
                            comp_id[nr][nc] = cid
                            stack.append((nr, nc))

            rows = {x for x, _ in cells}
            cols = {y for _, y in cells}

            if len(cells) == 1:
                orient = "S"
            elif len(rows) == 1:
                orient = "H"
            elif len(cols) == 1:
                orient = "V"
            else:
                orient = "X"

            cells_sorted = tuple(sorted(cells))
            info = {
                "cells": cells_sorted,
                "set": set(cells_sorted),
                "orient": orient,
            }

            if orient == "H":
                row = next(iter(rows))
                cs = [cc for _, cc in cells]
                info["row"] = row
                info["min_col"] = min(cs)
                info["max_col"] = max(cs)
            elif orient == "V":
                col = next(iter(cols))
                rs = [rr for rr, _ in cells]
                info["col"] = col
                info["min_row"] = min(rs)
                info["max_row"] = max(rs)

            comps.append(info)

    return comps, comp_id


def _segments_for_component(comp, length):
    """Yield placements of a given length that contain an entire line component."""
    orient = comp["orient"]

    if orient == "H":
        row = comp["row"]
        lo = comp["min_col"]
        hi = comp["max_col"]
        start_min = max(0, hi - length + 1)
        start_max = min(lo, N - length)
        for s in range(start_min, start_max + 1):
            yield tuple((row, c) for c in range(s, s + length))

    elif orient == "V":
        col = comp["col"]
        lo = comp["min_row"]
        hi = comp["max_row"]
        start_min = max(0, hi - length + 1)
        start_max = min(lo, N - length)
        for s in range(start_min, start_max + 1):
            yield tuple((r, col) for r in range(s, s + length))


def _has_longer_geometric_fit(comp, board):
    """Can this line component be part of any longer ship without crossing a miss?"""
    k = len(comp["cells"])
    if comp["orient"] not in ("H", "V"):
        return False

    for length in _UNIQUE_LENGTHS:
        if length <= k:
            continue
        for cells in _segments_for_component(comp, length):
            ok = True
            for r, c in cells:
                if board[r][c] == -1:
                    ok = False
                    break
            if ok:
                return True
    return False


def _infer_resolved(board, comps):
    """
    Conservatively mark hit-line components as resolved when no longer ship can
    extend them geometrically. Removes their ship length from the remaining fleet.
    """
    counts = {5: 1, 4: 1, 3: 2, 2: 1}
    resolved = set()

    # Longer components are more informative, so process them first.
    order = sorted(range(len(comps)), key=lambda i: len(comps[i]["cells"]), reverse=True)

    for idx in order:
        comp = comps[idx]
        k = len(comp["cells"])
        orient = comp["orient"]

        if orient not in ("H", "V"):
            continue
        if k not in counts or counts[k] <= 0:
            continue

        # Length 5 cannot be extended. Shorter ships are resolved only if misses
        # or borders prevent every longer placement.
        if k >= 5 or not _has_longer_geometric_fit(comp, board):
            resolved.add(idx)
            counts[k] -= 1

    remaining = counts.copy()
    avail = []
    for length in SHIP_LENGTHS:
        if remaining.get(length, 0) > 0:
            avail.append(length)
            remaining[length] -= 1

    return resolved, tuple(avail)


def _placement_compatible(cells, orient, touched_ids, comps):
    """
    A placement that touches a multi-hit straight component must align with it
    and cover the whole component. This prevents shooting perpendicular to an
    already established ship direction.
    """
    if not touched_ids:
        return True

    cell_set = None

    for cid in touched_ids:
        comp = comps[cid]
        comp_len = len(comp["cells"])
        comp_orient = comp["orient"]

        # Only enforce this for plausible single-ship straight components.
        # Nonlinear or overlong components may be caused by touching ships.
        if comp_orient in ("H", "V") and 2 <= comp_len <= 5:
            if orient != comp_orient:
                return False
            if cell_set is None:
                cell_set = set(cells)
            for pos in comp["cells"]:
                if pos not in cell_set:
                    return False

    return True


def _score_targets(board, comps, comp_id, resolved_ids, avail_lengths):
    """
    Score unknown cells that could belong to ships already hit.
    Exponential weighting strongly prefers finishing larger hit groups.
    """
    target = [[0.0 for _ in range(N)] for _ in range(N)]

    if not avail_lengths:
        return target

    for length in avail_lengths:
        for cells, orient in _PLACEMENTS[length]:
            good = True
            touched = set()
            hit_indices = []

            for i, (r, c) in enumerate(cells):
                v = board[r][c]
                if v == -1:
                    good = False
                    break
                if v == 1:
                    cid = comp_id[r][c]
                    if cid < 0 or cid in resolved_ids:
                        good = False
                        break
                    touched.add(cid)
                    hit_indices.append(i)

            if not good or not hit_indices:
                continue
            if not _placement_compatible(cells, orient, touched, comps):
                continue

            h = len(hit_indices)
            base = 35.0 ** h

            for i, (r, c) in enumerate(cells):
                if board[r][c] != 0:
                    continue
                d = min(abs(i - j) for j in hit_indices)
                if d <= 0:
                    continue
                # Adjacent cells are usually best for quickly finishing a ship,
                # but gap-filling cells farther away still get some probability.
                factor = 3.0 if d == 1 else 1.0 / float(d)
                target[r][c] += base * factor

    return target


def _score_hunt(board, lengths):
    """
    Probability-density hunt score for undiscovered ships.
    Known hits and misses are treated as blocked for hunt placements.
    """
    hunt = [[0.0 for _ in range(N)] for _ in range(N)]

    for length in lengths:
        for cells, _orient in _PLACEMENTS[length]:
            ok = True
            for r, c in cells:
                if board[r][c] != 0:
                    ok = False
                    break
            if not ok:
                continue

            for r, c in cells:
                hunt[r][c] += 1.0

    return hunt


def _policy_impl(board):
    zeros = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
    if not zeros:
        return (0, 0)

    comps, comp_id = _get_components(board)
    resolved_ids, avail_lengths = _infer_resolved(board, comps)

    target = _score_targets(board, comps, comp_id, resolved_ids, avail_lengths)

    # If our inference says every ship is resolved but the game still asks for a
    # move, fall back to generic density so the move remains sensible and legal.
    hunt_lengths = avail_lengths if avail_lengths else SHIP_LENGTHS
    hunt = _score_hunt(board, hunt_lengths)

    # Target mode: finish known ships first.
    target_max = max(target[r][c] for r, c in zeros)
    if target_max > 1e-9:
        best = zeros[0]
        best_key = None
        for r, c in zeros:
            cv = _center_value(r, c)
            key = (
                target[r][c],
                0.05 * hunt[r][c] + 0.0001 * cv,
                cv,
                -r,
                -c,
            )
            if best_key is None or key > best_key:
                best_key = key
                best = (r, c)
        return best

    # Hunt mode: use a modulo pattern based on the shortest remaining ship.
    # For min length m, every horizontal/vertical ship of length >= m crosses
    # every residue of (row + col) % m.
    min_len = min(avail_lengths) if avail_lengths else 2
    pattern_cells = [
        (r, c)
        for r, c in zeros
        if (r + c) % min_len == 0 and hunt[r][c] > 0
    ]

    if not pattern_cells:
        pattern_cells = [(r, c) for r, c in zeros if hunt[r][c] > 0]
    if not pattern_cells:
        pattern_cells = zeros

    best = pattern_cells[0]
    best_key = None
    for r, c in pattern_cells:
        cv = _center_value(r, c)
        key = (hunt[r][c], cv, -r, -c)
        if best_key is None or key > best_key:
            best_key = key
            best = (r, c)

    return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Required arena API. Returns a legal unshot coordinate (row, col).
    """
    try:
        r, c = _policy_impl(board)
        r, c = int(r), int(c)
        if 0 <= r < N and 0 <= c < N and board[r][c] == 0:
            return (r, c)
    except Exception:
        pass

    return _fallback(board)
