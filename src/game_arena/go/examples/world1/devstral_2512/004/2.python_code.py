
import random
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Initialize board representation
    board = np.zeros((19, 19), dtype=int)
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = -1

    # Directions for neighbor checks
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    # 1. Check for urgent defensive moves (stones in atari)
    for r, c in me:
        if count_liberties(board, r-1, c-1) == 1:
            # Find the liberty and play there
            for dr, dc in directions:
                nr, nc = r-1 + dr, c-1 + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                    return (nr+1, nc+1)

    # 2. Check for offensive opportunities (opponent stones in atari)
    for r, c in opponent:
        if count_liberties(board, r-1, c-1) == 1:
            # Find the liberty and play there
            for dr, dc in directions:
                nr, nc = r-1 + dr, c-1 + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                    return (nr+1, nc+1)

    # 3. Check for connection moves to strengthen weak groups
    for r, c in me:
        if count_liberties(board, r-1, c-1) <= 2:
            # Look for adjacent empty points to connect
            for dr, dc in directions:
                nr, nc = r-1 + dr, c-1 + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                    # Check if this move would connect to another friendly stone
                    for ddr, ddc in directions:
                        nnr, nnc = nr + ddr, nc + ddc
                        if 0 <= nnr < 19 and 0 <= nnc < 19 and board[nnr, nnc] == 1:
                            return (nr+1, nc+1)

    # 4. Calculate influence map
    influence = np.zeros((19, 19))
    for r in range(19):
        for c in range(19):
            if board[r, c] != 0:
                continue
            # Simple influence calculation based on distance to stones
            my_influence = 0
            opp_influence = 0
            for i in range(19):
                for j in range(19):
                    if board[i, j] == 1:
                        my_influence += 1 / (1 + abs(i - r) + abs(j - c))
                    elif board[i, j] == -1:
                        opp_influence += 1 / (1 + abs(i - r) + abs(j - c))
            influence[r, c] = my_influence - opp_influence

    # 5. Find best move based on influence
    best_move = None
    best_score = -float('inf')

    # Consider all empty points
    empty_points = []
    for r in range(19):
        for c in range(19):
            if board[r, c] == 0:
                empty_points.append((r, c))

    # Add some randomness to avoid predictability
    random.shuffle(empty_points)

    for r, c in empty_points:
        # Skip if it's an eye (surrounded by own stones)
        if is_eye(board, r, c, 1):
            continue

        # Calculate move score
        score = influence[r, c]

        # Bonus for being near opponent stones (potential to attack)
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == -1:
                score += 0.5

        # Bonus for being near own stones (potential to connect)
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 1:
                score += 0.3

        if score > best_score:
            best_score = score
            best_move = (r+1, c+1)

    # If no good move found, pass
    if best_move is None:
        return (0, 0)

    return best_move

def count_liberties(board, r, c):
    """Count liberties of a stone/group at (r, c)"""
    if board[r, c] == 0:
        return 0

    color = board[r, c]
    visited = np.zeros((19, 19), dtype=bool)
    queue = deque([(r, c)])
    visited[r, c] = True
    liberties = 0

    while queue:
        x, y = queue.popleft()
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 19 and 0 <= ny < 19:
                if not visited[nx, ny]:
                    if board[nx, ny] == 0:
                        liberties += 1
                    elif board[nx, ny] == color:
                        visited[nx, ny] = True
                        queue.append((nx, ny))

    return liberties

def is_eye(board, r, c, color):
    """Check if a point is an eye (surrounded by friendly stones)"""
    if board[r, c] != 0:
        return False

    # Check all 4 directions
    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19:
            if board[nr, nc] != color:
                return False
        else:
            return False

    return True
