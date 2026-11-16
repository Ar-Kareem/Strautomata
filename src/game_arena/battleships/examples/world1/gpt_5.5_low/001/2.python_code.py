
from typing import List, Tuple

BOARD_SIZE = 10
SHIP_LENGTHS = [5, 4, 3, 3, 2]


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Battleship policy for a 10x10 board.

    board values:
        0  = unknown
        -1 = miss
        1  = hit

    Returns:
        (row, col) for an unknown cell.
    """

    n = BOARD_SIZE

    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < n and 0 <= c < n

    def first_legal() -> Tuple[int, int]:
        for r in range(n):
            for c in range(n):
                if board[r][c] == 0:
                    return (r, c)
        # Should never happen in a valid game state, but return legal-shaped tuple.
        return (0, 0)

    try:
        scores = [[0.0 for _ in range(n)] for _ in range(n)]

        hits = []
        unknown_count = 0
        for r in range(n):
            for c in range(n):
                if board[r][c] == 1:
                    hits.append((r, c))
                elif board[r][c] == 0:
                    unknown_count += 1

        if unknown_count == 0:
            return (0, 0)

        # ------------------------------------------------------------------
        # Probability density from all ship placements that do not hit misses.
        # Placements containing known hits get a large bonus.
        # ------------------------------------------------------------------
        for length in SHIP_LENGTHS:
            # Horizontal placements
            for r in range(n):
                for c0 in range(n - length + 1):
                    cells = [(r, c0 + i) for i in range(length)]
                    if any(board[rr][cc] == -1 for rr, cc in cells):
                        continue

                    hit_count = sum(1 for rr, cc in cells if board[rr][cc] == 1)

                    # Weight hit-covering placements heavily.
                    # Squared term helps complete partially discovered ships.
                    weight = 1.0 + 8.0 * hit_count + 6.0 * hit_count * hit_count

                    for rr, cc in cells:
                        if board[rr][cc] == 0:
                            scores[rr][cc] += weight

            # Vertical placements
            for r0 in range(n - length + 1):
                for c in range(n):
                    cells = [(r0 + i, c) for i in range(length)]
                    if any(board[rr][cc] == -1 for rr, cc in cells):
                        continue

                    hit_count = sum(1 for rr, cc in cells if board[rr][cc] == 1)
                    weight = 1.0 + 8.0 * hit_count + 6.0 * hit_count * hit_count

                    for rr, cc in cells:
                        if board[rr][cc] == 0:
                            scores[rr][cc] += weight

        # ------------------------------------------------------------------
        # Tactical targeting bonuses around connected hit clusters.
        # ------------------------------------------------------------------
        visited = [[False for _ in range(n)] for _ in range(n)]

        for sr, sc in hits:
            if visited[sr][sc]:
                continue

            # BFS connected component of hit cells.
            stack = [(sr, sc)]
            visited[sr][sc] = True
            comp = []

            while stack:
                r, c = stack.pop()
                comp.append((r, c))

                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        in_bounds(nr, nc)
                        and not visited[nr][nc]
                        and board[nr][nc] == 1
                    ):
                        visited[nr][nc] = True
                        stack.append((nr, nc))

            # Single isolated hit: try all four neighbors.
            if len(comp) == 1:
                r, c = comp[0]
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if in_bounds(nr, nc) and board[nr][nc] == 0:
                        scores[nr][nc] += 250.0

            else:
                rows = {r for r, _ in comp}
                cols = {c for _, c in comp}

                # Horizontal hit line.
                if len(rows) == 1:
                    r = next(iter(rows))
                    cs = sorted(c for _, c in comp)
                    left = cs[0] - 1
                    right = cs[-1] + 1

                    if in_bounds(r, left) and board[r][left] == 0:
                        scores[r][left] += 500.0 + 80.0 * len(comp)
                    if in_bounds(r, right) and board[r][right] == 0:
                        scores[r][right] += 500.0 + 80.0 * len(comp)

                    # If there are gaps between known hits, fill them first.
                    for c in range(cs[0], cs[-1] + 1):
                        if board[r][c] == 0:
                            scores[r][c] += 700.0

                # Vertical hit line.
                elif len(cols) == 1:
                    c = next(iter(cols))
                    rs = sorted(r for r, _ in comp)
                    up = rs[0] - 1
                    down = rs[-1] + 1

                    if in_bounds(up, c) and board[up][c] == 0:
                        scores[up][c] += 500.0 + 80.0 * len(comp)
                    if in_bounds(down, c) and board[down][c] == 0:
                        scores[down][c] += 500.0 + 80.0 * len(comp)

                    # If there are gaps between known hits, fill them first.
                    for r in range(rs[0], rs[-1] + 1):
                        if board[r][c] == 0:
                            scores[r][c] += 700.0

                # Irregular component should be rare, but target its perimeter.
                else:
                    for r, c in comp:
                        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            nr, nc = r + dr, c + dc
                            if in_bounds(nr, nc) and board[nr][nc] == 0:
                                scores[nr][nc] += 180.0

        # ------------------------------------------------------------------
        # Early-game hunt enhancement:
        # Slight checkerboard preference because all ships have length >= 2.
        # Density scoring already captures most of this, so keep it modest.
        # ------------------------------------------------------------------
        if not hits:
            for r in range(n):
                for c in range(n):
                    if board[r][c] == 0:
                        if (r + c) % 2 == 0:
                            scores[r][c] += 2.0

                        # Mild central preference: ships have more placements near center.
                        center_dist = abs(r - 4.5) + abs(c - 4.5)
                        scores[r][c] += max(0.0, 5.0 - center_dist) * 0.15

        # Pick highest-scoring unknown cell.
        best = None
        best_score = -1.0

        for r in range(n):
            for c in range(n):
                if board[r][c] == 0 and scores[r][c] > best_score:
                    best_score = scores[r][c]
                    best = (r, c)

        if best is not None:
            return best

        return first_legal()

    except Exception:
        # Absolute safety: always return a legal move if possible.
        return first_legal()
