

import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    hits = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                hits.append((i, j))
    candidates = set()
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for (i, j) in hits:
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if 0 <= ni < 10 and 0 <= nj < 10:
                if board[ni][nj] == 0:
                    candidates.add((ni, nj))
    if candidates:
        return random.choice(list(candidates))
    else:
        for i in range(10):
            for j in range(10):
                if board[i][j] == 0:
                    return (i, j)
        raise RuntimeError("No valid move found")