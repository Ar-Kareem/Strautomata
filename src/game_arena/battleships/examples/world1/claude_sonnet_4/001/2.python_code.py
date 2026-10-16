
import random
from collections import defaultdict

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Battleship targeting policy that combines hunt mode and target mode.
    """
    
    def get_unknown_cells():
        """Return list of all unknown cells (value 0)"""
        unknown = []
        for r in range(10):
            for c in range(10):
                if board[r][c] == 0:
                    unknown.append((r, c))
        return unknown
    
    def get_hit_cells():
        """Return list of all hit cells (value 1)"""
        hits = []
        for r in range(10):
            for c in range(10):
                if board[r][c] == 1:
                    hits.append((r, c))
        return hits
    
    def get_adjacent_cells(r, c):
        """Return valid adjacent cells (up, down, left, right)"""
        adjacent = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10:
                adjacent.append((nr, nc))
        return adjacent
    
    def find_ship_segments():
        """Group connected hit cells into ship segments"""
        hits = get_hit_cells()
        if not hits:
            return []
        
        segments = []
        used = set()
        
        for hit in hits:
            if hit in used:
                continue
                
            # Start a new segment
            segment = [hit]
            used.add(hit)
            queue = [hit]
            
            # Find all connected hits
            while queue:
                r, c = queue.pop(0)
                for nr, nc in get_adjacent_cells(r, c):
                    if (nr, nc) not in used and board[nr][nc] == 1:
                        segment.append((nr, nc))
                        used.add((nr, nc))
                        queue.append((nr, nc))
            
            segments.append(segment)
        
        return segments
    
    def get_segment_targets(segment):
        """Get potential target cells for extending a ship segment"""
        if len(segment) == 1:
            # Single hit, check all adjacent cells
            r, c = segment[0]
            targets = []
            for nr, nc in get_adjacent_cells(r, c):
                if board[nr][nc] == 0:
                    targets.append((nr, nc))
            return targets
        
        # Multiple hits, determine orientation and extend
        segment.sort()
        targets = []
        
        # Check if horizontal or vertical
        if all(r == segment[0][0] for r, c in segment):
            # Horizontal ship
            row = segment[0][0]
            min_col = min(c for r, c in segment)
            max_col = max(c for r, c in segment)
            
            # Extend left
            if min_col > 0 and board[row][min_col - 1] == 0:
                targets.append((row, min_col - 1))
            
            # Extend right
            if max_col < 9 and board[row][max_col + 1] == 0:
                targets.append((row, max_col + 1))
                
        elif all(c == segment[0][1] for r, c in segment):
            # Vertical ship
            col = segment[0][1]
            min_row = min(r for r, c in segment)
            max_row = max(r for r, c in segment)
            
            # Extend up
            if min_row > 0 and board[min_row - 1][col] == 0:
                targets.append((min_row - 1, col))
            
            # Extend down
            if max_row < 9 and board[max_row + 1][col] == 0:
                targets.append((max_row + 1, col))
        
        return targets
    
    def hunt_mode():
        """Hunt for ships using checkerboard pattern"""
        unknown = get_unknown_cells()
        
        # Try checkerboard pattern first (every other cell)
        checkerboard = []
        for r, c in unknown:
            if (r + c) % 2 == 0:
                checkerboard.append((r, c))
        
        if checkerboard:
            return random.choice(checkerboard)
        
        # If checkerboard is exhausted, pick any unknown cell
        if unknown:
            return random.choice(unknown)
        
        return None
    
    # Main targeting logic
    unknown_cells = get_unknown_cells()
    
    if not unknown_cells:
        # Should not happen in normal gameplay
        return (0, 0)
    
    # Find ship segments and potential targets
    segments = find_ship_segments()
    
    all_targets = []
    for segment in segments:
        targets = get_segment_targets(segment)
        all_targets.extend(targets)
    
    # If we have targets from hit ships, prioritize them
    if all_targets:
        return random.choice(all_targets)
    
    # Otherwise, use hunt mode
    target = hunt_mode()
    if target:
        return target
    
    # Fallback to any unknown cell
    return random.choice(unknown_cells)
