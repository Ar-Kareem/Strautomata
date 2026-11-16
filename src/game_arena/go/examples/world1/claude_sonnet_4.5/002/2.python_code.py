
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    import random
    
    BOARD_SIZE = 19
    me_set = set(me)
    opp_set = set(opponent)
    all_stones = me_set | opp_set
    
    def is_valid(row, col):
        return 1 <= row <= BOARD_SIZE and 1 <= col <= BOARD_SIZE
    
    def get_neighbors(row, col):
        neighbors = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = row + dr, col + dc
            if is_valid(nr, nc):
                neighbors.append((nr, nc))
        return neighbors
    
    def count_liberties(stones, all_occupied):
        """Count liberties for a group of stones"""
        liberties = set()
        for stone in stones:
            for neighbor in get_neighbors(stone[0], stone[1]):
                if neighbor not in all_occupied:
                    liberties.add(neighbor)
        return len(liberties)
    
    def get_group(stone, stone_set):
        """Get all connected stones of the same color"""
        group = set()
        stack = [stone]
        while stack:
            current = stack.pop()
            if current in group:
                continue
            group.add(current)
            for neighbor in get_neighbors(current[0], current[1]):
                if neighbor in stone_set and neighbor not in group:
                    stack.append(neighbor)
        return group
    
    def is_legal_move(row, col):
        if not is_valid(row, col) or (row, col) in all_stones:
            return False
        
        # Simple suicide check - would need full implementation for complete rules
        temp_all = all_stones | {(row, col)}
        temp_me = me_set | {(row, col)}
        
        # Check if we have liberties
        for neighbor in get_neighbors(row, col):
            if neighbor not in temp_all:
                return True
        
        # Check if we capture something
        for neighbor in get_neighbors(row, col):
            if neighbor in opp_set:
                opp_group = get_group(neighbor, opp_set)
                if count_liberties(opp_group, temp_all) == 0:
                    return True
        
        # Check if we connect to friendly group with liberties
        for neighbor in get_neighbors(row, col):
            if neighbor in me_set:
                my_group = get_group(neighbor, me_set)
                my_group.add((row, col))
                if count_liberties(my_group, temp_all) > 0:
                    return True
        
        return False
    
    # Priority 1: Save our stones in atari
    for stone in me:
        group = get_group(stone, me_set)
        if count_liberties(group, all_stones) == 1:
            for s in group:
                for neighbor in get_neighbors(s[0], s[1]):
                    if is_legal_move(neighbor[0], neighbor[1]):
                        return neighbor
    
    # Priority 2: Capture opponent stones in atari
    for stone in opponent:
        group = get_group(stone, opp_set)
        if count_liberties(group, all_stones) == 1:
            for s in group:
                for neighbor in get_neighbors(s[0], s[1]):
                    if is_legal_move(neighbor[0], neighbor[1]):
                        return neighbor
    
    # Priority 3: Respond to opponent threats (stones with 2 liberties)
    for stone in opponent:
        group = get_group(stone, opp_set)
        libs = count_liberties(group, all_stones)
        if libs == 2 and len(group) >= 2:
            for s in group:
                for neighbor in get_neighbors(s[0], s[1]):
                    if is_legal_move(neighbor[0], neighbor[1]):
                        return neighbor
    
    # Priority 4: Opening moves on star points
    if len(all_stones) < 10:
        star_points = [(4, 4), (4, 16), (16, 4), (16, 16), (10, 10), (4, 10), (10, 4), (16, 10), (10, 16)]
        for point in star_points:
            if is_legal_move(point[0], point[1]):
                return point
    
    # Priority 5: Expand territory - play near our stones
    candidates = []
    for stone in me:
        for neighbor in get_neighbors(stone[0], stone[1]):
            if is_legal_move(neighbor[0], neighbor[1]):
                candidates.append(neighbor)
    
    if candidates:
        return random.choice(candidates)
    
    # Priority 6: Play anywhere legal, preferring center
    moves = []
    for row in range(1, BOARD_SIZE + 1):
        for col in range(1, BOARD_SIZE + 1):
            if is_legal_move(row, col):
                # Prefer center positions
                distance_from_center = abs(row - 10) + abs(col - 10)
                moves.append((distance_from_center, row, col))
    
    if moves:
        moves.sort()
        return (moves[0][1], moves[0][2])
    
    # Last resort: pass
    return (0, 0)
