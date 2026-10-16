
import random

def policy(me, opponent):
    """
    A tactical Go policy prioritizing captures, defense, and Atari attacks.
    """
    my_stones = set(me)
    opp_stones = set(opponent)
    occupied = my_stones.union(opp_stones)
    BOARD_SIZE = 19

    # Helper to find neighbors
    def get_neighbors(r, c):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                yield nr, nc

    # BFS to find group and its liberties
    def get_group_info(start_r, start_c, player_stones, all_occupied):
        if (start_r, start_c) not in player_stones:
            return set(), set()
        
        queue = [(start_r, start_c)]
        visited = set()
        group = set()
        liberties = set()
        
        while queue:
            r, c = queue.pop(0)
            if (r, c) in visited:
                continue
            visited.add((r, c))
            group.add((r, c))
            
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in all_occupied:
                    liberties.add((nr, nc))
                elif (nr, nc) in player_stones and (nr, nc) not in visited:
                    queue.append((nr, nc))
                    
        return group, liberties

    # Check if a move is legal (not suicide, not occupied)
    # A move is legal if:
    # 1. The spot is empty.
    # 2. It captures opponent stones (opponent group liberties become 0).
    # 3. OR, if no capture, the placed stone's group has > 0 liberties.
    def is_legal_move(r, c, current_player_stones, current_opp_stones, current_occupied):
        if (r, c) in current_occupied:
            return False
        
        # Check for capture
        captures_opponent = False
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in current_opp_stones:
                opp_group, opp_libs = get_group_info(nr, nc, current_opp_stones, current_occupied)
                # If opponent group has exactly 1 liberty, and that liberty is (r,c), we capture it.
                if len(opp_libs) == 1 and (r, c) in opp_libs:
                    captures_opponent = True
                    break
        
        if captures_opponent:
            return True # Capturing moves are always legal (non-suicide)

        # Check for suicide
        # Calculate liberties of the resulting group if we play at (r,c)
        # Liberties come from:
        # 1. Empty neighbors of (r,c)
        # 2. Liberties of connected friendly groups (minus the spot (r,c) itself)
        
        resulting_liberties = set()
        
        # Add empty neighbors as liberties
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) not in current_occupied:
                resulting_liberties.add((nr, nc))
        
        # Check friendly neighbors
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in current_player_stones:
                # We connect to this group. Its liberties are valid except for (r,c)
                f_group, f_libs = get_group_info(nr, nc, current_player_stones, current_occupied)
                resulting_liberties.update(f_libs)
        
        # The spot (r,c) itself was counted as a liberty for neighbors, but we are filling it.
        # However, empty neighbors of (r,c) are still liberties.
        # Basically, if we have any liberties left, it's not suicide.
        # Note: We must remove (r,c) from the liberty count if it was counted in f_libs
        # (which it was, because it was empty).
        if (r, c) in resulting_liberties:
            resulting_liberties.remove((r, c))
            
        return len(resulting_liberties) > 0

    # --- Strategy Logic ---

    # 1. Capture Opponent Stones (Highest Priority)
    # Find opponent groups with 1 liberty.
    checked_opp_groups = set()
    capture_candidates = []
    
    for r, c in opp_stones:
        if (r, c) in checked_opp_groups:
            continue
        
        group, libs = get_group_info(r, c, opp_stones, occupied)
        checked_opp_groups.update(group)
        
        if len(libs) == 1:
            move = list(libs)[0]
            # Prioritize capturing larger groups
            capture_candidates.append((1000 + len(group), move))

    # Sort by size descending
    capture_candidates.sort(key=lambda x: x[0], reverse=True)
    for score, move in capture_candidates:
        # Capture moves are always legal, but double check bounds/empty just in case
        if is_legal_move(move[0], move[1], my_stones, opp_stones, occupied):
            return move

    # 2. Save Own Stones (Atari Defense)
    # Find my groups with 1 liberty.
    checked_my_groups = set()
    defense_candidates = []
    
    for r, c in my_stones:
        if (r, c) in checked_my_groups:
            continue
            
        group, libs = get_group_info(r, c, my_stones, occupied)
        checked_my_groups.update(group)
        
        if len(libs) == 1:
            # We are in Atari. The only liberty is the escape point.
            move = list(libs)[0]
            # Check if extending saves us (is legal and results in >0 libs)
            # Since we verified it's legal, we consider it.
            defense_candidates.append(move)

    # For defense, we might want to check if the escape point is a trap (self-atari again),
    # but simple bots should try to extend.
    # Let's filter for legality to be safe.
    for move in defense_candidates:
        if is_legal_move(move[0], move[1], my_stones, opp_stones, occupied):
            return move

    # 3. Attack Opponent (Put in Atari)
    # Find opponent groups with 2 liberties. Playing one creates AtarI.
    attack_candidates = []
    # Re-use checked_opp_groups logic or re-scan. Re-scanning is safer/easier here.
    analyzed_opp_groups = set()
    for r, c in opp_stones:
        if (r, c) in analyzed_opp_groups:
            continue
        
        group, libs = get_group_info(r, c, opp_stones, occupied)
        analyzed_opp_groups.update(group)
        
        if len(libs) == 2:
            # Try both liberties
            for move in libs:
                if is_legal_move(move[0], move[1], my_stones, opp_stones, occupied):
                    # Add some randomness to which liberty we pick, or score them
                    attack_candidates.append(move)

    if attack_candidates:
        return random.choice(attack_candidates)

    # 4. Shape Moves (Extension/Connection)
    # If no tactical moves, play near existing stones.
    shape_candidates = []
    
    # If we have stones, play near them
    if my_stones:
        for r, c in my_stones:
            # Check neighbors (One point jump, Diagonal, Knight's move)
            # Offsets: (1,1), (1,2), (2,1), (2,2), (1,-1)...
            # Standard good shape offsets
            offsets = [
                (1, 1), (1, -1), (-1, 1), (-1, -1), # Diagonals
                (1, 2), (2, 1), (-1, 2), (-2, 1),   # Knights
                (1, -2), (2, -1), (-1, -2), (-2, -1),
                (2, 0), (-2, 0), (0, 2), (0, -2)    # Two space jumps
            ]
            for dr, dc in offsets:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                    if (nr, nc) not in occupied:
                        shape_candidates.append((nr, nc))
    
    # Verify legality of shape moves
    random.shuffle(shape_candidates)
    for move in shape_candidates:
        if is_legal_move(move[0], move[1], my_stones, opp_stones, occupied):
            return move

    # 5. Fallback: Random Legal Move
    # If board is empty or shape moves failed, pick a random empty spot.
    empty_spots = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if (r, c) not in occupied:
                empty_spots.append((r, c))
    
    random.shuffle(empty_spots)
    
    # Limit checks to save time, or check until found
    # Since board is likely full if we are here, checks are fast.
    for move in empty_spots:
        if is_legal_move(move[0], move[1], my_stones, opp_stones, occupied):
            return move

    # 6. Pass
    return (0, 0)
