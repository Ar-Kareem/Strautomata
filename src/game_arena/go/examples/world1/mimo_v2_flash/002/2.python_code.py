
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Set dimensions for a standard Go board
    DIM = 19
    
    # Helper to check if a coordinate is on the board
    def on_board(r, c):
        return 1 <= r <= DIM and 1 <= c <= DIM

    # Helper to get valid neighbors
    def get_neighbors(r, c):
        return [
            (r + dr, c + dc) 
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)] 
            if on_board(r + dr, c + dc)
        ]

    # Build a set of all occupied stones for fast lookup
    stones = set(me + opponent)
    
    # Function to find connected groups and their liberties
    def get_groups_and_liberties(player_stones):
        groups = []
        visited = set()
        
        for stone in player_stones:
            if stone in visited:
                continue
            
            # Start BFS for this group
            group = []
            queue = [stone]
            visited.add(stone)
            liberties = set()
            
            while queue:
                curr_r, curr_c = queue.pop(0)
                group.append((curr_r, curr_c))
                
                for nr, nc in get_neighbors(curr_r, curr_c):
                    if (nr, nc) in player_stones and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
                    elif (nr, nc) not in stones: # Empty intersection is a liberty
                        liberties.add((nr, nc))
            
            groups.append({
                'stones': group,
                'liberties': liberties,
                'liberty_count': len(liberties)
            })
        return groups

    # Analyze groups
    my_groups = get_groups_and_liberties(me)
    opponent_groups = get_groups_and_liberties(opponent)

    # Priority 1: Capture opponent stones
    # Look for opponent groups with exactly 1 liberty
    capture_moves = []
    for grp in opponent_groups:
        if grp['liberty_count'] == 1:
            capture_moves.extend(list(grp['liberties']))
    
    if capture_moves:
        return random.choice(capture_moves)

    # Priority 2: Save own stones
    # Look for my groups with 1 liberty
    save_moves = []
    for grp in my_groups:
        if grp['liberty_count'] == 1:
            save_moves.extend(list(grp['liberties']))
    
    if save_moves:
        return random.choice(save_moves)

    # Priority 3: Expansion / Influence
    # Find neighbors of existing stones to expand
    expansion_candidates = set()
    for r, c in me:
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) not in stones:
                expansion_candidates.add((nr, nc))
    
    if expansion_candidates:
        # Heuristic: Prioritize moves that extend lines or solidify shapes
        # Simplified: Just pick a valid expansion spot
        return random.choice(list(expansion_candidates))

    # Fallback: Pick any random empty spot if no expansion points found
    # (This shouldn't happen early in the game, but ensures legality)
    empty_spots = []
    for r in range(1, DIM + 1):
        for c in range(1, DIM + 1):
            if (r, c) not in stones:
                empty_spots.append((r, c))
    
    if empty_spots:
        return random.choice(empty_spots)
    
    # Pass if board is full (extreme edge case)
    return (0, 0)
