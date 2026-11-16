
import random
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Flatten board to track visited cells (0: unexplored, -1: miss, 1: hit)
    unexplored_cells = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                unexplored_cells.append((i, j))

    # If fewer than 20 shots fired, randomize to explore
    if len(unexplored_cells) > 80:  # First ~20 shots (10x10=100, so 80 unexplored means ~20 fired)
        return random.choice(unexplored_cells)

    # Find all hit cells (1) and their adjacent unexplored cells
    hit_cells = [(i, j) for i in range(10) for j in range(10) if board[i][j] == 1]
    potential_moves = []

    for (i, j) in hit_cells:
        # Check adjacent cells (up, down, left, right)
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                potential_moves.append((ni, nj))

    # If no adjacent unexplored cells (isolated hit), pick a random unexplored cell
    if not potential_moves:
        return random.choice(unexplored_cells)

    # Prioritize moves that extend existing hit lines (likely part of a ship)
    # Group adjacent hits into potential ships
    ships = []
    visited = set()
    for (i, j) in hit_cells:
        if (i, j) not in visited:
            queue = deque([(i, j)])
            visited.add((i, j))
            current_ship = []
            while queue:
                x, y = queue.popleft()
                current_ship.append((x, y))
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 10 and 0 <= ny < 10 and board[nx][ny] == 1 and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
            ships.append(current_ship)

    # If no ships detected (unlikely due to hit_cells), randomize
    if not ships:
        return random.choice(unexplored_cells)

    # Find the largest remaining ship (5,4,3,3,2) and prioritize its unexplored adjacent cells
    largest_ship = max(ships, key=lambda s: len(s))
    best_moves = []

    for (i, j) in largest_ship:
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                best_moves.append((ni, nj))

    # If no best moves (ship fully surrounded), pick a random unexplored cell
    if not best_moves:
        return random.choice(unexplored_cells)

    # Return the first best move (prioritize extending largest ship)
    return best_moves[0]
