
from __future__ import annotations

from typing import List, Tuple, Dict, Iterable


SHIP_LENGTHS = [5, 4, 3, 3, 2]
N = 10


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Return (row, col) for the next shot.
    board[r][c] == 0 unknown, -1 miss, 1 hit.
    Must always return an unshot cell (0) if any exist.
    """
    # Collect unknowns quickly
    unknowns = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
    if not unknowns:
        # Should not happen in a valid game, but keep total safety.
        return (0, 0)

    # Find hit components (4-neighbor)
    components = _hit_components(board)

    # If we have hits, try high-quality target shots first
    if components:
        target_scores = _score_target_candidates(board, components)
        if target_scores:
            # Break ties by global probability map, then center bias, then lexicographic
            prob = _probability_map(board, SHIP_LENGTHS)
            best = _argmax_cells(
                [(cell, sc) for cell, sc in target_scores.items()],
                secondary=prob,
            )
            if best is not None:
                return best

    # Otherwise (or if targeting produced no candidates), hunt with probability map
    prob = _probability_map(board, SHIP_LENGTHS)

    # If no hits at all, prefer parity if any parity cells remain
    any_hit = any(board[r][c] == 1 for r in range(N) for c in range(N))
    if not any_hit:
        parity_cells = [(r, c) for (r, c) in unknowns if (r + c) % 2 == 0]
        if parity_cells:
            return _argmax_cells([(cell, prob[cell[0]][cell[1]]) for cell in parity_cells], secondary=None)  # type: ignore
        # else fall through to full unknowns

    # Choose max-probability unknown cell with stable tie-breaking
    return _argmax_cells([(cell, prob[cell[0]][cell[1]]) for cell in unknowns], secondary=None)  # type: ignore


# -------------------- Helpers --------------------

def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def _neighbors4(r: int, c: int) -> Iterable[Tuple[int, int]]:
    yield r - 1, c
    yield r + 1, c
    yield r, c - 1
    yield r, c + 1


def _hit_components(board: List[List[int]]) -> List[List[Tuple[int, int]]]:
    seen = [[False] * N for _ in range(N)]
    comps: List[List[Tuple[int, int]]] = []

    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                comp: List[Tuple[int, int]] = []
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for nr, nc in _neighbors4(cr, cc):
                        if _in_bounds(nr, nc) and not seen[nr][nc] and board[nr][nc] == 1:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                comps.append(comp)
    return comps


def _score_target_candidates(
    board: List[List[int]],
    components: List[List[Tuple[int, int]]],
) -> Dict[Tuple[int, int], int]:
    """
    For each hit component, propose adjacent unknown cells and score them by how many
    ship-length placements could still fit including the existing hit segment and that candidate.
    """
    scores: Dict[Tuple[int, int], int] = {}

    for comp in components:
        rows = [r for r, _ in comp]
        cols = [c for _, c in comp]
        min_r, max_r = min(rows), max(rows)
        min_c, max_c = min(cols), max(cols)

        # Determine orientation if possible
        same_row = (min_r == max_r)
        same_col = (min_c == max_c)

        if len(comp) >= 2 and (same_row or same_col):
            # Oriented segment
            if same_row:
                r = min_r
                seg_min, seg_max = min_c, max_c
                # candidate ends
                cand = []
                if _in_bounds(r, seg_min - 1) and board[r][seg_min - 1] == 0:
                    cand.append((r, seg_min - 1))
                if _in_bounds(r, seg_max + 1) and board[r][seg_max + 1] == 0:
                    cand.append((r, seg_max + 1))
                for cell in cand:
                    sc = _line_extension_score(board, oriented="H", fixed=r, seg_a=seg_min, seg_b=seg_max, candidate=cell)
                    if sc > 0:
                        scores[cell] = scores.get(cell, 0) + sc
            else:
                c = min_c
                seg_min, seg_max = min_r, max_r
                cand = []
                if _in_bounds(seg_min - 1, c) and board[seg_min - 1][c] == 0:
                    cand.append((seg_min - 1, c))
                if _in_bounds(seg_max + 1, c) and board[seg_max + 1][c] == 0:
                    cand.append((seg_max + 1, c))
                for cell in cand:
                    sc = _line_extension_score(board, oriented="V", fixed=c, seg_a=seg_min, seg_b=seg_max, candidate=cell)
                    if sc > 0:
                        scores[cell] = scores.get(cell, 0) + sc

        else:
            # Single hit (or an L-shape due to incomplete info): try all 4 neighbors of each hit in comp.
            # This is robust to unusual patterns and still prioritizes finishing.
            cand_set = set()
            for r, c in comp:
                for nr, nc in _neighbors4(r, c):
                    if _in_bounds(nr, nc) and board[nr][nc] == 0:
                        cand_set.add((nr, nc))

            for (nr, nc) in cand_set:
                sc = _single_hit_candidate_score(board, comp, (nr, nc))
                if sc > 0:
                    scores[(nr, nc)] = scores.get((nr, nc), 0) + sc

    return scores


def _line_extension_score(
    board: List[List[int]],
    oriented: str,
    fixed: int,
    seg_a: int,
    seg_b: int,
    candidate: Tuple[int, int],
) -> int:
    """
    Score an end-extension candidate for a known oriented hit segment.
    oriented: "H" (row fixed) or "V" (col fixed)
    seg_a..seg_b inclusive are the hit segment coordinates along the varying axis.
    candidate must be adjacent to one end.
    """
    # Segment length
    hit_len = seg_b - seg_a + 1
    if hit_len <= 0:
        return 0

    # Count feasible placements for each ship length that would include:
    # - the entire hit segment
    # - the candidate cell
    # - no misses in the ship cells
    # This approximates "how likely this extension is correct".
    score = 0
    for L in SHIP_LENGTHS:
        if L < hit_len + 1:
            continue

        # placements along the oriented axis: choose start so that segment+candidate lie within [start, start+L-1]
        # and within board, and do not include misses
        if oriented == "H":
            r = fixed
            cand_c = candidate[1]
            min_required = min(seg_a, cand_c)
            max_required = max(seg_b, cand_c)
            # start can range so that start <= min_required and start+L-1 >= max_required
            start_min = max(0, max_required - (L - 1))
            start_max = min(min_required, N - L)
            for start in range(start_min, start_max + 1):
                end = start + L - 1
                if end < max_required or start > min_required:
                    continue
                if _segment_has_miss_row(board, r, start, end):
                    continue
                score += 3  # oriented extension is highly valuable
        else:
            c = fixed
            cand_r = candidate[0]
            min_required = min(seg_a, cand_r)
            max_required = max(seg_b, cand_r)
            start_min = max(0, max_required - (L - 1))
            start_max = min(min_required, N - L)
            for start in range(start_min, start_max + 1):
                end = start + L - 1
                if end < max_required or start > min_required:
                    continue
                if _segment_has_miss_col(board, c, start, end):
                    continue
                score += 3
    return score


def _single_hit_candidate_score(
    board: List[List[int]],
    comp: List[Tuple[int, int]],
    candidate: Tuple[int, int],
) -> int:
    """
    Score a candidate next to a hit (or hit cluster without clear orientation),
    by counting ship placements of any orientation that cover the component and candidate,
    avoiding misses.
    """
    # We approximate by treating each hit in the component as a required cell, but only
    # for placements that are straight lines (as ships must be).
    # So: only consider placements that align with a row or a column and could cover all hit cells + candidate.
    hit_cells = comp[:]
    req = hit_cells + [candidate]
    req_rows = {r for r, _ in req}
    req_cols = {c for _, c in req}
    score = 0

    # Horizontal possible if all in same row
    if len(req_rows) == 1:
        r = next(iter(req_rows))
        cs = [c for _, c in req]
        min_c, max_c = min(cs), max(cs)
        need_len = max_c - min_c + 1
        for L in SHIP_LENGTHS:
            if L < need_len:
                continue
            start_min = max(0, max_c - (L - 1))
            start_max = min(min_c, N - L)
            for start in range(start_min, start_max + 1):
                end = start + L - 1
                if _segment_has_miss_row(board, r, start, end):
                    continue
                # Encourage forming/continuing lines through existing hits
                hits_covered = sum(1 for c in range(start, end + 1) if board[r][c] == 1)
                score += 1 + 2 * hits_covered

    # Vertical possible if all in same col
    if len(req_cols) == 1:
        c = next(iter(req_cols))
        rs = [r for r, _ in req]
        min_r, max_r = min(rs), max(rs)
        need_len = max_r - min_r + 1
        for L in SHIP_LENGTHS:
            if L < need_len:
                continue
            start_min = max(0, max_r - (L - 1))
            start_max = min(min_r, N - L)
            for start in range(start_min, start_max + 1):
                end = start + L - 1
                if _segment_has_miss_col(board, c, start, end):
                    continue
                hits_covered = sum(1 for r in range(start, end + 1) if board[r][c] == 1)
                score += 1 + 2 * hits_covered

    # If neither horizontal nor vertical can include both, still lightly score adjacency
    # (this can happen for multi-hit components that are not yet linear due to partial info).
    if score == 0:
        # Prefer candidates adjacent to multiple hits
        adj_hits = 0
        cr, cc = candidate
        for nr, nc in _neighbors4(cr, cc):
            if _in_bounds(nr, nc) and board[nr][nc] == 1:
                adj_hits += 1
        score = adj_hits

    return score


def _segment_has_miss_row(board: List[List[int]], r: int, c1: int, c2: int) -> bool:
    for c in range(c1, c2 + 1):
        if board[r][c] == -1:
            return True
    return False


def _segment_has_miss_col(board: List[List[int]], c: int, r1: int, r2: int) -> bool:
    for r in range(r1, r2 + 1):
        if board[r][c] == -1:
            return True
    return False


def _probability_map(board: List[List[int]], ship_lengths: List[int]) -> List[List[int]]:
    """
    Build a heatmap where each cell's score is the sum over all legal ship placements
    (for each length, both orientations) that include the cell, excluding placements
    that pass through misses. Placements that include hits are weighted higher.
    """
    prob = [[0] * N for _ in range(N)]

    for L in ship_lengths:
        # Horizontal placements
        for r in range(N):
            for start_c in range(N - L + 1):
                cells = [(r, c) for c in range(start_c, start_c + L)]
                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue
                hits_in = sum(1 for rr, cc in cells if board[rr][cc] == 1)
                # Weight placements with hits more, to pull the hunt map toward finishing lines
                w = 1 + 6 * hits_in
                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        prob[rr][cc] += w

        # Vertical placements
        for c in range(N):
            for start_r in range(N - L + 1):
                cells = [(r, c) for r in range(start_r, start_r + L)]
                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue
                hits_in = sum(1 for rr, cc in cells if board[rr][cc] == 1)
                w = 1 + 6 * hits_in
                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        prob[rr][cc] += w

    return prob


def _argmax_cells(
    cell_scores: List[Tuple[Tuple[int, int], int]],
    secondary: List[List[int]] | None,
) -> None:
    """
    Choose the best cell from (cell, primary_score) pairs.
    Tie-breakers:
      1) higher primary score
      2) higher secondary[cell] if provided
      3) closer to center (4.5,4.5)
      4) lexicographically smallest (row,col)
    """
    if not cell_scores:
        return None

    def center_bias(cell: Tuple[int, int]) -> float:
        r, c = cell
        dr = r - 4.5
        dc = c - 4.5
        return -(dr * dr + dc * dc)  # higher is better (less distance)

    best_cell = None
    best_key = None

    for (cell, sc) in cell_scores:
        r, c = cell
        sec = secondary[r][c] if secondary is not None else 0
        key = (sc, sec, center_bias(cell), -r, -c)  # maximize sc/sec/center; then prefer smaller r,c -> use -r,-c in max
        if best_key is None or key > best_key:
            best_key = key
            best_cell = cell

    return best_cell
