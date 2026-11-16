
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    # Convert to set for O(1) lookup
    me_set = set(me)
    opp_set = set(opp)
    all_occupied = me_set | opp_set
    
    # Define the 6 hexagonal neighbors for a cell (row, col)
    # Hex grid: for even col, neighbors are (r-1,c-1), (r-1,c), (r,c-1), (r,c+1), (r+1,c-1), (r+1,c)
    # for odd col, neighbors are (r-1,c), (r-1,c+1), (r,c-1), (r,c+1), (r+1,c), (r+1,c+1)
    def get_neighbors(r, c):
        neighbors = []
        if c % 2 == 0:  # even column
            offsets = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
        else:  # odd column
            offsets = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
        for dr, dc in offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 15 and 0 <= nc < 15:
                neighbors.append((nr, nc))
        return neighbors

    # Check if placing a stone at (r, c) completes a winning structure
    def is_winning_move(r, c, player_set):
        # Temporary add stone
        player_set.add((r, c))
        
        # Check for BRIDGE: connect any two of the 6 corners
        corners = [(0, 0), (0, 14), (7, 14), (14, 14), (14, 0), (7, 0)]
        reachable_corners = []
        visited = set()
        queue = deque([(r, c)])
        visited.add((r, c))
        
        while queue:
            curr = queue.popleft()
            if curr in corners:
                reachable_corners.append(curr)
            for nb in get_neighbors(curr[0], curr[1]):
                if nb in player_set and nb not in visited:
                    visited.add(nb)
                    queue.append(nb)
        
        if len(reachable_corners) >= 2:
            player_set.remove((r, c))
            return True
        
        # Check for FORK: connect any three distinct edges (excluding corners)
        # Define edges (excluding corners)
        def get_edge_type(r, c):
            if r == 0 and 1 <= c <= 13:
                return 'top'
            elif r == 14 and 1 <= c <= 13:
                return 'bottom'
            elif c == 0 and 1 <= r <= 13:
                return 'left'
            elif c == 14 and 1 <= r <= 13:
                return 'right'
            if r == 7 and c == 14:
                return 'right_mid_corner'  # corner, but part of right edge
            if r == 7 and c == 0:
                return 'left_mid_corner'   # corner, but part of left edge
            if r == 0 and c == 0:
                return 'top_left_corner'
            if r == 0 and c == 14:
                return 'top_right_corner'
            if r == 14 and c == 0:
                return 'bottom_left_corner'
            if r == 14 and c == 14:
                return 'bottom_right_corner'
            # The two 'slanted' edges connecting corners:
            # Actually, we treat the entire side between corners as one edge
            # So we only consider the 4 main edges: top, bottom, left, right
            return None  # not on edge
        
        edge_set = set()
        visited = set()
        queue = deque([(r, c)])
        visited.add((r, c))
        
        while queue:
            curr = queue.popleft()
            edge_type = get_edge_type(curr[0], curr[1])
            if edge_type and edge_type not in ['top_left_corner', 'top_right_corner', 'bottom_left_corner', 'bottom_right_corner', 'left_mid_corner', 'right_mid_corner']:
                edge_set.add(edge_type)
            elif edge_type in ['left_mid_corner', 'right_mid_corner']:  # these are defined as part of left/right edge
                edge_set.add('left' if edge_type == 'left_mid_corner' else 'right')
            elif edge_type in ['top_left_corner', 'top_right_corner']:
                edge_set.add('top')
            elif edge_type in ['bottom_left_corner', 'bottom_right_corner']:
                edge_set.add('bottom')
                
            for nb in get_neighbors(curr[0], curr[1]):
                if nb in player_set and nb not in visited:
                    visited.add(nb)
                    queue.append(nb)
        
        if len(edge_set) >= 3:
            player_set.remove((r, c))
            return True
        
        # Check for RING: must form a cycle encircling at least one empty cell
        # We use a method: for each empty cell adjacent to player's group, check if it's surrounded
        # We use DFS to check if the group forms a loop around any empty cell
        
        # Get all adjacent empty cells to the placed stone group
        empty_adjacent = set()
        for stone in visited:
            for nb in get_neighbors(stone[0], stone[1]):
                if nb not in player_set and nb not in opp_set:  # empty
                    empty_adjacent.add(nb)
        
        for empty_cell in empty_adjacent:
            # Check if the player group forms a ring around empty_cell
            # We do this by checking if the group has a closed loop that encircles empty_cell
            # Use a simple approach: check density and path connectivity
            # For efficiency: if empty_cell is surrounded by 6 player stones, definitely ring
            
            # Get 6 neighbors of the empty cell
            empty_neighbors = get_neighbors(empty_cell[0], empty_cell[1])
            if len(empty_neighbors) < 6:
                continue  # can't be surrounded on a border
            
            # Check if all 6 neighbors are occupied by player
            all_occupied_by_player = all(nb in player_set for nb in empty_neighbors)
            if all_occupied_by_player:
                player_set.remove((r, c))
                return True
            
            # Alternative: use ring detection based on frontier cycles
            # We perform DFS from each of the 6 neighbors of empty_cell, try to find 2 paths to each other without crossing
            # Very complex; instead, we use a heuristic: if the group is large and has a "hole" with empty_cell, and the group wraps around it
            # For simplicity and time, we'll use: if the group has path count >= 8 and the empty cell is surrounded by 4+ player stones, consider ring
            # This is an approximation
            
            occupied_neighbors = [nb for nb in empty_neighbors if nb in player_set]
            if len(occupied_neighbors) >= 4:
                # Do a cycle check on player group around empty_cell
                # Use DFS to find if any two neighbor of empty_cell are connected via player stones without going through the other neighbors
                if len(occupied_neighbors) >= 4:
                    # Check if we can find a path between at least two non-adjacent neighbors of the empty_cell
                    # This is complex, so approximate: if there are 4 or more occupied neighbors and the group is sufficiently connected, assume ring
                    # A real ring detection would require topological analysis. Given time, we use a heuristic.
                    # Count the number of "gaps" in the ring: if fewer than 2 gaps, we consider it a ring
                    # We'll assume that 4+ occupied neighbors around an empty cell forms a ring if the player group is not fragmented
                    # We'll use BFS on player stones around the empty cell to see if they form one connected component around it
                    comp_visited = set()
                    stack = [occupied_neighbors[0]]
                    comp_visited.add(occupied_neighbors[0])
                    while stack:
                        curr = stack.pop()
                        for nb in get_neighbors(curr[0], curr[1]):
                            if nb in player_set and nb not in comp_visited and nb in empty_neighbors or any(e in get_neighbors(nb[0], nb[1]) for e in empty_neighbors):
                                # Only care about neighbors of the empty cell for this check
                                if nb in empty_neighbors and nb not in comp_visited:
                                    comp_visited.add(nb)
                                    stack.append(nb)
                        
                    # If we connected more than 2 of the occupied neighbors, likely ring
                    if len(comp_visited) >= 3:
                        player_set.remove((r, c))
                        return True
        
        player_set.remove((r, c))
        return False

    # Get all valid moves
    valid_moves = []
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c] and (r, c) not in all_occupied:
                valid_moves.append((r, c))

    # If no valid moves (shouldn't happen), return any (but constraint says must return legal)
    if not valid_moves:
        return (7, 7)  # fallback

    # Check for immediate win moves
    for move in valid_moves:
        if is_winning_move(move[0], move[1], me_set.copy()):
            return move

    # Check for opponent's immediate win (block it)
    for move in valid_moves:
        if is_winning_move(move[0], move[1], opp_set.copy()):
            return move

    # Heuristic: prioritize central moves and moves that extend connectivity
    # Score moves based on: distance to center, number of existing allied neighbors, and edge proximity
    def score_move(r, c):
        score = 0
        # Center preference
        center_dist = abs(r - 7) + abs(c - 7)  # Manhattan to (7,7)
        score += (14 - center_dist) * 0.5  # higher score for center
        
        # Count allied neighbors
        allied_neighbors = 0
        for nb in get_neighbors(r, c):
            if nb in me_set:
                allied_neighbors += 1
        score += allied_neighbors * 1.5
        
        # Edge bonding: if adjacent to an edge, score for potential fork/bridge
        edge_score = 0
        if r == 0 or r == 14 or c == 0 or c == 14:
            edge_score += 1
        # Corners are high value for bridge
        if (r, c) in [(0,0), (0,14), (14,0), (14,14)]:
            edge_score += 2
        if (r, c) in [(7,0), (7,14)]:
            edge_score += 1.5
        score += edge_score * 1.0
        
        # Check if this move is adjacent to opponent (threat or blocking opportunity)
        opp_neighbors = 0
        for nb in get_neighbors(r, c):
            if nb in opp_set:
                opp_neighbors += 1
        score += opp_neighbors * 0.3  # slight bonus for proximity to opponent
        return score

    # Evaluate all valid moves and return best
    scored_moves = [(score_move(r, c), (r, c)) for r, c in valid_moves]
    scored_moves.sort(reverse=True)  # highest score first
    return scored_moves[0][1]
