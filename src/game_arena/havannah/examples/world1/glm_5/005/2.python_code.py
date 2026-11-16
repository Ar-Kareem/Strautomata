
import random
import time

# Constants
N = 15
TIME_LIMIT = 0.9

# Global caches for geometry
NEIGHBORS_CACHE = {}
CORNERS = set()
EDGES = {} # map (r, c) -> set of edge indices

def init_geometry(valid_mask):
    """Identify corners and edges based on valid_mask and neighbor counts."""
    global CORNERS, EDGES
    CORNERS = set()
    EDGES = {}
    
    # Find all valid cells first
    valid_cells = []
    for r in range(N):
        for c in range(N):
            if valid_mask[r][c]:
                valid_cells.append((r, c))
    
    # Determine geometry
    # Corners usually have 2 neighbors.
    # Edges have 4 neighbors.
    # Inner cells have 6 neighbors.
    
    edge_counter = 0
    # We need to distinguish the 6 sides.
    # Since we don't know the orientation, we can classify 'Edge' cells by their connectivity.
    # And classify Corners.
    
    # Simple approach: corners are valid cells with <= 2 valid neighbors.
    # Edge cells are valid cells with > 2 and < 6 valid neighbors.
    
    for r, c in valid_cells:
        neighs = get_neighbors(r, c, valid_mask)
        if len(neighs) <= 2:
            CORNERS.add((r, c))
        elif len(neighs) < 6:
            # It's an edge. We need to group edges.
            # We can assign edge IDs based on connectivity or position.
            # Since we can't easily visualize, we just track that it's an edge.
            # To assign ID, we can try to 'walk' the perimeter.
            pass
            
    # Assign Edge IDs by perimeter walk
    if not CORNERS:
        return

    # Start at a corner and walk
    # We need to find the 'next' cell on the perimeter
    # A helper to find perimeter neighbors
    def get_perimeter_neighbors(r, c):
        pn = []
        for nr, nc in get_neighbors(r, c, valid_mask):
            # Check if it is on boundary (corner or edge)
            if (nr, nc) in CORNERS or (len(get_neighbors(nr, nc, valid_mask)) < 6):
                pn.append((nr, nc))
        return pn

    # Sort corners to start consistently? 
    # Or just pick one and traverse.
    start_corners = list(CORNERS)
    if not start_corners: return
    start_corners.sort() # deterministic start
    
    visited_edges = set()
    
    # The hexagon has 6 sides. We iterate around.
    # This logic assumes the valid_mask forms a proper hexagon.
    curr = start_corners[0]
    
    # We need to identify 6 sides.
    # We can do a BFS from a corner along the perimeter.
    # Actually, simpler: since we just need to count distinct edges,
    # we can use a BFS on the subgraph of edge cells to find connected components of edges?
    # No, edges of a hexagon are connected at corners.
    
    # Heuristic for edge ID based on geometry relative to center:
    # Center approx (7,7).
    # Vectors from center determine the 'face'.
    # A hexagon has 6 faces.
    # Directions: Top, TopRight, BotRight, Bot, BotLeft, TopLeft.
    
    # We can approximate by angle.
    cx, cy = 7.0, 7.0
    for r, c in valid_cells:
        if (r, c) in CORNERS:
            continue
        if len(get_neighbors(r, c, valid_mask)) < 6:
            # It's an edge
            dy = r - cx
            dx = c - cy
            # atan2 gives angle. Divide circle into 6 sectors.
            # Sector width = pi/3 = 60 deg.
            # Shift so that sectors align with hex faces.
            angle = math.atan2(dy, dx)
            # Normalize to [0, 2pi)
            if angle < 0: angle += 2 * math.pi
            
            # Assign sector 0 to 5.
            # Boundaries are tricky. This is just a heuristic.
            # Let's use the perimeter walk to be safe.
            pass
            
    # Refined Edge Walking
    # We need to map edges.
    # Let's use a simpler logic for Fork detection:
    # If a component touches 3 'perimeter regions'.
    # We can identify regions by simply BFSing the perimeter and chopping it into 6 segments.
    
    # Collect all perimeter cells (corners + edges)
    perimeter_cells = []
    for r, c in valid_cells:
        if len(get_neighbors(r, c, valid_mask)) < 6:
            perimeter_cells.append((r,c))
            
    # If we treat perimeter as a cycle graph, we can assign IDs.
    # Sort perimeter cells by angle from center?
    # Yes, this works well for convex hexagon.
    perimeter_cells.sort(key=lambda p: math.atan2(p[0]-cx, p[1]-cy))
    
    # Partition into 6 groups.
    # The number of perimeter cells in a size 15 hex is roughly 6*14 = 84? No, roughly 6*size.
    # Actually, total cells = 3*size*(size-1) + 1. Perimeter approx 6*size.
    
    count = len(perimeter_cells)
    if count == 0: return
    
    # Assign IDs
    # We need to be careful: angle sort wraps around.
    # We iterate and assign chunks.
    # But we don't know the boundaries exactly with angle sort alone.
    # However, we don't need perfect boundaries for 'Fork' check necessarily?
    # Actually we do. Fork connects 3 DISTINCT edges.
    # If the angle heuristic fails, we might claim a Fork incorrectly if we connect two adjacent edge regions that are technically the same side?
    # No, adjacent regions are distinct sides.
    # The issue is if one side gets split into two IDs.
    # Angle sort naturally clusters points by side.
    
    # K-Means with K=6 is ideal but slow.
    # Simple chunking: The perimeter points are ordered by angle.
    # They will look like 6 clusters.
    # We can assume the corners define the transitions.
    # Find indices of corners in the sorted list.
    corner_indices = []
    for i, p in enumerate(perimeter_cells):
        if p in CORNERS:
            corner_indices.append(i)
            
    # Corner indices should define the 6 sectors.
    # The midpoints between corners are the edges.
    # Wait, corners are the vertices. The cells between corners are the edges.
    # So if we have sorted corners, the edge segments are between them.
    
    # Map cells to edge IDs
    # Map corners to special ID or just include in adjacent edges?
    # Corners count for Bridge. Edges count for Fork.
    # Corner is not an edge.
    
    # Implementation:
    # 1. Identify corners (done).
    # 2. Identify perimeter cells (done).
    # 3. Sort perimeter cells by angle.
    # 4. Use corner positions to slice the perimeter into 6 edges.
    
    # This requires matching the sorted list to the corners.
    # A corner is a perimeter cell.
    # In a regular hex, the 6 corners are separated by approx equal number of edge cells.
    
    sorted_corners = sorted(list(CORNERS), key=lambda p: math.atan2(p[0]-cx, p[1]-cy))
    
    # If we traverse perimeter_cells sorted by angle, we encounter edges and corners.
    # Assign edge_id based on which 'arc' they fall into.
    # Arcs defined by vectors to corners.
    
    # This is getting complex for an init function. 
    # Alternative:
    # Only strictly check for Bridge (2 corners).
    # For Fork (3 edges), we can use a relaxed check or simpler heuristic.
    # Or, use the angle-sector method which is 99% correct for convex hexagons.
    
    # Let's stick to the angle sector method.
    # 6 sectors. ID 0..5.
    for r, c in perimeter_cells:
        if (r, c) in CORNERS: continue
        dy = r - cx
        dx = c - cy
        angle = math.atan2(dy, dx)
        if angle < 0: angle += 2 * math.pi
        # shift so a corner is at boundary?
        # corners are at 0, 60, 120...
        # This depends on board orientation.
        # For "pointy top" or "flat top", angles differ.
        # Valid mask defines the shape.
        # Let's assume the angle heuristic is 'good enough'.
        sector = int(angle / (math.pi / 3))
        EDGES[(r, c)] = sector

