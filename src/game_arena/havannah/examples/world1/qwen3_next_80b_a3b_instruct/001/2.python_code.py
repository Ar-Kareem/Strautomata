
import numpy as np
from collections import deque

# Define the six corners
CORNERS = [(0, 0), (0, 14), (14, 0), (14, 14), (7, 0), (7, 14)]

# Define the six edge segments (excluding corners)
EDGES = [
    # North: row 0, col 1 to 13
    {(0, c) for c in range(1, 14)},
    # Northeast top: col 14, row 1 to 6
    {(r, 14) for r in range(1, 7)},
    # Southeast: col 14, row 8 to 13
    {(r, 14) for r in range(8, 14)},
    # South: row 14, col 1 to 13
    {(14, c) for c in range(1, 14)},
    # Southwest: col 0, row 8 to 13
    {(r, 0) for r in range(8, 14)},
    # Northwest: col 0, row 1 to 6
    {(r, 0) for r in range(1, 7)}
]

# Define the six neighbor offsets in hex grid: row, col
# According to the example: (r-1, c-1), (r-1, c), (r, c-1), (r, c+1), (r+1, c-1), (r+1, c)
NEIGHBORS = [
    (-1, -1), (-1, 0),
    (0, -1),  (0, 1),
    (1, -1),  (1, 0)
]

def get_neighbors(r, c):
    """Return the six neighbor coordinates of (r, c)."""
    return [(r + dr, c + dc) for dr, dc in NEIGHBORS]

def is_on_board(r, c):
    """Check if (r, c) is within the 15x15 board."""
    return 0 <= r < 15 and 0 <= c < 15

def check_bridge(player_stones, corners):
    """Check if the player has a path connecting any two of the six corners."""
    stone_set = set(player_stones)
    visited = set()
    # For each corner, try to find a path to another corner
    for start in corners:
        if start not in stone_set:
            continue
        if start in visited:
            continue
        queue = deque([start])
        visited_component = set([start])
        while queue:
            r, c = queue.popleft()
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in stone_set and (nr, nc) not in visited_component:
                    if (nr, nc) in corners:
                        return True  # found connection to another corner
                    visited_component.add((nr, nc))
                    queue.append((nr, nc))
        # mark entire connected component as visited
        visited.update(visited_component)
    return False

def check_fork(player_stones, edges):
    """Check if the player has stones connected to three different edges."""
    stone_set = set(player_stones)
    visited = set()
    edge_touches = set()  # set of edge indices that are touched
    
    for i, edge in enumerate(edges):
        # check if any stone in this edge is in player's stones
        for cell in edge:
            if cell in stone_set:
                edge_touches.add(i)
                break
    
    if len(edge_touches) >= 3:
        # But we need to check connectivity — stones on three edges must be connected!
        # Use BFS from each edge cell to see if they are in the same component
        components = []
        visited_global = set()
        
        for cell in stone_set:
            if cell in visited_global:
                continue
            component = set()
            queue = deque([cell])
            visited_global.add(cell)
            component.add(cell)
            while queue:
                r, c = queue.popleft()
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in stone_set and (nr, nc) not in visited_global:
                        visited_global.add((nr, nc))
                        component.add((nr, nc))
                        queue.append((nr, nc))
            components.append(component)
        
        # For each component, check how many different edges it touches
        for comp in components:
            touched_edges = set()
            for cell in comp:
                for i, edge in enumerate(edges):
                    if cell in edge:
                        touched_edges.add(i)
            if len(touched_edges) >= 3:
                return True
                
    return False

def find_cycle_bfs(player_stones):
    """Check for any ring (cycle in the graph)."""
    if len(player_stones) < 5:
        return False  # minimum 5 stones for cycle in hex grid
    stone_set = set(player_stones)
    visited = set()
    
    for start in player_stones:
        if start in visited:
            continue
        # BFS with parent tracking to detect cycle
        queue = deque([(start, None)])  # (node, parent)
        visited_component = set([start])
        
        while queue:
            node, parent = queue.popleft()
            r, c = node
            for neighbor in get_neighbors(r, c):
                if neighbor not in stone_set:
                    continue
                if neighbor == parent:
                    continue
                if neighbor in visited_component:
                    # found a cycle
                    return True
                visited_component.add(neighbor)
                queue.append((neighbor, node))
        
        visited.update(visited_component)
    
    return False

