
import numpy as np
from typing import List, Tuple, Set

# Board size
SIZE = 19

# Direction vectors for adjacent positions (up, down, left, right)
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def in_bounds(r: int, c: int) -> bool:
    return 1 <= r <= SIZE and 1 <= c <= SIZE

def to_idx(r: int, c: int) -> int:
    return (r - 1) * SIZE + (c - 1)

def from_idx(idx: int) -> tuple[int, int]:
    return (idx // SIZE) + 1, (idx % SIZE) + 1

def get_neighbors(r: int, c: int) -> List[Tuple[int, int]]:
    neighbors = []
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc):
            neighbors.append((nr, nc))
    return neighbors

def is_liberty(board: np.ndarray, r: int, c: int) -> bool:
    return in_bounds(r, c) and board[r-1, c-1] == 0

def find_group(board: np.ndarray, r: int, c: int) -> Set[Tuple[int, int]]:
    color = board[r-1, c-1]
    if color == 0:
        return set()
    group = set()
    stack = [(r, c)]
    visited = np.zeros((SIZE, SIZE), dtype=bool)
    visited[r-1, c-1] = True

    while stack:
        cr, cc = stack.pop()
        group.add((cr, cc))
        for nr, nc in get_neighbors(cr, cc):
            if not visited[nr-1, nc-1] and board[nr-1, nc-1] == color:
                visited[nr-1, nc-1] = True
                stack.append((nr, nc))
    return group

def has_liberty(board: np.ndarray, r: int, c: int) -> bool:
    group = find_group(board, r, c)
    for gr, gc in group:
        for nr, nc in get_neighbors(gr, gc):
            if board[nr-1, nc-1] == 0:
                return True
    return False

def would_have_liberty(board: np.ndarray, r: int, c: int, color: int) -> bool:
    # Simulate placing the stone
    board_copy = board.copy()
    board_copy[r-1, c-1] = color
    # Remove captured opponent groups
    opponent_color = 3 - color
    for nr, nc in get_neighbors(r, c):
        if board_copy[nr-1, nc-1] == opponent_color:
            if not has_liberty(board_copy, nr, nc):
                # Remove this group
                group = find_group(board_copy, nr, nc)
                for gr, gc in group:
                    board_copy[gr-1, gc-1] = 0
    # Check if own group has liberty
    return has_liberty(board_copy, r, c)

def is_legal_move(board: np.ndarray, r: int, c: int, color: int) -> bool:
    if not in_bounds(r, c) or board[r-1, c-1] != 0:
        return False
    if would_have_liberty(board, r, c, color):
        return True
    return False

def count_liberties(board: np.ndarray, r: int, c: int) -> int:
    group = find_group(board, r, c)
    liberties = set()
    for gr, gc in group:
        for nr, nc in get_neighbors(gr, gc):
            if board[nr-1, nc-1] == 0:
                liberties.add((nr, nc))
    return len(liberties)

# Predefined priority points: corners and sides
CORNER_CENTRAL = [(4,4), (4,16), (16,4), (16,16)]
CORNER_33 = [(4,4), (4,16), (16,4), (16,16)]
SIDE_34 = [(4,3), (4,17), (3,4), (17,4), (3,16), (17,16), (4,3), (4,17)]  # adjusted
CENTER = [(10,10)]
PRIORITY_POINTS = CORNER_33 + SIDE_34 + CORNER_CENTRAL + CENTER

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    # Create board state: 1 for me, 2 for opponent, 0 for empty
    board = np.zeros((SIZE, SIZE), dtype=np.int8)
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = 2

    my_color = 1
    opponent_color = 2

    # Step 1: Check for any immediate capture (play to capture opponent group)
    for r in range(1, SIZE + 1):
        for c in range(1, SIZE + 1):
            if not is_legal_move(board, r, c, my_color):
                continue
            # Simulate move and check if any opponent group is captured
            board_sim = board.copy()
            board_sim[r-1, c-1] = my_color
            capture_made = False
            for nr, nc in get_neighbors(r, c):
                if board_sim[nr-1, nc-1] == opponent_color:
                    if not has_liberty(board_sim, nr, nc):
                        capture_made = True
                        break
            if capture_made:
                return (r, c)

    # Step 2: Prevent self-capture (save our group from atari)
    for my_stone in me:
        r, c = my_stone
        if count_liberties(board, r, c) == 1:  # In atari
            for nr, nc in get_neighbors(r, c):
                if is_legal_move(board, nr, nc, my_color):
                    # Check if playing here saves the group
                    if would_have_liberty(board, nr, nc, my_color):
                        return (nr, nc)

    # Step 3: Play on high-priority points (openings)
    for pr, pc in PRIORITY_POINTS:
        if is_legal_move(board, pr, pc, my_color):
            return (pr, pc)

    # Step 4: Expand influence or fill empty territory
    # Look for moves adjacent to our stones with open space
    for r in range(1, SIZE + 1):
        for c in range(1, SIZE + 1):
            if board[r-1, c-1] != 0:
                continue
            if is_legal_move(board, r, c, my_color):
                # Prefer moves near our stones
                adjacent_to_me = False
                for nr, nc in get_neighbors(r, c):
                    if board[nr-1, nc-1] == my_color:
                        adjacent_to_me = True
                        break
                if adjacent_to_me:
                    return (r, c)

    # Step 5: Fallback to first legal move found
    for r in range(1, SIZE + 1):
        for c in range(1, SIZE + 1):
            if is_legal_move(board, r, c, my_color):
                return (r, c)

    # If no legal move, pass
    return (0, 0)
