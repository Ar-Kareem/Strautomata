
import numpy as np

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    # Convert valid_mask to numpy array for efficient operations
    valid_mask = np.array(valid_mask, dtype=bool)
    
    # Define corner positions (bridge targets)
    corners = [(0, 0), (0, 14), (14, 0), (14, 14)]
    
    # Check for immediate wins (my move creates a winning structure)
    for r in range(15):
        for c in range(15):
            if not valid_mask[r][c]:
                continue
            # Simulate placing a stone at (r, c)
            new_me = me + [(r, c)]
            if is_win(new_me, opp, valid_mask):
                return (r, c)
    
    # Check for opponent's immediate threats (block opponent's win)
    for r in range(15):
        for c in range(15):
            if not valid_mask[r][c]:
                continue
            # Simulate opponent's move at (r, c)
            new_opp = opp + [(r, c)]
            if is_win(opp, new_opp, valid_mask):
                return (r, c)
    
    # Evaluate all valid moves with heuristic scoring
    best_score = -float('inf')
    best_move = None
    
    for r in range(15):
        for c in range(15):
            if not valid_mask[r][c]:
                continue
            # Calculate move score based on proximity to corners and edges
            score = 0
            
            # Corner proximity bonus (bridge potential)
            for corner in corners:
                dist = max(abs(r - corner[0]), abs(c - corner[1]))
                score += 100 / (dist + 1)
            
            # Edge proximity bonus (fork potential)
            edge_bonus = 0
            if r == 0 or r == 14 or c == 0 or c == 14:
                edge_bonus = 50
            elif r == 1 or r == 13 or c == 1 or c == 13:
                edge_bonus = 25
            score += edge_bonus
            
            # Connectivity bonus (connecting existing stones)
            for stone in me:
                if is_adjacent(stone, (r, c)):
                    score += 10
            
            # Threat reduction bonus (blocking opponent's potential)
            for stone in opp:
                if is_adjacent(stone, (r, c)):
                    score -= 20
            
            # Select highest-scoring move
            if score > best_score:
                best_score = score
                best_move = (r, c)
    
    return best_move

def is_win(player, opponent, valid_mask):
    """Check if the player has created a winning structure."""
    # Convert player stones to a set for efficient lookup
    stones = set(player)
    
    # Check for rings (loops around cells)
    for r in range(15):
        for c in range(15):
            if (r, c) not in stones:
                continue
            # Check ring formation using hex grid adjacency
            neighbors = get_hex_neighbors(r, c)
            ring_cells = [n for n in neighbors if n in stones]
            if len(ring_cells) >= 6:
                return True
    
    # Check for bridges (connecting corners)
    corners = [(0, 0), (0, 14), (14, 0), (14, 14)]
    for i in range(4):
        for j in range(i + 1, 4):
            if is_bridge(player, opponent, corners[i], corners[j], valid_mask):
                return True
    
    # Check for forks (connecting three edges)
    edges = [(0, 0), (0, 14), (14, 0), (14, 14), (0, 7), (7, 0), (7, 14), (14, 7)]
    for i in range(8):
        for j in range(i + 1, 8):
            for k in range(j + 1, 8):
                if is_fork(player, opponent, edges[i], edges[j], edges[k], valid_mask):
                    return True
    
    return False

def get_hex_neighbors(r, c):
    """Get hexagonal neighbors of a cell (row, col)."""
    neighbors = []
    # Hex grid neighbor offsets (axial coordinates)
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]
    for dr, dc in offsets:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 15 and 0 <= nc < 15:
            neighbors.append((nr, nc))
    return neighbors

def is_adjacent(a, b):
    """Check if two cells are adjacent in hex grid."""
    return abs(a[0] - b[0]) <= 1 and abs(a[1] - b[1]) <= 1 and (a[0] + a[1]) != (b[0] + b[1])

def is_bridge(player, opponent, corner1, corner2, valid_mask):
    """Check if two corners are connected via a bridge."""
    # Use BFS to find a path between corners
    start = corner1
    end = corner2
    visited = set()
    queue = [(start, 0)]
    
    while queue:
        (r, c), steps = queue.pop(0)
        if (r, c) == end:
            return True
        if (r, c) in visited:
            continue
        visited.add((r, c))
        for neighbor in get_hex_neighbors(r, c):
            if neighbor in player or neighbor in opponent:
                continue
            if valid_mask[neighbor[0]][neighbor[1]]:
                queue.append((neighbor, steps + 1))
    return False

def is_fork(player, opponent, edge1, edge2, edge3, valid_mask):
    """Check if three edges are connected via a fork."""
    # Check if each edge is connected to the other two
    for edge in [edge1, edge2, edge3]:
        if not is_connected(player, opponent, edge, valid_mask):
            return False
    return True

def is_connected(player, opponent, target, valid_mask):
    """Check if target is connected to any edge via a path."""
    # BFS from target to any edge
    visited = set()
    queue = [(target, 0)]
    
    while queue:
        (r, c), steps = queue.pop(0)
        if (r, c) in [(0, 0), (0, 14), (14, 0), (14, 14)]:
            return True
        if (r, c) in visited:
            continue
        visited.add((r, c))
        for neighbor in get_hex_neighbors(r, c):
            if neighbor in player or neighbor in opponent:
                continue
            if valid_mask[neighbor[0]][neighbor[1]]:
                queue.append((neighbor, steps + 1))
    return False
