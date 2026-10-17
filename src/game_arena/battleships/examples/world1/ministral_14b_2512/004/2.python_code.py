
import random

def policy(board):
    # Collect all hits
    hits = [(i, j) for i in range(10) for j in range(10) if board[i][j] == 1]

    # If no hits, pick a random unexplored cell
    if not hits:
        unexplored = [(i, j) for i in range(10) for j in range(10) if board[i][j] == 0]
        return random.choice(unexplored)

    # Generate candidates: cells adjacent to hits that are unexplored
    candidates = set()
    for i, j in hits:
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                candidates.add((ni, nj))

    # If no candidates, pick a random unexplored cell
    if not candidates:
        unexplored = [(i, j) for i in range(10) for j in range(10) if board[i][j] == 0]
        return random.choice(unexplored)

    # Score candidates based on how likely they are to be part of a ship
    scored_candidates = []
    for (i, j) in candidates:
        score = 0
        # Check horizontal line
        left = j - 1
        while left >= 0 and board[i][left] == 1:
            left -= 1
        right = j + 1
        while right < 10 and board[i][right] == 1:
            right += 1
        line_length = right - left - 1
        if line_length >= 2:  # At least two hits in a row
            score += line_length

        # Check vertical line
        up = i - 1
        while up >= 0 and board[up][j] == 1:
            up -= 1
        down = i + 1
        while down < 10 and board[down][j] == 1:
            down += 1
        line_length = down - up - 1
        if line_length >= 2:  # At least two hits in a row
            score += line_length

        scored_candidates.append((score, (i, j)))

    # Sort by score descending, then pick the first one
    scored_candidates.sort(reverse=True, key=lambda x: x[0])
    best_candidate = scored_candidates[0][1]

    return best_candidate
