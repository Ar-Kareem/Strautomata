
import random
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Advanced Battleship targeting policy using hunt and target modes.
    """
    n = len(board)
    
    # Find all hits and misses
    hits = []
    unknowns = []
    
    for r in range(n):
        for c in range(n):
            if board[r][c] == 1:
                hits.append((r, c))
            elif board[r][c] == 0:
                unknowns.append((r, c))
    
    # If we have hits, enter target mode
    if hits:
        # Find unsunk ships (groups of connected hits)
        visited = set()
        unsunk_groups = []
        
        for hit in hits:
            if hit in visited:
                continue
            
            # BFS to find connected hits
            group = []
            queue = deque([hit])
            visited.add(hit)
            
            while queue:
                r, c = queue.popleft()
                group.append((r, c))
                
                # Check all 4 directions
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in visited:
                        if board[nr][nc] == 1:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
            
            unsunk_groups.append(group)
        
        # Target cells adjacent to unsunk ships
        target_cells = []
        
        for group in unsunk_groups:
            # Determine orientation of the group
            if len(group) == 1:
                # Single hit - check all 4 directions
                r, c = group[0]
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0:
                        target_cells.append((nr, nc))
            else:
                # Multiple hits - determine if horizontal or vertical
                group.sort()
                rows = [r for r, c in group]
                cols = [c for r, c in group]
                
                if len(set(rows)) == 1:
                    # Horizontal ship
                    r = rows[0]
                    min_c = min(cols)
                    max_c = max(cols)
                    
                    # Check left and right ends
                    if min_c > 0 and board[r][min_c - 1] == 0:
                        target_cells.append((r, min_c - 1))
                    if max_c < n - 1 and board[r][max_c + 1] == 0:
                        target_cells.append((r, max_c + 1))
                else:
                    # Vertical ship
                    c = cols[0]
                    min_r = min(rows)
                    max_r = max(rows)
                    
                    # Check top and bottom ends
                    if min_r > 0 and board[min_r - 1][c] == 0:
                        target_cells.append((min_r - 1, c))
                    if max_r < n - 1 and board[max_r + 1][c] == 0:
                        target_cells.append((max_r + 1, c))
        
        if target_cells:
            return random.choice(target_cells)
    
    # Hunt mode: use checkerboard pattern with priority
    # Prioritize cells that can fit remaining ships
    ship_lengths = [5, 4, 3, 3, 2]
    
    # Calculate probability density for each unknown cell
    cell_scores = {}
    
    for r, c in unknowns:
        score = 0
        
        # Check horizontal placements
        for ship_len in ship_lengths:
            for start_c in range(max(0, c - ship_len + 1), min(n - ship_len + 1, c + 1)):
                if all(0 <= start_c + i < n and board[r][start_c + i] != -1 
                       for i in range(ship_len)):
                    score += 1
        
        # Check vertical placements
        for ship_len in ship_lengths:
            for start_r in range(max(0, r - ship_len + 1), min(n - ship_len + 1, r + 1)):
                if all(0 <= start_r + i < n and board[start_r + i][c] != -1 
                       for i in range(ship_len)):
                    score += 1
        
        cell_scores[(r, c)] = score
    
    # Filter by checkerboard pattern for efficiency
    checkerboard_cells = [(r, c) for r, c in unknowns if (r + c) % 2 == 0]
    
    if checkerboard_cells:
        # Choose best scoring cell from checkerboard
        best_cell = max(checkerboard_cells, key=lambda pos: cell_scores[pos])
        return best_cell
    elif unknowns:
        # Fallback to best scoring cell overall
        best_cell = max(unknowns, key=lambda pos: cell_scores[pos])
        return best_cell
    
    # Should never reach here, but return a random unknown cell as fallback
    return random.choice(unknowns) if unknowns else (0, 0)
