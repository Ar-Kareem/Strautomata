
from collections import deque

def move_legal(r, c, me, opponent):
    """Check if placing a stone at (r, c) is legal."""
    existing = set(me) | set(opponent)
    if (r, c) in existing:
        return False

    # Create temporary sets for evaluation
    temp_me = set(me)
    temp_me.add((r, c))
    temp_existing = temp_me.union(set(opponent))

    # Find the group connected to (r, c)
    visited = set()
    queue = deque([(r, c)])
    visited.add((r, c))
    while queue:
        x, y = queue.popleft()
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 1 <= nx <= 19 and 1 <= ny <= 19:
                if (nx, ny) in temp_me and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))

    # Check for liberties of the group
    liberties = 0
    for x, y in visited:
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 1 <= nx <= 19 and 1 <= ny <= 19:
                if (nx, ny) not in temp_existing:
                    liberties += 1
                    if liberties > 0:
                        break
        if liberties > 0:
            break

    return liberties > 0


def policy(me, opponent):
    # Generate all possible positions and collect legal ones
    existing = set(me) | set(opponent)
    empty_cells = []
    for r in range(1, 20):
        for c in range(1, 20):
            cell = (r, c)
            if cell not in existing and move_legal(r, c, me, opponent):
                empty_cells.append(cell)

    if not empty_cells:
        return (0, 0)  # No legal moves, must pass

    # Evaluate each legal move and pick the best one
    best_move = None
    best_score = -float('inf')

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for move in empty_cells:
        rx, cx = move
        min_corner_dist = min(
            abs(rx - 1) + abs(cx - 1),
            abs(rx - 1) + abs(19 - cx),
            abs(19 - rx) + abs(cx - 1),
            abs(19 - rx) + abs(19 - cx)
        )
        corner_score = 50.0 / (min_corner_dist + 1)  # Prioritize corners

        # Count adjacent opponent's stones
        adj_opponent = 0
        for dx, dy in directions:
            nr, nc = rx + dx, cx + dy
            if (nr, nc) in opponent:
                adj_opponent += 1

        # Count adjacency to our own stones
        own_count = 0
        for dx, dy in directions:
            nr, nc = rx + dx, cx + dy
            if (nr, nc) in me:
                own_count += 1

        # Combine the scores
        adj_score = adj_opponent * 5
        move_score = adj_score + corner_score + own_count * 2

        if move_score > best_score or (move_score == best_score and best_move is None):
            best_score = move_score
            best_move = move

    return best_move
