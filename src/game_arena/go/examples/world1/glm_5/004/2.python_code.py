
import random
import numpy as np

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    Tactical Go policy focusing on capturing, saving groups, and legal move generation.
    """
    size = 19
    # Initialize board with padding (1-indexed logic, 0 and 20 are borders)
    # 0 = empty, 1 = me, 2 = opponent, 3 = border
    board = np.full((size + 2, size + 2), 0, dtype=int)
    for r, c in [(0, i) for i in range(size + 2)] + [(size + 1, i) for i in range(size + 2)] + \
                [(i, 0) for i in range(size + 2)] + [(i, size + 1) for i in range(size + 2)]:
        board[r, c] = 3

    my_stones_set = set(me)
    opp_stones_set = set(opponent)

    for r, c in me:
        board[r, c] = 1
    for r, c in opponent:
        board[r, c] = 2

    def get_neighbors(r, c):
        return [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]

    def get_group_info(r, c):
        """Returns (set of stones in group, set of liberties)."""
        color = board[r, c]
        if color == 0 or color == 3:
            return set(), set()
        
        stones = set()
        liberties = set()
        stack = [(r, c)]
        visited = set()
        
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in visited:
                continue
            visited.add((cr, cc))
            
            if board[cr, cc] == color:
                stones.add((cr, cc))
                for nr, nc in get_neighbors(cr, cc):
                    if board[nr, nc] == 0:
                        liberties.add((nr, nc))
                    elif board[nr, nc] == color:
                        stack.append((nr, nc))
        return stones, liberties

    # --- 1. CAPTURE PRIORITY ---
    # Check if any opponent group is in Atari (1 liberty) and capture it.
    # Prioritize capturing larger groups.
    best_capture_move = None
    max_captured = 0
    processed_opp_groups = set()

    for r, c in opponent:
        if (r, c) in processed_opp_groups:
            continue
        
        stones, liberties = get_group_info(r, c)
        processed_opp_groups.update(stones)
        
        if len(liberties) == 1:
            # Group is in Atari. The move is the liberty.
            move = list(liberties)[0]
            # We must verify if this move is legal (not suicide).
            # Usually capturing moves are safe, but we check if we'd be placed in Atari immediately.
            # For a capture bot, we assume taking the stone is good.
            if len(stones) > max_captured:
                # Check simple legality (not suicide into a closed space if capture fails?)
                # If we capture, the opponent stones are removed, so it's usually safe.
                best_capture_move = move
                max_captured = len(stones)

    if best_capture_move:
        return best_capture_move

    # --- 2. DEFENSE PRIORITY ---
    # Check if any of my groups is in Atari and try to save it.
    processed_my_groups = set()
    defense_moves = []

    for r, c in me:
        if (r, c) in processed_my_groups:
            continue
        
        stones, liberties = get_group_info(r, c)
        processed_my_groups.update(stones)

        if len(liberties) == 1:
            # We are in trouble.
            lib = list(liberties)[0]
            
            # Strategy A: Counter-attack.
            # Check if adding a stone to this liberty captures an adjacent opponent group.
            # Simulate the move briefly by looking at neighbors of the liberty.
            adj_to_lib = get_neighbors(*lib)
            captures_attacker = False
            for nr, nc in adj_to_lib:
                if board[nr, nc] == 2: # Opponent
                    opp_stones, opp_libs = get_group_info(nr, nc)
                    if len(opp_libs) == 1 and lib in opp_libs:
                         # We can capture the attacker
                         captures_attacker = True
                         break
            
            if captures_attacker:
                return lib

            # Strategy B: Extend (Run).
            # Check if playing at the liberty increases our liberties.
            # Simulate move
            board[lib] = 1
            _, new_liberties = get_group_info(*lib)
            board[lib] = 0 # Undo
            
            if len(new_liberties) > 1:
                defense_moves.append(lib)

    if defense_moves:
        return random.choice(defense_moves)

    # --- 3. GOOD SHAPE / RANDOM LEGAL MOVE ---
    # If no immediate tactics, find a sensible move.
    empty_points = []
    for r in range(1, size + 1):
        for c in range(1, size + 1):
            if board[r, c] == 0:
                empty_points.append((r, c))
    
    random.shuffle(empty_points)
    
    # Heuristic: Prefer extensions or moves near existing stones.
    # We'll iterate and check for legality and basic "eye-filling" avoidance.
    
    # Helper to check if a move is clearly bad (filling own eye)
    def is_own_eye(r, c):
        # Simple check: All neighbors are my stones (or wall)
        n_coords = get_neighbors(r, c)
        colors = [board[nr, nc] for nr, nc in n_coords]
        # If all neighbors are me (1) or border (3), treat as eye.
        # Actual eyes are complex, but this is a safe heuristic for a bot.
        return all(col == 1 or col == 3 for col in colors)

    # Helper for suicide check
    def is_suicide(r, c):
        # A move is suicide if:
        # 1. It has no liberties immediately
        # 2. It doesn't capture any opponent stones
        # 3. It doesn't connect to a friendly group with liberties
        
        # Check 1: Immediate liberties
        has_lib = False
        for nr, nc in get_neighbors(r, c):
            if board[nr, nc] == 0:
                has_lib = True
                break
        
        if has_lib:
            return False
            
        # Check 2: Capture?
        for nr, nc in get_neighbors(r, c):
            if board[nr, nc] == 2:
                _, opp_libs = get_group_info(nr, nc)
                if len(opp_libs) == 1 and (r, c) in opp_libs:
                    return False # Capture is possible
        
        # Check 3: Connection?
        for nr, nc in get_neighbors(r, c):
            if board[nr, nc] == 1:
                _, my_libs = get_group_info(nr, nc)
                # If we connect to a group that has > 1 liberty (the spot we are filling + another), it's safe.
                # Actually, simpler: check liberties of the merged group.
                board[r, c] = 1
                _, merged_libs = get_group_info(r, c)
                board[r, c] = 0
                if len(merged_libs) > 0:
                    return False
        
        return True

    # Opening Logic: If board is empty, play corner.
    if not me and not opponent:
        return (4, 4) # Play 4-4 point

    for r, c in empty_points:
        if is_own_eye(r, c):
            continue
        
        if is_suicide(r, c):
            continue
            
        # Proximity heuristic: prefer moves somewhat near existing stones (Manhattan dist <= 4)
        # to avoid playing "pass" equivalent moves in mid-game.
        near_stone = False
        if me or opponent:
            for mr, mc in list(me)[:5] + list(opponent)[:5]: # Check closest few
                if abs(r - mr) + abs(c - mc) <= 5:
                    near_stone = True
                    break
            if not near_stone and len(me) < 100: # Don't play far away if game is young
                # If we really have nothing, just play random legal.
                continue
        
        return (r, c)

    # If all else fails, pass
    return (0, 0)
