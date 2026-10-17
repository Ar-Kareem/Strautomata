
import numpy as np
from collections import deque

def get_neighbors(row, col, size=15):
    """Get valid neighboring hexagonal cells for a given cell on the board."""
    neighbors = []
    # Same row neighbors
    if col > 0:
        neighbors.append((row, col - 1))
    if col < size - 1:
        neighbors.append((row, col + 1))
        
    # Upper row neighbors
    if row > 0:
        neighbors.append((row - 1, col))
        if col > 0:
            neighbors.append((row - 1, col - 1))
            
    # Lower row neighbors
    if row < size - 1:
        neighbors.append((row + 1, col))
        if col < size - 1:
            neighbors.append((row + 1, col + 1))
            
    return neighbors

def bfs_connected_component(start, player_stones_set, size=15):
    """Find all stones connected to start using BFS."""
    visited = set()
    queue = deque([start])
    component = []
    
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        component.append(node)
        
        for neighbor in get_neighbors(node[0], node[1], size):
            if neighbor in player_stones_set and neighbor not in visited:
                queue.append(neighbor)
                
    return component

def find_connected_components(stones, size=15):
    """Find all connected components for a player."""
    stones_set = set(stones)
    components = []
    visited = set()
    
    for stone in stones:
        if stone not in visited:
            component = bfs_connected_component(stone, stones_set, size)
            components.append(component)
            visited.update(component)
            
    return components

def is_corner(row, col, size=15):
    """Check if a position is a corner of the Havannah board."""
    return (row == 0 and col == 0) or \
           (row == 0 and col == size-1) or \
           (row == size-1 and col == 0) or \
           (row == size-1 and col == size-1) or \
           (row == (size-1)//2 and col == 0) or \
           (row == (size-1)//2 and col == size-1)

def is_edge(row, col, size=15):
    """Check if a position is on an edge (but not a corner)."""
    if is_corner(row, col, size):
        return False
    return row == 0 or col == 0 or row == size-1 or col == size-1 or \
           (row == col) or (row + col == size - 1)

def count_corners_occupied(component):
    """Count how many corners are occupied by a component."""
    count = 0
    for r, c in component:
        if is_corner(r, c):
            count += 1
    return count

def count_edges_touched(component):
    """Count distinct edges touched by a component (excluding corners)."""
    edges = set()
    for r, c in component:
        if is_edge(r, c):
            # Classify which edge this point belongs to
            # We'll use a simple classification:
            # Edge 0: top (row=0, not corners)
            # Edge 1: bottom (row=size-1, not corners)
            # Edge 2: left (col=0, not corners)
            # Edge 3: right (col=size-1, not corners)
            # Edge 4: diagonal from top-left to bottom-right
            # Edge 5: diagonal from top-right to bottom-left
            if r == 0 and not is_corner(r, c):
                edges.add(0)
            elif r == 14 and not is_corner(r, c):
                edges.add(1)
            elif c == 0 and not is_corner(r, c):
                edges.add(2)
            elif c == 14 and not is_corner(r, c):
                edges.add(3)
            elif r == c and not is_corner(r, c):
                edges.add(4)
            elif r + c == 14 and not is_corner(r, c):
                edges.add(5)
    return len(edges)

def evaluate_move(move, me, opp, valid_mask):
    """Evaluate the potential value of a move."""
    row, col = move
    new_me = me + [move]
    
    # Check if this move wins
    me_components = find_connected_components(new_me)
    for comp in me_components:
        # Check for ring (simplified: at least 6 stones and encircles something)
        if len(comp) >= 6:
            # Simplified ring detection
            pass  # Full implementation would be more complex
        
        # Check for bridge (connecting two corners)
        corners = count_corners_occupied(comp)
        if corners >= 2:
            return 10000  # Bridge win
            
        # Check for fork (touching 3 edges)
        edges = count_edges_touched(comp)
        if edges >= 3:
            return 10000  # Fork win
    
    # Otherwise, evaluate strategically
    score = 0
    
    # 1. Try to connect own groups
    connected_groups = 0
    for r, c in get_neighbors(row, col):
        if (r, c) in me:
            connected_groups += 1
    score += connected_groups * 10
    
    # 2. Block opponent's potential winning moves
    opp_components = find_connected_components(opp)
    block_score = 0
    for comp in opp_components:
        # If opponent is close to winning, try to block
        corners = count_corners_occupied(comp)
        edges = count_edges_touched(comp)
        if corners >= 1 or edges >= 2:
            # Check if our move can block this component
            for r, c in get_neighbors(row, col):
                if (r, c) in comp:
                    block_score += 50
    score += block_score
    
    # 3. Control center (position value)
    center_row, center_col = 7, 7
    distance_to_center = abs(row - center_row) + abs(col - center_col)
    score += (14 - distance_to_center)  # Prefer center positions
    
    # 4. Avoid isolated moves unless connecting is impossible
    if connected_groups == 0:
        # Check if it connects to any existing stone at all
        any_connection = False
        for r, c in get_neighbors(row, col):
            if (r, c) in me or (r, c) in opp:
                any_connection = True
                break
        if not any_connection:
            score -= 5  # Slight penalty for completely isolated moves
            
    return score

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    # If it's the first move, play in the center
    if not me and not opp:
        return (7, 7)
        
    # Get all valid moves
    valid_moves = [(i, j) for i in range(15) for j in range(15) if valid_mask[i][j]]
    
    # If only one valid move, take it
    if len(valid_moves) == 1:
        return valid_moves[0]
    
    # Evaluate each valid move
    best_move = valid_moves[0]
    best_score = float('-inf')
    
    for move in valid_moves[:min(20, len(valid_moves))]:  # Limit search for performance
        score = evaluate_move(move, me, opp, valid_mask)
        if score > best_score:
            best_score = score
            best_move = move
            
    return best_move