def has_winning_move(stones, edges, corners):
    """Check if stones can win immediately with a single move (bridge, fork, ring)."""
    # First, check ring: any cycle? (if we are about to form one)
    if find_cycle_bfs(stones):
        return True
    
    if check_bridge(stones, corners):
        return True
    
    if check_fork(stones, edges):
        return True
    
    return False

def heuristic_score(r, c, me_set, opp_set, edges, corners):
    """Compute a heuristic score for move (r,c)."""
    score = 0.0

    # Center bonus
    if r == 7 and c == 7:
        score += 50
    
    # Edge bonus
    for edge_set in edges:
        if (r, c) in edge_set:
            score += 25
            break
    
    # Neighbor bonuses
    own_neighbors = 0
    opp_neighbors = 0
    for nr, nc in get_neighbors(r, c):
        if is_on_board(nr, nc):
            if (nr, nc) in me_set:
                own_neighbors += 1
            elif (nr, nc) in opp_set:
                opp_neighbors += 1
    
    score += own_neighbors * 10
    score += opp_neighbors * 5  # blocking or threatening
    
    # Connectivity bonus: measure closeness to existing components
    # Count how many groups in me_set this stone can connect to?
    me_graph = me_set | {(r, c)}
    components = []
    visited = set()
    for cell in me_graph:
        if cell in visited:
            continue
        component = set()
        queue = deque([cell])
        visited.add(cell)
        component.add(cell)
        while queue:
            cr, cc = queue.popleft()
            for nr, nc in get_neighbors(cr, cc):
                if (nr, nc) in me_graph and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    component.add((nr, nc))
                    queue.append((nr, nc))
        components.append(component)
    
    # The new stone can potentially connect components
    if len(components) == 1:  # it's connected to an existing group
        score += 20
    elif len(components) > 1:
        # isolating? But it connected multiple? Then it connected them.
        # We added one stone that connected multiple components? But we built components including the new stone.
        # Actually, if it connects 2 or more components, score bonus
        connected_components = set()
        for cell in me_graph:
            for comp in components:
                if cell in comp:
                    connected_components.add(id(comp))
        # This is messy; we'll instead use the size of the largest component
        sizes = [len(comp) for comp in components]
        biggest = max(sizes)
        score += max(0, biggest - 1) * 2  # bonus for large groups
    
    return score

def find_opponent_winning_move(me_set, opp_set, edges, corners, valid_mask):
    """Find if there is any unoccupied cell that, if played by opponent, would win."""
    for r in range(15):
        for c in range(15):
            if not valid_mask[r][c] or (r, c) in me_set or (r, c) in opp_set:
                continue
            # Simulate opponent playing here
            opp_with_move = opp_set | {(r, c)}
            if has_winning_move(opp_with_move, edges, corners):
                return (r, c)
    return None

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    
    valid_moves = []
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c] and (r, c) not in occupied:
                valid_moves.append((r, c))
    
    # Check for immediate win moves
    for r, c in valid_moves:
        me_with_move = me_set | {(r, c)}
        if has_winning_move(me_with_move, EDGES, CORNERS):
            return (r, c)
    
    # Check for opponent immediate win and block it
    block_move = find_opponent_winning_move(me_set, opp_set, EDGES, CORNERS, valid_mask)
    if block_move is not None:
        return block_move
    
    # If no immediate threats, use heuristic to choose best move
    best_move = None
    best_score = -1e9
    
    for r, c in valid_moves:
        score = heuristic_score(r, c, me_set, opp_set, EDGES, CORNERS)
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    # If for some reason no move scored, pick any valid move
    if best_move is None:
        best_move = valid_moves[0] if valid_moves else (0, 0)
    
    return best_move
