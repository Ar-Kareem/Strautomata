
import numpy as np
import random

# Constants
SIZE = 19
EMPTY = 0
ME = 1
OPPONENT = 2

# Direction vectors for neighbors (up, down, left, right)
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

# Star points (1-based indexing)
STAR_POINTS = [
    (4, 4), (4, 10), (4, 16),
    (10, 4), (10, 10), (10, 16),
    (16, 4), (16, 10), (16, 16)
]

def get_group_liberties(board, r, c):
    """
    Flood fill to find the group of stones at (r, c) and count its liberties.
    Returns (liberties_count, group_stones_set).
    Uses iterative stack to avoid recursion limits.
    """
    color = board[r, c]
    if color == EMPTY:
        return 0, set()

    stack = [(r, c)]
    visited = {(r, c)}
    liberties = set()
    
    while stack:
        curr_r, curr_c = stack.pop()
        
        for dr, dc in DIRECTIONS:
            nr, nc = curr_r + dr, curr_c + dc
            
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                neighbor_color = board[nr, nc]
                if neighbor_color == EMPTY:
                    liberties.add((nr, nc))
                elif neighbor_color == color and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    stack.append((nr, nc))
                    
    return len(liberties), visited

def remove_group(board, group_stones):
    """
    Removes a group of stones from the board.
    Returns the number of stones removed.
    """
    count = 0
    for r, c in group_stones:
        board[r, c] = EMPTY
        count += 1
    return count

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # 1. Initialize Board
    # Using 0-based indexing for internal logic
    board = np.zeros((SIZE, SIZE), dtype=int)
    
    for r, c in me:
        board[r-1, c-1] = ME
    for r, c in opponent:
        board[r-1, c-1] = OPPONENT

    # 2. Generate Candidates
    candidates = set()
    
    # Total stones on board to determine game phase
    total_stones = len(me) + len(opponent)
    
    # Opening Heuristics: Add empty star points if early game
    if total_stones < 10:
        for r, c in STAR_POINTS:
            if board[r-1, c-1] == EMPTY:
                candidates.add((r-1, c-1))
                
    # Adjacency Heuristics: Add empty spots adjacent to existing stones
    # This reduces search space significantly and focuses on relevant moves
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r, c] == EMPTY:
                is_candidate = False
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr, nc] != EMPTY:
                        is_candidate = True
                        break
                if is_candidate:
                    candidates.add((r, c))

    if not candidates:
        return (0, 0)

    # 3. Evaluate Candidates
    best_move = (0, 0)
    best_score = -float('inf')
    
    # Shuffle candidates to ensure non-deterministic play if scores are equal
    candidate_list = list(candidates)
    random.shuffle(candidate_list)
    
    # Pre-calculate 1-based center for distance heuristic
    center_r, center_c = 9, 9

    for r, c in candidate_list:
        # Check basic occupancy (should be empty based on generation, but safe to check)
        if board[r, c] != EMPTY:
            continue
            
        # Simulate the move
        board_copy = board.copy()
        board_copy[r, c] = ME
        
        captured_stones = 0
        captured_groups = []
        
        # Check neighbors for captures (opponent groups with 0 liberties)
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE and board_copy[nr, nc] == OPPONENT:
                libs, group = get_group_liberties(board_copy, nr, nc)
                if libs == 0:
                    # Verify we haven't already counted this group (if 2 neighbors belong to same group)
                    # Since we remove them immediately or mark them, checking board state is tricky.
                    # Easier: just use a set of tuple coords to track groups already marked for capture
                    group_key = frozenset(group)
                    if group_key not in captured_groups:
                        captured_groups.append(group_key)
                        captured_stones += remove_group(board_copy, group)
        
        # Suicide Rule: If no stones captured and the placed stone has 0 liberties, move is illegal
        is_suicide = False
        if captured_stones == 0:
            my_libs, _ = get_group_liberties(board_copy, r, c)
            if my_libs == 0:
                is_suicide = True
        
        if is_suicide:
            continue
            
        # --- Scoring Heuristics ---
        score = 0
        
        # A. Capture Priority: High reward for capturing
        score += captured_stones * 1000
        
        # B. Atari Threat: Check if we put opponent in atari (1 liberty)
        # Only check if we didn't just capture (capturing is better than threatening)
        if captured_stones == 0:
            atari_threats = 0
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE and board_copy[nr, nc] == OPPONENT:
                    libs, _ = get_group_liberties(board_copy, nr, nc)
                    if libs == 1:
                        atari_threats += 1
            score += atari_threats * 100
            
        # C. Self Safety: Strong penalty for putting self in atari
        my_libs, _ = get_group_liberties(board_copy, r, c)
        if my_libs == 1:
            score -= 500
        else:
            # Bonus for having many liberties (life)
            score += my_libs * 2
            
        # D. Shape / Connection: Bonus for connecting to friendly stones
        friendly_neighbors = 0
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr, nc] == ME:
                friendly_neighbors += 1
        
        if friendly_neighbors > 1:
            score += 10 # Good connection
            
        # E. Positional Heuristic: Slight preference for center/star points in opening
        # and avoiding edges in general
        dist_to_center = abs(r - center_r) + abs(c - center_c)
        score -= dist_to_center * 0.5
        
        # F. Random Noise: To break ties and vary play
        score += random.uniform(0, 5)

        # Update Best Move
        if score > best_score:
            best_score = score
            # Convert back to 1-based indexing for return
            best_move = (r + 1, c + 1)
            
    return best_move
