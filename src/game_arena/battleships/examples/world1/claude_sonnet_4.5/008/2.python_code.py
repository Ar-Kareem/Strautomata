
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Battleship targeting policy that combines hunt and target modes.
    """
    # Ship lengths we're looking for
    SHIP_LENGTHS = [5, 4, 3, 3, 2]
    
    # Find all hits and unknowns
    hits = []
    unknowns = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.append((r, c))
            elif board[r][c] == 0:
                unknowns.append((r, c))
    
    if not unknowns:
        return (0, 0)  # Should never happen in valid game
    
    # TARGET MODE: If we have hits, focus on sinking those ships
    if hits:
        target = find_best_target_around_hits(board, hits, unknowns)
        if target:
            return target
    
    # HUNT MODE: Use probability density to find most likely ship locations
    best_cell = find_highest_probability_cell(board, unknowns, SHIP_LENGTHS)
    return best_cell


def find_best_target_around_hits(board, hits, unknowns):
    """
    Find the best cell to target when we have existing hits.
    Prioritize extending lines of hits or checking adjacent to isolated hits.
    """
    unknown_set = set(unknowns)
    
    # Check for hits that form lines (partially found ships)
    for hit in hits:
        r, c = hit
        # Check horizontal line
        left_hits = count_consecutive_hits(board, r, c, 0, -1)
        right_hits = count_consecutive_hits(board, r, c, 0, 1)
        if left_hits > 0 or right_hits > 0:
            # We have a horizontal line, extend it
            # Try left end
            if (r, c - left_hits - 1) in unknown_set:
                return (r, c - left_hits - 1)
            # Try right end
            if (r, c + right_hits + 1) in unknown_set:
                return (r, c + right_hits + 1)
        
        # Check vertical line
        up_hits = count_consecutive_hits(board, r, c, -1, 0)
        down_hits = count_consecutive_hits(board, r, c, 1, 0)
        if up_hits > 0 or down_hits > 0:
            # We have a vertical line, extend it
            # Try up end
            if (r - up_hits - 1, c) in unknown_set:
                return (r - up_hits - 1, c)
            # Try down end
            if (r + down_hits + 1, c) in unknown_set:
                return (r + down_hits + 1, c)
    
    # Check for isolated hits (no adjacent hits) - fire at adjacent unknowns
    for hit in hits:
        r, c = hit
        # Check if this hit is isolated (no adjacent hits)
        has_adjacent_hit = False
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
                has_adjacent_hit = True
                break
        
        if not has_adjacent_hit:
            # Fire at adjacent unknowns
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in unknown_set:
                    return (nr, nc)
    
    return None


def count_consecutive_hits(board, r, c, dr, dc):
    """Count consecutive hits in a direction from (r,c), not including (r,c)."""
    count = 0
    nr, nc = r + dr, c + dc
    while 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
        count += 1
        nr += dr
        nc += dc
    return count


def find_highest_probability_cell(board, unknowns, ship_lengths):
    """
    Calculate probability density for each unknown cell based on 
    possible ship placements.
    """
    probability = {}
    
    for cell in unknowns:
        probability[cell] = 0
    
    # For each ship length, count valid placements through each cell
    for ship_len in ship_lengths:
        for r, c in unknowns:
            # Check horizontal placements through this cell
            for start_c in range(max(0, c - ship_len + 1), min(10 - ship_len + 1, c + 1)):
                if can_place_ship(board, r, start_c, ship_len, horizontal=True):
                    probability[(r, c)] += 1
            
            # Check vertical placements through this cell
            for start_r in range(max(0, r - ship_len + 1), min(10 - ship_len + 1, r + 1)):
                if can_place_ship(board, start_r, c, ship_len, horizontal=False):
                    probability[(r, c)] += 1
    
    # Return cell with highest probability
    if probability:
        best_cell = max(probability.items(), key=lambda x: x[1])[0]
        return best_cell
    
    # Fallback: return random unknown
    return random.choice(unknowns)


def can_place_ship(board, r, c, length, horizontal):
    """Check if a ship of given length can be placed at position."""
    if horizontal:
        if c + length > 10:
            return False
        for i in range(length):
            if board[r][c + i] == -1:  # Hit a miss
                return False
        return True
    else:  # vertical
        if r + length > 10:
            return False
        for i in range(length):
            if board[r + i][c] == -1:  # Hit a miss
                return False
        return True
