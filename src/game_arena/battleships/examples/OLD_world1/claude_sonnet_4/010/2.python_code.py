
import random
from typing import List, Tuple, Set

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Advanced Battleship targeting policy using hunt and target strategy
    with probability density mapping and smart ship placement logic.
    """
    
    # Ship lengths in the game
    SHIP_LENGTHS = [5, 4, 3, 3, 2]
    BOARD_SIZE = 10
    
    def get_unfired_cells() -> Set[Tuple[int, int]]:
        """Get all cells that haven't been fired at yet."""
        unfired = set()
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] == 0:
                    unfired.add((r, c))
        return unfired
    
    def get_hits() -> List[Tuple[int, int]]:
        """Get all hit cells."""
        hits = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] == 1:
                    hits.append((r, c))
        return hits
    
    def get_neighbors(r: int, c: int) -> List[Tuple[int, int]]:
        """Get valid neighboring cells (up, down, left, right)."""
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                neighbors.append((nr, nc))
        return neighbors
    
    def find_ship_groups() -> List[List[Tuple[int, int]]]:
        """Group connected hits into potential ships."""
        hits = get_hits()
        visited = set()
        groups = []
        
        def dfs(r: int, c: int, group: List[Tuple[int, int]]):
            if (r, c) in visited or board[r][c] != 1:
                return
            visited.add((r, c))
            group.append((r, c))
            
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in visited and board[nr][nc] == 1:
                    dfs(nr, nc, group)
        
        for r, c in hits:
            if (r, c) not in visited:
                group = []
                dfs(r, c, group)
                if group:
                    groups.append(group)
        
        return groups
    
    def get_targeting_candidates() -> List[Tuple[int, int]]:
        """Get high-priority targets adjacent to hits."""
        candidates = []
        ship_groups = find_ship_groups()
        
        for group in ship_groups:
            if len(group) == 1:
                # Single hit - target all adjacent unfired cells
                r, c = group[0]
                for nr, nc in get_neighbors(r, c):
                    if board[nr][nc] == 0:
                        candidates.append((nr, nc))
            else:
                # Multiple connected hits - determine ship orientation
                group.sort()
                
                # Check if horizontal or vertical
                is_horizontal = all(pos[0] == group[0][0] for pos in group)
                is_vertical = all(pos[1] == group[0][1] for pos in group)
                
                if is_horizontal:
                    # Target ends of horizontal ship
                    row = group[0][0]
                    min_col = min(pos[1] for pos in group)
                    max_col = max(pos[1] for pos in group)
                    
                    if min_col > 0 and board[row][min_col - 1] == 0:
                        candidates.append((row, min_col - 1))
                    if max_col < BOARD_SIZE - 1 and board[row][max_col + 1] == 0:
                        candidates.append((row, max_col + 1))
                        
                elif is_vertical:
                    # Target ends of vertical ship
                    col = group[0][1]
                    min_row = min(pos[0] for pos in group)
                    max_row = max(pos[0] for pos in group)
                    
                    if min_row > 0 and board[min_row - 1][col] == 0:
                        candidates.append((min_row - 1, col))
                    if max_row < BOARD_SIZE - 1 and board[max_row + 1][col] == 0:
                        candidates.append((max_row + 1, col))
        
        return candidates
    
    def calculate_probability_density() -> List[List[float]]:
        """Calculate probability density for each cell based on possible ship placements."""
        density = [[0.0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        
        # Determine which ships are likely still alive
        ship_groups = find_ship_groups()
        total_hits = sum(len(group) for group in ship_groups)
        total_ship_cells = sum(SHIP_LENGTHS)
        remaining_ships = SHIP_LENGTHS[:]
        
        # Remove ships that are likely sunk (rough estimation)
        for group in ship_groups:
            if len(group) in remaining_ships:
                remaining_ships.remove(len(group))
        
        # For each remaining ship length, calculate placement probability
        for ship_length in remaining_ships:
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    # Try horizontal placement
                    if c + ship_length <= BOARD_SIZE:
                        valid = True
                        for dc in range(ship_length):
                            if board[r][c + dc] == -1:  # Can't place on miss
                                valid = False
                                break
                        if valid:
                            for dc in range(ship_length):
                                density[r][c + dc] += 1.0
                    
                    # Try vertical placement
                    if r + ship_length <= BOARD_SIZE:
                        valid = True
                        for dr in range(ship_length):
                            if board[r + dr][c] == -1:  # Can't place on miss
                                valid = False
                                break
                        if valid:
                            for dr in range(ship_length):
                                density[r + dr][c] += 1.0
        
        return density
    
    def get_hunt_target() -> Tuple[int, int]:
        """Use probability density and parity to find best hunting target."""
        unfired = get_unfired_cells()
        
        if not unfired:
            # Fallback - shouldn't happen
            return (0, 0)
        
        # Calculate probability density
        density = calculate_probability_density()
        
        # Find cells with maximum density
        max_density = 0
        best_cells = []
        
        for r, c in unfired:
            cell_density = density[r][c]
            if cell_density > max_density:
                max_density = cell_density
                best_cells = [(r, c)]
            elif cell_density == max_density:
                best_cells.append((r, c))
        
        if not best_cells:
            best_cells = list(unfired)
        
        # Apply parity pattern (checkerboard) as tiebreaker for early game
        total_shots = sum(1 for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] != 0)
        
        if total_shots < 30:  # Early game - use parity
            parity_cells = [(r, c) for r, c in best_cells if (r + c) % 2 == 0]
            if parity_cells:
                best_cells = parity_cells
        
        return random.choice(best_cells)
    
    # Main strategy logic
    unfired = get_unfired_cells()
    if not unfired:
        return (0, 0)
    
    # Priority 1: Target adjacent to known hits
    targeting_candidates = get_targeting_candidates()
    if targeting_candidates:
        return random.choice(targeting_candidates)
    
    # Priority 2: Hunt mode using probability density
    return get_hunt_target()
