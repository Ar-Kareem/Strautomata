
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Convert to numpy arrays and mark occupied positions
    board = np.zeros((19, 19))
    for (r, c) in me:
        board[r-1][c-1] = 1  # 1 is our stones
    for (r, c) in opponent:
        board[r-1][c-1] = 2  # 2 is opponent stones

    # Check for immediate capture moves
    capture_move = find_capture_move(board, opponent)
    if capture_move:
        return capture_move

    # Try to occupy valuable points (corners and sides first)
    valuable_points = [(1, 1), (1, 19), (19, 1), (19, 19)]  # Corners
    valuable_points += [(1, c) for c in range(2, 19)]  # Top edge
    valuable_points += [(19, c) for c in range(2, 19)]  # Bottom edge
    valuable_points += [(r, 1) for r in range(2, 19)]  # Left edge
    valuable_points += [(r, 19) for r in range(2, 19)]  # Right edge
    
    for (r, c) in valuable_points:
        if board[r-1][c-1] == 0 and is_legal_move(board, r-1, c-1, is_black=True):
            return (r, c)

    # Try to play near our existing stones (expansion)
    for (r, c) in me:
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= 19 and 1 <= nc <= 19:
                    if board[nr-1][nc-1] == 0 and is_legal_move(board, nr-1, nc-1, is_black=True):
                        return (nr, nc)

    # Fallback: pick first available legal move
    for r in range(1, 20):
        for c in range(1, 20):
            if board[r-1][c-1] == 0 and is_legal_move(board, r-1, c-1, is_black=True):
                return (r, c)
    
    # If no legal moves, pass
    return (0, 0)

def find_capture_move(board, opponent_stones):
    # Check if opponent has any stones with 1 liberty
    for (r, c) in opponent_stones:
        if count_liberties(board, r-1, c-1) == 1:
            # Find the liberty position
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r-1 + dr, c-1 + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr][nc] == 0:
                    if is_legal_move(board, nr, nc, is_black=True):
                        return (nr+1, nc+1)
    return None

def count_liberties(board, row, col):
    if board[row][col] == 0:
        return 0
    
    stone_type = board[row][col]
    visited = set()
    liberties = set()
    q = deque()
    q.append((row, col))
    visited.add((row, col))
    
    while q:
        r, c = q.popleft()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                if board[nr][nc] == 0:
                    liberties.add((nr, nc))
                elif board[nr][nc] == stone_type and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
    
    return len(liberties)

def is_legal_move(board, row, col, is_black):
    # Check if move is on empty intersection
    if board[row][col] != 0:
        return False
    
    # Temporarily place the stone
    stone_type = 1 if is_black else 2
    board[row][col] = stone_type
    
    # Check if the move has any liberties
    has_liberties = count_liberties(board, row, col) > 0
    
    # Check if any opponent groups are captured
    opponent = 2 if is_black else 1
    captures = False
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 19 and 0 <= nc < 19:
            if board[nr][nc] == opponent and count_liberties(board, nr, nc) == 0:
                captures = True
                break
    
    # Undo temporary placement
    board[row][col] = 0
    
    # Move is legal if it has liberties or captures opponent stones
    return has_liberties or captures
