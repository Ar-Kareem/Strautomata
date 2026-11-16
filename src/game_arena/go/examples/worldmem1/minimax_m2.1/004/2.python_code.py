
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """
    Go policy that prioritizes:
    1. Capturing opponent stones
    2. Defending against captures
    3. Strategic territory and influence
    
    Args:
        me: List of (row, col) tuples for our stones
        opponent: List of (row, col) tuples for opponent's stones
        memory: Dictionary for storing state between calls
    
    Returns:
        tuple: ((row, col) move, memory_dict)
    """
    
    # Create sets for efficient lookup
    my_stones = set(me)
    opponent_stones = set(opponent)
    all_stones = my_stones | opponent_stones
    
    # All possible empty points
    empty_points = set()
    for row in range(1, 20):
        for col in range(1, 20):
            point = (row, col)
            if point not in all_stones:
                empty_points.add(point)
    
    def get_group_and_liberties(start_pos, stone_set):
        """
        BFS to find a connected group and its liberties.
        Returns: (set of stones in group, set of liberty points)
        """
        if start_pos not in stone_set:
            return set(), set()
            
        group = set()
        liberties = set()
        queue = [start_pos]
        visited = set()
        
        while queue:
            pos = queue.pop(0)
            if pos in visited:
                continue
            visited.add(pos)
            group.add(pos)
            
            # Check 4 adjacent points
            for d_row, d_col in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                adj_row, adj_col = pos[0] + d_row, pos[1] + d_col
                if 1 <= adj_row <= 19 and 1 <= adj_col <= 19:
                    adj_point = (adj_row, adj_col)
                    if adj_point in stone_set and adj_point not in visited:
                        queue.append(adj_point)
                    elif adj_point not in all_stones:
                        liberties.add(adj_point)
        
        return group, liberties
    
    def count_group_liberties(stone_pos, stone_set):
        """Count total liberties for the group containing stone_pos."""
        group, liberties = get_group_and_liberties(stone_pos, stone_set)
        return len(liberties)
    
    def simulate_capture(move, stone_set):
        """
        Simulate placing a stone at move and check if it captures any groups.
        Returns the set of captured opponent stones.
        """
        if move in stone_set:
            return set()
            
        # Temporary board state with the move played
        temp_all_stones = all_stones | {move}
        temp_stone_set = stone_set | {move}
        captured = set()
        
        # Check each adjacent opponent group
        for d_row, d_col in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            adj_row, adj_col = move[0] + d_row, move[1] + d_col
            if 1 <= adj_row <= 19 and 1 <= adj_col <= 19:
                adj_point = (adj_row, adj_col)
                if adj_point in stone_set:
                    group, liberties = get_group_and_liberties(adj_point, stone_set)
                    # Group has no liberties after our move - it's captured!
                    if len(liberties) == 0 and len(group) > 0:
                        captured.update(group)
        
        return captured
    
    def is_suicidal(move):
        """Check if a move is suicidal (places stone with no liberties)."""
        # Temporarily place our stone
        temp_my_stones = my_stones | {move}
        
        # Check if the new stone has liberties or captures something
        group, liberties = get_group_and_liberties(move, temp_my_stones)
        if len(liberties) == 0:
            # No liberties - but check if we captured opponent stones
            captured = simulate_capture(move, opponent_stones)
            return len(captured) == 0
        
        return False
    
    # PRIORITY 1: Check for capturing moves
    capture_moves = []
    for move in empty_points:
        if is_suicidal(move):
            continue
            
        captured = simulate_capture(move, opponent_stones)
        if len(captured) > 0:
            capture_moves.append((move, len(captured)))
    
    # Sort by number of captured stones (descending)
    capture_moves.sort(key=lambda x: -x[1])
    if capture_moves:
        return capture_moves[0][0], memory
    
    # PRIORITY 2: Defensive moves - save groups in atari
    defense_moves = []
    for move in empty_points:
        if is_suicidal(move):
            continue
        
        # Check if this move saves a group in atari
        for d_row, d_col in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            adj_row, adj_col = move[0] + d_row, move[1] + d_col
            if 1 <= adj_row <= 19 and 1 <= adj_col <= 19:
                adj_point = (adj_row, adj_col)
                if adj_point in my_stones:
                    current_liberties = count_group_liberties(adj_point, my_stones)
                    if current_liberties == 1:  # Group is in atari
                        # Simulate placing our stone
                        temp_my = my_stones | {move}
                        new_liberties = count_group_liberties(adj_point, temp_my)
                        if new_liberties > 1:  # Move saves the group
                            defense_moves.append((move, 1))  # Priority 1 defense
                            break
    
    if defense_moves:
        return defense_moves[0][0], memory
    
    # PRIORITY 3: Extend from existing stones (influence)
    strategic_moves = []
    for move in empty_points:
        if is_suicidal(move):
            continue
            
        score = 0
        
        # Bonus for being near center (16,16 is the ideal center)
        center_distance = abs(move[0] - 10) + abs(move[1] - 10)
        score += (20 - center_distance) * 2
        
        # Bonus for extending from own stones
        for d_row, d_col in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            adj_row, adj_col = move[0] + d_row, move[1] + d_col
            if 1 <= adj_row <= 19 and 1 <= adj_col <= 19:
                adj_point = (adj_row, adj_col)
                if adj_point in my_stones:
                    score += 15
                elif adj_point in opponent_stones:
                    score += 5  # Proximity to opponent (pressure)
        
        strategic_moves.append((move, score))
    
    # Sort by score (descending)
    strategic_moves.sort(key=lambda x: -x[1])
    if strategic_moves:
        return strategic_moves[0][0], memory
    
    # PRIORITY 4: Opening points if board is mostly empty
    if len(all_stones) < 10:  # Early game
        opening_points = [
            (4, 4), (4, 16), (16, 4), (16, 16),  # 4-4 points
            (4, 5), (4, 15), (5, 4), (5, 15),    # 3-4 points
            (15, 4), (15, 15), (16, 5), (16, 15) # Other 3-4 points
        ]
        
        for point in opening_points:
            if point in empty_points:
                return point, memory
    
    # PRIORITY 5: Any legal move
    for move in empty_points:
        if not is_suicidal(move):
            return move, memory
    
    # No valid moves, pass
    return (0, 0), memory
