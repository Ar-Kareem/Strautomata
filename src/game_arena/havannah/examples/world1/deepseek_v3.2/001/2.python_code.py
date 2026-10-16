
import numpy as np
from collections import deque
import itertools
import time

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask):
    start_time = time.time()
    board_size = 15
    # Convert to faster set for lookups
    my_stones = set(me)
    opp_stones = set(opp)
    all_stones = my_stones | opp_stones
    
    # Precompute hex neighbors offsets
    # For even rows: left cols are (row-1, col-1), (row-1, col); right cols are (row+1, col), (row+1, col+1)
    # For odd rows: left cols are (row-1, col), (row-1, col+1); right cols are (row+1, col-1), (row+1, col)
    def get_neighbors(r, c):
        if r % 2 == 0:  # even row
            neighbors = [
                (r-1, c-1), (r-1, c),   # up-left
                (r, c-1), (r, c+1),     # left, right
                (r+1, c), (r+1, c+1)    # down-left, down-right
            ]
        else:  # odd row
            neighbors = [
                (r-1, c), (r-1, c+1),   # up-left, up-right
                (r, c-1), (r, c+1),     # left, right
                (r+1, c-1), (r+1, c)    # down-left, down-right
            ]
        return [(nr, nc) for nr, nc in neighbors 
                if 0 <= nr < board_size and 0 <= nc < board_size]
    
    # Helper: BFS to find connected component
    def bfs_component(start, stones_set):
        visited = set()
        queue = deque([start])
        component = []
        while queue:
            r, c = queue.popleft()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            component.append((r, c))
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in stones_set and (nr, nc) not in visited:
                    queue.append((nr, nc))
        return component
    
    # Check if a set of stones contains a winning structure
    # We'll check for bridge, fork, and ring
    def has_win(stones_set, player_is_me):
        if len(stones_set) < 3:
            return False
        
        # 1. Bridge: connect any two corners
        corners = [(0,0), (0,7), (0,14), 
                   (7,0), (7,14),
                   (14,0), (14,7), (14,14)]
        player_corners = [c for c in corners if c in stones_set]
        
        # Check connectivity between each pair
        for i in range(len(player_corners)):
            for j in range(i+1, len(player_corners)):
                if connected(player_corners[i], player_corners[j], stones_set):
                    return True
        
        # 2. Fork: connect any three edges
        # Edges: top (row=0), bottom (row=14), left (col=0), right (col=14)
        # Also the two diagonal edges: top-left to bottom-left and top-right to bottom-right
        # Actually in hex, edges are: top-left, top-right, right, bottom-right, bottom-left, left
        # We'll use simplified: check if stones touch three different edge types
        
        edge_types = set()
        for r, c in stones_set:
            if r == 0:
                if c < 7: edge_types.add("top_left")
                else: edge_types.add("top_right")
            elif r == 14:
                if c < 7: edge_types.add("bottom_left")
                else: edge_types.add("bottom_right")
            if c == 0:
                edge_types.add("left")
            elif c == 14:
                edge_types.add("right")
        if len(edge_types) >= 3:
            # Check if they're connected through the same component
            components = []
            visited = set()
            for stone in stones_set:
                if stone not in visited:
                    comp = bfs_component(stone, stones_set)
                    components.append(comp)
                    visited.update(comp)
            for comp in components:
                edge_types_comp = set()
                for r, c in comp:
                    if r == 0:
                        if c < 7: edge_types_comp.add("top_left")
                        else: edge_types_comp.add("top_right")
                    elif r == 14:
                        if c < 7: edge_types_comp.add("bottom_left")
                        else: edge_types_comp.add("bottom_right")
                    if c == 0:
                        edge_types_comp.add("left")
                    elif c == 14:
                        edge_types_comp.add("right")
                if len(edge_types_comp) >= 3:
                    return True
        
        # 3. Ring: a loop that encloses at least one cell
        # Use flood fill from empty cells
        empty_cells = [(r, c) for r in range(board_size) for c in range(board_size) 
                       if (r, c) not in all_stones and valid_mask[r][c]]
        visited_empty = set()
        for cell in empty_cells:
            if cell in visited_empty:
                continue
            # Flood fill this empty region
            region = []
            stack = [cell]
            boundary_stones = set()
            touches_boundary = False
            while stack:
                r, c = stack.pop()
                if (r, c) in visited_empty:
                    continue
                visited_empty.add((r, c))
                region.append((r, c))
                for nr, nc in get_neighbors(r, c):
                    if not (0 <= nr < board_size and 0 <= nc < board_size):
                        touches_boundary = True
                        continue
                    if (nr, nc) in stones_set:
                        boundary_stones.add((nr, nc))
                    elif (nr, nc) not in all_stones:
                        if (nr, nc) not in visited_empty:
                            stack.append((nr, nc))
            # If region is surrounded by stones of same color and doesn't touch board edge
            if not touches_boundary and len(boundary_stones) > 0:
                # Check if all boundary stones are connected in a cycle
                # Simplified: if region exists and boundary stones > 5, likely ring
                if len(boundary_stones) >= 6:
                    # Verify they form a cycle (BFS through boundary stones only)
                    if forms_cycle(boundary_stones):
                        return True
        return False
    
    def connected(a, b, stones_set):
        if a not in stones_set or b not in stones_set:
            return False
        visited = set()
        stack = [a]
        while stack:
            r, c = stack.pop()
            if (r, c) == b:
                return True
            if (r, c) in visited:
                continue
            visited.add((r, c))
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in stones_set and (nr, nc) not in visited:
                    stack.append((nr, nc))
        return False
    
    def forms_cycle(stones_set):
        if len(stones_set) < 6:
            return False
        # Pick any stone, do BFS and check if we can return to start with >2 steps
        start = next(iter(stones_set))
        visited = set()
        parent = {}
        stack = [(start, None)]
        while stack:
            curr, par = stack.pop()
            if curr in visited:
                # Found a cycle
                return True
            visited.add(curr)
            for nr, nc in get_neighbors(*curr):
                if (nr, nc) in stones_set and (nr, nc) != par:
                    stack.append(((nr, nc), curr))
        return False
    
    # 1. Check immediate winning move
    for r in range(board_size):
        for c in range(board_size):
            if valid_mask[r][c] and (r, c) not in all_stones:
                # Try placing my stone
                new_my = my_stones | {(r, c)}
                if has_win(new_my, True):
                    return (r, c)
    
    # 2. Block opponent's winning move
    for r in range(board_size):
        for c in range(board_size):
            if valid_mask[r][c] and (r, c) not in all_stones:
                new_opp = opp_stones | {(r, c)}
                if has_win(new_opp, False):
                    return (r, c)
    
    # 3. Heuristic evaluation for non-winning moves
    # Score based on:
    # - Connection to existing stones
    # - Proximity to edges/corners
    # - Freedom (empty neighbors)
    
    def evaluate_move(r, c, for_player):
        stones = my_stones if for_player else opp_stones
        other = opp_stones if for_player else my_stones
        
        score = 0
        
        # Connection bonus
        connected_count = 0
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in stones:
                connected_count += 1
            elif (nr, nc) in other:
                score -= 5  # adjacency to opponent is bad
        score += connected_count * 10
        
        # Edge proximity
        if r == 0 or r == 14 or c == 0 or c == 14:
            score += 8
        elif r == 1 or r == 13 or c == 1 or c == 13:
            score += 4
        
        # Corner bonus
        corners = [(0,0), (0,14), (14,0), (14,14)]
        if (r, c) in corners:
            score += 12
        
        # Center control (less important but good for flexibility)
        dist_from_center = abs(r - 7) + abs(c - 7)
        score += (14 - dist_from_center) * 0.5
        
        # Empty neighbors (potential for growth)
        empty_neighbors = 0
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) not in all_stones and valid_mask[nr][nc]:
                empty_neighbors += 1
        score += empty_neighbors * 2
        
        # Block opponent connections
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in other:
                # Count how many other opponent stones this blocks from connecting
                for nr2, nc2 in get_neighbors(nr, nc):
                    if (nr2, nc2) in other and (nr2, nc2) != (r, c):
                        score += 3
        
        return score
    
    # 4. Select best move by heuristic
    best_score = -float('inf')
    best_move = None
    
    # If board is empty, start near center
    if len(all_stones) == 0:
        return (7, 7)
    
    # Sample moves to stay within time limit
    # We'll check all valid moves but use fast evaluation
    for r in range(board_size):
        for c in range(board_size):
            if valid_mask[r][c] and (r, c) not in all_stones:
                # My score minus opponent's potential score if they play here
                my_score = evaluate_move(r, c, True)
                opp_score = evaluate_move(r, c, False)
                total_score = my_score - opp_score * 0.7
                
                # Small random tie-breaker
                import random
                total_score += random.random() * 0.1
                
                if total_score > best_score:
                    best_score = total_score
                    best_move = (r, c)
    
    # Safety: if no move found (shouldn't happen), return first valid
    if best_move is None:
        for r in range(board_size):
            for c in range(board_size):
                if valid_mask[r][c] and (r, c) not in all_stones:
                    return (r, c)
    
    return best_move
