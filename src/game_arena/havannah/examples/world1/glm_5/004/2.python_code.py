
import numpy as np
from collections import deque

# Constants
BOARD_SIZE = 15
EMPTY = 0
ME = 1
OPP = 2

# Global caches for performance
_neighbors_cache = {}
_geometry_cache = {}

def get_neighbors(r, c):
    if (r, c) in _neighbors_cache:
        return _neighbors_cache[(r, c)]
    
    # Hex grid neighbors based on prompt description
    # Even rows: neighbors shift "up" visually in left/right columns relative to prompt mapping?
    # Prompt: (4,1) touches (3,0), (4,0) [Left] and (3,2), (4,2) [Right]
    # (4,1) is row 4 (even).
    # Left: (r-1, c-1), (r, c-1).
    # Right: (r-1, c+1), (r, c+1).
    # Vertical: (r-1, c), (r+1, c).
    
    # Odd rows (e.g. r=3):
    # Symmetry implies: 
    # Left: (r, c-1), (r+1, c-1).
    # Right: (r, c+1), (r+1, c+1).
    
    if r % 2 == 0: # Even row
        offsets = [(-1, 0), (1, 0), (-1, -1), (0, -1), (-1, 1), (0, 1)]
    else: # Odd row
        offsets = [(-1, 0), (1, 0), (0, -1), (1, -1), (0, 1), (1, 1)]
        
    n = []
    for dr, dc in offsets:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            n.append((nr, nc))
    
    _neighbors_cache[(r, c)] = n
    return n

