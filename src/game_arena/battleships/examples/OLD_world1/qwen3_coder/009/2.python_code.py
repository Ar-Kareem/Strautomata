
import random
from collections import Counter

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Targeting policy for Battleship game.
    
    Strategy:
    1. If there are no hits, use a smart search pattern (checkerboard)
    2. If there are hits but no ships are sunk, focus on adjacent cells to hit
    3. If we have a potential ship alignment, continue along that line
    """
    n = 10
    # Convert board to more convenient format
    hits = []
    misses = []
    unknown = []
    
    for i in range(n):
        for j in range(n):
            if board[i][j] == 1:
                hits.append((i, j))
            elif board[i][j] == -1:
                misses.append((i, j))
            else:
                unknown.append((i, j))
    
    # If no hits yet, use checkerboard pattern for initial search
    if not hits:
        # Checkerboard pattern - only check even parity positions first
        checkerboard = [(i, j) for i, j in unknown if (i + j) % 2 == 0]
        if checkerboard:
            return random.choice(checkerboard)
        else:
            return random.choice(unknown)
    
    # Find adjacent cells to hits that are still unknown
    def get_adjacent(row, col):
        adj = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            r, c = row + dr, col + dc
            if 0 <= r < n and 0 <= c < n and board[r][c] == 0:
                adj.append((r, c))
        return adj
    
    # If we have hits, try to determine ship orientations
    # Look for lines of hits to determine ship direction
    potential_targets = set()
    
    # For each hit, look at adjacent hits to determine direction
    for hit in hits:
        row, col = hit
        adj_hits = []
        # Check adjacent hits
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            r, c = row + dr, col + dc
            if 0 <= r < n and 0 <= c < n and board[r][c] == 1:
                adj_hits.append((r, c))
        
        # If adjacent hits exist, line them up
        if adj_hits:
            # Try horizontal
            if any(h[0] == row for h in adj_hits):
                # Horizontal line - extend left and right
                min_c = min(col, *[h[1] for h in adj_hits if h[0] == row])
                max_c = max(col, *[h[1] for h in adj_hits if h[0] == row])
                # Check left
                if col > 0 and board[row][col-1] == 0:
                    potential_targets.add((row, col-1))
                # Check right
                if col < n-1 and board[row][col+1] == 0:
                    potential_targets.add((row, col+1))
                # Also add a few more spots along the line for longer ships
                for offset in range(1, 4):
                    if min_c - offset >= 0 and board[row][min_c - offset] == 0:
                        potential_targets.add((row, min_c - offset))
                    if max_c + offset < n and board[row][max_c + offset] == 0:
                        potential_targets.add((row, max_c + offset))
            
            # Try vertical
            if any(h[1] == col for h in adj_hits):
                # Vertical line - extend up and down
                min_r = min(row, *[h[0] for h in adj_hits if h[1] == col])
                max_r = max(row, *[h[0] for h in adj_hits if h[1] == col])
                # Check up
                if row > 0 and board[row-1][col] == 0:
                    potential_targets.add((row-1, col))
                # Check down
                if row < n-1 and board[row+1][col] == 0:
                    potential_targets.add((row+1, col))
                # Also add a few more spots along the line for longer ships
                for offset in range(1, 4):
                    if min_r - offset >= 0 and board[min_r - offset][col] == 0:
                        potential_targets.add((min_r - offset, col))
                    if max_r + offset < n and board[max_r + offset][col] == 0:
                        potential_targets.add((max_r + offset, col))
        else:
            # No adjacent hits, so try adjacent unknown cells
            adj_unknown = get_adjacent(row, col)
            for cell in adj_unknown:
                potential_targets.add(cell)
    
    # Filter to only valid targets (unknown cells)
    valid_targets = [t for t in potential_targets if board[t[0]][t[1]] == 0]
    
    if valid_targets:
        # Prefer targets that fit ship sizes
        # Count how many possible ships could be there
        target_scores = {}
        ship_lengths = [2, 3, 3, 4, 5]
        
        for target in valid_targets:
            r, c = target
            score = 0
            # Horizontal placement possibilities
            for length in ship_lengths:
                for i in range(length):
                    # Check if ship of this length fits with target at position i
                    start_c = c - i
                    end_c = start_c + length - 1
                    if start_c >= 0 and end_c < n:
                        # Check if all positions in ship are either empty or hits
                        valid_ship = True
                        for j in range(start_c, end_c + 1):
                            if board[r][j] == -1:  # We know this is water
                                valid_ship = False
                                break
                        if valid_ship:
                            score += 1
            
            # Vertical placement possibilities
            for length in ship_lengths:
                for i in range(length):
                    # Check if ship of this length fits with target at position i
                    start_r = r - i
                    end_r = start_r + length - 1
                    if start_r >= 0 and end_r < n:
                        # Check if all positions in ship are either empty or hits
                        valid_ship = True
                        for j in range(start_r, end_r + 1):
                            if board[j][c] == -1:  # We know this is water
                                valid_ship = False
                                break
                        if valid_ship:
                            score += 1
            target_scores[target] = score
        
        # Choose highest scoring target, or random among highest scores
        max_score = max(target_scores.values())
        best_targets = [t for t, s in target_scores.items() if s == max_score]
        return random.choice(best_targets)
    
    # If no potential targets from logic, fall back to adjacent to any hit
    for hit in hits:
        adj_unknown = get_adjacent(hit[0], hit[1])
        if adj_unknown:
            return random.choice(adj_unknown)
    
    # If all adjacent to hits are tried, go back to checkerboard
    checkerboard = [(i, j) for i, j in unknown if (i + j) % 2 == 0]
    if checkerboard:
        return random.choice(checkerboard)
    
    # Final fallback - random choice
    return random.choice(unknown)
