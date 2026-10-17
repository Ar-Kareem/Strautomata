
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    import random
    
    BOARD_SIZE = 19
    me_set = set(me)
    opp_set = set(opponent)
    all_stones = me_set | opp_set
    
    def is_valid_move(pos):
        """Check if a position is on the board and empty"""
        r, c = pos
        return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE and pos not in all_stones
    
    def get_neighbors(pos):
        """Get all orthogonal neighbors"""
        r, c = pos
        return [(r+1, c), (r-1, c), (r, c+1), (r, c-1)]
    
    def get_liberties(group):
        """Count liberties of a group of stones"""
        liberties = set()
        for stone in group:
            for neighbor in get_neighbors(stone):
                if neighbor not in all_stones:
                    liberties.add(neighbor)
        return liberties
    
    def get_group(pos, stone_set):
        """Get all connected stones of the same color"""
        if pos not in stone_set:
            return set()
        group = set()
        stack = [pos]
        while stack:
            current = stack.pop()
            if current in group:
                continue
            group.add(current)
            for neighbor in get_neighbors(current):
                if neighbor in stone_set and neighbor not in group:
                    stack.append(neighbor)
        return group
    
    def would_capture(pos, enemy_set):
        """Check if placing a stone would capture enemy stones"""
        captured = []
        for neighbor in get_neighbors(pos):
            if neighbor in enemy_set:
                group = get_group(neighbor, enemy_set)
                liberties = get_liberties(group)
                if liberties == {pos}:  # Only liberty is our new stone
                    captured.extend(group)
        return captured
    
    def is_legal_move(pos):
        """Check if move is legal (not suicide, not occupied)"""
        if not is_valid_move(pos):
            return False
        
        # Check if we capture anything
        if would_capture(pos, opp_set):
            return True
        
        # Check if we would have liberties
        temp_me = me_set | {pos}
        temp_all = all_stones | {pos}
        
        # Find our group after placing stone
        our_group = {pos}
        stack = [pos]
        visited = {pos}
        while stack:
            current = stack.pop()
            for neighbor in get_neighbors(current):
                if neighbor not in visited and neighbor in temp_me:
                    visited.add(neighbor)
                    our_group.add(neighbor)
                    stack.append(neighbor)
        
        # Check liberties
        liberties = set()
        for stone in our_group:
            for neighbor in get_neighbors(stone):
                if neighbor not in temp_all:
                    liberties.add(neighbor)
        
        return len(liberties) > 0
    
    def score_position(pos):
        """Score a position based on multiple factors"""
        r, c = pos
        score = 0.0
        
        # Corner and edge bonuses (early game)
        if len(all_stones) < 30:
            # 3-4 points (traditional opening)
            if (r, c) in [(3, 4), (3, 16), (17, 4), (17, 16), (4, 3), (4, 17), (16, 3), (16, 17)]:
                score += 50
            # Star points
            elif (r, c) in [(4, 4), (4, 10), (4, 16), (10, 4), (10, 10), (10, 16), (16, 4), (16, 10), (16, 16)]:
                score += 45
        
        # Check for captures
        captured = would_capture(pos, opp_set)
        score += len(captured) * 30
        
        # Check if we're in danger and this saves us
        for neighbor in get_neighbors(pos):
            if neighbor in me_set:
                group = get_group(neighbor, me_set)
                liberties = get_liberties(group)
                if len(liberties) <= 2:
                    score += 40  # Saving endangered group
        
        # Count liberties after placing
        temp_me = me_set | {pos}
        group = get_group(pos, temp_me)
        temp_all = all_stones | {pos}
        temp_all -= set(captured)
        liberties = 0
        for stone in group:
            for neighbor in get_neighbors(stone):
                if neighbor not in temp_all:
                    liberties += 1
        score += liberties * 2
        
        # Adjacent to opponent (attacking/reducing)
        opp_neighbors = sum(1 for n in get_neighbors(pos) if n in opp_set)
        score += opp_neighbors * 5
        
        # Adjacent to own stones (connection)
        my_neighbors = sum(1 for n in get_neighbors(pos) if n in me_set)
        score += my_neighbors * 3
        
        # Check if opponent groups nearby are weak
        for neighbor in get_neighbors(pos):
            if neighbor in opp_set:
                opp_group = get_group(neighbor, opp_set)
                opp_libs = get_liberties(opp_group)
                if len(opp_libs) <= 3:
                    score += (4 - len(opp_libs)) * 10
        
        # Distance from center (mid-game preference)
        if 10 < len(all_stones) < 100:
            center_dist = abs(r - 10) + abs(c - 10)
            score -= center_dist * 0.5
        
        return score
    
    # Generate candidate moves
    candidates = []
    
    # Consider all empty points adjacent to existing stones
    candidate_set = set()
    if len(all_stones) == 0:
        # First move - take a corner
        candidate_set = {(4, 4), (4, 16), (16, 4), (16, 16)}
    else:
        for stone in all_stones:
            for neighbor in get_neighbors(stone):
                if is_valid_move(neighbor):
                    candidate_set.add(neighbor)
        
        # Add some random exploration in early game
        if len(all_stones) < 20:
            for _ in range(5):
                candidate_set.add((random.randint(3, 17), random.randint(3, 17)))
    
    # Score and filter legal moves
    for pos in candidate_set:
        if is_legal_move(pos):
            candidates.append((score_position(pos), pos))
    
    # Choose best move
    if candidates:
        candidates.sort(reverse=True)
        _, best_move = candidates[0]
        return (best_move, memory)
    
    # Fallback: pass if no legal moves
    return ((0, 0), memory)
