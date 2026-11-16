
import itertools

# Precompute all possible ship placements for lengths 2,3,3,4,5.
# We treat the two length-3 ships separately by duplicating placements.
PLACEMENTS = []
for length in [2, 3, 3, 4, 5]:
    # horizontal placements
    for r in range(10):
        for c in range(10 - length + 1):
            placement = set()
            for i in range(length):
                placement.add((r, c + i))
            PLACEMENTS.append(placement)
    # vertical placements
    for r in range(10 - length + 1):
        for c in range(10):
            placement = set()
            for i in range(length):
                placement.add((r + i, c))
            PLACEMENTS.append(placement)


def policy(board: list[list[int]]) -> tuple[int, int]:
    """Return the next shot (row, col) based on the current board state."""

    def get_components(hits):
        """Return list of connected components (sets of coordinates) from hits."""
        components = []
        visited = set()
        for hit in hits:
            if hit in visited:
                continue
            # start BFS
            queue = [hit]
            component = set()
            while queue:
                r, c = queue.pop()
                if (r, c) in component:
                    continue
                component.add((r, c))
                visited.add((r, c))
                # 4-neighbors
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and (nr, nc) in hits and (nr, nc) not in component:
                        queue.append((nr, nc))
            components.append(component)
        return components

    def get_candidates(component, board):
        """Return a list of candidate shots for a given component, in a fixed order."""
        if len(component) == 1:
            # single hit: try up, down, left, right
            r, c = next(iter(component))
            candidates = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    candidates.append((nr, nc))
            return candidates
        else:
            # multiple hits: determine orientation
            rows = {r for (r, c) in component}
            cols = {c for (r, c) in component}
            if len(rows) == 1:
                # horizontal
                row = list(rows)[0]
                cols_sorted = sorted(cols)
                min_c = cols_sorted[0]
                max_c = cols_sorted[-1]
                candidates = []
                # left end
                if min_c - 1 >= 0 and board[row][min_c - 1] == 0:
                    candidates.append((row, min_c - 1))
                # right end
                if max_c + 1 < 10 and board[row][max_c + 1] == 0:
                    candidates.append((row, max_c + 1))
                return candidates
            elif len(cols) == 1:
                # vertical
                col = list(cols)[0]
                rows_sorted = sorted(rows)
                min_r = rows_sorted[0]
                max_r = rows_sorted[-1]
                candidates = []
                # top end
                if min_r - 1 >= 0 and board[min_r - 1][col] == 0:
                    candidates.append((min_r - 1, col))
                # bottom end
                if max_r + 1 < 10 and board[max_r + 1][col] == 0:
                    candidates.append((max_r + 1, col))
                return candidates
            else:
                # should not happen for straight ships; return no candidates
                return []

    # Collect all hit coordinates
    hits = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 1]

    if hits:
        # Group hits into connected components
        components = get_components(hits)
        # Sort components by size descending, then by min row, min col for tie-breaking
        components.sort(key=lambda comp: (-len(comp), min(comp)))
        for comp in components:
            candidates = get_candidates(comp, board)
            if candidates:
                # Return the first candidate (fixed order from get_candidates)
                return candidates[0]

    # Hunt mode: no hits or no candidates from hits
    # Compute probability map
    prob_map = [[0] * 10 for _ in range(10)]
    for placement in PLACEMENTS:
        # Check if placement is still possible (all cells unknown)
        valid = True
        for r, c in placement:
            if board[r][c] != 0:
                valid = False
                break
        if valid:
            for r, c in placement:
                prob_map[r][c] += 1

    # Find the unknown cell with highest probability
    best_prob = -1
    best_cell = None
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                if prob_map[r][c] > best_prob:
                    best_prob = prob_map[r][c]
                    best_cell = (r, c)
                elif prob_map[r][c] == best_prob and best_cell is not None:
                    # tie-break: smaller row, then smaller column
                    if r < best_cell[0] or (r == best_cell[0] and c < best_cell[1]):
                        best_cell = (r, c)

    # There will always be at least one unknown cell
    return best_cell
