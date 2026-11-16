
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Initialize board representation
    board = np.zeros((19, 19), dtype=int)
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = -1

    # Directions for neighbor checks (up, down, left, right)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def is_on_board(r, c):
        return 0 <= r < 19 and 0 <= c < 19

    def get_liberties(r, c, visited=None):
        if visited is None:
            visited = set()
        if (r, c) in visited or not is_on_board(r, c) or board[r, c] != board[r, c]:
            return 0
        visited.add((r, c))
        liberties = 0
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if not is_on_board(nr, nc) or board[nr, nc] == 0:
                liberties += 1
            elif board[nr, nc] == board[r, c] and (nr, nc) not in visited:
                liberties += get_liberties(nr, nc, visited)
        return liberties

    def is_eye(r, c, color):
        if not is_on_board(r, c) or board[r, c] != 0:
            return False
        # Check if surrounded by our stones
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if not is_on_board(nr, nc) or board[nr, nc] != color:
                return False
        return True

    def find_atari_groups(color):
        atari_groups = []
        visited = set()
        for r in range(19):
            for c in range(19):
                if board[r, c] == color and (r, c) not in visited:
                    group = []
                    queue = deque([(r, c)])
                    visited.add((r, c))
                    while queue:
                        x, y = queue.popleft()
                        group.append((x, y))
                        for dx, dy in directions:
                            nx, ny = x + dx, y + dy
                            if is_on_board(nx, ny) and board[nx, ny] == color and (nx, ny) not in visited:
                                visited.add((nx, ny))
                                queue.append((nx, ny))
                    liberties = 0
                    for x, y in group:
                        for dx, dy in directions:
                            nx, ny = x + dx, y + dy
                            if is_on_board(nx, ny) and board[nx, ny] == 0:
                                liberties += 1
                    if liberties == 1:
                        atari_groups.append((group, liberties))
        return atari_groups

    def evaluate_move(r, c):
        if not is_on_board(r, c) or board[r, c] != 0:
            return -float('inf')

        # Check if move is self-atari (bad)
        temp_board = board.copy()
        temp_board[r, c] = 1
        liberties = 0
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if is_on_board(nr, nc) and temp_board[nr, nc] == 0:
                liberties += 1
        if liberties == 0:
            return -float('inf')

        score = 0

        # Eye creation/protection
        if is_eye(r, c, 1):
            score += 100

        # Defend our atari groups
        for group, libs in find_atari_groups(1):
            for x, y in group:
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if (nx, ny) == (r, c):
                        score += 50

        # Attack opponent's atari groups
        for group, libs in find_atari_groups(-1):
            for x, y in group:
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if (nx, ny) == (r, c):
                        score += 40

        # Connection moves
        friendly_neighbors = 0
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if is_on_board(nr, nc) and board[nr, nc] == 1:
                friendly_neighbors += 1
        if friendly_neighbors >= 2:
            score += 30

        # Cutting moves
        opponent_neighbors = 0
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if is_on_board(nr, nc) and board[nr, nc] == -1:
                opponent_neighbors += 1
        if opponent_neighbors >= 2:
            score += 25

        # Territory expansion
        empty_neighbors = 0
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if is_on_board(nr, nc) and board[nr, nc] == 0:
                empty_neighbors += 1
        score += empty_neighbors * 2

        return score

    # Generate candidate moves
    candidates = []
    for r in range(19):
        for c in range(19):
            if board[r, c] == 0:
                candidates.append((r, c))

    # Add some strategic points
    for r in range(19):
        for c in range(19):
            if board[r, c] == 1:
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if is_on_board(nr, nc) and board[nr, nc] == 0:
                        if (nr, nc) not in candidates:
                            candidates.append((nr, nc))

    # Evaluate all candidates
    best_move = (0, 0)
    best_score = -float('inf')

    for r, c in candidates:
        score = evaluate_move(r, c)
        if score > best_score:
            best_score = score
            best_move = (r, c)

    # If no good move found, pass
    if best_score == -float('inf'):
        return (0, 0)

    return (best_move[0] + 1, best_move[1] + 1)
