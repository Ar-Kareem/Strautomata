
import numpy as np
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    A strong heuristic-based Go policy that handles capture/defense tactics
    and general positional strategy.
    """
    BOARD_SIZE = 19
    
    # 0: Empty, 1: Me, 2: Opponent
    board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = 2
        
    DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    def get_neighbors(r, c):
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                yield nr, nc

    # --- 1. Identify Groups and Liberties ---
    # group_map: (19, 19) grid -> group_id
    # group_liberties: dict[group_id] -> set of liberty coordinates (r, c)
    # group_stones: dict[group_id] -> list of stone coordinates
    
    group_map = np.full((BOARD_SIZE, BOARD_SIZE), -1, dtype=int)
    group_liberties = {}
    group_stones = {}
    next_gid = 0
    
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r, c] != 0 and group_map[r, c] == -1:
                color = board[r, c]
                stack = [(r, c)]
                group_map[r, c] = next_gid
                stones = []
                liberties = set()
                seen_liberties = set() # optimization
                
                while stack:
                    curr_r, curr_c = stack.pop()
                    stones.append((curr_r, curr_c))
                    
                    for nr, nc in get_neighbors(curr_r, curr_c):
                        if board[nr, nc] == 0:
                            if (nr, nc) not in seen_liberties:
                                liberties.add((nr, nc))
                                seen_liberties.add((nr, nc))
                        elif board[nr, nc] == color and group_map[nr, nc] == -1:
                            group_map[nr, nc] = next_gid
                            stack.append((nr, nc))
                            
                group_liberties[next_gid] = liberties
                group_stones[next_gid] = stones
                next_gid += 1

    # --- 2. Calculate Heuristic Scores ---
    scores = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=float)
    # Add random noise to break ties/loops
    scores += np.random.rand(BOARD_SIZE, BOARD_SIZE) * 0.5
    
    # Tactical Analysis: Find groups in Atari (1 liberty)
    my_atari_groups = []
    opp_atari_groups = []
    
    for gid, libs in group_liberties.items():
        if len(libs) == 1:
            liberties_list = list(libs)
            stone_coord = group_stones[gid][0]
            if board[stone_coord] == 1: # Me
                my_atari_groups.append(liberties_list[0])
            else: # Opponent
                opp_atari_groups.append(liberties_list[0])

    # Apply Scores
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r, c] != 0:
                scores[r, c] = -99999.0
                continue
            
            # --- Tactical Priority ---
            # Capture Opponent: Highest Priority
            if (r, c) in opp_atari_groups:
                scores[r, c] += 1000.0
            
            # Save Self: High Priority
            if (r, c) in my_atari_groups:
                scores[r, c] += 500.0
            
            # --- Positional Strategy ---
            # Distance from edge (0-indexed)
            dist_edge = min(r, c, BOARD_SIZE - 1 - r, BOARD_SIZE - 1 - c)
            
            # Prefer 3rd and 4th lines (influence & territory balance)
            if dist_edge == 2 or dist_edge == 3:
                scores[r, c] += 5.0
            elif dist_edge < 2:
                # Penalize 1st and 2nd line early on
                scores[r, c] -= 2.0
            
            # Local engagement: Prefer playing near stones
            my_m = 0
            opp_n = 0
            for nr, nc in get_neighbors(r, c):
                val = board[nr, nc]
                if val == 1: my_m += 1
                elif val == 2: opp_n += 1
            
            if my_m > 0: scores[r, c] += 1.0
            if opp_n > 0: scores[r, c] += 1.5
            
            # Suicide/Eye heuristic check
            # Don't fill own eyes (surrounded by me, empty)
            if my_m == 4:
                scores[r, c] -= 20.0
            elif my_m == 3 and dist_edge == 0:
                scores[r, c] -= 20.0

    # --- 3. Validate and Select Move ---
    # Sort empty spots by score descending
    flat_indices = np.argsort(scores, axis=None)[::-1]
    
    for idx in flat_indices:
        r, c = np.unravel_index(idx, scores.shape)
        
        # If score is too low, we essentially have no good moves -> Pass
        if scores[r, c] < -5000:
            break
            
        if board[r, c] != 0: continue
            
        # --- Legality Check: Suicide Rule ---
        # A move is suicide if it has 0 liberties and captures no opponent stones.
        
        captures_something = False
        neighbors = list(get_neighbors(r, c))
        
        # Check adjacent opponent groups to see if they die
        for nr, nc in neighbors:
            if board[nr, nc] == 2:
                n_gid = group_map[nr, nc]
                # If this group has exactly 1 liberty and it is (r,c), move captures
                if len(group_liberties[n_gid]) == 1 and (r, c) in group_liberties[n_gid]:
                    captures_something = True
                    break
        
        if captures_something:
            return (r + 1, c + 1)
            
        # If no capture, check if the resulting stone/group has liberties
        has_liberty = False
        
        # 1. Immediate liberty?
        for nr, nc in neighbors:
            if board[nr, nc] == 0:
                has_liberty = True
                break
        
        # 2. Connection to friendly group with other liberties?
        if not has_liberty:
            for nr, nc in neighbors:
                if board[nr, nc] == 1:
                    n_gid = group_map[nr, nc]
                    libs = group_liberties[n_gid]
                    # If this neighbor group has >1 liberties (one is r,c, others exist),
                    # then merging saves us.
                    if len(libs) > 1:
                        has_liberty = True
                        break
        
        if has_liberty:
            return (r + 1, c + 1)
            
        # If no capture and no liberty -> Suicide (Illegal) -> Skip move
    
    return (0, 0) # Pass
