
import numpy as np
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """
    A Havannah policy for selecting the next move.

    Args:
        me: A list of (row, col) tuples for player-0 stones.
        opp: A list of (row, col) tuples for player-1 stones.
        valid_mask: A 2D array (shape NxN) where True marks playable cells.

    Returns:
        A tuple (row, col) representing the next move.
    """

    N = valid_mask.shape[0]
    corners = [(0, 0), (0, N - 1), (N - 1, 0), (N - 1, N - 1)]
    edges = []
    for i in range(1, N - 1):
        edges.append((0, i))
        edges.append((N - 1, i))
        edges.append((i, 0))
        edges.append((i, N - 1))

    occupied = set(me + opp)
    empty_cells = []
    for r in range(N):
        for c in range(N):
            if valid_mask[r][c] and (r, c) not in occupied:
                empty_cells.append((r, c))

    # 1. Immediate Block (if applicable): Not implemented for brevity in this example. Requires win condition check.

    # 2. Corner Prioritization:
    for corner in corners:
        if valid_mask[corner[0]][corner[1]] and corner not in occupied:
            return corner

    # 3. Edge Prioritization:
    for edge in edges:
        if valid_mask[edge[0]][edge[1]] and edge not in occupied:
            return edge

    # 4. Connectivity (Prioritize connecting to own stones):
    for r, c in me:
        neighbors = get_neighbors(r, c, N)
        for nr, nc in neighbors:
            if valid_mask[nr][nc] and (nr, nc) not in occupied:
                return (nr, nc)

    # 5. Weighted Random Choice based on edge proximity:
    weights = []
    for r, c in empty_cells:
        edge_distance = min(r, c, N - 1 - r, N - 1 - c)
        weights.append(max(0.1, 1 / (edge_distance + 1))) # avoid division by zero, small value so it is only used when no other choice is available.

    if empty_cells:
        weights = np.array(weights) / np.sum(weights)
        index = np.random.choice(len(empty_cells), p=weights)
        return empty_cells[index]

    # 6. If all else fails, return a random valid move
    legal_moves = []
    for r in range(N):
        for c in range(N):
            if valid_mask[r][c] and (r, c) not in occupied:
                legal_moves.append((r, c))

    if legal_moves:
        return random.choice(legal_moves)

    # If no valid moves remain (which should not happen), return (0, 0) as a last resort
    return (0, 0)


def get_neighbors(row, col, N):
    neighbors = []
    if row > 0:
        neighbors.append((row - 1, col))
    if row < N - 1:
        neighbors.append((row + 1, col))
    if col > 0:
        neighbors.append((row, col - 1))
        if row < N - 1:
            neighbors.append((row + 1, col - 1))
    if col < N - 1:
        neighbors.append((row, col + 1))
        if row > 0:
            neighbors.append((row - 1, col + 1))

    return neighbors
