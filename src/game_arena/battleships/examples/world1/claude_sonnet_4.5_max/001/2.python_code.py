
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Smart Battleship policy combining target mode and hunt mode.
    
    Target mode: When we have hits, focus on sinking those ships.
    Hunt mode: Use probability-based search to find new ships.
    """
    # Find all hits
    hits = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 1]
    
    # Target mode: prioritize finishing ships we've already hit
    if hits:
        target = get_target_move(board, hits)
        if target:
            return target
    
    # Hunt mode: search for new ships using probability map
    return get_hunt_move(board)


def get_target_move(board, hits):
    """
    Find the best move to continue targeting existing hits.
    Prioritizes smaller groups to finish sinking ships faster.
    """
    groups = find_hit_groups(board, hits)
    groups.sort(key=lambda g: len(g))  # Smaller groups first
    
    for group in groups:
        candidates = find_candidates_for_group(board, group)
        if candidates:
            return random.choice(candidates)
    
    return None


def find_candidates_for_group(board, group):
    """
    Find valid target cells for a group of connected hits.
    """
    if len(group) == 1:
        # Single hit: try all 4 adjacent cells
        r, c = group[0]
        candidates = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                candidates.append((nr, nc))
        return candidates
    
    # Multiple hits: check if they form a line
    group.sort()
    
    # Horizontal line
    if all(r == group[0][0] for r, c in group):
        r = group[0][0]
        min_c = min(c for _, c in group)
        max_c = max(c for _, c in group)
        
        candidates = []
        if min_c > 0 and board[r][min_c - 1] == 0:
            candidates.append((r, min_c - 1))
        if max_c < 9 and board[r][max_c + 1] == 0:
            candidates.append((r, max_c + 1))
        return candidates
    
    # Vertical line
    if all(c == group[0][1] for r, c in group):
        c = group[0][1]
        min_r = min(r for r, _ in group)
        max_r = max(r for r, _ in group)
        
        candidates = []
        if min_r > 0 and board[min_r - 1][c] == 0:
            candidates.append((min_r - 1, c))
        if max_r < 9 and board[max_r + 1][c] == 0:
            candidates.append((max_r + 1, c))
        return candidates
    
    # Non-linear group (edge case)
    candidates = []
    for r, c in group:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                if (nr, nc) not in candidates:
                    candidates.append((nr, nc))
    return candidates


def find_hit_groups(board, hits):
    """
    Group connected hits using BFS.
    """
    visited = set()
    groups = []
    
    for hit in hits:
        if hit in visited:
            continue
        
        group = []
        queue = [hit]
        
        while queue:
            r, c = queue.pop(0)
            if (r, c) in visited:
                continue
            
            visited.add((r, c))
            group.append((r, c))
            
            # Check adjacent cells
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < 10 and 0 <= nc < 10 and 
                    board[nr][nc] == 1 and (nr, nc) not in visited):
                    queue.append((nr, nc))
        
        groups.append(group)
    
    return groups


def get_hunt_move(board):
    """
    Find the best cell to target using probability density.
    Counts how many valid ship placements cover each cell.
    """
    ships = [5, 4, 3, 3, 2]
    prob_map = [[0 for _ in range(10)] for _ in range(10)]
    
    # Count valid placements for each ship
    for ship_len in ships:
        # Horizontal placements
        for r in range(10):
            for c in range(10 - ship_len + 1):
                # Check if ship can fit (no misses in the way)
                if all(board[r][c + i] != -1 for i in range(ship_len)):
                    for i in range(ship_len):
                        if board[r][c + i] == 0:
                            prob_map[r][c + i] += 1
        
        # Vertical placements
        for r in range(10 - ship_len + 1):
            for c in range(10):
                # Check if ship can fit (no misses in the way)
                if all(board[r + i][c] != -1 for i in range(ship_len)):
                    for i in range(ship_len):
                        if board[r + i][c] == 0:
                            prob_map[r + i][c] += 1
    
    # Find cell(s) with maximum probability
    max_prob = -1
    best_cells = []
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                if prob_map[r][c] > max_prob:
                    max_prob = prob_map[r][c]
                    best_cells = [(r, c)]
                elif prob_map[r][c] == max_prob:
                    best_cells.append((r, c))
    
    if best_cells:
        return random.choice(best_cells)
    
    # Fallback: return any available cell
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    
    return (0, 0)
