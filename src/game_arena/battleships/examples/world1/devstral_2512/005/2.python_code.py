
import numpy as np
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)

    # Initialize variables
    rows, cols = board.shape
    hits = np.argwhere(board == 1)
    misses = np.argwhere(board == -1)
    unknown = np.argwhere(board == 0)

    # If we have hits, prioritize finding the rest of the ship
    if len(hits) > 0:
        # Find all hit clusters (potential ships)
        visited = set()
        clusters = []

        for hit in hits:
            if tuple(hit) not in visited:
                cluster = []
                queue = deque([hit])
                visited.add(tuple(hit))

                while queue:
                    current = queue.popleft()
                    cluster.append(current)

                    # Check adjacent cells
                    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nr, nc = current[0] + dr, current[1] + dc
                        if (0 <= nr < rows and 0 <= nc < cols and
                            board[nr, nc] == 1 and (nr, nc) not in visited):
                            visited.add((nr, nc))
                            queue.append([nr, nc])

                clusters.append(cluster)

        # For each cluster, find the best next move
        for cluster in clusters:
            # Determine orientation (horizontal or vertical)
            if len(cluster) >= 2:
                # Check if horizontal
                if all(cluster[i][0] == cluster[0][0] for i in range(len(cluster))):
                    orientation = 'horizontal'
                # Check if vertical
                elif all(cluster[i][1] == cluster[0][1] for i in range(len(cluster))):
                    orientation = 'vertical'
                else:
                    # Diagonal or single hit - treat as unknown
                    orientation = 'unknown'
            else:
                orientation = 'unknown'

            # Generate potential moves based on orientation
            if orientation == 'horizontal':
                row = cluster[0][0]
                min_col = min(c[1] for c in cluster)
                max_col = max(c[1] for c in cluster)

                # Check left of leftmost hit
                if min_col > 0 and board[row, min_col - 1] == 0:
                    return (row, min_col - 1)
                # Check right of rightmost hit
                if max_col < cols - 1 and board[row, max_col + 1] == 0:
                    return (row, max_col + 1)

            elif orientation == 'vertical':
                col = cluster[0][1]
                min_row = min(c[0] for c in cluster)
                max_row = max(c[0] for c in cluster)

                # Check above topmost hit
                if min_row > 0 and board[min_row - 1, col] == 0:
                    return (min_row - 1, col)
                # Check below bottommost hit
                if max_row < rows - 1 and board[max_row + 1, col] == 0:
                    return (max_row + 1, col)

            else:
                # For unknown orientation or single hit, check all 4 directions
                for hit in cluster:
                    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nr, nc = hit[0] + dr, hit[1] + dc
                        if (0 <= nr < rows and 0 <= nc < cols and
                            board[nr, nc] == 0):
                            return (nr, nc)

    # If no hits or no valid moves around hits, use probability-based targeting
    # Create a probability map where ships are most likely to be
    prob_map = np.zeros((rows, cols))

    # Ships can't be placed adjacent to each other (though this isn't strictly enforced in all versions)
    # We'll use a simple probability distribution that favors center cells
    for i in range(rows):
        for j in range(cols):
            if board[i, j] != 0:
                continue  # Already fired here

            # Distance from edges (ships are less likely to be at edges)
            dist_from_edge = min(i, rows - 1 - i, j, cols - 1 - j)
            prob_map[i, j] = dist_from_edge

            # Penalize cells adjacent to misses (ships can't be adjacent)
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                nr, nc = i + dr, j + dc
                if 0 <= nr < rows and 0 <= nc < cols and board[nr, nc] == -1:
                    prob_map[i, j] -= 0.5

    # Find the cell with highest probability that hasn't been fired at
    max_prob = -1
    best_move = (0, 0)

    for i in range(rows):
        for j in range(cols):
            if board[i, j] == 0 and prob_map[i, j] > max_prob:
                max_prob = prob_map[i, j]
                best_move = (i, j)

    return best_move
