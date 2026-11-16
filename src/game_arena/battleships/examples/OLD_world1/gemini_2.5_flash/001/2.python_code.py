
import random
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    n = len(board)
    board_np = np.array(board)

    # 1. Hunt Mode: If no ship is currently being targeted, search for a new ship.
    #    This can be done by firing at a checkerboard pattern or randomly.
    #    Here, we'll implement a checkerboard pattern for better coverage.

    # Check if there are any active hits that haven't been fully explored.
    hit_cells = np.argwhere(board_np == 1)

    if len(hit_cells) > 0:
        # 2. Target Mode: If we've hit a ship, try to sink it.
        #    This involves expanding from the hit cell to find the ship's orientation.

        # Find all cells that have been hit but potentially not yet sunk
        # (i.e., we have a 1, and its neighbors haven't all been explored to be misses or hits)
        potential_ship_cells = []
        for r, c in hit_cells:
            # Check neighbors
            neighbors = []
            if r > 0 and board[r - 1][c] == 0: neighbors.append((r - 1, c))
            if r < n - 1 and board[r + 1][c] == 0: neighbors.append((r + 1, c))
            if c > 0 and board[r][c - 1] == 0: neighbors.append((r, c - 1))
            if c < n - 1 and board[r][c + 1] == 0: neighbors.append((r, c + 1))
            if neighbors:
                potential_ship_cells.append((r, c))

        if potential_ship_cells:
            # Prioritize expanding ships that we've already hit multiple times in a line.
            # This helps in quickly sinking known ships.

            # Identify groups of connected hits
            visited = set()
            ship_segments = []
            for r_hit, c_hit in potential_ship_cells:
                if (r_hit, c_hit) not in visited:
                    current_segment = []
                    q = [(r_hit, c_hit)]
                    visited.add((r_hit, c_hit))

                    while q:
                        r, c = q.pop(0)
                        current_segment.append((r, c))

                        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 1 and (nr, nc) not in visited:
                                visited.add((nr, nc))
                                q.append((nr, nc))
                    ship_segments.append(current_segment)

            # Sort segments by length (longer segments are more established)
            ship_segments.sort(key=len, reverse=True)

            for segment in ship_segments:
                if len(segment) == 1:
                    # Single hit, try all four directions
                    r, c = segment[0]
                    possible_targets = []
                    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0:
                            possible_targets.append((nr, nc))
                    if possible_targets:
                        return random.choice(possible_targets)
                else:
                    # Multiple hits, try to extend the line
                    rows = sorted(list(set([r for r, _ in segment])))
                    cols = sorted(list(set([c for _, c in segment])))

                    if len(rows) == 1:  # Horizontal segment
                        r = rows[0]
                        min_c, max_c = min(cols), max(cols)
                        # Try extending left
                        if min_c > 0 and board[r][min_c - 1] == 0:
                            return r, min_c - 1
                        # Try extending right
                        elif max_c < n - 1 and board[r][max_c + 1] == 0:
                            return r, max_c + 1
                    elif len(cols) == 1:  # Vertical segment
                        c = cols[0]
                        min_r, max_r = min(rows), max(rows)
                        # Try extending up
                        if min_r > 0 and board[min_r - 1][c] == 0:
                            return min_r - 1, c
                        # Try extending down
                        elif max_r < n - 1 and board[max_r + 1][c] == 0:
                            return max_r + 1, c

            # If no clear extension found, but we still have hits with unexplored neighbors,
            # just pick one of those neighbors randomly.
            for r_hit, c_hit in potential_ship_cells:
                possible_targets = []
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r_hit + dr, c_hit + dc
                    if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0:
                        possible_targets.append((nr, nc))
                if possible_targets:
                    return random.choice(possible_targets)
    
    # If no active hits or all hit segments are fully surrounded by misses/edges,
    # switch to hunt mode.
    # Hunt mode strategy: Prioritize cells with a checkerboard pattern.
    # This helps in quickly finding ships, especially longer ones.
    
    available_targets_checkerboard = []
    available_targets_all = []

    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                available_targets_all.append((r, c))
                # Checkerboard pattern: (r + c) % 2 == 0
                if (r + c) % 2 == 0:
                    available_targets_checkerboard.append((r, c))

    if available_targets_checkerboard:
        return random.choice(available_targets_checkerboard)
    elif available_targets_all:
        return random.choice(available_targets_all)
    else:
        # All cells fired at, should not happen in a normal game.
        # Fallback to random if no un-fired cells are left.
        return random.randint(0, n - 1), random.randint(0, n - 1)

