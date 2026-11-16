
from typing import List, Tuple
import random

N = 10
SHIPS = (5, 4, 3, 3, 2)

def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N

def _unknown_cells(board):
    cells = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                cells.append((r, c))
    return cells

def _components(hits):
    hits = set(hits)
    comps = []
    while hits:
        start = hits.pop()
        stack = [start]
        comp = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                nb = (r + dr, c + dc)
                if nb in hits:
                    hits.remove(nb)
                    stack.append(nb)
                    comp.append(nb)
        comps.append(comp)
    return comps

def _valid_placements_for_length(board, length):
    placements = []
    for r in range(N):
        for c in range(N - length + 1):
            cells = tuple((r, c + k) for k in range(length))
            ok = True
            for rr, cc in cells:
                if board[rr][cc] == -1:
                    ok = False
                    break
            if ok:
                placements.append(cells)
    for r in range(N - length + 1):
        for c in range(N):
            cells = tuple((r + k, c) for k in range(length))
            ok = True
            for rr, cc in cells:
                if board[rr][cc] == -1:
                    ok = False
                    break
            if ok:
                placements.append(cells)
    return placements

def _target_bonus(board):
    bonus = [[0 for _ in range(N)] for __ in range(N)]
    hits = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 1]
    hitset = set(hits)

    for comp in _components(hits):
        if not comp:
            continue

        rows = {r for r, c in comp}
        cols = {c for r, c in comp}

        if len(comp) >= 2 and len(rows) == 1:
            r = comp[0][0]
            minc = min(c for _, c in comp)
            maxc = max(c for _, c in comp)
            for cc in (minc - 1, maxc + 1):
                if _in_bounds(r, cc) and board[r][cc] == 0:
                    bonus[r][cc] += 80 + 20 * len(comp)
            for _, c in comp:
                for cc in (c - 1, c + 1):
                    if _in_bounds(r, cc) and board[r][cc] == 0:
                        bonus[r][cc] += 8

        elif len(comp) >= 2 and len(cols) == 1:
            c = comp[0][1]
            minr = min(r for r, _ in comp)
            maxr = max(r for r, _ in comp)
            for rr in (minr - 1, maxr + 1):
                if _in_bounds(rr, c) and board[rr][c] == 0:
                    bonus[rr][c] += 80 + 20 * len(comp)
            for r, _ in comp:
                for rr in (r - 1, r + 1):
                    if _in_bounds(rr, c) and board[rr][c] == 0:
                        bonus[rr][c] += 8

        else:
            r, c = comp[0]
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                rr, cc = r + dr, c + dc
                if _in_bounds(rr, cc) and board[rr][cc] == 0:
                    bonus[rr][cc] += 120
            for dr, dc in ((2,0),(-2,0),(0,2),(0,-2)):
                rr, cc = r + dr, c + dc
                if _in_bounds(rr, cc) and board[rr][cc] == 0:
                    bonus[rr][cc] += 15

    return bonus

def _fallback(board):
    bonus = _target_bonus(board)
    best = None
    best_score = -10**9

    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue

            score = bonus[r][c]

            # Checkerboard hunt pattern catches every ship of length >= 2.
            if (r + c) % 2 == 0:
                score += 6

            # Prefer cells that participate in longer open runs.
            horiz = 1
            cc = c - 1
            while cc >= 0 and board[r][cc] == 0:
                horiz += 1
                cc -= 1
            cc = c + 1
            while cc < N and board[r][cc] == 0:
                horiz += 1
                cc += 1

            vert = 1
            rr = r - 1
            while rr >= 0 and board[rr][c] == 0:
                vert += 1
                rr -= 1
            rr = r + 1
            while rr < N and board[rr][c] == 0:
                vert += 1
                rr += 1

            score += min(horiz, 5) + min(vert, 5)

            # Slight central preference.
            score -= abs(r - 4.5) * 0.05 + abs(c - 4.5) * 0.05

            if score > best_score:
                best_score = score
                best = (r, c)

    if best is not None:
        return best

    # Should only happen if board is full; still return legal-shaped coordinate.
    return (0, 0)

def policy(board: List[List[int]]) -> Tuple[int, int]:
    unknown = _unknown_cells(board)
    if not unknown:
        return (0, 0)

    hits = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 1]
    hitset = set(hits)

    # Generate candidate placements for each ship length.
    placements_by_len = {L: _valid_placements_for_length(board, L) for L in set(SHIPS)}

    heat = [[0 for _ in range(N)] for __ in range(N)]

    # Count every placement that is locally legal. This is robust even without sunk-ship info.
    for L in SHIPS:
        for cells in placements_by_len[L]:
            # Placements not touching any known hit are useful in hunt mode.
            # Placements containing hits become very important in target mode.
            contains = sum((cell in hitset) for cell in cells)
            weight = 1 + 25 * contains
            for rr, cc in cells:
                if board[rr][cc] == 0:
                    heat[rr][cc] += weight

    # Additional focused target heuristic for connected hit clusters.
    bonus = _target_bonus(board)

    best = None
    best_score = -1

    for r, c in unknown:
        score = heat[r][c] + bonus[r][c]

        # Parity is valuable while hunting, but do not let it override target mode.
        if not hits and (r + c) % 2 == 0:
            score += 3

        # Tiny deterministic tie-break: prefer central cells.
        score -= (abs(r - 4.5) + abs(c - 4.5)) * 0.001

        if score > best_score:
            best_score = score
            best = (r, c)

    if best is not None and board[best[0]][best[1]] == 0:
        return best

    return _fallback(board)
