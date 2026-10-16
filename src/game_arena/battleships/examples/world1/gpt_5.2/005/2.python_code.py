
from __future__ import annotations

from collections import deque
from typing import List, Tuple, Iterable, Optional


N = 10
FLEET = [5, 4, 3, 3, 2]


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Battleship policy:
      - Track hit components; infer some are sunk if capped by misses/edges.
      - If any "active" (unsunk) hits exist: target mode via placement-consistency heatmap.
      - Else: hunt mode via classic ship-placement density heatmap.
    Always returns a legal move (row, col) with board[row][col] == 0 when possible.
    """
    # Defensive: ensure dimensions; if not, fallback to first legal in provided structure.
    if not board or len(board) != N or any(len(row) != N for row in board):
        for r, row in enumerate(board):
            for c, v in enumerate(row):
                if v == 0:
                    return (r, c)
        return (0, 0)

    # --- Helpers over the raw list board (avoid numpy overhead; 10x10 is tiny) ---
    def inb(r: int, c: int) -> bool:
        return 0 <= r < N and 0 <= c < N

    def neighbors4(r: int, c: int) -> Iterable[Tuple[int, int]]:
        if r > 0:
            yield (r - 1, c)
        if r + 1 < N:
            yield (r + 1, c)
        if c > 0:
            yield (r, c - 1)
        if c + 1 < N:
            yield (r, c + 1)

    # --- Find connected components of hits (4-connected) ---
    visited = [[False] * N for _ in range(N)]
    hit_components: List[List[Tuple[int, int]]] = []

    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and not visited[r][c]:
                q = deque([(r, c)])
                visited[r][c] = True
                comp = []
                while q:
                    rr, cc = q.popleft()
                    comp.append((rr, cc))
                    for nr, nc in neighbors4(rr, cc):
                        if board[nr][nc] == 1 and not visited[nr][nc]:
                            visited[nr][nc] = True
                            q.append((nr, nc))
                hit_components.append(comp)

    # --- Infer some components as "certainly sunk" (conservative) ---
    # A component is considered sunk if:
    #   - it is linear (all same row or all same col),
    #   - its ends are capped by edge or a known miss (-1),
    #   - its length matches some remaining ship length.
    remaining = list(FLEET)
    sunk_cells = [[False] * N for _ in range(N)]

    def is_linear(comp: List[Tuple[int, int]]) -> Tuple[bool, Optional[str]]:
        if len(comp) <= 1:
            return True, None  # orientation unknown for a single hit
        rows = {r for r, _ in comp}
        cols = {c for _, c in comp}
        if len(rows) == 1:
            return True, "H"
        if len(cols) == 1:
            return True, "V"
        return False, None

    for comp in hit_components:
        linear, orient = is_linear(comp)
        if not linear:
            continue
        L = len(comp)

        # Determine capped ends only if we know an orientation (size>1).
        capped = False
        if orient == "H":
            row = comp[0][0]
            cols = [c for _, c in comp]
            cmin, cmax = min(cols), max(cols)
            left_blocked = (cmin == 0) or (board[row][cmin - 1] == -1)
            right_blocked = (cmax == N - 1) or (board[row][cmax + 1] == -1)
            capped = left_blocked and right_blocked
        elif orient == "V":
            col = comp[0][1]
            rows = [r for r, _ in comp]
            rmin, rmax = min(rows), max(rows)
            up_blocked = (rmin == 0) or (board[rmin - 1][col] == -1)
            down_blocked = (rmax == N - 1) or (board[rmax + 1][col] == -1)
            capped = up_blocked and down_blocked
        else:
            # Single hit: cannot ever be "certainly sunk" without explicit sink info.
            capped = False

        if capped and L in remaining:
            remaining.remove(L)
            for (r, c) in comp:
                sunk_cells[r][c] = True

    # Blocked cells for ship placement in hunt/target:
    # - misses are blocked
    # - inferred sunk hits are blocked (ships cannot overlap)
    blocked = [[False] * N for _ in range(N)]
    for r in range(N):
        for c in range(N):
            if board[r][c] == -1 or sunk_cells[r][c]:
                blocked[r][c] = True

    # Active hits are hits not inferred sunk
    active_hit = [[False] * N for _ in range(N)]
    active_hits_list: List[Tuple[int, int]] = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and not sunk_cells[r][c]:
                active_hit[r][c] = True
                active_hits_list.append((r, c))

    # Build active hit components (recompute with sunk removed)
    visited2 = [[False] * N for _ in range(N)]
    active_components: List[List[Tuple[int, int]]] = []
    for r, c in active_hits_list:
        if visited2[r][c]:
            continue
        q = deque([(r, c)])
        visited2[r][c] = True
        comp = []
        while q:
            rr, cc = q.popleft()
            comp.append((rr, cc))
            for nr, nc in neighbors4(rr, cc):
                if active_hit[nr][nc] and not visited2[nr][nc]:
                    visited2[nr][nc] = True
                    q.append((nr, nc))
        active_components.append(comp)

    # Scoring map (float) over unknown cells
    score = [[0.0] * N for _ in range(N)]

    def add_neighbor_bonus(local_weight: float = 0.05) -> None:
        """Small heuristic: prefer cells with more useful nearby unknown/active-hit neighbors."""
        for r in range(N):
            for c in range(N):
                if board[r][c] != 0:
                    continue
                cnt = 0
                for nr, nc in neighbors4(r, c):
                    if board[nr][nc] == 0 or active_hit[nr][nc]:
                        cnt += 1
                score[r][c] += local_weight * cnt

    def add_parity_bonus() -> None:
        """Mild parity preference when large ships remain (helps in open-water hunt)."""
        if not remaining:
            return
        if max(remaining) >= 3:
            for r in range(N):
                for c in range(N):
                    if board[r][c] == 0 and ((r + c) & 1) == 0:
                        score[r][c] += 0.15

    def place_cells(r0: int, c0: int, L: int, orient: str) -> List[Tuple[int, int]]:
        if orient == "H":
            return [(r0, c0 + k) for k in range(L)]
        else:
            return [(r0 + k, c0) for k in range(L)]

    def placement_valid(cells: List[Tuple[int, int]]) -> bool:
        # All cells must be in bounds and not blocked, and cannot include a miss.
        for r, c in cells:
            if not inb(r, c):
                return False
            if blocked[r][c]:
                return False
            if board[r][c] == -1:
                return False
        return True

    # --- Target mode: if there are active hits, concentrate on completing them ---
    if active_components:
        # For each active component, add probability mass for placements that can cover it.
        for comp in active_components:
            linear, orient = is_linear(comp)

            comp_set = set(comp)
            comp_len = len(comp)

            # Determine allowed orientations for placements that cover this component.
            allowed_orients: List[str]
            if comp_len >= 2 and orient in ("H", "V"):
                allowed_orients = [orient]
            else:
                allowed_orients = ["H", "V"]

            # For each ship length, enumerate starts that would cover the component.
            for L in remaining:
                if L < comp_len:
                    continue

                weight = 1.0 + 0.7 * comp_len  # emphasize completing bigger known segments

                for o in allowed_orients:
                    if o == "H":
                        # Component must all lie in same row to be coverable by a horizontal ship.
                        rows = {r for r, _ in comp}
                        if len(rows) != 1:
                            continue
                        row = next(iter(rows))
                        cols = [c for _, c in comp]
                        cmin, cmax = min(cols), max(cols)

                        start_min = cmax - L + 1
                        start_max = cmin
                        if start_min > start_max:
                            continue

                        for c0 in range(max(0, start_min), min(N - L, start_max) + 1):
                            cells = place_cells(row, c0, L, "H")
                            if not placement_valid(cells):
                                continue
                            # Ensure all component cells are included (should be by construction, but safe)
                            if not comp_set.issubset(cells):
                                continue
                            for rr, cc in cells:
                                if board[rr][cc] == 0:
                                    score[rr][cc] += weight

                    else:  # "V"
                        cols = {c for _, c in comp}
                        if len(cols) != 1:
                            continue
                        col = next(iter(cols))
                        rows = [r for r, _ in comp]
                        rmin, rmax = min(rows), max(rows)

                        start_min = rmax - L + 1
                        start_max = rmin
                        if start_min > start_max:
                            continue

                        for r0 in range(max(0, start_min), min(N - L, start_max) + 1):
                            cells = place_cells(r0, col, L, "V")
                            if not placement_valid(cells):
                                continue
                            if not comp_set.issubset(cells):
                                continue
                            for rr, cc in cells:
                                if board[rr][cc] == 0:
                                    score[rr][cc] += weight

        # If targeting heatmap is degenerate (can happen with weird boards), fallback to neighbor shots.
        best = None
        best_val = -1.0
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0 and score[r][c] > best_val:
                    best_val = score[r][c]
                    best = (r, c)

        if best is None or best_val <= 0.0:
            # Fallback: shoot any unknown neighbor of an active hit.
            for hr, hc in active_hits_list:
                for nr, nc in neighbors4(hr, hc):
                    if board[nr][nc] == 0:
                        return (nr, nc)
            # Last resort: first unknown anywhere.
            for r in range(N):
                for c in range(N):
                    if board[r][c] == 0:
                        return (r, c)
            return (0, 0)

        add_neighbor_bonus(0.07)  # slightly stronger local heuristic in target mode

        # Re-pick after neighbor bonus
        best = None
        best_val = -1.0
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0 and score[r][c] > best_val:
                    best_val = score[r][c]
                    best = (r, c)
        if best is not None:
            return best

        # Should never happen, but keep legal fallback.
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)

    # --- Hunt mode: no active hits; compute classic ship-placement density over unknowns ---
    # Valid hunt placement: all cells must be unknown (0), and not blocked.
    for L in remaining:
        # Horizontal placements
        for r in range(N):
            for c0 in range(N - L + 1):
                ok = True
                cells = []
                for k in range(L):
                    c = c0 + k
                    if blocked[r][c] or board[r][c] != 0:
                        ok = False
                        break
                    cells.append((r, c))
                if not ok:
                    continue
                for rr, cc in cells:
                    score[rr][cc] += 1.0

        # Vertical placements
        for c in range(N):
            for r0 in range(N - L + 1):
                ok = True
                cells = []
                for k in range(L):
                    r = r0 + k
                    if blocked[r][c] or board[r][c] != 0:
                        ok = False
                        break
                    cells.append((r, c))
                if not ok:
                    continue
                for rr, cc in cells:
                    score[rr][cc] += 1.0

    add_parity_bonus()
    add_neighbor_bonus(0.04)

    # Choose best unknown cell; tie-breaker: prefer closer to center (slight)
    def center_bias(r: int, c: int) -> float:
        # Manhattan distance to center (4.5, 4.5), negated
        return - (abs(r - 4.5) + abs(c - 4.5)) * 1e-3

    best_move = None
    best_val = -1e18
    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue
            val = score[r][c] + center_bias(r, c)
            if val > best_val:
                best_val = val
                best_move = (r, c)

    if best_move is not None:
        return best_move

    # Absolute last resort: if no legal moves exist, return (0,0) to satisfy API.
    return (0, 0)
