
import random
from typing import List, Tuple, Set

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Battleship targeting policy using probability density and hunt/target modes.
    """
    
    def get_unknown_cells():
        """Get all cells that haven't been fired at yet."""
        unknown = []
        for r in range(10):
            for c in range(10):
                if board[r][c] == 0:
                    unknown.append((r, c))
        return unknown
    
    def get_hits():
        """Get all hit cells."""
        hits = []
        for r in range(10):
            for c in range(10):
                if board[r][c] == 1:
                    hits.append((r, c))
        return hits
    
    def get_adjacent_unknowns(r, c):
        """Get adjacent unknown cells to a hit."""
        adjacent = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                adjacent.append((nr, nc))
        return adjacent
    
    def is_isolated_hit(r, c):
        """Check if a hit is completely surrounded by misses or edges."""
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10:
                if board[nr][nc] != -1:  # Not a miss
                    return False
        return True
    
    def find_ship_groups():
        """Find groups of connected hits that likely represent ships."""
        hits = get_hits()
        visited = set()
        groups = []
        
        def dfs(r, c, group):
            if (r, c) in visited:
                return
            visited.add((r, c))
            group.append((r, c))
            
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
                    dfs(nr, nc, group)
        
        for r, c in hits:
            if (r, c) not in visited:
                group = []
                dfs(r, c, group)
                groups.append(group)
        
        return groups
    
    def get_remaining_ships():
        """Estimate remaining ship sizes based on hits found."""
        ship_sizes = [5, 4, 3, 3, 2]
        groups = find_ship_groups()
        
        # Remove likely sunk ships
        remaining = ship_sizes[:]
        for group in groups:
            # If a group is completely isolated, consider the ship sunk
            is_sunk = True
            for r, c in group:
                if not is_isolated_hit(r, c):
                    is_sunk = False
                    break
            
            if is_sunk and len(group) in remaining:
                remaining.remove(len(group))
        
        return remaining
    
    def calculate_probability_density():
        """Calculate probability that each unknown cell contains a ship."""
        unknown_cells = get_unknown_cells()
        if not unknown_cells:
            return {}
        
        density = {cell: 0 for cell in unknown_cells}
        remaining_ships = get_remaining_ships()
        
        for ship_size in remaining_ships:
            # Try all possible ship placements
            for r in range(10):
                for c in range(10):
                    # Horizontal placement
                    if c + ship_size <= 10:
                        valid = True
                        cells = [(r, c + i) for i in range(ship_size)]
                        for cr, cc in cells:
                            if board[cr][cc] == -1:  # Hit a miss
                                valid = False
                                break
                        if valid:
                            for cr, cc in cells:
                                if (cr, cc) in density:
                                    density[(cr, cc)] += 1
                    
                    # Vertical placement
                    if r + ship_size <= 10:
                        valid = True
                        cells = [(r + i, c) for i in range(ship_size)]
                        for cr, cc in cells:
                            if board[cr][cc] == -1:  # Hit a miss
                                valid = False
                                break
                        if valid:
                            for cr, cc in cells:
                                if (cr, cc) in density:
                                    density[(cr, cc)] += 1
        
        return density
    
    def get_target_mode_candidates():
        """Get high-priority targets adjacent to existing hits."""
        candidates = []
        groups = find_ship_groups()
        
        for group in groups:
            if len(group) == 1:
                # Single hit - try all adjacent cells
                r, c = group[0]
                candidates.extend(get_adjacent_unknowns(r, c))
            else:
                # Multiple hits - try to continue the line
                group.sort()
                
                # Check if hits are in a line (horizontal or vertical)
                if len(set(r for r, c in group)) == 1:
                    # Horizontal line
                    r = group[0][0]
                    min_c = min(c for r, c in group)
                    max_c = max(c for r, c in group)
                    
                    # Try extending both ends
                    if min_c > 0 and board[r][min_c - 1] == 0:
                        candidates.append((r, min_c - 1))
                    if max_c < 9 and board[r][max_c + 1] == 0:
                        candidates.append((r, max_c + 1))
                        
                elif len(set(c for r, c in group)) == 1:
                    # Vertical line
                    c = group[0][1]
                    min_r = min(r for r, c in group)
                    max_r = max(r for r, c in group)
                    
                    # Try extending both ends
                    if min_r > 0 and board[min_r - 1][c] == 0:
                        candidates.append((min_r - 1, c))
                    if max_r < 9 and board[max_r + 1][c] == 0:
                        candidates.append((max_r + 1, c))
                else:
                    # Irregular pattern - try all adjacent unknowns
                    for r, c in group:
                        candidates.extend(get_adjacent_unknowns(r, c))
        
        return list(set(candidates))  # Remove duplicates
    
    # Main targeting logic
    unknown_cells = get_unknown_cells()
    if not unknown_cells:
        return (0, 0)  # Shouldn't happen
    
    # Target mode: prioritize cells adjacent to hits
    target_candidates = get_target_mode_candidates()
    if target_candidates:
        # If we have target candidates, use probability density among them
        density = calculate_probability_density()
        best_target = max(target_candidates, key=lambda cell: density.get(cell, 0))
        return best_target
    
    # Hunt mode: use probability density
    density = calculate_probability_density()
    if density:
        # Choose cell with highest probability
        best_cell = max(density.keys(), key=lambda cell: density[cell])
        return best_cell
    
    # Fallback: random unknown cell (shouldn't typically reach here)
    return random.choice(unknown_cells)
