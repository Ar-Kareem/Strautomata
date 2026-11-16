
import numpy as np
import random
from collections import deque

# Global cache for board topology
_neighbors_cache = {}
_corners = set()
_edges = {} # map cell -> edge_id (0-5)
_valid_cells = set()

# Standard Pointy-Top Hexagonal Grid Neighbor Offsets
# (row, col) offsets
_OFFSETS = [
    (1, 0), (-1, 0),    # South, North
    (0, 1), (0, -1),    # East, West
    (1, -1), (-1, 1)    # South-West, North-East
]

def init_board(valid_mask):
    """Initializes board topology: neighbors, corners, and edges."""
    global _neighbors_cache, _corners, _edges, _valid_cells
    
    if not valid_mask.any():
        return

    rows, cols = valid_mask.shape
    _valid_cells = set(zip(*np.where(valid_mask)))
    
    center_r, center_c = rows // 2, cols // 2
    edge_cells = []

    # Compute neighbors for all valid cells
    for r, c in _valid_cells:
        neighbors = []
        for dr, dc in _OFFSETS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and valid_mask[nr, nc]:
                neighbors.append((nr, nc))
        _neighbors_cache[(r, c)] = neighbors
        
        # Identify edge cells (cells with fewer than 6 neighbors)
        if len(neighbors) < 6:
            edge_cells.append((r, c))

    # Identify Corners and Edges
    # In a hexagon, corners are the "extremes". We sort edge cells by distance from center.
    # The furthest 6 cells are likely the 6 corners.
    if edge_cells:
        edge_cells.sort(key=lambda p: (p[0]-center_r)**2 + (p[1]-center_c)**2, reverse=True)
        _corners = set(edge_cells[:6])
        
        # Assign edge IDs to edge cells based on angle from center
        for r, c in edge_cells:
            angle = np.arctan2(r - center_r, c - center_c)
            # Map angle to 6 sectors (0-5)
            sector = int(((angle + np.pi) / (2 * np.pi)) * 6)
            if sector == 6: sector = 0
            _edges[(r, c)] = sector

def get_neighbors(r, c):
    """Returns list of neighbor coordinates for (r, c)."""
    return _neighbors_cache.get((r, c), [])

def has_ring(stones_set):
    """
    Checks for a Ring using graph theory.
    In any connected component, if Edges >= Vertices, a cycle exists.
    """
    if not stones_set: return False
    visited = set()
    
    for start in stones_set:
        if start in visited: continue
        
        # BFS to find component size (V) and total edges (E)
        q = [start]
        visited.add(start)
        v = 0
        e = 0
        
        while q:
            curr = q.pop()
            v += 1
            for n in get_neighbors(curr[0], curr[1]):
                if n in stones_set:
                    e += 1
                    if n not in visited:
                        visited.add(n)
                        q.append(n)
        
        # Every edge is counted twice (once from each endpoint)
        # So actual edges = e / 2
        if (e // 2) >= v:
            return True
            
    return False

def has_bridge(stones_set):
    """Checks if the player connects any two corners."""
    my_corners = _corners.intersection(stones_set)
    if len(my_corners) < 2: return False
    
    visited = set()
    
    # Group corners into connected components
    # We just need to find if any component contains >= 2 corners
    for c in my_corners:
        if c in visited: continue
        
        # BFS from corner c
        q = [c]
        visited.add(c)
        corners_in_group = 0
        
        while q:
            curr = q.pop()
            if curr in _corners:
                corners_in_group += 1
                if corners_in_group >= 2:
                    return True
            
            for n in get_neighbors(curr[0], curr[1]):
                if n in stones_set and n not in visited:
                    visited.add(n)
                    q.append(n)
                    
    return False

def has_fork(stones_set):
    """Checks if the player connects 3 distinct edges."""
    visited = set()
    
    for start in stones_set:
        if start in visited: continue
        
        q = [start]
        visited.add(start)
        edges_touched = set()
        
        while q:
            curr = q.pop()
            if curr in _edges:
                edges_touched.add(_edges[curr])
                if len(edges_touched) >= 3:
                    return True
            
            for n in get_neighbors(curr[0], curr[1]):
                if n in stones_set and n not in visited:
                    visited.add(n)
                    q.append(n)
                    
    return False

def is_winner(stones_set):
    return has_ring(stones_set) or has_bridge(stones_set) or has_fork(stones_set)

def policy(me, opp, valid_mask):
    """
    Returns the next move for the Havannah game.
    """
    # Initialize board topology on first call
    if not _neighbors_cache:
        init_board(valid_mask)

    me_set = set(me)
    opp_set = set(opp)
    
    # Generate candidate moves
    # We prioritize moves near existing stones to improve performance and relevance
    candidates = set()
    
    # Look at neighbors of my stones
    for r, c in me_set:
        for nr, nc in get_neighbors(r, c):
            if valid_mask[nr, nc] and (nr, nc) not in me_set and (nr, nc) not in opp_set:
                candidates.add((nr, nc))
                
    # If first move or isolated, look at center or random valid
    if not candidates:
        # Try center
        if valid_mask[7, 7] and (7, 7) not in opp_set:
            return (7, 7)
        # Fallback to any valid cell
        all_valid = list(zip(*np.where(valid_mask)))
        if all_valid:
            return random.choice(all_valid)
        return (-1, -1) # Should not happen

    candidates = list(candidates)
    random.shuffle(candidates) # Add randomness for tie-breaking

    # 1. Check for immediate Win
    for move in candidates:
        me_set.add(move)
        if is_winner(me_set):
            me_set.remove(move)
            return move
        me_set.remove(move)
        
    # 2. Check for immediate Loss (Block opponent)
    for move in candidates:
        opp_set.add(move)
        if is_winner(opp_set):
            opp_set.remove(move)
            return move
        opp_set.remove(move)
        
    # 3. Heuristic Evaluation
    best_score = -float('inf')
    best_move = None
    
    center_r, center_c = 7, 7
    
    for r, c in candidates:
        score = 0
        
        # Centrality: Prefer center (good for rings) or edges (good for bridges/forks)
        dist_center = abs(r - center_r) + abs(c - center_c)
        score -= dist_center * 0.1
        
        # Count neighbors
        nbrs = get_neighbors(r, c)
        my_count = sum(1 for n in nbrs if n in me_set)
        opp_count = sum(1 for n in nbrs if n in opp_set)
        
        score += my_count * 5    # Expand existing groups
        score += opp_count * 2   # Block opponent
        
        # Strategic placement
        if (r, c) in _corners:
            score += 10 # Corners are crucial for bridges
        elif (r, c) in _edges:
            score += 5  # Edges are needed for forks/bridges
            
        # Random jitter
        score += random.random()
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
            
    return best_move if best_move else random.choice(candidates)
