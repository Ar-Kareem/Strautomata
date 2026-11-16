
import random
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Advanced Battleship targeting policy that combines:
    1. Hunt mode: Strategic probability-based targeting on a parity pattern
    2. Target mode: When a hit is found, intelligently search around it
    """
    n = len(board)
    
    # Find all hits and determine if we're in target mode
    hits = []
    for r in range(n):
        for c in range(n):
            if board[r][c] == 1:
                hits.append((r, c))
    
    # Check if there are any unsunk ships (hits that need follow-up)
    target_hits = []
    for r, c in hits:
        # Check if this hit has adjacent unknown cells (not fully explored)
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0:
                target_hits.append((r, c))
                break
    
    # TARGET MODE: We have hits to follow up on
    if target_hits:
        # Find connected components of hits
        hit_groups = find_hit_groups(board, hits, n)
        
        # For each group, find the best next shot
        best_shot = None
        best_priority = -1
        
        for group in hit_groups:
            # Determine orientation of the group
            if len(group) == 1:
                # Single hit - check all 4 directions
                r, c = group[0]
                candidates = []
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0:
                        candidates.append((nr, nc))
                
                if candidates:
                    shot = random.choice(candidates)
                    if best_priority < 3:
                        best_shot = shot
                        best_priority = 3
            else:
                # Multiple hits in a line - continue in the same direction
                group_sorted = sorted(group)
                
                # Check if horizontal or vertical
                if all(r == group_sorted[0][0] for r, c in group_sorted):
                    # Horizontal line
                    row = group_sorted[0][0]
                    min_col = min(c for r, c in group_sorted)
                    max_col = max(c for r, c in group_sorted)
                    
                    candidates = []
                    # Try extending left
                    if min_col > 0 and board[row][min_col - 1] == 0:
                        candidates.append((row, min_col - 1))
                    # Try extending right
                    if max_col < n - 1 and board[row][max_col + 1] == 0:
                        candidates.append((row, max_col + 1))
                    
                    if candidates:
                        shot = random.choice(candidates)
                        if best_priority < 5:
                            best_shot = shot
                            best_priority = 5
                
                elif all(c == group_sorted[0][1] for r, c in group_sorted):
                    # Vertical line
                    col = group_sorted[0][1]
                    min_row = min(r for r, c in group_sorted)
                    max_row = max(r for r, c in group_sorted)
                    
                    candidates = []
                    # Try extending up
                    if min_row > 0 and board[min_row - 1][col] == 0:
                        candidates.append((min_row - 1, col))
                    # Try extending down
                    if max_row < n - 1 and board[max_row + 1][col] == 0:
                        candidates.append((max_row + 1, col))
                    
                    if candidates:
                        shot = random.choice(candidates)
                        if best_priority < 5:
                            best_shot = shot
                            best_priority = 5
        
        if best_shot:
            return best_shot
    
    # HUNT MODE: Use parity pattern with probability weighting
    # Use checkerboard pattern for efficiency (ships of length 2+ must hit parity cells)
    candidates = []
    
    # First, try parity pattern (checkerboard)
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0 and (r + c) % 2 == 0:
                candidates.append((r, c))
    
    # If no parity cells left, use all remaining cells
    if not candidates:
        for r in range(n):
            for c in range(n):
                if board[r][c] == 0:
                    candidates.append((r, c))
    
    # Return a random candidate
    if candidates:
        return random.choice(candidates)
    
    # Fallback (should never reach here in normal game)
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                return (r, c)
    
    return (0, 0)


def find_hit_groups(board, hits, n):
    """Find connected components of hits (ships being targeted)"""
    visited = set()
    groups = []
    
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
            
            # Only check orthogonal directions
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < n and 0 <= nc < n and 
                    (nr, nc) not in visited and board[nr][nc] == 1):
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        
        groups.append(group)
    
    return groups
