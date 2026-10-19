
from typing import List, Tuple
import random

N = 10
SHIPS = (5, 4, 3, 3, 2)

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Return the next legal shot (row, col) for a 10x10 Battleship board.
    board values: 0 unknown, -1 miss, 1 hit.
    """
    try:
        unknowns = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
        if not unknowns:
            return (0, 0)  # Should never happen in a valid game state.

        hits = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 1]

        # Identify connected hit components. Since the API does not tell us sunk ships,
        # all hit cells are treated as cells that must be covered by possible ship placements.
        hit_set = set(hits)
        seen = set()
        components = []
        for h in hits:
            if h in seen:
                continue
            stack = [h]
            seen.add(h)
            comp = []
            while stack:
                x, y = stack.pop()
                comp.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (nx, ny) in hit_set and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            components.append(comp)

        # Estimate which ship lengths may remain relevant. If a connected hit component
        # already has k cells, only ships of length >= k can cover it.
        # We keep all ships because sunk information is unavailable, but this helps scoring.
        max_comp_len = max((len(c) for c in components), default=0)
        candidate_lengths = [s for s in SHIPS if s >= max_comp_len] or list(SHIPS)

        heat = [[0.0 for _ in range(N)] for __ in range(N)]

        # Generate all placements for each ship length that do not conflict with misses.
        # A placement is valuable if it covers existing hits, and especially if it could
        # extend a line/cluster of hits.
        total_placements = 0
        for length in candidate_lengths:
            for horizontal in (True, False):
                max_r = N
                max_c = N - length + 1 if horizontal else N
                max_r = N if horizontal else N - length + 1

                for r in range(max_r):
                    for c in range(max_c):
                        cells = []
                        bad = False
                        covered_hits = 0
                        for k in range(length):
                            rr = r
                            cc = c
                            if horizontal:
                                cc += k
                            else:
                                rr += k

                            v = board[rr][cc]
                            if v == -1:
                                bad = True
                                break
                            if v == 1:
                                covered_hits += 1
                            cells.append((rr, cc))

                        if bad:
                            continue

                        # If hits exist, prefer placements that cover at least one hit.
                        # But still count all legal placements lightly for hunt mode.
                        total_placements += 1

                        if covered_hits:
                            weight = 30.0 * covered_hits * covered_hits + length
                        else:
                            weight = 1.0

                        # Extra weight for placements that can cover an entire hit component,
                        # which is useful for finishing a partially found ship.
                        cell_set = set(cells)
                        for comp in components:
                            if all(x in cell_set for x in comp):
                                weight += 50.0 * len(comp)

                        for rr, cc in cells:
                            if board[rr][cc] == 0:
                                heat[rr][cc] += weight

        # Direct target mode: unknown neighbors of hits get a major boost.
        # If hits form a line, extend the line preferentially.
        for comp in components:
            comp_set = set(comp)
            rows = {r for r, _ in comp}
            cols = {c for _, c in comp}

            if len(comp) >= 2 and len(rows) == 1:
                row = next(iter(rows))
                min_c = min(c for _, c in comp)
                max_c = max(c for _, c in comp)
                for cc in (min_c - 1, max_c + 1):
                    if 0 <= cc < N and board[row][cc] == 0:
                        heat[row][cc] += 10000.0 + 100.0 * len(comp)

            elif len(comp) >= 2 and len(cols) == 1:
                col = next(iter(cols))
                min_r = min(r for r, _ in comp)
                max_r = max(r for r, _ in comp)
                for rr in (min_r - 1, max_r + 1):
                    if 0 <= rr < N and board[rr][col] == 0:
                        heat[rr][col] += 10000.0 + 100.0 * len(comp)

            else:
                for r, c in comp:
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < N and 0 <= cc < N and board[rr][cc] == 0:
                            heat[rr][cc] += 5000.0

        # Hunt-mode parity bonus. Since smallest ship length is 2, checkerboard coverage
        # is efficient. Add mild center bias because more placements cross central cells.
        for r, c in unknowns:
            if (r + c) % 2 == 0:
                heat[r][c] += 2.5
            center_bias = 4.5 - (abs(r - 4.5) + abs(c - 4.5)) / 2.0
            heat[r][c] += max(0.0, center_bias) * 0.15

        # Select best legal move with deterministic tie-breaking plus tiny randomized
        # variation to avoid being too predictable if random is allowed by the arena.
        best = None
        best_score = -1e100
        for r, c in unknowns:
            score = heat[r][c]
            # Deterministic small tie-break: prefer central and parity cells.
            score += 1e-6 * (20 - abs(r - 4.5) - abs(c - 4.5))
            if score > best_score:
                best_score = score
                best = (r, c)

        if best is not None and board[best[0]][best[1]] == 0:
            return best

        # Absolute safety fallback.
        return unknowns[0]

    except Exception:
        # Never return an illegal move if anything unexpected occurs.
        for r in range(N):
            for c in range(N):
                try:
                    if board[r][c] == 0:
                        return (r, c)
                except Exception:
                    pass
        return (0, 0)