class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}
        # Metadata for win conditions
        # corners: set of corner indices connected (0-5)
        # edges: set of edge indices connected (0-5)
        self.corners = {}
        self.edges = {}
        self.size = {}

    def ensure(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
            self.corners[x] = set()
            self.edges[x] = set()
            self.size[x] = 1

    def find(self, x):
        self.ensure(x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y, corner_map, edge_map):
        # corner_map: node -> corner_index or None
        # edge_map: node -> edge_index or None
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return root_x

        if self.rank[root_x] < self.rank[root_y]:
            root_x, root_y = root_y, root_x

        self.parent[root_y] = root_x
        self.corners[root_x].update(self.corners[root_y])
        self.edges[root_x].update(self.edges[root_y])
        self.size[root_x] += self.size[root_y]
        
        if self.rank[root_x] == self.rank[root_y]:
            self.rank[root_x] += 1
        
        # Add current node metadata
        if x in corner_map: self.corners[root_x].add(corner_map[x])
        if y in corner_map: self.corners[root_x].add(corner_map[y])
        if x in edge_map: self.edges[root_x].add(edge_map[x])
        if y in edge_map: self.edges[root_x].add(edge_map[y])

        return root_x

    def get_data(self, x):
        root = self.find(x)
        return self.corners[root], self.edges[root], self.size[root]

def analyze_geometry(valid_mask):
    # We want to identify corners and edges.
    # Corners: Valid cells with 2 neighbors.
    # Edges: Valid cells with 3 or 4 neighbors.
    # Interior: 6 neighbors.
    
    # We also need to label edges 0-5 for Fork detection.
    # Strategy: BFS from corners along the boundary.
    
    valid_cells = zip(*np.where(valid_mask))
    corners = []
    edge_cells = set()
    
    # Identify corners and boundary cells
    for r, c in valid_cells:
        neighbors = [n for n in get_neighbors(r, c) if valid_mask[n]]
        deg = len(neighbors)
        if deg == 2:
            corners.append((r, c))
        elif deg < 6:
            edge_cells.add((r, c))
            
    # Sort corners to establish an order? 
    # Or just arbitrarily assign IDs 0-5.
    # We need to map corners to "Corner Pairs" for Bridge?
    # No, Bridge connects ANY two corners.
    # Fork connects ANY three edges.
    # But edges must be distinct.
    
    # Mapping cells to specific Edge Indices
    # We can traverse the perimeter.
    # But simpler: since the board topology is fixed (hexagon), we can check angle?
    # Or just BFS from corner to corner along edge_cells.
    
    # Map each corner to an ID
    corner_ids = {c: i for i, c in enumerate(corners)}
    
    # Map each edge cell to an Edge ID (0-5)
    # An edge is the set of boundary cells between corner K and corner K+1
    edge_ids = {}
    
    # Build adjacency for boundary traversal
    boundary_graph = {c: [] for c in edge_cells.union(set(corners))}
    for c in boundary_graph:
        for n in get_neighbors(c[0], c[1]):
            if n in boundary_graph:
                boundary_graph[c].append(n)

    # Traverse from each corner
    # Note: A corner connects two edges.
    # We define Edge K as the set of boundary nodes closer to Corner K's side?
    # Let's just propagate labels.
    # Start at Corner K, explore boundary neighbors that are not other corners.
    
    # Heuristic for edge ID based on position relative to center
    # This is risky if valid_mask is weird, but standard Havannah is hexagonal.
    # Let's use connectivity traversal.
    
    visited_edges = set()
    for start_corner in corners:
        cid = corner_ids[start_corner]
        # Explore neighbors on boundary
        q = deque([start_corner])
        # We don't label the corner as belonging to the edge segment exclusively, 
        # but the cells connected to it.
        # However, for fork detection, we just need to know if 3 distinct "sides" are connected.
        # We can treat each of the 6 sides as an index.
        
        # Let's try to map "Sides".
        # There are 6 sides.
        # Side 0 is between Corner 0 and 1? 
        pass

    # Alternative: Use coordinate heuristics to assign Side ID (0-5)
    # Assuming standard hexagon orientation (flat top/bottom or pointy?)
    # Prompt: (4,1) neighbors logic implies pointy top orientation?
    # Let's assign IDs based on local properties.
    # For simplicity, we define 6 edge zones.
    # Or simpler: Since we track Edge Sets in UnionFind, we just need to identify 
    # if two edge cells belong to the same "physical edge".
    # We can flood fill the boundary graph from corners.
    
    # Let's assign Edge IDs 0-5.
    # Traversal from corner i to corner (i+1)%6 is Edge i.
    # We need to find the ordering of corners.
    
    # Geometric sort of corners:
    # Center of mass
    if not corners: return {}, {}
    center = np.mean(corners, axis=0)
    # Sort by angle
    def angle(c):
        return np.arctan2(c[0] - center[0], c[1] - center[1])
    sorted_corners = sorted(corners, key=angle)
    # This gives a cyclic order.
    
    corner_id_map = {c: i for i, c in enumerate(sorted_corners)}
    
    # Assign Edge IDs
    # Edge i connects Corner i and Corner (i+1)%6
    # We perform BFS from Corner i along boundary, stopping at Corner (i+1)%6
    # All touched cells get Edge ID i.
    
    edge_id_map = {}
    
    for i in range(6):
        c_start = sorted_corners[i]
        c_end = sorted_corners[(i+1)%6]
        
        # BFS
        q = deque([c_start])
        visited = set()
        while q:
            curr = q.popleft()
            if curr == c_end: continue # Stop propagation past end corner? 
            # Actually corner belongs to two edges.
            # We only label non-corner edge cells.
            if curr in edge_id_map: continue # Already labeled
            
            if curr != c_start and curr in corner_id_map: continue # Hit another corner
            
            # Label
            if curr not in corner_id_map:
                edge_id_map[curr] = i
            
            for n in boundary_graph[curr]:
                if n not in visited:
                    visited.add(n)
                    q.append(n)
                    
    return corner_id_map, edge_id_map

def check_ring_creation(r, c, board, player):
    # A ring is formed if placing a stone at (r,c) completes a cycle 
    # that encloses at least one empty or opponent cell.
    # This happens if (r,c) connects to a friendly neighbor 'u' and another 'v'
    # such that u and v are in the same connected component, AND
    # the cycle formed encloses something.
    
    # Neighbors of same color
    my_stone = player
    opp_stone = 3 - player
    
    neighbors = get_neighbors(r, c)
    friendly_neighbors = [n for n in neighbors if board[n] == my_stone]
    
    # We need to check if connecting to existing components forms a ring.
    # Use a local UF or just trace?
    # If we connect two points u, v in the same component, we form a cycle.
    # Does that cycle enclose anything?
    # Enclosed check: Is there a neighbor of (r,c) that is "inside" the angle <u, r, v>?
    # And is that neighbor empty or opp?
    # Actually, simpler: 
    # If we join a component, does the new stone "wrap around" an opponent/empty cell?
    
    # Heuristic check for ring:
    # If we have >= 2 friendly neighbors.
    # If any two friendly neighbors are connected (same component), we form a cycle.
    # To verify if it's a Ring (winning condition):
    # The cycle must surround something.
    # In hex grids, small loops (lens) enclose cells.
    # If we connect two neighbors that are adjacent to each other in the grid:
    # e.g. we complete a triangle.
    # Does a triangle enclose anything? 
    # A triangle of stones in hex grid does NOT enclose a cell (cells are hexagons).
    # Minimal ring is a loop of 6 stones enclosing 1 cell.
    
    # Algorithm:
    # 1. Identify if (r,c) joins a component to itself (cycle).
    # 2. If so, identify the "interior" of this cycle.
    #    BFS on the "dual graph" or just checking neighbors of the cycle path.
    #    If the cycle encloses any Empty or Opp cell -> Win.
    
    # Optimization:
    # Since we only place ONE stone, the "hole" must be adjacent to (r,c) or enclosed by the path.
    # If the cycle surrounds (r,c)'s neighborhood, check neighbors of (r,c).
    # If any neighbor is Empty/Opp and is surrounded by the component, we win.
    
    # Fast check:
    # Flood fill from neighbors of (r,c) that are NOT my_stone.
    # Can they reach the boundary?
    # If NO, they are enclosed. We Win.
    
    # But we must ensure the enclosure is by the NEW configuration.
    # If a neighbor was already enclosed, we would have lost already?
    # No, enclosed regions only exist if we have a ring.
    # So if we create a cycle, we check isolation.
    
    # Temporarily place stone
    board[r, c] = my_stone
    
    # Check neighbors of (r,c) that are not my_stone
    candidates_to_check = []
    for n in neighbors:
        if board[n] != my_stone:
            candidates_to_check.append(n)
            
    # Also check cells "behind" neighbors?
    # Actually, if we complete a ring, the enclosed cells must be disconnected from boundary.
    
    # We check isolation of these candidates.
    # Optimization: Global check is expensive.
    # Local check: 
    # If we connect neighbors u and v, the boundary between u and v around r is closed.
    # The "arc" between u and v in the component forms the wall.
    # The "inside" is the neighbors of r between u and v.
    
    # For simplicity and correctness, we just run BFS for connectivity to boundary.
    # Boundary = any valid cell with neighbor count < 6 (edge/corner) OR any valid cell not enclosed.
    # Target: Can this cell reach any edge_cell on the board perimeter?
    
    perimeter_cells = set()
    # Find perimeter
    # This is slow to do inside the loop. 
    # But 'board' size is small.
    
    # Optimization: `valid_mask` boundary is constant.
    # We precompute boundary cells in analyze_geometry?
    # No, just check if a cell is on edge (neighbor count < 6).
    
    is_enclosed = False
    
    for start_r, start_c in candidates_to_check:
        # BFS
        q = deque([(start_r, start_c)])
        visited = {(start_r, start_c)}
        can_escape = False
        while q:
            cr, cc = q.popleft()
            # If this cell is an edge, it escapes
            n_neighs = len([x for x in get_neighbors(cr, cc) if board[x] != -1]) # valid check
            # Actually check valid_mask
            # valid_mask is global.
            # Here we assume board has -1 for invalid? No, valid_mask is separate.
            # We need valid_mask passed here.
            pass 
            # Check if edge
            # We need valid_mask here. Let's assume global access or pass it.
            # Since this function is inside policy, we use closure variables.
            # valid_mask is accessible in policy scope.
            
            # Check boundary status
            # If board[cr, cc] is on the edge of the valid_mask?
            # We use the logic: valid neighbors < 6
            is_boundary = False
            valid_n_count = 0
            for n in get_neighbors(cr, cc):
                # Check bounds and valid mask
                if 0 <= n[0] < BOARD_SIZE and 0 <= n[1] < BOARD_SIZE and valid_mask[n]:
                    valid_n_count += 1
            
            if valid_n_count < 6:
                can_escape = True
                break
            
            for nr, nc in get_neighbors(cr, cc):
                if (nr, nc) not in visited and board[nr, nc] != my_stone:
                    # Only traverse empty or opp stones
                    if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and valid_mask[nr, nc]:
                        visited.add((nr, nc))
                        q.append((nr, nc))
        
        if not can_escape:
            is_enclosed = True
            break
            
    # Revert stone
    board[r, c] = EMPTY
    return is_enclosed

def policy(me, opp, valid_mask):
    N = BOARD_SIZE
    board = np.zeros((N, N), dtype=int)
    # Fill board
    # 0 = Empty, 1 = Me, 2 = Opp
    # Mark invalid as -1?
    
    # Valid mask processing
    # valid_mask is (15, 15) boolean.
    
    # Precompute geometry if not cached
    # Use a hash of valid_mask? For now assume standard board.
    # For speed, we can compute once.
    if not _geometry_cache:
        _geometry_cache['corners'] = analyze_geometry(valid_mask)
    
    corner_id_map, edge_id_map = _geometry_cache['corners']
    
    # Populate board
    # Use -1 for invalid to help neighbor checks? 
    # No, we check valid_mask.
    
    # Set stones
    for r, c in me:
        board[r, c] = ME
    for r, c in opp:
        board[r, c] = OPP
        
    valid_moves = list(zip(*np.where(valid_mask)))
    
    # Helper to check win
    def check_move_win(r, c, player):
        # Place stone
        # Check Bridge: Connects 2 corners
        # Check Fork: Connects 3 edges
        # Check Ring: Encloses area
        
        my_stone = player
        
        # Fast checks using UnionFind simulation
        # We can't just use the main UF, we need a sim.
        # But for move ordering, we might check heuristics first.
        
        # BRIDGE / FORK CHECK
        # Identify corners/edges touched by this move
        touched_corners = set()
        touched_edges = set()
        
        if (r, c) in corner_id_map:
            touched_corners.add(corner_id_map[(r, c)])
        if (r, c) in edge_id_map:
            touched_edges.add(edge_id_map[(r, c)])
            
        # Check neighbors
        neighbors = get_neighbors(r, c)
        # In a real game, we'd update a global UF.
        # Here we check if neighbors belong to same groups.
        # We need a quick way to see "What groups do my neighbors belong to?"
        # And "What metadata do those groups have?"
        
        # Since we don't maintain a global UF across calls (stateless policy),
        # we must build it or simulate.
        # Building UF for every move is O(N). 225 ops. 
        # We have 100 valid moves -> 22500 ops. Very cheap.
        
        # Build UF for the prospective board state
        uf = UnionFind()
        
        # Add current stones
        current_stones = me if player == ME else opp
        for sr, sc in current_stones:
            uf.ensure((sr, sc))
            if (sr, sc) in corner_id_map: uf.corners[uf.find((sr, sc))].add(corner_id_map[(sr, sc)])
            if (sr, sc) in edge_id_map: uf.edges[uf.find((sr, sc))].add(edge_id_map[(sr, sc)])
            
        # Add new stone
        uf.ensure((r, c))
        if (r, c) in corner_id_map: uf.corners[uf.find((r, c))].add(corner_id_map[(r, c)])
        if (r, c) in edge_id_map: uf.edges[uf.find((r, c))].add(edge_id_map[(r, c)])
        
        # Unify
        for nr, nc in neighbors:
            if board[nr, nc] == my_stone:
                uf.union((r, c), (nr, nc), corner_id_map, edge_id_map)
        
        c_corners, c_edges, _ = uf.get_data((r, c))
        
        if len(c_corners) >= 2: return True # Bridge
        if len(c_edges) >= 3: return True # Fork
        
        # RING CHECK
        if check_ring_creation(r, c, board, player):
            return True
            
        return False

    # 1. Check for immediate win
    for r, c in valid_moves:
        if check_move_win(r, c, ME):
            return (r, c)
            
    # 2. Check for blocking opponent win
    threats = []
    for r, c in valid_moves:
        # Check if opponent plays here and wins
        # Temporarily switch perspective
        # We can reuse check_move_win with player=OPP
        # But we need to update board state temporarily or adapt check_move_win
        # check_move_win reads from 'board' and 'me'/'opp' lists.
        # It assumes 'player' places the stone.
        # Logic holds.
        if check_move_win(r, c, OPP):
            threats.append((r, c))
            
    if len(threats) == 1:
        return threats[0]
    if len(threats) > 1:
        # Multiple threats, likely losing. Pick one.
        # Could try to find a move that blocks multiple?
        # Or creates a threat of our own?
        # For now, pick first.
        return threats[0]

    # 3. Heuristic Search / Evaluation
    # Simple MC approach or Greedy?
    # Let's use a greedy heuristic based on "gains".
    
    best_score = -1e9
    best_move = valid_moves[0] # Default
    
    # Center preference
    center = (7, 7)
    
    for r, c in valid_moves:
        score = 0
        
        # Connectivity Score
        # Count friendly neighbors
        friendly_neighbors = 0
        empty_neighbors = 0
        for nr, nc in get_neighbors(r, c):
            if not (0 <= nr < N and 0 <= nc < N and valid_mask[nr, nc]): continue
            if board[nr, nc] == ME: friendly_neighbors += 1
            elif board[nr, nc] == EMPTY: empty_neighbors += 1
        
        score += friendly_neighbors * 10
        score += empty_neighbors * 2 # Openness
        
        # Positional Score
        # Distance to center
        dist = abs(r - center[0]) + abs(c - center[1])
        score += (15 - dist) * 2
        
        # Edge/Corner bonuses
        if (r, c) in corner_id_map:
            score += 50 # Corners are valuable for Bridges
        elif (r, c) in edge_id_map:
            score += 20 # Edges are valuable for Forks
            
        # Structure Bonus
        # If connecting two groups
        # Reuse UF logic? Too slow for every move loop inside a loop.
        # But we already iterated. We can cache UF structures? No.
        # Just approximate.
        # If friendly_neighbors >= 2, check if they are connected?
        # If not connected, we are joining groups. High value.
        # We need a cheap connectivity check.
        # Since we don't have a global UF, let's skip complex group merge scoring.
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
            
    return best_move
