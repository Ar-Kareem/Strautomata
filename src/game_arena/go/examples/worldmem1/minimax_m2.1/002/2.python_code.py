
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """
    A smart Go policy that uses multi-factor heuristic evaluation.
    
    Priority order:
    1. Capture opponent stones if possible
    2. Defend own stones in atari
    3. Take valuable territory
    4. Build influence toward center
    5. Extend from existing stones
    """
    BOARD_SIZE = 19
    
    # Build board representation (0=empty, 1=me, 2=opponent)
    board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    
    for r, c in me:
        board[r-1][c-1] = 1
    for r, c in opponent:
        board[r-1][c-1] = 2
    
    # Find all groups and their liberties
    def find_groups(player):
        visited = [[False for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        groups = []
        
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] == player and not visited[r][c]:
                    group, liberties = flood_fill_group(r, c, player, visited)
                    groups.append((group, liberties))
        return groups
    
    def flood_fill_group(start_r, start_c, player, visited):
        stack = [(start_r, start_c)]
        group = []
        liberties = set()
        
        while stack:
            r, c = stack.pop()
            if visited[r][c]:
                continue
            visited[r][c] = True
            group.append((r, c))
            
            # Check neighbors for liberties
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    if board[nr][nc] == 0:
                        liberties.add((nr, nc))
                    elif board[nr][nc] == player and not visited[nr][nc]:
                        stack.append((nr, nc))
        
        return group, liberties
    
    # Get groups for both players
    my_groups = find_groups(1)
    opp_groups = find_groups(2)
    
    # Find all empty points
    empty_points = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == 0:
                empty_points.append((r, c))
    
    if not empty_points:
        return (0, 0), memory
    
    def get_liberties_after_move(move_r, move_c, player):
        """Calculate liberties if we place a stone at move_r, move_c"""
        # Temporarily place stone
        board[move_r][move_c] = player
        
        # Check all connected groups
        visited = [[False for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        all_liberties = set()
        
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] == player and not visited[r][c]:
                    _, group_liberties = flood_fill_group(r, c, player, visited)
                    all_liberties.update(group_liberties)
        
        # Remove the stone
        board[move_r][move_c] = 0
        
        # Remove the move position itself if it's in liberties (it's now occupied)
        all_liberties.discard((move_r, move_c))
        
        return all_liberties
    
    def would_capture(move_r, move_c, player):
        """Check if placing at move_r, move_c would capture opponent stones"""
        # Temporarily place stone
        board[move_r][move_c] = player
        
        opponent_player = 2 if player == 1 else 1
        captured = []
        
        # Check if any opponent groups now have 0 liberties
        visited = [[False for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] == opponent_player and not visited[r][c]:
                    group, liberties = flood_fill_group(r, c, opponent_player, visited)
                    if len(liberties) == 0:
                        captured.extend(group)
        
        # Remove the stone
        board[move_r][move_c] = 0
        
        return captured
    
    def is_suicide(move_r, move_c, player):
        """Check if move is suicide (places stone with no liberties and captures nothing)"""
        board[move_r][move_c] = player
        liberties = get_liberties_after_move(move_r, move_c, player)
        captures = would_capture(move_r, move_c, player)
        board[move_r][move_c] = 0
        
        return len(liberties) == 0 and len(captures) == 0
    
    def count_adjacent(r, c, player):
        """Count adjacent stones of a given player"""
        count = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                if board[nr][nc] == player:
                    count += 1
        return count
    
    def calculate_territorial_value(r, c):
        """Calculate potential territorial value of a point"""
        value = 0
        
        # Check 3x3 area around the point
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    if board[nr][nc] == 0:
                        value += 1
                    elif board[nr][nc] == 1:  # Our stone nearby
                        value += 0.5
        
        return value
    
    def calculate_center_bonus(r, c):
        """Calculate bonus for being closer to center"""
        center = BOARD_SIZE // 2
        distance_to_center = abs(r - center) + abs(c - center)
        max_distance = 2 * center
        return (max_distance - distance_to_center) / max_distance
    
    # Evaluate each possible move
    best_move = None
    best_score = -float('inf')
    
    for move_r, move_c in empty_points:
        # Skip suicide moves (unless they capture)
        if is_suicide(move_r, move_c, 1):
            continue
        
        score = 0
        
        # PRIORITY 1: Check if this move captures opponent stones
        captures = would_capture(move_r, move_c, 1)
        if len(captures) > 0:
            score += 1000 * len(captures)  # High priority for captures
        
        # PRIORITY 2: Check if this move saves our atari stones
        # Place stone temporarily and check our groups
        board[move_r][move_c] = 1
        my_liberties_after = get_liberties_after_move(move_r, move_c, 1)
        board[move_r][move_c] = 0
        
        # Check if any of our groups were in atari and are now safe
        saved_from_atari = False
        for group, liberties in my_groups:
            if len(liberties) == 1 and (liberties[0] if liberties else None) == (move_r, move_c):
                saved_from_atari = True
                break
        
        if saved_from_atari:
            score += 500
        
        # Check if this move itself would be in atari (bad)
        if len(my_liberties_after) == 1:
            score -= 200  # Penalty for playing into atari
        
        # PRIORITY 3: Number of adjacent stones (connect and extend)
        adjacent_own = count_adjacent(move_r, move_c, 1)
        adjacent_opp = count_adjacent(move_r, move_c, 2)
        score += adjacent_own * 10
        score -= adjacent_opp * 5  # Slight penalty for adjacent opponent
        
        # PRIORITY 4: Territorial value
        score += calculate_territorial_value(move_r, move_c) * 5
        
        # PRIORITY 5: Center control bonus
        score += calculate_center_bonus(move_r, move_c) * 20
        
        # PRIORITY 6: Liberty count after move
        score += len(my_liberties_after) * 3
        
        # Small randomization to avoid predictable play
        score += hash((move_r, move_c, len(me))) % 10
        
        if score > best_score:
            best_score = score
            best_move = (move_r + 1, move_c + 1)  # Convert to 1-indexed
    
    # If no good move found, pass
    if best_move is None:
        return (0, 0), memory
    
    return best_move, memory
