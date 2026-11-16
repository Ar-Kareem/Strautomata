
import numpy as np
import random
from collections import deque

# Cache for board geometry based on valid_mask to avoid recomputation
_geometry_cache = {}

def get_neighbors(r, c):
    """Returns list of (r, c) neighbors based on the hexagonal grid logic."""
    # Even rows (0, 2, 4...) neighbors
    if r % 2 == 0:
        return [
            (r - 1, c), (r + 1, c),     # Same column
            (r, c - 1), (r - 1, c - 1), # Left column
            (r, c + 1), (r - 1, c + 1)  # Right column
        ]
    # Odd rows (1, 3, 5...) neighbors
    else:
        return [
            (r - 1, c), (r + 1, c),     # Same column
            (r, c - 1), (r + 1, c - 1), # Left column
            (r, c + 1), (r + 1, c + 1)  # Right column
        ]

def analyze_geometry(valid_mask):
    """Precomputes neighbors, corners, and edge IDs for the board."""
    h, w = valid_mask.shape
    neighbors_map = {}
    valid_cells = []
    
    # Build neighbors
    for r in range(h):
        for c in range(w):
            if valid_mask[r, c]:
                valid_cells.append((r, c))
                neigh = []
                for nr, nc in get_neighbors(r, c):
                    if 0 <= nr < h and 0 <= nc < w and valid_mask[nr, nc]:
                        neigh.append((nr, nc))
                neighbors_map[(r, c)] = neigh

    # Identify corners (degree 2) and edges (degree 3 or 4, not corners)
    # Note: On a hexagon board, corners have 2 neighbors, edge cells have 4, center has 6.
    corners = set()
    edges = {} # (r, c) -> edge_id (0-5)
    
    for cell in valid_cells:
        deg = len(neighbors_map[cell])
        if deg == 2:
            corners.add(cell)
    
    # Group edges into 6 contiguous segments
    # We perform a flood fill on the boundary cells
    # Boundary cells are valid cells that have at least one invalid neighbor or are corners
    # Actually, simpler: corners are fixed. We trace edges between corners.
    
    # Sort corners to establish a perimeter order?
    # Let's just find connected components of non-corner edge cells that are adjacent to a corner.
    # A robust way for hexagons:
    # 1. Identify all non-corner cells with degree < 6 (Edge cells).
    # 2. Group them.
    # 3. Assign ID based on which corner they are closest to or connected to.
    
    edge_cells = [c for c in valid_cells if len(neighbors_map[c]) < 6 and c not in corners]
    visited_edges = set()
    edge_segments = []
    
    for start in edge_cells:
        if start not in visited_edges:
            q = deque([start])
            component = []
            visited_edges.add(start)
            while q:
                curr = q.popleft()
                component.append(curr)
                for n in neighbors_map[curr]:
                    if n in edge_cells and n not in visited_edges:
                        visited_edges.add(n)
                        q.append(n)
            edge_segments.append(component)
            
    # Now map segments to edge IDs. There should be 6 segments.
    # We match segments to corners.
    for i, segment in enumerate(edge_segments):
        for cell in segment:
            edges[cell] = i

    # If there are exactly 6 corners, we can verify geometry.
    # Map corners to edges as well for Bridge checks (corners are targets)
    # Corners are technically not "edges" for Fork calculation (Rule: "Corner points are not considered parts of an edge")
    # So edges dict remains only for non-corner boundary cells.

    return neighbors_map, corners, edges

