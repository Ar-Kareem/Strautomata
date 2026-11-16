
from collections import deque
import copy

DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

def get_group(board, r, c, color):
    """Return the group of stones of the given color at (r,c) and its liberties."""
    if board[r][c] != color:
        return set(), set()
    group = set()
    liberties = set()
    visited = set()
    queue = deque()
    queue.append((r, c))
    visited.add((r, c))
    while queue:
        x, y = queue.popleft()
        group.add((x, y))
        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 19 and 0 <= ny < 19:
                if board[nx][ny] == color and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
                elif board[nx][ny] == 0:
                    liberties.add((nx, ny))
    return group, liberties

def is_legal_move(board, r, c, color):
    """Check if placing a stone of the given color at (r,c) is legal."""
    if board[r][c] != 0:
        return False
    new_board = copy.deepcopy(board)
    new_board[r][c] = color
    # Check adjacent opponent groups for capture
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and new_board[nr][nc] == 3 - color:
            group, liberties = get_group(new_board, nr, nc, 3 - color)
            if len(liberties) == 0:
                # Capture the group
                for (i, j) in group:
                    new_board[i][j] = 0
    # Check liberties of the new group
    group, liberties = get_group(new_board, r, c, color)
    return len(liberties) > 0

def policy(me, opponent, memory):
    # Build board representation (0-indexed)
    board = [[0] * 19 for _ in range(19)]
    for (r, c) in me:
        board[r - 1][c - 1] = 1
    for (r, c) in opponent:
        board[r - 1][c - 1] = 2

    # Generate capture moves (opponent groups with one liberty)
    capture_moves = set()
    visited_opponent = set()
    for r in range(19):
        for c in range(19):
            if board[r][c] == 2 and (r, c) not in visited_opponent:
                group, liberties = get_group(board, r, c, 2)
                for stone in group:
                    visited_opponent.add(stone)
                if len(liberties) == 1:
                    move = next(iter(liberties))
                    capture_moves.add(move)

    if capture_moves:
        move = next(iter(capture_moves))
        return (move[0] + 1, move[1] + 1), memory

    # Generate defensive moves (our groups with one liberty)
    defense_moves = set()
    visited_us = set()
    for r in range(19):
        for c in range(19):
            if board[r][c] == 1 and (r, c) not in visited_us:
                group, liberties = get_group(board, r, c, 1)
                for stone in group:
                    visited_us.add(stone)
                if len(liberties) == 1:
                    move = next(iter(liberties))
                    if is_legal_move(board, move[0], move[1], 1):
                        defense_moves.add(move)

    if defense_moves:
        move = next(iter(defense_moves))
        return (move[0] + 1, move[1] + 1), memory

    # Generate expansion moves (adjacent to our stones, not capture or defense)
    expansion_moves = set()
    for (r, c) in me:
        for dr, dc in DIRECTIONS:
            nr, nc = r - 1 + dr, c - 1 + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr][nc] == 0:
                if is_legal_move(board, nr, nc, 1):
                    expansion_moves.add((nr, nc))

    if expansion_moves:
        move = next(iter(expansion_moves))
        return (move[0] + 1, move[1] + 1), memory

    # Try any other legal move
    for r in range(19):
        for c in range(19):
            if board[r][c] == 0 and is_legal_move(board, r, c, 1):
                return (r + 1, c + 1), memory

    # If no move found, pass
    return (0, 0), memory
