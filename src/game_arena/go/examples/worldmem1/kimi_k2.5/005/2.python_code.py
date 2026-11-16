
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    import random
    from collections import deque

    # Convert to sets for O(1) lookups
    my_set = set(me)
    opp_set = set(opponent)
    board = {}  # (r,c) -> 1 (me) or 2 (opponent)
    
    for p in me:
        board[p] = 1
    for p in opponent:
        board[p] = 2

    # Helper: Get group liberties and stones for a specific board state
    def get_group(board_dict, r, c, owner):
        """Returns (liberties_set, group_set) for the group at (r,c)"""
        queue = deque([(r, c)])
        group = {(r, c)}
        liberties = set()
        
        while queue:
            cr, cc = queue.popleft()
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = cr + dr, cc + dc
                if 1 <= nr <= 19 and 1 <= nc <= 19:
                    if (nr, nc) not in board_dict:
                        liberties.add((nr, nc))
                    elif board_dict[(nr, nc)] == owner and (nr, nc) not in group:
                        group.add((nr, nc))
                        queue.append((nr, nc))
        return liberties, group

    best_move = (0, 0)  # Pass by default
    best_score = -float('inf')

    # Generate candidate moves (empty intersections)
    candidates = [(r, c) for r in range(1, 20) for c in range(1, 20) if (r, c) not in board]
    random.shuffle(candidates)  # Randomize for tie-breaking

    # Cache for original board opponent groups to avoid recomputation
    opp_group_cache = {}

    for r, c in candidates:
        # Simulate move
        temp_board = board.copy()
        temp_board[(r, c)] = 1
        
        # Check for captures of adjacent opponent groups
        captured_stones = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in opp_set:
                if (nr, nc) not in opp_group_cache:
                    opp_group_cache[(nr, nc)] = get_group(board, nr, nc, 2)
                libs, _ = opp_group_cache[(nr, nc)]
                
                # Check liberties after placing stone (temp_board)
                # If original group had 1 liberty and it's (r,c), it will be captured
                if len(libs) == 1 and (r, c) in libs:
                    # Recalculate group in temp_board to be sure, or just use cached group
                    _, grp = get_group(temp_board, nr, nc, 2)
                    captured_stones.extend(list(grp))
        
        # Remove captured stones for suicide check
        for stone in captured_stones:
            if stone in temp_board:
                del temp_board[stone]
        
        # Check suicide (illegal unless it captures, which we handled)
        my_libs, my_group = get_group(temp_board, r, c, 1)
        if len(my_libs) == 0:
            continue  # Suicide move, skip
        
        # Score calculation
        score = random.random() * 0.1
        
        if captured_stones:
            # High priority for capture
            score += 10000 + len(captured_stones) * 100
        else:
            # Not a capture move
            
            # 1. Defense: Check if we are saving a group in atari
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in my_set:
                    # Check original liberties of that neighbor group
                    if (nr, nc) not in opp_group_cache:  # Reuse cache var name for my groups too
                        opp_group_cache[(nr, nc)] = get_group(board, nr, nc, 1)
                    orig_libs, _ = opp_group_cache[(nr, nc)]
                    if len(orig_libs) == 1:
                        score += 3000  # Saving a stone from capture
                        break
            
            # 2. Threat: Check if we put opponent in atari
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in opp_set:
                    new_opp_libs, _ = get_group(temp_board, nr, nc, 2)
                    if len(new_opp_libs) == 1:
                        score += 200
                        break
            
            # 3. Connection: Bonus for touching own stones
            adj_my = sum(1 for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)] 
                        if (r + dr, c + dc) in my_set)
            score += adj_my * 3
            
            # 4. Liberty: Prefer moves with more liberties (but not too isolated)
            score += min(len(my_libs), 10) * 0.5
            
            # 5. Opening/Center control
            total_stones = len(me) + len(opponent)
            if total_stones < 12:
                # Prefer corners (4-4 points): (4,4), (4,16), (16,4), (16,16)
                corner_bonus = max(0, 10 - min(
                    (r-4)**2 + (c-4)**2,
                    (r-4)**2 + (c-16)**2,
                    (r-16)**2 + (c-4)**2,
                    (r-16)**2 + (c-16)**2
                )**0.5)
                score += corner_bonus
            else:
                # Slight preference for center in mid/late game
                score -= ((r - 10)**2 + (c - 10)**2) * 0.005
            
            # 6. Avoid filling eyes (don't play inside own territory surrounded on 4 sides)
            if adj_my == 4:
                # Check if all 4 neighbors are mine (simple eye fill)
                is_eye_fill = True
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if not (1 <= nr <= 19 and 1 <= nc <= 19 and temp_board.get((nr, nc)) == 1):
                        is_eye_fill = False
                        break
                if is_eye_fill:
                    score -= 1000  # Heavy penalty
        
        if score > best_score:
            best_score = score
            best_move = (r, c)

    # If no valid move found (very rare), pass
    if best_score == -float('inf'):
        return (0, 0), {}
    
    return best_move, {}
