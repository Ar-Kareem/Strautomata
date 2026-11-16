
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Directions: up, down, left, right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # Step 1: Collect all adjacent cells to hits to target next
    queue = deque()

    # First pass: add all adjacent cells to hits to the queue
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                        queue.append((ni, nj))

    # Step 2: If queue is not empty, return the next cell
    if queue:
        return queue.popleft()

    # Step 3: If queue is empty, perform a systematic search (row by row)
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                return (i, j)

    # Fallback (shouldn't happen in a valid game)
    return (0, 0)