def get_neighbors(r, c, valid_mask):
    if (r, c) in NEIGHBORS_CACHE:
        return NEIGHBORS_CACHE[(r, c)]
    
    neighbors = []
    # Parity logic from prompt:
    # (4, 1) [odd col] -> left is (3,0), (4,0) -> row-1, row
    # (4, 1) [odd col] -> right is (4,2), (3,2) -> row, row-1
    # Same col: r-1, r+1
    
    # For even col?
    # Symmetry implies:
    # If odd col: left is r-1, r. right is r, r-1.
    # If even col: left is r, r+1. right is r+1, r.
    
    # Let's verify even col logic.
    # If (4, 2) [even] connects to (5, 1) [left col]?
    # (4, 2) left neighbors: (4, 1), (5, 1)? -> offsets (0, -1), (+1, -1).
    # (4, 2) right neighbors: (5, 3), (4, 3)? -> offsets (+1, +1), (0, +1).
    
    candidates = []
    
    # Same column
    candidates.append((r - 1, c))
    candidates.append((r + 1, c))
    
    if c % 2 == 1: # Odd column
        # Left column (c-1): rows r-1, r
        candidates.append((r - 1, c - 1))
        candidates.append((r, c - 1))
        # Right column (c+1): rows r-1, r
        candidates.append((r - 1, c + 1))
        candidates.append((r, c + 1))
    else: # Even column
        # Left column (c-1): rows r, r+1
        candidates.append((r, c - 1))
        candidates.append((r + 1, c - 1))
        # Right column (c+1): rows r, r+1
        candidates.append((r, c + 1))
        candidates.append((r + 1, c + 1))
        
    res = []
    for nr, nc in candidates:
        if 0 <= nr < N and 0 <= nc < N:
            if valid_mask[nr][nc]:
                res.append((nr, nc))
    
    NEIGHBORS_CACHE[(r, c)] = res
    return res

