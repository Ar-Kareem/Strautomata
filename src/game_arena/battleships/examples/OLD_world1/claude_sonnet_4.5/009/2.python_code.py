
import random
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Advanced Battleship targeting policy combining hunt and target modes.
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
    
    # If there are hits, enter TARGET mode
    if hits:
        # Find unsunk ships (connected components of hits)
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
                
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < n and 0 <= nc < n and 
                        (nr, nc) not in visited and board[nr][nc] == 1):
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            
            unsunk_groups.append(group)
        
        # Target unsunk ships
        best_targets = []
        
        for group in unsunk_groups:
            if len(group) == 1:
                # Single hit - check all 4 directions
                r, c = group[0]
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0:
                        best_targets.append((nr, nc))
            else:
                # Multiple hits - determine orientation and extend
                group_sorted = sorted(group)
                
                if all(r == group_sorted[0][0] for r, c in group_sorted):
                    # Horizontal ship
                    r = group_sorted[0][0]
                    min_c = min(c for _, c in group_sorted)
                    max_c = max(c for _, c in group_sorted)
                    
                    # Check ends
                    if min_c > 0 and board[r][min_c - 1] == 0:
                        best_targets.append((r, min_c - 1))
                    if max_c < n - 1 and board[r][max_c + 1] == 0:
                        best_targets.append((r, max_c + 1))
                else:
                    # Vertical ship
                    c = group_sorted[0][1]
                    min_r = min(r for r, _ in group_sorted)
                    max_r = max(r for r, _ in group_sorted)
                    
                    # Check ends
                    if min_r > 0 and board[min_r - 1][c] == 0:
                        best_targets.append((min_r - 1, c))
                    if max_r < n - 1 and board[max_r + 1][c] == 0:
                        best_targets.append((max_r + 1, c))
        
        if best_targets:
            return random.choice(best_targets)
    
    # HUNT mode - use checkerboard pattern with probability weighting
    # Calculate probability density for remaining ships
    ship_lengths = [5, 4, 3, 3, 2]
    
    # Count how many ships are potentially sunk
    total_hits = len(hits)
    # Estimate remaining ship cells (conservative approach)
    # This is simplified - in reality we'd track sunk ships
    
    # Use checkerboard pattern prioritizing cells
    checkerboard_cells = []
    other_cells = []
    
    for r, c in unknowns:
        if (r + c) % 2 == 0:
            checkerboard_cells.append((r, c))
        else:
            other_cells.append((r, c))
    
    # Prefer checkerboard pattern initially
    if checkerboard_cells:
        # Weight by density - prefer center and areas near edges of scanned regions
        def density_score(pos):
            r, c = pos
            score = 0
            
            # Prefer cells that could be part of multiple ship orientations
            for length in ship_lengths:
                # Horizontal
                for start_c in range(max(0, c - length + 1), min(n - length + 1, c + 1)):
                    if all(board[r][c2] != -1 for c2 in range(start_c, start_c + length)):
                        score += 1
                
                # Vertical
                for start_r in range(max(0, r - length + 1), min(n - length + 1, r + 1)):
                    if all(board[r2][c] != -1 for r2 in range(start_r, start_r + length)):
                        score += 1
            
            return score
        
        # Score all checkerboard cells
        scored = [(density_score(pos), pos) for pos in checkerboard_cells]
        scored.sort(reverse=True)
        
        # Pick from top candidates with some randomness
        top_n = min(5, len(scored))
        return random.choice([pos for _, pos in scored[:top_n]])
    
    # Fallback to any unknown cell
    if other_cells:
        return random.choice(other_cells)
    
    # Should never reach here, but fallback
    return random.choice(unknowns)
