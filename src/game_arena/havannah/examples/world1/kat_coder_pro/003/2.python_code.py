
import numpy as np
from collections import deque

# Board size
N = 15

# Directions for hexagonal neighbors
# Directions in axial coordinates: 
# (col_offset, row_offset) for the 6 neighbors
DIRECTIONS = [
    (0, -1),  # Up
    (1, -1),  # Up-Right
    (1, 0),   # Down-Right
    (0, 1),   # Down
    (-1, 1),  # Down-Left
    (-1, 0),  # Up-Left
]

# Precompute valid board coordinates and neighbors
VALID_MASK = np.zeros((N, N), dtype=bool)
NEIGHBORS = {}

for col in range(N):
    for row in range(N):
        # In Havannah, the board is a hexagon.
        # Valid cells are those where:
        # -14 <= row - col <= 14
        # 0 <= row <= 14
        # 0 <= col <= 14
        if 0 <= row <= 14 and 0 <= col <= 14 and -14 <= row - col <= 14:
            VALID_MASK[row, col] = True
            neighbors = []
            for dc, dr in DIRECTIONS:
                nr, nc = row + dr, col + dc
                if 0 <= nr < N and 0 <= nc < N and VALID_MASK[nr, nc]:
                    neighbors.append((nr, nc))
            NEIGHBORS[(row, col)] = neighbors

# Edge indices (0 to 5) for corner/edge identification
# 0: Top edge (col=0), 5: Bottom edge (col=14)
# 1: Top-Right edge (row=0), 4: Bottom-Left edge (row=14)
# 2: Bottom-Right edge (row-col=14), 3: Top-Left edge (row-col=-14)
EDGES = {
    # Top edge (col = 0, row-col in [-14, -1])
    "top": [(r, 0) for r in range(14)],
    # Bottom edge (col = 14, row-col in [0, 14])
    "bottom": [(r, 14) for r in range(1, 15)],
    # Top-Right edge (row = 0, col in [0, 14])
    "top_right": [(0, c) for c in range(15)],
    # Bottom-Left edge (row = 14, col in [0, 14])
    "bottom_left": [(14, c) for c in range(15)],
    # Bottom-Right edge (row - col = 14, row in [14, 14], col in [0, 0])
    "bottom_right": [(r, c) for r in range(15) for c in range(15) if r - c == 14],
    # Top-Left edge (row - col = -14, row in [0, 0], col in [14, 14])
    "top_left": [(r, c) for r in range(15) for c in range(15) if r - c == -14],
}

# Corner cells
CORNERS = [(0, 0), (0, 14), (7, 7), (14, 0), (14, 14)]

def is_connected_group(board, start, visited):
    """Find connected group using BFS."""
    group = set()
    queue = deque([start])
    visited.add(start)
    group.add(start)
    
    while queue:
        node = queue.popleft()
        for neighbor in NEIGHBORS[node]:
            if neighbor not in visited and board[neighbor[0], neighbor[1]] == 1:
                visited.add(neighbor)
                group.add(neighbor)
                queue.append(neighbor)
    return group

def check_ring(group, board):
    """Check if a group forms a ring."""
    # Find boundary of the group
    boundary = set()
    for r, c in group:
        for nr, nc in NEIGHBORS[(r, c)]:
            if board[nr, nc] == 0:
                boundary.add((nr, nc))
    
    # Check if any cell inside the boundary is empty
    # We need to check if the group encloses any empty space
    # We can do this by checking if there's an empty cell inside the convex hull of the group
    # However, a simpler approach is to check if there's an empty cell that is surrounded by the group
    # This can be done by checking if there's an empty cell that is not connected to the edge
    
    # For simplicity, we check if there's an empty cell that is surrounded by the group
    # We can do this by checking if there's an empty cell inside the bounding box of the group
    # that is not connected to the edge
    
    # Get bounding box
    min_r = min(r for r, c in group)
    max_r = max(r for r, c in group)
    min_c = min(c for r, c in group)
    max_c = max(c for r, c in group)
    
    # Check if there's an empty cell inside the bounding box
    # that is not connected to the edge
    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            if board[r, c] == 0:
                # Check if this empty cell is inside the group
                # by checking if it's surrounded by the group
                surrounded = True
                for nr, nc in NEIGHBORS[(r, c)]:
                    if board[nr, nc] == 0 or (nr, nc) not in group:
                        surrounded = False
                        break
                if surrounded:
                    return True
    return False

def check_bridge(group):
    """Check if a group forms a bridge."""
    corners_in_group = [corner for corner in CORNERS if corner in group]
    return len(corners_in_group) >= 2

def check_fork(group):
    """Check if a group forms a fork."""
    edges_touched = set()
    for r, c in group:
        # Check which edges this stone touches
        if (r, c) in EDGES["top"]:
            edges_touched.add("top")
        if (r, c) in EDGES["bottom"]:
            edges_touched.add("bottom")
        if (r, c) in EDGES["top_right"]:
            edges_touched.add("top_right")
        if (r, c) in EDGES["bottom_left"]:
            edges_touched.add("bottom_left")
        if (r, c) in EDGES["bottom_right"]:
            edges_touched.add("bottom_right")
        if (r, c) in EDGES["top_left"]:
            edges_touched.add("top_left")
    return len(edges_touched) >= 3

def has_winning_move(me, opp, valid_mask, player):
    """Check if the current player has a winning move."""
    # Create a board representation
    board = np.zeros((N, N), dtype=int)
    for r, c in me:
        board[r, c] = 1
    for r, c in opp:
        board[r, c] = -1
    
    # Get all empty cells
    empty_cells = [(r, c) for r in range(N) for c in range(N) if valid_mask[r, c] and board[r, c] == 0]
    
    # Check each empty cell
    for r, c in empty_cells:
        # Temporarily place the stone
        board[r, c] = 1 if player == 0 else -1
        
        # Find connected groups
        visited = set()
        for start in [(r, c)] + me + opp:
            if board[start[0], start[1]] == (1 if player == 0 else -1) and start not in visited:
                group = is_connected_group(board, start, visited)
                
                # Check for winning conditions
                if check_ring(group, board) or check_bridge(group) or check_fork(group):
                    return (r, c)
        
        # Remove the stone
        board[r, c] = 0
    
    return None

def policy(me, opp, valid_mask):
    """Main policy function."""
    # Check if we have a winning move
    winning_move = has_winning_move(me, opp, valid_mask, 0)
    if winning_move:
        return winning_move
    
    # Check if opponent has a winning move
    opponent_winning_move = has_winning_move(me, opp, valid_mask, 1)
    if opponent_winning_move:
        return opponent_winning_move
    
    # If no winning moves, play a strategic move
    # Prefer center, then edges, then corners
    center = (7, 7)
    if valid_mask[center[0], center[1]]:
        return center
    
    # Prefer edges
    for r in range(N):
        for c in range(N):
            if valid_mask[r, c] and (r == 0 or r == 14 or c == 0 or c == 14 or r - c == 14 or r - c == -14):
                return (r, c)
    
    # Prefer corners
    for corner in CORNERS:
        if valid_mask[corner[0], corner[1]]:
            return corner
    
    # Last resort: play any valid move
    for r in range(N):
        for c in range(N):
            if valid_mask[r, c]:
                return (r, c)
