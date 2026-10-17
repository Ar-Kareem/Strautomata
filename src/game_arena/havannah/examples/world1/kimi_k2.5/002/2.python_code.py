
import numpy as np
from collections import deque
from typing import List, Tuple, Set, Dict

# Directions: [(-1, 0), (1, 0), (-1, -1), (0, -1), (-1, 1), (0, 1)]
# Based on problem description: UP, DOWN, UP-LEFT, DOWN-LEFT, UP-RIGHT, DOWN-RIGHT
DIRS = [(-1, 0), (1, 0), (-1, -1), (0, -1), (-1, 1), (0, 1)]

def get_neighbors(r: int, c: int, valid_mask: np.ndarray) -> List[Tuple[int, int]]:
    """Get valid neighbors within the hex board."""
    neighbors = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 15 and 0 <= nc < 15 and valid_mask[nr, nc]:
            neighbors.append((nr, nc))
    return neighbors

def classify_board(valid_mask: np.ndarray):
    """Classify cells into corners (2 neighbors) and edges (3-5 neighbors)."""
    corners = []
    edges = []
    edge_id = {}  # Maps edge cell to the direction of the missing neighbor (0-5)
    
    for r in range(15):
        for c in range(15):
            if not valid_mask[r, c]:
                continue
            nbrs = get_neighbors(r, c, valid_mask)
            count = len(nbrs)
            if count == 2:
                corners.append((r, c))
            elif count < 6:
                edges.append((r, c))
                # Determine which edge it belongs to by finding invalid neighbor direction
                for i, (dr, dc) in enumerate(DIRS):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < 15 and 0 <= nc < 15 and valid_mask[nr, nc]):
                        edge_id[(r, c)] = i
                        break
    return corners, edges, edge_id

def bfs_component(start: Tuple[int, int], stones: Set[Tuple[int, int]], valid_mask: np.ndarray) -> Set[Tuple[int, int]]:
    """BFS to find connected component of stones containing start."""
    if start not in stones:
        return set()
    visited = {start}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for nr, nc in get_neighbors(r, c, valid_mask):
            if (nr, nc) in stones and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc))
    return visited

def is_winning(stones_set: Set[Tuple[int, int]], move: Tuple[int, int], 
               valid_mask: np.ndarray, corners_set: Set[Tuple[int, int]], 
               edge_id: Dict[Tuple[int, int], int]) -> bool:
    """Check if placing 'move' creates a win (ring, bridge, or fork)."""
    # Temporarily add move to stones for BFS
    test_stones = stones_set | {move}
    
    # Get component containing move
    component = bfs_component(move, test_stones, valid_mask)
    
    # Check Bridge: Component touches >= 2 corners
    corner_touches = sum(1 for cell in corners_set if cell in component)
    if corner_touches >= 2:
        return True
    
    # Check Fork: Component touches >= 3 distinct edges (corners excluded)
    edges_touched = set()
    for cell in component:
        if cell in corners_set:
            continue
        if cell in edge_id:
            edges_touched.add(edge_id[cell])
    if len(edges_touched) >= 3:
        return True
    
    # Check Ring: Move connects two stones already connected via other path
    # Find neighbors of move that were already in stones_set
    stone_neighbors = [n for n in get_neighbors(move[0], move[1], valid_mask) if n in stones_set]
    if len(stone_neighbors) < 2:
        return False
    
    # Check if any two stone_neighbors are connected in stones_set (without using move)
    # BFS from first neighbor
    start = stone_neighbors[0]
    targets = set(stone_neighbors[1:])
    visited = {start}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        if (r, c) in targets:
            return True
        for nr, nc in get_neighbors(r, c, valid_mask):
            if (nr, nc) in stones_set and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc))
    return False

def evaluate_move(move: Tuple[int, int], me_set: Set[Tuple[int, int]], 
                 opp_set: Set[Tuple[int, int]], valid_mask: np.ndarray,
                 corners_set: Set[Tuple[int, int]], edge_set: Set[Tuple[int, int]],
                 edge_id: Dict[Tuple[int, int], int]) -> float:
    """Heuristic evaluation of a move."""
    r, c = move
    score = 0.0
    
    # Connectivity bonuses
    my_nbrs = [n for n in get_neighbors(r, c, valid_mask) if n in me_set]
    opp_nbrs = [n for n in get_neighbors(r, c, valid_mask) if n in opp_set]
    
    score += len(my_nbrs) * 15.0  # Connect to friends
    score += len(opp_nbrs) * 8.0   # Block opponent
    
    # Ring potential: if two friendly neighbors are connected
    if len(my_nbrs) >= 2:
        # Check if any pair is adjacent
        for i, n1 in enumerate(my_nbrs):
            for n2 in my_nbrs[i+1:]:
                if n2 in get_neighbors(n1[0], n1[1], valid_mask):
                    score += 80.0
                    break
    
    # Proximity to corners (Bridge potential)
    min_corner_dist = min(abs(r - cr) + abs(c - cc) for cr, cc in corners_set) if corners_set else 100
    score += (10 - min_corner_dist) * 2.0
    
    # Edge cells (Fork potential)
    if move in edge_set:
        score += 10.0
    
    # Centrality (prefer center early game)
    score -= ((r - 7) ** 2 + (c - 7) ** 2) * 0.05
    
    return score

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], valid_mask) -> Tuple[int, int]:
    # Convert inputs
    me_set = set(me)
    opp_set = set(opp)
    valid_mask_arr = np.array(valid_mask, dtype=bool)
    
    # Precompute board geometry
    corners, edges, edge_id = classify_board(valid_mask_arr)
    corners_set = set(corners)
    edge_set = set(edges)
    
    # Get all valid empty cells
    valid_cells = []
    for r in range(15):
        for c in range(15):
            if valid_mask_arr[r, c] and (r, c) not in me_set and (r, c) not in opp_set:
                valid_cells.append((r, c))
    
    if not valid_cells:
        return (0, 0)  # Should not happen in valid game
    
    # 1. Check for immediate winning move
    for move in valid_cells:
        if is_winning(me_set, move, valid_mask_arr, corners_set, edge_id):
            return move
    
    # 2. Check for opponent immediate wins (blocking)
    blocks = []
    for move in valid_cells:
        if is_winning(opp_set, move, valid_mask_arr, corners_set, edge_id):
            blocks.append(move)
    
    if len(blocks) == 1:
        return blocks[0]
    # If multiple opponent threats, we can't block all; proceed to heuristic
    
    # 3. Evaluate all candidates
    best_move = valid_cells[0]
    best_score = -1e9
    
    for move in valid_cells:
        score = evaluate_move(move, me_set, opp_set, valid_mask_arr, 
                             corners_set, edge_set, edge_id)
        
        # Prioritize blocks even if multiple (choose the "best" block)
        if move in blocks:
            score += 1000  # High priority but evaluate which block is better
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
