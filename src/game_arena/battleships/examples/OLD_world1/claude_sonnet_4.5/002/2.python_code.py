
import random
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Adaptive Battleship targeting policy that combines:
    1. Hunt mode: probabilistic targeting based on ship placement possibilities
    2. Target mode: focused firing around hits with directional pursuit
    """
    n = len(board)
    ships = [5, 4, 3, 3, 2]
    
    # Find all hits and determine which ships are still active
    hits = []
    misses = []
    unknowns = []
    
    for r in range(n):
        for c in range(n):
            if board[r][c] == 1:
                hits.append((r, c))
            elif board[r][c] == -1:
                misses.append((r, c))
            elif board[r][c] == 0:
                unknowns.append((r, c))
    
    # If we have hits, use target mode
    if hits:
        # Find unsunk ships (hits that aren't part of complete sunk ships)
        target = find_best_target_around_hits(board, n, ships)
        if target:
            return target
    
    # Hunt mode: use probability density
    return hunt_mode(board, n, ships, unknowns)


def find_best_target_around_hits(board, n, ships):
    """Target mode: intelligently fire around existing hits"""
    hits = [(r, c) for r in range(n) for c in range(n) if board[r][c] == 1]
    
    # Group hits into potential ship segments
    hit_groups = group_connected_hits(hits, board, n)
    
    for group in hit_groups:
        if len(group) == 1:
            # Single isolated hit - check all 4 directions
            r, c = group[0]
            candidates = []
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0:
                    candidates.append((nr, nc))
            if candidates:
                return random.choice(candidates)
        else:
            # Multiple hits in a line - extend the line
            group_sorted = sorted(group)
            
            # Check if horizontal or vertical
            if all(r == group_sorted[0][0] for r, c in group_sorted):
                # Horizontal line
                row = group_sorted[0][0]
                min_col = min(c for r, c in group_sorted)
                max_col = max(c for r, c in group_sorted)
                
                # Try extending both ends
                candidates = []
                if min_col > 0 and board[row][min_col - 1] == 0:
                    candidates.append((row, min_col - 1))
                if max_col < n - 1 and board[row][max_col + 1] == 0:
                    candidates.append((row, max_col + 1))
                if candidates:
                    return random.choice(candidates)
            
            elif all(c == group_sorted[0][1] for r, c in group_sorted):
                # Vertical line
                col = group_sorted[0][1]
                min_row = min(r for r, c in group_sorted)
                max_row = max(r for r, c in group_sorted)
                
                # Try extending both ends
                candidates = []
                if min_row > 0 and board[min_row - 1][col] == 0:
                    candidates.append((min_row - 1, col))
                if max_row < n - 1 and board[max_row + 1][col] == 0:
                    candidates.append((max_row + 1, col))
                if candidates:
                    return random.choice(candidates)
    
    return None


def group_connected_hits(hits, board, n):
    """Group hits that are adjacent to each other"""
    if not hits:
        return []
    
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
            
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < n and 0 <= nc < n and 
                    (nr, nc) in hits and (nr, nc) not in visited):
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        
        groups.append(group)
    
    return groups


def hunt_mode(board, n, ships, unknowns):
    """Hunt mode: use probability density to find best cell"""
    # Calculate probability for each unknown cell
    prob_map = [[0.0 for _ in range(n)] for _ in range(n)]
    
    remaining_ships = estimate_remaining_ships(board, n, ships)
    
    for ship_len in remaining_ships:
        # Try placing ship at each position in both orientations
        for r in range(n):
            for c in range(n):
                # Horizontal
                if can_place_ship(board, r, c, ship_len, horizontal=True, n=n):
                    for i in range(ship_len):
                        prob_map[r][c + i] += 1
                
                # Vertical
                if can_place_ship(board, r, c, ship_len, horizontal=False, n=n):
                    for i in range(ship_len):
                        prob_map[r + i][c] += 1
    
    # Use checkerboard pattern bias early in game
    total_shots = sum(1 for r in range(n) for c in range(n) if board[r][c] != 0)
    if total_shots < 30:
        for r in range(n):
            for c in range(n):
                if (r + c) % 2 == 0:
                    prob_map[r][c] *= 1.5
    
    # Find best unknown cell
    best_prob = -1
    best_cells = []
    
    for r, c in unknowns:
        if prob_map[r][c] > best_prob:
            best_prob = prob_map[r][c]
            best_cells = [(r, c)]
        elif prob_map[r][c] == best_prob:
            best_cells.append((r, c))
    
    return random.choice(best_cells) if best_cells else random.choice(unknowns)


def can_place_ship(board, r, c, length, horizontal, n):
    """Check if a ship of given length can be placed at position"""
    if horizontal:
        if c + length > n:
            return False
        for i in range(length):
            if board[r][c + i] == -1:  # Known miss
                return False
    else:
        if r + length > n:
            return False
        for i in range(length):
            if board[r + i][c] == -1:  # Known miss
                return False
    
    return True


def estimate_remaining_ships(board, n, ships):
    """Estimate which ships are still afloat based on hit patterns"""
    # Simple heuristic: assume all ships are still active
    # A more sophisticated approach would try to identify sunk ships
    hits = [(r, c) for r in range(n) for c in range(n) if board[r][c] == 1]
    
    if not hits:
        return ships
    
    # For now, just return all ships (could be improved by detecting sunk ships)
    return ships
