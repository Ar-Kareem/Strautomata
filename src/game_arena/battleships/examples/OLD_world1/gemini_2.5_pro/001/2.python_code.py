
import random

# --- Constants and Board Utilities ---

GRID_SIZE = 10

def is_valid(r: int, c: int) -> bool:
    """Check if a coordinate is within the board boundaries."""
    return 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE

def is_unknown(board: list[list[int]], r: int, c: int) -> bool:
    """Check if a cell is valid and has not been fired at."""
    return is_valid(r, c) and board[r][c] == 0

# --- Targeting Modes ---

def _hunt_mode(board: list[list[int]], unknowns: list[tuple[int, int]]) -> tuple[int, int]:
    """
    In Hunt Mode, we search for the first hit on a new ship.
    
    Strategy: Use a checkerboard pattern. The smallest ship is of length 2,
    so it must occupy at least one cell of a given "color" on a checkerboard.
    This strategy effectively cuts the search space in half.
    """
    # Prioritize cells in a checkerboard pattern (e.g., where r + c is even).
    checkerboard_targets = []
    for r, c in unknowns:
        if (r + c) % 2 == 0:
            checkerboard_targets.append((r, c))

    if checkerboard_targets:
        # Return a random target from the high-priority checkerboard cells.
        return random.choice(checkerboard_targets)
    
    # If all primary checkerboard cells have been shot, target the remaining ones.
    if unknowns:
        return random.choice(unknowns)
    
    # Fallback, should not be reached if the game is running correctly.
    return (0, 0)

def _target_mode(board: list[list[int]], hits: list[tuple[int, int]]) -> None:
    """
    In Target Mode, we have at least one hit and focus fire to sink the ship.
    
    Strategy:
    1. Prioritize extending known lines of hits. If we have two or more adjacent
       hits, we know the ship's orientation and should fire at its ends.
    2. If all hits are isolated, fire in a cross pattern around one of them to
       determine the ship's orientation.
    3. If no valid targets can be generated (e.g., all hits are fully boxed in
       by misses), return None to signal a switch back to Hunt Mode.
    """
    # Sort hits to make segment detection deterministic (always find top-left first).
    sorted_hits = sorted(hits)
    
    line_targets = set()
    checked_hits = set()

    # --- Phase 1: Find line segments and target their ends ---
    for r_hit, c_hit in sorted_hits:
        if (r_hit, c_hit) in checked_hits:
            continue

        # Check for start of a horizontal segment
        if is_valid(r_hit, c_hit + 1) and board[r_hit][c_hit + 1] == 1:
            segment = []
            c = c_hit
            while is_valid(r_hit, c) and board[r_hit][c] == 1:
                segment.append((r_hit, c))
                checked_hits.add((r_hit, c))
                c += 1
            leftmost, rightmost = segment[0], segment[-1]
            if is_unknown(board, leftmost[0], leftmost[1] - 1):
                line_targets.add((leftmost[0], leftmost[1] - 1))
            if is_unknown(board, rightmost[0], rightmost[1] + 1):
                line_targets.add((rightmost[0], rightmost[1] + 1))

        # Check for start of a vertical segment
        elif is_valid(r_hit + 1, c_hit) and board[r_hit + 1][c_hit] == 1:
            segment = []
            r = r_hit
            while is_valid(r, c_hit) and board[r][c_hit] == 1:
                segment.append((r, c_hit))
                checked_hits.add((r, c_hit))
                r += 1
            topmost, bottommost = segment[0], segment[-1]
            if is_unknown(board, topmost[0] - 1, topmost[1]):
                line_targets.add((topmost[0] - 1, topmost[1]))
            if is_unknown(board, bottommost[0] + 1, bottommost[1]):
                line_targets.add((bottommost[0] + 1, bottommost[1]))

    if line_targets:
        return random.choice(list(line_targets))

    # --- Phase 2: No lines found, target around isolated hits ---
    isolated_hits = [h for h in sorted_hits if h not in checked_hits]
    cross_targets = set()
    for r_hit, c_hit in isolated_hits:
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            if is_unknown(board, r_hit + dr, c_hit + dc):
                cross_targets.add((r_hit + dr, c_hit + dc))

    if cross_targets:
        return random.choice(list(cross_targets))

    # --- Phase 3: No valid target moves found ---
    return None

# --- Main Policy Function ---

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next shot to take based on the current state of the board.

    The policy implements a Hunt/Target strategy:
    1. HUNT: If no ships have been hit, search for them using a checkerboard pattern.
    2. TARGET: Once a ship is hit, focus fire around the hit to sink it quickly.
    
    `board` state:
     -  0: Unknown
     - -1: Miss
     -  1: Hit
    """
    # Scan the board to gather current state
    hits = []
    unknowns = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == 1:
                hits.append((r, c))
            elif board[r][c] == 0:
                unknowns.append((r,c))

    # This should not happen in a valid game, but is a safeguard.
    if not unknowns:
        return (0, 0)
        
    # If there are hits, enter Target Mode.
    if hits:
        shot = _target_mode(board, hits)
        if shot:
            return shot
            
    # If there are no hits OR Target Mode found no moves (i.e., all hit segments
    # are complete), enter Hunt Mode.
    return _hunt_mode(board, unknowns)