def evaluate_state(stones, neighbors_map, corners, edges):
    """
    Evaluates a set of stones.
    Returns: (has_ring, corners_connected_set, edges_connected_set)
    """
    if not stones:
        return False, set(), set()

    stone_set = set(stones)
    parent = {s: s for s in stones}
    rank = {s: 0 for s in stones}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        xroot = find(x)
        yroot = find(y)
        if xroot == yroot:
            return True # Cycle detected (Ring)
        if rank[xroot] < rank[yroot]:
            parent[xroot] = yroot
        elif rank[xroot] > rank[yroot]:
            parent[yroot] = xroot
        else:
            parent[yroot] = xroot
            rank[xroot] += 1
        return False

    has_ring = False
    
    # Build Union-Find and detect ring
    for s in stones:
        for n in neighbors_map[s]:
            if n in stone_set:
                if union(s, n):
                    has_ring = True

    # Analyze components for Bridge and Fork
    # Group by root
    components = defaultdict(list)
    for s in stones:
        components[find(s)].append(s)

    best_corners = set()
    best_edges = set()

    for root, comp_stones in components.items():
        c_con = set()
        e_con = set()
        
        for s in comp_stones:
            if s in corners:
                c_con.add(s)
            if s in edges:
                e_con.add(edges[s])
        
        if len(c_con) > len(best_corners):
            best_corners = c_con
        if len(e_con) > len(best_edges):
            best_edges = e_con
            
    return has_ring, best_corners, best_edges

def policy(me, opp, valid_mask):
    """
    Selects the best move for the player 'me'.
    """
    # Convert lists to sets for O(1) lookup
    me_set = set(me)
    opp_set = set(opp)
    
    # Get or compute geometry
    mask_key = valid_mask.tobytes()
    if mask_key not in _geometry_cache:
        _geometry_cache[mask_key] = analyze_geometry(valid_mask)
    
    neighbors, corners, edges = _geometry_cache[mask_key]
    
    # Helper to check win
    def is_win(stones):
        has_ring, c_con, e_con = evaluate_state(stones, neighbors, corners, edges)
        if has_ring: return True
        if len(c_con) >= 2: return True # Bridge
        if len(e_con) >= 3: return True # Fork
        return False

    # Identify valid moves
    h, w = valid_mask.shape
    valid_moves = []
    for r in range(h):
        for c in range(w):
            if valid_mask[r, c] and (r, c) not in me_set and (r, c) not in opp_set:
                valid_moves.append((r, c))
                
    if not valid_moves:
        # Should not happen unless board full
        return None

    # 1. Check for immediate winning move
    for move in valid_moves:
        if is_win(me_set | {move}):
            return move

    # 2. Heuristic Evaluation
    best_score = -float('inf')
    best_moves = []
    
    # Pre-evaluate opponent state to save time (optional, but good for blocking)
    # We evaluate opponent threats in the loop for accuracy
    
    for move in valid_moves:
        # My perspective
        me_new = me_set | {move}
        ring_m, corn_m, edge_m = evaluate_state(me_new, neighbors, corners, edges)
        
        score = 0
        
        # Scoring weights
        if ring_m: score += 100000
        if len(corn_m) >= 2: score += 50000 # Virtual win
        else: score += len(corn_m) ** 2 * 500 # Bridge potential
        
        if len(edge_m) >= 3: score += 50000 # Virtual win
        else: score += len(edge_m) ** 3 * 200 # Fork potential
        
        # Positional bias (center control)
        # Center is roughly (7,7)
        dr = move[0] - 7
        dc = move[1] - 7
        dist_sq = dr*dr + dc*dc
        score += (200 - dist_sq) * 2
        
        # Blocking logic
        opp_new = opp_set | {move}
        ring_o, corn_o, edge_o = evaluate_state(opp_new, neighbors, corners, edges)
        
        block_score = 0
        if ring_o: block_score += 90000
        if len(corn_o) >= 2: block_score += 40000
        else: block_score += len(corn_o) ** 2 * 400
        if len(edge_o) >= 3: block_score += 40000
        else: block_score += len(edge_o) ** 3 * 150
        
        total_score = score + block_score
        
        # Add small random noise to break ties and vary play
        total_score += random.random() * 10
        
        if total_score > best_score:
            best_score = total_score
            best_moves = [move]
        elif abs(total_score - best_score) < 1e-6:
            best_moves.append(move)
            
    return random.choice(best_moves)
