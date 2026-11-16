
import random

# Hexagonal neighbor directions based on the provided example:
# (r-1, c), (r+1, c), (r, c-1), (r-1, c-1), (r, c+1), (r-1, c+1)
NEIGHBORS = [(-1, 0), (1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1)]

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    N = 15
    
    # Convert valid mask to a set of coordinates for O(1) lookups
    valid_set = {(r, c) for r in range(N) for c in range(N) if valid_mask[r][c]}
    
    my_stones = set(me)
    opp_stones = set(opp)
    
    # --- Precompute Board Topology ---
    # We identify corners and edges once per turn (or could be cached, but fast enough)
    corners = set()
    # Map from cell to set of edge indices it belongs to
    cell_edges = {} 
    # Precompute neighbors for all valid cells
    neighbors_map = {}
    
    for r, c in valid_set:
        nbs = []
        for i, (dr, dc) in enumerate(NEIGHBORS):
            nr, nc = r + dr, c + dc
            if (nr, nc) in valid_set:
                nbs.append((nr, nc))
        
        neighbors_map[(r, c)] = nbs
        
        # Identify edges: A cell is on an edge if a neighbor is missing in that direction
        missing_dirs = []
        for i, (dr, dc) in enumerate(NEIGHBORS):
            nr, nc = r + dr, c + dc
            if (nr, nc) not in valid_set:
                missing_dirs.append(i)
        
        # Corners are cells with exactly 2 neighbors (in a standard hexagon)
        if len(nbs) == 2:
            corners.add((r, c))
        # Edge cells (non-corner) usually have 4 neighbors in a hexagon board
        # We assume valid_mask represents a standard hexagon
        elif len(nbs) == 4:
            # Store edge membership. 
            # Prompt: "corner points are not considered parts of an edge"
            cell_edges[(r, c)] = set(missing_dirs)
            
    valid_moves = list(valid_set - my_stones - opp_stones)
    if not valid_moves:
        # Should not happen in a normal game, but safe fallback
        return (-1, -1) 

    # --- Helper: Check Win Condition ---
    def check_win(candidate_move, player_stones):
        # Add move temporarily
        player_stones.add(candidate_move)
        
        # Find connected component containing the new stone
        stack = [candidate_move]
        visited = set()
        component = set()
        
        while stack:
            curr = stack.pop()
            if curr in visited:
                continue
            visited.add(curr)
            component.add(curr)
            
            for nb in neighbors_map[curr]:
                if nb in player_stones:
                    stack.append(nb)
        
        # 1. Check Ring (Cycle)
        # Perform DFS on the component to detect cycles
        has_cycle = False
        if component:
            cycle_stack = [(candidate_move, None)]
            cycle_visited = set()
            while cycle_stack:
                node, parent = cycle_stack.pop()
                if node in cycle_visited:
                    has_cycle = True
                    break
                cycle_visited.add(node)
                for nb in neighbors_map[node]:
                    if nb in player_stones and nb != parent:
                        cycle_stack.append((nb, node))
        
        # 2. Check Bridge
        # Connects at least two corners
        is_bridge = len(component & corners) >= 2
        
        # 3. Check Fork
        # Connects at least three edges (corners do not count)
        touched_edges = set()
        for stone in component:
            if stone in cell_edges:
                touched_edges.update(cell_edges[stone])
        is_fork = len(touched_edges) >= 3
        
        # Remove move (backtrack)
        player_stones.remove(candidate_move)
        
        return has_cycle or is_bridge or is_fork

    # --- 1. Check for Immediate Win ---
    # Shuffle to add variety if multiple wins exist
    random.shuffle(valid_moves)
    for mv in valid_moves:
        if check_win(mv, my_stones):
            return mv

    # --- 2. Check for Opponent Threats (Block) ---
    for mv in valid_moves:
        if check_win(mv, opp_stones):
            return mv

    # --- 3. Heuristic Strategy ---
    best_score = -float('inf')
    best_move = None
    center_r, center_c = 7, 7

    for mv in valid_moves:
        r, c = mv
        score = 0
        
        # Centrality: Prefer moves near the center
        dist = abs(r - center_r) + abs(c - center_c)
        score += (14 - dist) * 5
        
        # Connectivity: Prefer connecting to my own stones
        friendly_adj = 0
        enemy_adj = 0
        for nb in neighbors_map[mv]:
            if nb in my_stones:
                friendly_adj += 1
            elif nb in opp_stones:
                enemy_adj += 1
        
        score += friendly_adj * 10
        
        # Defense: Slight bonus for being adjacent to opponent (block potential)
        score += enemy_adj * 2
        
        # Random noise to break ties and vary play
        score += random.random() * 0.5
        
        if score > best_score:
            best_score = score
            best_move = mv

    return best_move
