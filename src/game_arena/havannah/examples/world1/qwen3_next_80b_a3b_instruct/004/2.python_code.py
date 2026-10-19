
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    # Convert to set for O(1) lookup
    me_set = set(me)
    opp_set = set(opp)
    board_size = 15
    
    # Define the 6 hexagonal neighbors for a cell (row, col)
    # In hex grid with axial-like coordinates, neighbors are:
    # (dr, dc): (0,1), (0,-1), (1,0), (1,-1), (-1,0), (-1,1)
    # But we map to 2D grid as described: 
    # Given (r, c), neighbors are:
    # (r, c+1), (r, c-1), (r+1, c), (r+1, c-1), (r-1, c), (r-1, c+1)
    # This aligns with the example: (4,1) -> (5,1), (3,1), (3,0), (4,0), (4,2), (3,2)
    neighbors = [
        (0, 1),   # right
        (0, -1),  # left
        (1, 0),   # down
        (1, -1),  # down-left
        (-1, 0),  # up
        (-1, 1)   # up-right
    ]
    
    def is_valid(r, c):
        return 0 <= r < board_size and 0 <= c < board_size
    
    def get_neighbors(r, c):
        nb = []
        for dr, dc in neighbors:
            nr, nc = r + dr, c + dc
            if is_valid(nr, nc):
                nb.append((nr, nc))
        return nb
    
    def is_corner(r, c):
        corners = [(0, 0), (0, 14), (7, 14), (14, 14), (14, 0), (7, 0)]
        return (r, c) in corners
    
    def is_edge(r, c):
        # Edges are boundaries excluding corners
        # Top edge: row=0, col 1-13
        # Bottom edge: row=14, col 1-13
        # Left edge: col=0, row 1-13 (excluding (7,0))
        # Right edge: col=14, row 1-13 (excluding (7,14))
        # Also, the two "diagonal" edges: top-right to bottom-left and top-left to bottom-right
        # But in this representation, the hex grid's "edges" are traditionally:
        # We consider the 6 sides of the hexagon. Since the board is a 15x15 grid in square form
        # representing a hex grid, the actual edges are:
        # We'll define 6 edges in the hex grid context:
        # 1. Top edge: row=0, all columns
        # 2. Bottom edge: row=14, all columns
        # 3. Top-right edge: cells where r + c == 14 (but we need to define as the hex diagonal)
        # 4. Bottom-right edge: c == 14, but not corner
        # 5. Bottom-left edge: r == 14 - c, etc.

        # Actually, given the square representation of hex grid, it's easier to use the following:
        # The six edges of the hexagonal board are defined as:
        # - Top: row == 0
        # - Bottom: row == 14
        # - Right: col == 14 and row >= 7? Not exactly.

        # Standard Havannah board: the six edge segments are:
        # 1. Top-left to Top-right: row=0, col from 0 to 14
        # 2. Top-right to Bottom-right: from (0,14) to (7,14), then (8,13) ... actually this doesn't align.
        
        # Due to the complexity, and the fact that the problem states: "corner points are not considered parts of an edge"
        # We define edges as the non-corner boundary segments:
        #   Edge 1: row=0, 1<=col<=13
        #   Edge 2: col=14, 1<=row<=13 and row !=7
        #   Edge 3: row=14, 1<=col<=13
        #   Edge 4: col=0, 1<=row<=13 and row !=7
        #   Edge 5: on the "right" diagonal: cells with r + c = 14, excluding corners (0,14), (14,0)
        #   Edge 6: on the "left" diagonal: cells with r == c, excluding corners (0,0), (14,14)

        # But the problem doesn't define these explicitly. Let's use the standard Havannah hex grid edge definition:
        # The six edges correspond to the six sides of the hexagon, which in our grid alignment are:
        # According to known Havannah rules: the edges are:
        # - Bottom: row=14 (cols 0-14)
        # - Top: row=0 (cols 0-14)
        # - Right: line from (0,14) to (7,14) and then down to (14,0) ? No.

        # Actually, in the standard 15-cell-per-side hex grid, the board has 15 cells per side.
        # The square grid representation maps the hex grid such that:
        # The top edge: row=0
        # The bottom edge: row=14
        # The top-right edge: col=14 for rows 0 to 7, and row=14-col for rows 8 to 14? This is complex.

        # Given the example correlation: (4,1) touches (3,0) meaning left-up, and (4,2) meaning right-up,
        # it seems the grid is arranged so that the board is diamond-shaped.
        # The six edges are:
        # 1. Top: row=0
        # 2. Top-right: col=14 for row in [0,7] and r+c=14 for row in [8,14]? But then (8,6) is on r+c=14.

        # To simplify and match known Havannah implementations, we'll use:
        # The six "edge" segments (cells that touch the boundary) excluding corners:
        # We'll define 6 edge lines:
        if (r, c) in [(0,0), (0,14), (14,14), (14,0), (7,14), (7,0)]:
            return False  # corners are not edges

        # Edge 1: top row, excluding corners
        if r == 0 and 1 <= c <= 13:
            return True
        # Edge 2: bottom row, excluding corners
        if r == 14 and 1 <= c <= 13:
            return True
        # Edge 3: right boundary - col=14, but not the corners (0,14) and (14,14) and (7,14)
        if c == 14 and 1 <= r <= 13 and r != 7:
            return True
        # Edge 4: left boundary - col=0, but not corners (0,0), (14,0), and (7,0)
        if c == 0 and 1 <= r <= 13 and r != 7:
            return True
        # Edge 5: The top-right to bottom-left diagonal - cells where r + c == 14, excluding corners
        if r + c == 14 and not is_corner(r, c) and 1 <= r <= 13 and 1 <= c <= 13:
            return True
        # Edge 6: The top-left to bottom-right diagonal - cells where r == c, excluding corners
        if r == c and not is_corner(r, c) and 1 <= r <= 13 and 1 <= c <= 13:
            return True

        return False
    
    def get_edge_type(r, c):
        """Return which edge the cell belongs to, or None if not on edge"""
        if (r, c) in [(0,0), (0,14), (14,14), (14,0), (7,14), (7,0)]:
            return None  # corner
        if r == 0 and 1 <= c <= 13:
            return "top"
        if r == 14 and 1 <= c <= 13:
            return "bottom"
        if c == 14 and 1 <= r <= 13 and r != 7:
            return "right"
        if c == 0 and 1 <= r <= 13 and r != 7:
            return "left"
        if r + c == 14 and not is_corner(r, c):
            return "diag1"
        if r == c and not is_corner(r, c):
            return "diag2"
        return None

    def count_edges_reached(stones):
        """Count how many distinct edges (not corners) the group of stones touches"""
        edges = set()
        for r, c in stones:
            edge = get_edge_type(r, c)
            if edge:
                edges.add(edge)
        return len(edges)
    
    def get_corners_reached(stones):
        """Count how many corner cells are adjacent to the group of stones"""
        corners = set()
        for r, c in stones:
            for nr, nc in get_neighbors(r, c):
                if is_corner(nr, nc):
                    corners.add((nr, nc))
        return len(corners), corners

    def has_ring(stones):
        """Check if the set of stones contains a ring (closed loop)"""
        if len(stones) < 4:
            return False
        
        # BFS to find cycles in the graph of connected stones
        # Represent stones as a set
        stone_set = set(stones)
        for start in stones:
            visited = set()
            queue = deque([(start, None)])  # (node, parent)
            visited.add(start)
            
            while queue:
                node, parent = queue.popleft()
                for neighbor in get_neighbors(*node):
                    if neighbor not in stone_set:
                        continue
                    if neighbor == parent:
                        continue
                    if neighbor in visited:
                        # Found a cycle (ring)
                        return True
                    visited.add(neighbor)
                    queue.append((neighbor, node))
        return False

    def is_winning_move(move):
        """Check if placing a stone at move completes a win (ring, bridge, or fork)"""
        stones = list(me_set) + [move]
        
        # Check ring
        if has_ring(stones):
            return True
        
        # Check bridge: connects two corners
        _, corners_reached = get_corners_reached(stones)
        if len(corners_reached) >= 2:
            return True
        
        # Check fork: connects three distinct edges
        edge_count = count_edges_reached(stones)
        if edge_count >= 3:
            return True
        
        return False

    # First: check if any immediate winning move exists
    valid_moves = []
    for r in range(board_size):
        for c in range(board_size):
            if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set:
                valid_moves.append((r, c))
                
    # Check for immediate win
    for move in valid_moves:
        if is_winning_move(move):
            return move
    
    # Candidate moves by heuristic scoring
    scores = {}
    
    # Offense: score moves based on potential to build winning structures
    # Defend: block opponent's good moves
    # For each move, evaluate score
    
    # Step 1: Block opponent's immediate threat
    for move in valid_moves:
        # Simulate opponent placing here on next turn, then check if they win
        # We only check if placing here blocks a potential future win for opponent
        # This is a simplified threat blocking: if opponent has two moves to win, blocking one won't help, but if they have one immediate move, block it.
        # For simplicity, check if opponent has a winning move right now (but they can't because it's our turn)
        # We look for opponent stones that are one move away from winning
        # We simulate: if opponent had placed at move, would they win?
        opp_threat = False
        opp_stones = list(opp_set) + [move]
        if len(opp_stones) >= 3:  # need at least 3 stones
            if has_ring(opp_stones) or count_edges_reached(opp_stones) >= 3:
                opp_threat = True
            else:
                _, corners = get_corners_reached(opp_stones)
                if len(corners) >= 2:
                    opp_threat = True
        
        # If blocking this would prevent an opponent win, give high priority
        if opp_threat:
            scores[move] = float('inf')
            continue
            
    # If we found a blocking move, use it
    if any(scores[m] == float('inf') for m in scores):
        best_block = max(scores.keys(), key=lambda m: scores[m])
        return best_block
    
    # Step 2: Score each valid move by heuristic
    # Initialize base score
    for move in valid_moves:
        score = 0
        r, c = move
        
        # Proximity to center (favor center)
        center_dist = abs(r - 7) + abs(c - 7)
        score += (14 - center_dist) * 0.3  # max 4.2
        
        # Connectivity to own stones
        own_neighbors = 0
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in me_set:
                own_neighbors += 1
        score += own_neighbors * 1.5
        
        # Connectivity to edges
        if is_edge(r, c):
            score += 2.0
        
        # Potential to connect to corners
        corner_contacts = 0
        for nr, nc in get_neighbors(r, c):
            if is_corner(nr, nc):
                corner_contacts += 1
        score += corner_contacts * 2.5
        
        # Threat to opponent: place near opponent stones to hinder them
        opp_neighbors = 0
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in opp_set:
                opp_neighbors += 1
        score += opp_neighbors * 0.5
        
        # Encirclement potential: if surrounded by own stones, may help ring
        # We'll look at how many of the 6 neighbors are own, and how many are empty
        total_neighbors = 0
        own_in_neighbors = 0
        for nr, nc in get_neighbors(r, c):
            if is_valid(nr, nc):
                total_neighbors += 1
                if (nr, nc) in me_set:
                    own_in_neighbors += 1
        # More own neighbors around might help in constructing a ring
        score += (own_in_neighbors / 6) * 1.0
        
        scores[move] = score
    
    # Choose highest scoring move
    best_move = max(scores.keys(), key=lambda m: scores[m])
    return best_move
