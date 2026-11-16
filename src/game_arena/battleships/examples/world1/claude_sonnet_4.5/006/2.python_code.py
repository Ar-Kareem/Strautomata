
def policy(board: list[list[int]]) -> tuple[int, int]:
    import numpy as np
    
    board = np.array(board)
    SHIP_LENGTHS = [5, 4, 3, 3, 2]
    
    # Find all hits and unknowns
    hits = set(zip(*np.where(board == 1)))
    unknowns = set(zip(*np.where(board == 0)))
    
    if not unknowns:
        return (0, 0)  # Should never happen
    
    # Find groups of connected hits (potential unsunk ships)
    def get_connected_groups(hits):
        groups = []
        remaining = set(hits)
        while remaining:
            group = set()
            stack = [remaining.pop()]
            while stack:
                r, c = stack.pop()
                if (r, c) in group:
                    continue
                group.add((r, c))
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in remaining:
                        remaining.discard((nr, nc))
                        stack.append((nr, nc))
            groups.append(group)
        return groups
    
    hit_groups = get_connected_groups(hits) if hits else []
    
    # Determine which ships are likely still afloat
    sunk_lengths = []
    unsunk_groups = []
    
    for group in hit_groups:
        # Check if this group forms a line and might be a complete ship
        if len(group) >= 2:
            rows, cols = zip(*group)
            if len(set(rows)) == 1 or len(set(cols)) == 1:  # Forms a line
                # Check if surrounded by water/edges (sunk)
                is_sunk = True
                if len(set(rows)) == 1:  # Horizontal
                    r = rows[0]
                    min_c, max_c = min(cols), max(cols)
                    # Check ends
                    for c in [min_c - 1, max_c + 1]:
                        if 0 <= c < 10 and board[r, c] == 0:
                            is_sunk = False
                else:  # Vertical
                    c = cols[0]
                    min_r, max_r = min(rows), max(rows)
                    for r in [min_r - 1, max_r + 1]:
                        if 0 <= r < 10 and board[r, c] == 0:
                            is_sunk = False
                
                if is_sunk and len(group) in SHIP_LENGTHS:
                    sunk_lengths.append(len(group))
                else:
                    unsunk_groups.append(group)
            else:
                unsunk_groups.append(group)
        else:
            unsunk_groups.append(group)
    
    remaining_ships = SHIP_LENGTHS.copy()
    for length in sunk_lengths:
        if length in remaining_ships:
            remaining_ships.remove(length)
    
    # Priority 1: Cells adjacent to unsunk hits
    adjacent_to_hits = set()
    for group in unsunk_groups:
        for r, c in group:
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and (nr, nc) in unknowns:
                    adjacent_to_hits.add((nr, nc))
    
    if adjacent_to_hits:
        # Among adjacent cells, pick using probability
        target_cells = adjacent_to_hits
    else:
        target_cells = unknowns
    
    # Calculate probability density for each target cell
    def calc_probability(cell, ships):
        r, c = cell
        count = 0
        for ship_len in ships:
            # Horizontal placements
            for start_c in range(max(0, c - ship_len + 1), min(10 - ship_len + 1, c + 1)):
                valid = True
                for dc in range(ship_len):
                    check_c = start_c + dc
                    if board[r, check_c] == -1:
                        valid = False
                        break
                    # Must include unsunk hits if any in this row
                    if board[r, check_c] == 1 and not any((r, check_c) in g for g in unsunk_groups):
                        valid = False
                        break
                if valid:
                    count += 1
            
            # Vertical placements
            for start_r in range(max(0, r - ship_len + 1), min(10 - ship_len + 1, r + 1)):
                valid = True
                for dr in range(ship_len):
                    check_r = start_r + dr
                    if board[check_r, c] == -1:
                        valid = False
                        break
                    if board[check_r, c] == 1 and not any((check_r, c) in g for g in unsunk_groups):
                        valid = False
                        break
                if valid:
                    count += 1
        
        return count
    
    # Find cell with max probability
    best_cell = max(target_cells, key=lambda cell: calc_probability(cell, remaining_ships))
    
    return best_cell
