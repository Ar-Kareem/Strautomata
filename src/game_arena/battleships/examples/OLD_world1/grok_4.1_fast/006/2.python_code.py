
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    grid = np.array(board)
    candidates = [(i, j) for i in range(10) for j in range(10) if grid[i, j] == 0]
    if not candidates:
        return (0, 0)  # shouldn't happen
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    ships = [2, 3, 3, 4, 5]
    heat = np.zeros((10, 10))
    for length in ships:
        # horizontal
        for r in range(10):
            for sc in range(11 - length):
                valid = True
                for k in range(length):
                    if grid[r, sc + k] == -1:
                        valid = False
                        break
                if valid:
                    for k in range(length):
                        heat[r, sc + k] += 1
        # vertical
        for c in range(10):
            for sr in range(11 - length):
                valid = True
                for k in range(length):
                    if grid[sr + k, c] == -1:
                        valid = False
                        break
                if valid:
                    for k in range(length):
                        heat[sr + k, c] += 1
    scored = []
    for r, c in candidates:
        adj = 0
        for dr, dc in dirs:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and grid[nr, nc] == 1:
                adj += 1
        score = adj * 1000 + heat[r, c]
        scored.append((-score, r, c))
    scored.sort()
    return scored[0][1], scored[0][2]
