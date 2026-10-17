
from collections import deque

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    me_set = set(me)
    opponent_set = set(opponent)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    corners = [(1, 1), (1, 19), (19, 1), (19, 19)]

    legal_moves = []

    # Step 1: Generate all empty cells
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) in me_set or (r, c) in opponent_set:
                continue

            # Simulate placing a stone at (r, c)
            temp_me = me_set.copy()
            temp_me.add((r, c))

            # Find the connected group using BFS
            group = set()
            queue = deque([(r, c)])
            visited = set([(r, c)])

            while queue:
                x, y = queue.popleft()
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 1 <= nx <= 19 and 1 <= ny <= 19:
                        if (nx, ny) in temp_me and (nx, ny) not in visited:
                            visited.add((nx, ny))
                            queue.append((nx, ny))

            # Calculate liberties
            liberties = 0
            for x, y in visited:
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 1 <= nx <= 19 and 1 <= ny <= 19:
                        if (nx, ny) not in temp_me and (nx, ny) not in opponent_set:
                            liberties += 1

            # Only add to legal moves if it's not a suicide
            if liberties > 0:
                legal.append((r, c))

    # Step 2: If no legal moves, return pass
    if not legal:
        return (0, 0), memory

    # Step 3: Try to place a corner first if any are legal
    for corner in corners:
        if corner in legal:
            return corner, memory

    # Step 4: If no legal corner, choose move with highest liberties and closest to corners
    move_data = []

    for move in legal:
        r, c = move
        min_corner_dist = min(
            abs(r - 1) + abs(c - 1),
            abs(r - 1) + abs(c - 19),
            abs(r - 19) + abs(c - 1),
            abs(r - 19) + abs(c - 19)
        )
        # Recompute liberties for sorting
        temp_me = me_set | {move}
        visited = set()
        queue = deque([move])
        visited.add(move)

        while queue:
            x, y = queue.popleft()
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 1 <= nx <= 19 and 1 <= ny <= 19:
                    if (nx, ny) in temp_me and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))

        libs = 0
        for x, y in visited:
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 1 <= nx <= 19 and 1 <= ny <= 19:
                    if (nx, ny) not in temp_me and (nx, ny) not in opponent_set:
                        libs += 1

        move_data.append((min_corner_dist, -libs, move))

    # Sort by min corner distance (ascending), then by liberties (descending)
    move_data.sort()
    best_move = move_data[0][2]

    return best_move, memory
