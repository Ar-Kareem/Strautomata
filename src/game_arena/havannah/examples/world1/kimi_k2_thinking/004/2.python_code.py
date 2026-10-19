
import numpy as np
from collections import deque
import random

# Constants for a 15x15 Havannah board
BOARD_SIZE = 15

# Six corner positions of the hexagonal board
CORNERS = [(0, 0), (0, 14), (7, 14), (14, 14), (14, 0), (7, 0)]

def get_neighbors(r, c):
    """
    Get all valid neighboring cells for a hexagonal grid using odd-r offset coordinates.
    Neighbor pattern depends on whether the row is even or odd.
    """
    if r % 2 == 0:
        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1)]
    else:
        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1), (1, -1), (1, 1)]
    
    return [(r + dr, c + dc) for dr, dc in offsets 
            if 0 <= r + dr < BOARD_SIZE and 0 <= c + dc < BOARD_SIZE]

def bfs_component(start, stones_set):
    """
    Find all stones connected to 'start' using BFS.
    Returns a set of all stones in the same component.
    """
    if start not in stones_set:
        return set()
    
    component = {start}
    queue = deque([start])
    
    while queue:
        current = queue.popleft()
        for neighbor in get_neighbors(*current):
            if neighbor in stones_set and neighbor not in component:
                component.add(neighbor)
                queue.append(neighbor)
    
    return component

def distance(pos1, pos2):
    """
    Calculate hexagonal distance between two positions using axial coordinate conversion.
    Converts from odd-r offset to axial coordinates then computes cube distance.
    """
    r1, c1 = pos1
    r2, c2 = pos2
    
    # Convert offset to axial coordinates
    q1 = c1 - (r1 - (r1 & 1)) // 2
    q2 = c2 - (r2 - (r2 & 1)) // 2
    
    # Convert axial to cube coordinates
    x1, z1 = q1, r1
    x2, z2 = q2, r2
    y1, y2 = -x1 - z1, -x2 - z2
    
    # Manhattan distance in cube coordinates
    return (abs(x1 - x2) + abs(y1 - y2) + abs(z1 - z2)) // 2

def corners_touching(component):
    """
    Count how many distinct corners are adjacent to or part of the component.
    Used to evaluate bridge potential.
    """
    touched = 0
    for corner in CORNERS:
        for stone in component:
            if distance(stone, corner) <= 1:  # Directly adjacent or on corner
                touched += 1
                break
    return touched

def edges_touching(component):
    """
    Heuristic to count edges touched by the component for fork evaluation.
    Uses coordinate-based heuristics to detect proximity to the six edges.
    """
    edges = set()
    for r, c in component:
        # Top edge (row 0)
        if r == 0:
            edges.add(0)
        # Bottom edge (row 14)
        if r == BOARD_SIZE - 1:
            edges.add(3)
        # Left edge (column 0)
        if c == 0:
            edges.add(5)
        # Right edge (column 14)
        if c == BOARD_SIZE - 1:
            edges.add(1)
        # Bottom-left diagonal edge
        if r - c == 7:
            edges.add(4)
        # Bottom-right diagonal edge
        if r + c == 21:
            edges.add(2)
    return len(edges)

def evaluate_move(me, opp, move, valid_mask, move_num):
    """
    Heuristic evaluation of a potential move.
    Higher scores represent better moves.
    """
    r, c = move
    me_set = set(me)
    opp_set = set(opp)
    
    # Base score with small random tiebreaker
    score = random.random()
    
    # Analyze my component after playing this move
    new_me_set = me_set | {move}
    component = bfs_component(move, new_me_set)
    
    # 1. Connectivity value: larger components are stronger
    score += len(component) * 5
    
    # 2. Bridge potential: components touching 2+ corners are winning moves
    corners = corners_touching(component)
    if corners >= 2:
        score += 10000  # Massive bonus for winning bridge
    elif corners == 1:
        score += 50  # Encourage corner connections
    
    # 3. Fork potential: components touching 3+ edges are winning moves
    edges = edges_touching(component)
    if edges >= 3:
        score += 10000  # Massive bonus for winning fork
    elif edges >= 2:
        score += 40  # Encourage edge connections
    
    # 4. Blocking opponent's threats
    max_opp_corners = 0
    max_opp_edges = 0
    for nr, nc in get_neighbors(r, c):
        if (nr, nc) in opp_set:
            opp_component = bfs_component((nr, nc), opp_set)
            max_opp_corners = max(max_opp_corners, corners_touching(opp_component))
            max_opp_edges = max(max_opp_edges, edges_touching(opp_component))
    
    # High priority to block opponent's winning formations
    if max_opp_corners >= 2 or max_opp_edges >= 3:
        score += 9000
    
    # 5. Center control: central positions are valuable for ring formation
    center_dist = distance(move, (7, 7))
    score += max(0, 15 - center_dist) * 2
    
    # 6. Local density: prefer stones adjacent to existing stones
    my_neighbors = sum(1 for nr, nc in get_neighbors(r, c) if (nr, nc) in me_set)
    score += my_neighbors * 10
    
    # 7. Ring formation heuristic: well-surrounded stones likely form rings
    if my_neighbors >= 4:
        score += 200
    
    # 8. Early game penalty: avoid isolated moves
    if move_num < 40 and my_neighbors == 0:
        score -= 20
    
    return score

def policy(me, opp, valid_mask):
    """
    Main policy function: selects the best move using heuristic evaluation.
    """
    me_set = set(me)
    opp_set = set(opp)
    move_num = len(me) + len(opp)
    
    # Collect all valid and empty positions
    valid_moves = [(r, c) for r in range(BOARD_SIZE) 
                   for c in range(BOARD_SIZE) 
                   if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set]
    
    # Fallback: return first available cell if no valid moves found
    if not valid_moves:
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if valid_mask[r][c]:
                    return (r, c)
        return (7, 7)  # Center fallback
    
    # Evaluate all moves and return the best one
    return max(valid_moves, key=lambda m: evaluate_move(me, opp, m, valid_mask, move_num))
