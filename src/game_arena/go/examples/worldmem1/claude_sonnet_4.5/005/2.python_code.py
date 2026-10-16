
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    import random
    
    BOARD_SIZE = 19
    
    def is_valid_move(row, col, me_set, opp_set):
        """Check if a move is on the board and not occupied"""
        if row < 1 or row > BOARD_SIZE or col < 1 or col > BOARD_SIZE:
            return False
        return (row, col) not in me_set and (row, col) not in opp_set
    
    def get_neighbors(row, col):
        """Get all adjacent positions"""
        neighbors = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbors.append((row + dr, col + dc))
        return neighbors
    
    def count_liberties(stones, me_set, opp_set):
        """Count liberties for a group of stones"""
        liberties = set()
        for stone in stones:
            for neighbor in get_neighbors(stone[0], stone[1]):
                if 1 <= neighbor[0] <= BOARD_SIZE and 1 <= neighbor[1] <= BOARD_SIZE:
                    if neighbor not in me_set and neighbor not in opp_set:
                        liberties.add(neighbor)
        return liberties
    
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
    
    def would_capture(move, me_set, opp_set):
        """Check if a move would capture opponent stones"""
        captures = []
        for neighbor in get_neighbors(move[0], move[1]):
            if neighbor in opp_set:
                group = get_group(neighbor, opp_set)
                # Simulate the move
                temp_me = me_set | {move}
                liberties = count_liberties(group, temp_me, opp_set)
                if len(liberties) == 0:
                    captures.extend(group)
        return captures
    
    def is_suicide(move, me_set, opp_set):
        """Check if a move is suicidal (illegal in most rulesets)"""
        # If the move captures something, it's not suicide
        if would_capture(move, me_set, opp_set):
            return False
        
        # Check if the move would have liberties
        temp_me = me_set | {move}
        group = get_group(move, temp_me)
        liberties = count_liberties(group, temp_me, opp_set)
        return len(liberties) == 0
    
    def evaluate_move(move, me_set, opp_set):
        """Evaluate the quality of a move"""
        score = 0.0
        row, col = move
        
        # Capture value
        captures = would_capture(move, me_set, opp_set)
        score += len(captures) * 30
        
        # Check if move saves our stones from atari
        for neighbor in get_neighbors(row, col):
            if neighbor in me_set:
                group = get_group(neighbor, me_set)
                liberties = count_liberties(group, me_set, opp_set)
                if len(liberties) == 1:  # In atari
                    score += 25
        
        # Check if move puts opponent in atari
        temp_me = me_set | {move}
        for neighbor in get_neighbors(row, col):
            if neighbor in opp_set:
                group = get_group(neighbor, opp_set)
                liberties = count_liberties(group, temp_me, opp_set)
                if len(liberties) == 1:
                    score += 15
        
        # Strategic position value (corners and edges are valuable)
        dist_from_edge = min(row - 1, BOARD_SIZE - row, col - 1, BOARD_SIZE - col)
        if dist_from_edge == 3:  # Star points and similar
            score += 8
        elif dist_from_edge <= 2:  # Near edge
            score += 5
        
        # Connectivity - prefer moves near our stones
        friendly_neighbors = sum(1 for n in get_neighbors(row, col) if n in me_set)
        score += friendly_neighbors * 3
        
        # Influence - count nearby friendly stones
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = row + dr, col + dc
                if (nr, nc) in me_set:
                    score += 1
                elif (nr, nc) in opp_set:
                    score += 0.5  # Some value in being near opponent
        
        return score
    
    me_set = set(me)
    opp_set = set(opponent)
    
    # Star points for opening
    star_points = [(4, 4), (4, 16), (16, 4), (16, 16), (10, 10), (4, 10), (10, 4), (16, 10), (10, 16)]
    
    # Early game - use star points
    total_stones = len(me) + len(opponent)
    if total_stones < 6:
        for point in star_points:
            if is_valid_move(point[0], point[1], me_set, opp_set):
                return (point, memory)
    
    # Generate and evaluate all legal moves
    candidates = []
    for row in range(1, BOARD_SIZE + 1):
        for col in range(1, BOARD_SIZE + 1):
            if is_valid_move(row, col, me_set, opp_set):
                if not is_suicide((row, col), me_set, opp_set):
                    score = evaluate_move((row, col), me_set, opp_set)
                    candidates.append(((row, col), score))
    
    # If no valid moves, pass
    if not candidates:
        return ((0, 0), memory)
    
    # Sort by score and pick the best
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Add some randomness to top moves to avoid predictability
    top_moves = candidates[:min(5, len(candidates))]
    weights = [move[1] + 1 for move in top_moves]  # +1 to avoid zero weights
    best_move = random.choices(top_moves, weights=weights, k=1)[0][0]
    
    return (best_move, memory)