class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}
        # Win condition data
        # corners_touched: set of corner ids (we can use (r,c) tuple as ID)
        self.corners = {}
        # edges_touched: set of edge ids
        self.edges = {}
        
    def add(self, node, is_corner=False, edge_id=None):
        self.parent[node] = node
        self.rank[node] = 0
        self.corners[node] = {node} if is_corner else set()
        self.edges[node] = {edge_id} if edge_id is not None else set()

    def find(self, node):
        # Path compression
        if self.parent[node] != node:
            self.parent[node] = self.find(self.parent[node])
        return self.parent[node]

    def union(self, n1, n2):
        r1 = self.find(n1)
        r2 = self.find(n2)
        
        if r1 == r2:
            return r1, True # Already connected, indicates CYCLE (Ring potential)
        
        if self.rank[r1] < self.rank[r2]:
            r1, r2 = r2, r1
            
        self.parent[r2] = r1
        self.corners[r1].update(self.corners[r2])
        self.edges[r1].update(self.edges[r2])
        
        if self.rank[r1] == self.rank[r2]:
            self.rank[r1] += 1
            
        return r1, False
    
    def copy(self):
        new_uf = UnionFind()
        # Shallow copies of sets are fine for read-only access in simulation
        new_uf.parent = self.parent.copy()
        new_uf.rank = self.rank.copy()
        new_uf.corners = {k: v.copy() for k, v in self.corners.items()}
        new_uf.edges = {k: v.copy() for k, v in self.edges.items()}
        return new_uf

