
import numpy as np
from collections import defaultdict

def policy(board: list[list[int]]) -> tuple[int, int]:
    n = 10
    board = np.array(board)
    
    # Predefined ship lengths
    ship_lengths = [5, 4, 3, 3, 2]
    
    def get_hit_cells():
        return set(zip(*np.where(board == 1)))
    
    def get_miss_cells():
        return set(zip(*np.where(board == -1)))
    
    def get_unknown_cells():
        unknown = set(zip(*np.where(board == 0)))
        return unknown
    
    def get_adjacent(cell):
        r, c = cell
        adj = set()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n:
                adj.add((nr, nc))
        return adj
    
    def check_valid_ship(points):
        points = list(points)
        points.sort()
        # Check if all in a line
        if len(set(p[0] for p in points)) == 1:  # horizontal
            cols = [p[1] for p in points]
            if cols == list(range(min(cols), max(cols) + 1)):
                return True
        elif len(set(p[1] for p in points)) == 1:  # vertical
            rows = [p[0] for p in points]
            if rows == list(range(min(rows), max(rows) + 1)):
                return True
        return False
    
    def generate_possible_ships(hits, length):
        if len(hits) == 1:
            # Generate all possible continuations
            directions = []
            r, c = next(iter(hits))
            # Horizontal left
            if c - (length - 1) >= 0:
                ship = set([(r, c - i) for i in range(length)])
                if ship.isdisjoint(miss_cells):
                    directions.append(ship)
            # Horizontal right
            if c + (length - 1) < n:
                ship = set([(r, c + i) for i in range(length)])
                if ship.isdisjoint(miss_cells):
                    directions.append(ship)
            # Vertical up
            if r - (length - 1) >= 0:
                ship = set([(r - i, c) for i in range(length)])
                if ship.isdisjoint(miss_cells):
                    directions.append(ship)
            # Vertical down
            if r + (length - 1) < n:
                ship = set([(r + i, c) for i in range(length)])
                if ship.isdisjoint(miss_cells):
                    directions.append(ship)
            return directions
        
        else:
            # Try to extend existing hits
            if check_valid_ship(hits):
                # Find orientation
                rows = {p[0] for p in hits}
                cols = {p[1] for p in hits}
                
                if len(rows) == 1:  # horizontal
                    min_col = min(p[1] for p in hits)
                    max_col = max(p[1] for p in hits)
                    # Try extending left
                    needed_left = length - len(hits)
                    start_col = min_col - needed_left
                    if start_col >= 0:
                        ship = set([(rows.pop(), col) for col in range(start_col, max_col + 1)])
                        if (ship - hits).issubset(unknown_cells) and ship.isdisjoint(miss_cells):
                            return [ship]
                    # Try extending right
                    end_col = max_col + needed_left
                    if end_col < n:
                        ship = set([(rows.pop(), col) for col in range(min_col, end_col + 1)])
                        if (ship - hits).issubset(unknown_cells) and ship.isdisjoint(miss_cells):
                            return [ship]
                
                elif len(cols) == 1:  # vertical
                    min_row = min(p[0] for p in hits)
                    max_row = max(p[0] for p in hits)
                    # Try extending up
                    needed_up = length - len(hits)
                    start_row = min_row - needed_up
                    if start_row >= 0:
                        ship = set([(row, cols.pop()) for row in range(start_row, max_row + 1)])
                        if (ship - hits).issubset(unknown_cells) and ship.isdisjoint(miss_cells):
                            return [ship]
                    # Try extending down
                    end_row = max_row + needed_up
                    if end_row < n:
                        ship = set([(row, cols.pop()) for row in range(min_row, end_row + 1)])
                        if (ship - hits).issubset(unknown_cells) and ship.isdisjoint(miss_cells):
                            return [ship]
            return []
    
    # Get current state
    hit_cells = get_hit_cells()
    miss_cells = get_miss_cells()
    unknown_cells = get_unknown_cells()
    
    # Phase 1: Target around existing hits
    if hit_cells:
        # Group hits into connected components (potential ships)
        hit_groups = []
        used_hits = set()
        
        for hit in hit_cells:
            if hit in used_hits:
                continue
            # Find all connected hits
            queue = [hit]
            current_group = set()
            while queue:
                cell = queue.pop()
                if cell in current_group:
                    continue
                current_group.add(cell)
                used_hits.add(cell)
                for adj in get_adjacent(cell):
                    if adj in hit_cells and adj not in current_group:
                        queue.append(adj)
            hit_groups.append(current_group)
        
        # For each hit group, try to determine the best next move
        targeting_probability = np.zeros((n, n))
        
        for group in hit_groups:
            # Determine possible ships this group could be part of
            group_len = len(group)
            possible_lengths = [l for l in ship_lengths if l >= group_len]
            
            for length in possible_lengths:
                possible_ships = generate_possible_ships(group, length)
                for ship in possible_ships:
                    # Only consider unknown cells in the ship
                    targets = ship & unknown_cells
                    # Uniformly distribute probability among possible extensions
                    for cell in targets:
                        targeting_probability[cell] += 1.0 / max(1, len(targets))
        
        # If we have any probability on targeting around hits, use that
        if np.any(targeting_probability > 0):
            max_prob = np.max(targeting_probability)
            candidates = np.argwhere(targeting_probability == max_prob)
            # Prefer cells that have more adjacent hits (more likely to be correct direction)
            best_cell = None
            best_score = -1
            for cell in candidates:
                r, c = cell
                score = sum(1 for adj in get_adjacent((r, c)) if adj in hit_cells)
                if score > best_score or best_cell is None:
                    best_score = score
                    best_cell = (r, c)
            return tuple(best_cell)
    
    # Phase 2: Probabilistic targeting - no good hits to follow up on
    # Calculate probability for each unknown cell based on possible ship placements
    
    # Initialize probability map
    prob_map = np.zeros((n, n))
    unknown_list = list(unknown_cells)
    
    # Try all possible ship placements
    for length in ship_lengths:
        # Horizontal placements
        for r in range(n):
            for c in range(n - length + 1):
                cells = [(r, c + i) for i in range(length)]
                if all(cell in unknown_cells for cell in cells):
                    for cell in cells:
                        prob_map[cell] += 1
        
        # Vertical placements
        for r in range(n - length + 1):
            for c in range(n):
                cells = [(r + i, c) for i in range(length)]
                if all(cell in unknown_cells for cell in cells):
                    for cell in cells:
                        prob_map[cell] += 1
    
    # Don't consider already fired positions (they should be filtered by unknown_cells)
    # Find all cells with maximum probability
    if np.max(prob_map) > 0:
        max_prob = np.max(prob_map)
        candidates = np.argwhere(prob_map == max_prob)
    else:
        # If no possible ships (shouldn't happen), just pick random unknown
        candidates = np.array(list(unknown_cells))
    
    # Among max candidates, pick one with most adjacent unknowns (in checkerboard pattern)
    if len(candidates) > 1:
        # Implement checkerboard pattern preference
        checkerboard_scores = np.zeros((n, n))
        for r in range(n):
            for c in range(n):
                checkerboard_scores[r, c] = (r + c) % 2  # 0 or 1
        
        # Prefer cells with higher checkerboard score (more sparse pattern)
        best_score = -1
        best_cell = None
        for cell in candidates:
            r, c = cell
            current_score = checkerboard_scores[r, c]
            if current_score > best_score or best_cell is None:
                best_score = current_score
                best_cell = (r, c)
        return tuple(best_cell)
    else:
        return tuple(candidates[0])
