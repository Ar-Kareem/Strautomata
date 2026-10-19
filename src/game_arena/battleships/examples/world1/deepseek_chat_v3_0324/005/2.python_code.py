
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # First, check if there are any hits to target around (target mode)
    hit_positions = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                hit_positions.append((i, j))

    # If there are hits, try to sink the ship by targeting adjacent cells
    if hit_positions:
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        random.shuffle(directions)  # Randomize direction selection
        for i, j in hit_positions:
            for di, dj in directions:
                ni, nj = i + di, j + dj
                if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                    return ni, nj

    # If no hits to target, use a checkerboard search pattern (search mode)
    # Alternate between two phases for better coverage
    for i in range(10):
        for j in range(10):
            if (i + j) % 2 == 0 and board[i][j] == 0:
                return i, j

    # Fallback: target any remaining unknown cell if checkerboard is exhausted
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                return i, j

    # Shouldn't reach here if there are unknown cells left
    return 0, 0