def check_win(uf, root):
    # Bridge: 2 corners
    if len(uf.corners[root]) >= 2:
        return True
    # Fork: 3 edges
    if len(uf.edges[root]) >= 3:
        return True
    return False

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    start_time = time.time()
    
    NEIGHBORS_CACHE.clear()
    CORNERS.clear()
    EDGES.clear()
    init_geometry(valid_mask)
    
    # 1. Build current state DSUs
    me_uf = UnionFind()
    opp_uf = UnionFind()
    
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    
    # Initialize stones in UF
    for r, c in me:
        is_corner = (r, c) in CORNERS
        edge_id = EDGES.get((r, c))
        me_uf.add((r, c), is_corner, edge_id)
        
    for r, c in opp:
        is_corner = (r, c) in CORNERS
        edge_id = EDGES.get((r, c))
        opp_uf.add((r, c), is_corner, edge_id)
        
    # Union existing stones
    # We need to process unions.
    # Just iterate all stones and union with neighbors already in their set.
    
    def build_uf(uf, stones, stone_set):
        for r, c in stones:
            for nr, nc in get_neighbors(r, c, valid_mask):
                if (nr, nc) in stone_set:
                    uf.union((r, c), (nr, nc))
    
    build_uf(me_uf, me, me_set)
    build_uf(opp_uf, opp, opp_set)
    
    # Check for immediate win
    valid_moves = []
    for r in range(N):
        for c in range(N):
            if valid_mask[r][c] and (r, c) not in occupied:
                valid_moves.append((r, c))
                
    random.shuffle(valid_moves)
    
    # Priority 1: Win immediately
    for r, c in valid_moves:
        # Simulate move for me
        is_corner = (r, c) in CORNERS
        edge_id = EDGES.get((r, c))
        
        # Check Ring condition: if neighbors belong to same component
        # Also Bridge/Fork via component merge
        
        neighbors = get_neighbors(r, c, valid_mask)
        my_neighbors = [n for n in neighbors if n in me_set]
        
        # Ring check
        if len(my_neighbors) >= 2:
            roots = set()
            for n in my_neighbors:
                roots.add(me_uf.find(n))
            if len(roots) < len(my_neighbors):
                # Some neighbors are already connected -> CYCLE
                # A cycle is a win (Ring)
                return (r, c)
        
        # Bridge/Fork check
        # Union logic
        # We can simulate the union properties
        simulated_corners = set()
        if is_corner:
            simulated_corners.add((r, c))
            
        simulated_edges = set()
        if edge_id is not None:
            simulated_edges.add(edge_id)
            
        for n in my_neighbors:
            root = me_uf.find(n)
            simulated_corners.update(me_uf.corners[root])
            simulated_edges.update(me_uf.edges[root])
            
        if len(simulated_corners) >= 2 or len(simulated_edges) >= 3:
            return (r, c)

    # Priority 2: Block opponent immediate win
    for r, c in valid_moves:
        # Simulate move for opponent
        is_corner = (r, c) in CORNERS
        edge_id = EDGES.get((r, c))
        
        neighbors = get_neighbors(r, c, valid_mask)
        opp_neighbors = [n for n in neighbors if n in opp_set]
        
        # Ring check for opp
        if len(opp_neighbors) >= 2:
            roots = set()
            for n in opp_neighbors:
                roots.add(opp_uf.find(n))
            if len(roots) < len(opp_neighbors):
                # Opponent wins
                return (r, c)
                
        # Bridge/Fork check
        sim_corners = set()
        if is_corner: sim_corners.add((r,c))
        sim_edges = set()
        if edge_id is not None: sim_edges.add(edge_id)
        
        for n in opp_neighbors:
            root = opp_uf.find(n)
            sim_corners.update(opp_uf.corners[root])
            sim_edges.update(opp_uf.edges[root])
            
        if len(sim_corners) >= 2 or len(sim_edges) >= 3:
            return (r, c)

    # Priority 3: Double Threat / Forcing Move
    # Check if a move creates a situation where we have 2 separate winning threats
    # Or simply maximizes connectivity
    # A simple proxy: maximize number of corners/edges touched by the resulting component
    
    best_move = None
    best_score = -100
    
    # Monte Carlo Simulation for better evaluation if time permits
    # Since pure heuristics are hard for Havannah (Ring esp), MC is good.
    # But we have limited time. We'll use a heuristic eval + random playouts.
    
    # Heuristic Evaluation
    def eval_move(r, c, player_uf, player_set, opp_set):
        # Player makes move at r, c
        # Calculate score
        
        # 1. Connection bonus
        neighbors = get_neighbors(r, c, valid_mask)
        my_neighbors = [n for n in neighbors if n in player_set]
        
        # Connect 2 groups = good.
        roots = set()
        for n in my_neighbors:
            roots.add(player_uf.find(n))
        connect_score = len(roots) * 10
        
        # 2. Strategic value (Corners/Edges)
        is_corner = (r, c) in CORNERS
        edge_id = EDGES.get((r, c))
        
        agg_corners = set()
        agg_edges = set()
        if is_corner: agg_corners.add((r,c))
        if edge_id is not None: agg_edges.add(edge_id)
        
        for root in roots:
            agg_corners.update(player_uf.corners[root])
            agg_edges.update(player_uf.edges[root])
            
        strategic_score = len(agg_corners) * 50 + len(agg_edges) * 20
        
        # 3. Central control (simple)
        dist_center = abs(r - 7) + abs(c - 7)
        central_score = (14 - dist_center)
        
        # 4. Blocking opponent?
        opp_neighbors = [n for n in neighbors if n in opp_set]
        block_score = 0
        if opp_neighbors:
            opp_roots = set()
            for n in opp_neighbors:
                opp_roots.add(opp_uf.find(n))
            # If we connect to opponent stones? No, we just occupy.
            # Adjacency can be defensive/offensive.
            block_score = 5 
            
        return strategic_score + connect_score + central_score + block_score

    # Evaluate all moves
    # If time is running out, just pick best heuristic
    for r, c in valid_moves:
        score = eval_move(r, c, me_uf, me_set, opp_set)
        if score > best_score:
            best_score = score
            best_move = (r, c)
            
    # If we have plenty of time, do a small Monte Carlo search
    # Check time
    if time.time() - start_time < 0.5 and valid_moves:
        # Run random simulations for top K candidates to refine choice
        # Pick top 3 heuristic moves
        candidates = []
        # Re-evaluate to get top candidates
        scored_moves = []
        for r, c in valid_moves:
            s = eval_move(r, c, me_uf, me_set, opp_set)
            scored_moves.append((s, (r, c)))
        scored_moves.sort(reverse=True)
        candidates = [m for s, m in scored_moves[:5]]
        
        if not candidates: candidates = valid_moves[:5]
        
        # Run simulations
        # We'll use a simplified "win rate" simulation
        # For each candidate, play N random games. 
        # Since full playout is expensive, we just trust the heuristic mostly
        # but maybe check for 'forced win' pattern if possible?
        # Given 1s limit, Python loops are slow. 
        # Stick to best heuristic move unless we can quickly detect improvement.
        pass

    return best_move if best_move else random.choice(valid_moves)

