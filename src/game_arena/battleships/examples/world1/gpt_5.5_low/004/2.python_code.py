
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Battleship policy for a 10x10 board.

    board values:
      0  = unknown / legal shot
     -1  = miss
      1  = hit

    Returns:
      (row, col) where board[row][col] == 0
    """

    N = 10
    SHIPS = [5, 4, 3, 3, 2]

    # Collect legal moves and known hits.
    unknowns = []
    hits = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                unknowns.append((r, c))
            elif board[r][c] == 1:
                hits.append((r, c))

    # Absolute safety fallback.
    if not unknowns:
        return (0, 0)

    hit_count = len(hits)
    scores = [[0.0 for _ in range(N)] for _ in range(N)]

    # ------------------------------------------------------------------
    # Probability-density scoring:
    # Every ship placement that does not cross a miss contributes score
    # to its unknown cells. Placements containing hits are weighted much
    # more heavily, encouraging target mode.
    # ------------------------------------------------------------------
    for length in SHIPS:
        # Horizontal placements
        for r in range(N):
            for c0 in range(N - length + 1):
                cells = [(r, c0 + i) for i in range(length)]

                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue

                unknown_cells = [(rr, cc) for rr, cc in cells if board[rr][cc] == 0]
                if not unknown_cells:
                    continue

                k = sum(1 for rr, cc in cells if board[rr][cc] == 1)

                if hit_count:
                    # Placements touching known hits are far more likely
                    # to be useful than pure hunting placements.
                    if k:
                        weight = (18.0 ** k) * length
                    else:
                        weight = 0.15
                else:
                    weight = 1.0

                for rr, cc in unknown_cells:
                    scores[rr][cc] += weight

        # Vertical placements
        for r0 in range(N - length + 1):
            for c in range(N):
                cells = [(r0 + i, c) for i in range(length)]

                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue

                unknown_cells = [(rr, cc) for rr, cc in cells if board[rr][cc] == 0]
                if not unknown_cells:
                    continue

                k = sum(1 for rr, cc in cells if board[rr][cc] == 1)

                if hit_count:
                    if k:
                        weight = (18.0 ** k) * length
                    else:
                        weight = 0.15
                else:
                    weight = 1.0

                for rr, cc in unknown_cells:
                    scores[rr][cc] += weight

    # ------------------------------------------------------------------
    # Extra target-mode bonus:
    # If a hit has unknown neighbors, those are very attractive.
    # If multiple hits are aligned, extend along that line.
    # ------------------------------------------------------------------
    hit_set = set(hits)

    for r, c in hits:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                scores[nr][nc] += 80.0

    # Strongly prefer extending existing straight hit runs.
    visited = set()
    for r, c in hits:
        if (r, c) in visited:
            continue

        # Horizontal run
        if (r, c - 1) not in hit_set and (r, c + 1) in hit_set:
            run = []
            cc = c
            while (r, cc) in hit_set:
                run.append((r, cc))
                visited.add((r, cc))
                cc += 1

            left_c = run[0][1] - 1
            right_c = run[-1][1] + 1

            if 0 <= left_c < N and board[r][left_c] == 0:
                scores[r][left_c] += 500.0 + 100.0 * len(run)
            if 0 <= right_c < N and board[r][right_c] == 0:
                scores[r][right_c] += 500.0 + 100.0 * len(run)

        # Vertical run
        if (r - 1, c) not in hit_set and (r + 1, c) in hit_set:
            run = []
            rr = r
            while (rr, c) in hit_set:
                run.append((rr, c))
                visited.add((rr, c))
                rr += 1

            top_r = run[0][0] - 1
            bottom_r = run[-1][0] + 1

            if 0 <= top_r < N and board[top_r][c] == 0:
                scores[top_r][c] += 500.0 + 100.0 * len(run)
            if 0 <= bottom_r < N and board[bottom_r][c] == 0:
                scores[bottom_r][c] += 500.0 + 100.0 * len(run)

    # ------------------------------------------------------------------
    # Hunt-mode refinements:
    # Checkerboard parity is efficient because the smallest ship has
    # length 2. Center bias helps because more placements cross center.
    # ------------------------------------------------------------------
    for r, c in unknowns:
        if (r + c) % 2 == 0:
            scores[r][c] += 0.35

        # Slight center preference for deterministic tie-breaking.
        center_dist = abs(r - 4.5) + abs(c - 4.5)
        scores[r][c] += 0.01 * (9.0 - center_dist)

    # Choose the highest-scoring legal unknown cell.
    best_move = unknowns[0]
    best_score = scores[best_move[0]][best_move[1]]

    for r, c in unknowns:
        s = scores[r][c]
        if s > best_score:
            best_score = s
            best_move = (r, c)

    # Final legality guard.
    br, bc = best_move
    if 0 <= br < N and 0 <= bc < N and board[br][bc] == 0:
        return best_move

    # Guaranteed legal fallback.
    return unknowns[0]
