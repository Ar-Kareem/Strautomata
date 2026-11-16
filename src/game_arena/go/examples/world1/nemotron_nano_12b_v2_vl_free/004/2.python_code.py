
import sys
import numpy as np
from collections import defaultdict

def policy(me, opponent):
    rows = 19
    cols = 19

    # Initialize the board
    board = np.zeros((rows, cols), dtype=int)

    # Mark own stones
    for r, c in me:
        board[r-1, c-1] = 1

    # Mark opponent stones
    for r, c in opponent:
        board[r-1, c-1] = -1

    # Find all empty cells
    empty = []
    for i in range(rows):
        for j in range(cols):
            if board[i, j] == 0:
                empty.append((i+1, j+1))

    # If the board is full, return (0,0) to pass
    if not empty:
        return (0, 0)

    # Precompute opponent groups and their liberties
    visited = set()
    groups = []
    liberty_map = defaultdict(set)

    for i in range(rows):
        for j in range(cols):
            if board[i, j] == -1 and (i+1, j+1) not in visited:
                # BFS to find all connected opponent stones
                queue = [(i, j)]
                visited.add((i, j))
                group_cells = [(i+1, j+1)]  # Store 1-based for easier reference

                while queue:
                    x, y = queue.pop(0)
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < rows and 0 <= ny < cols and board[nx, ny] == -1 and (nx, ny) not in visited:
                            visited.add((nx, ny))
                            queue.append((nx, ny))
                            group_cells.append((nx+1, ny+1))

                # Compute liberties for this group
                liberties = set()
                for x1, y1 in group_cells:
                    x0, y0 = x1 - 1, y1 - 1
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        tx, ty = x0 + dr, y0 + dc
                        if 0 <= tx < rows and 0 <= ty < cols and board[tx, ty] == 0:
                            liberties.add((tx+1, ty+1))

                # Store group data
                groups.append((len(group_cells), len(liberties), liberties))
                # Map each group's liberty to its index
                for cell in liberties:
                    liberty_map[cell].add(len(groups) - 1)

    # Evaluate each empty cell for capture potential
    move_scores = []
    for move in empty:
        r, c = move
        # Find all opponent groups that have this cell as a liberty
        groups_affected = liberty_map.get(move, set())
        captured = 0
        for group_idx in groups_affected:
            if groups[group_idx][1] == 1:
                captured += groups[group_idx][0]

        # Compute liberties of the move itself (safety evaluation)
        move_liberties = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19 and board[nr-1, nc-1] == 0:
                move_liberties += 1

        # Compute distance from center (heuristic for strategic positioning)
        distance = (r - 10)**2 + (c - 10)**2

        move_scores.append((captured, move_liberties, distance, move))

    # Sort by captured stones descending, liberties descending, distance ascending
    move_scores.sort(key=lambda x: (-x[0], -x[1], x[2]))

    # Return the best move
    return move_scores[0][3]

