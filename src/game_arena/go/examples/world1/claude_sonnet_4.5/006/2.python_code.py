
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    import random
    
    BOARD_SIZE = 19
    
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set
    
    def is_valid(r, c):
        return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE
    
    def get_neighbors(r, c):
        neighbors = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if is_valid(nr, nc):
                neighbors.append((nr, nc))
        return neighbors
    
    def count_liberties(group, board_me, board_opp):
        liberties = set()
        for stone in group:
            for neighbor in get_neighbors(stone[0], stone[1]):
                if neighbor not in board_me and neighbor not in board_opp:
                    liberties.add(neighbor)
        return len(liberties)
    
    def get_group(stone, board):
        group = set()
        stack = [stone]
        while stack:
            current = stack.pop()
            if current in group:
                continue
            group.add(current)
            for neighbor in get_neighbors(current[0], current[1]):
                if neighbor in board and neighbor not in group:
                    stack.append(neighbor)
        return group
    
    # Find opponent groups in atari (1 liberty)
    def find_capture_moves():
        captures = []
        checked = set()
        for stone in opponent:
            if stone in checked:
                continue
            group = get_group(stone, opp_set)
            checked.update(group)
            if count_liberties(group, me_set, opp_set) == 1:
                # Find the liberty
                for s in group:
                    for neighbor in get_neighbors(s[0], s[1]):
                        if neighbor not in occupied:
                            captures.append((neighbor, len(group)))
        return captures
    
    # Find our groups in atari that need defense
    def find_defense_moves():
        defenses = []
        checked = set()
        for stone in me:
            if stone in checked:
                continue
            group = get_group(stone, me_set)
            checked.update(group)
            if count_liberties(group, me_set, opp_set) == 1:
                for s in group:
                    for neighbor in get_neighbors(s[0], s[1]):
                        if neighbor not in occupied:
                            defenses.append((neighbor, len(group)))
        return defenses
    
    # Early game: play on strategic points
    if len(occupied) < 10:
        star_points = [(4, 4), (4, 16), (16, 4), (16, 16), (10, 10),
                       (4, 10), (10, 4), (10, 16), (16, 10)]
        for point in star_points:
            if point not in occupied:
                return point
    
    # Try to capture opponent stones
    captures = find_capture_moves()
    if captures:
        # Prioritize larger captures
        captures.sort(key=lambda x: x[1], reverse=True)
        return captures[0][0]
    
    # Defend our stones in atari
    defenses = find_defense_moves()
    if defenses:
        defenses.sort(key=lambda x: x[1], reverse=True)
        return defenses[0][0]
    
    # Calculate influence map
    influence = {}
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if (r, c) in occupied:
                continue
            
            score = 0.0
            # Distance-based influence
            for stone in me:
                dist = abs(r - stone[0]) + abs(c - stone[1])
                if dist <= 3:
                    score += (4 - dist) * 2
            
            for stone in opponent:
                dist = abs(r - stone[0]) + abs(c - stone[1])
                if dist <= 3:
                    score -= (4 - dist) * 1.5
            
            # Bonus for edge and corner proximity in opening
            if len(occupied) < 30:
                edge_dist = min(r - 1, BOARD_SIZE - r, c - 1, BOARD_SIZE - c)
                if edge_dist <= 3:
                    score += (4 - edge_dist) * 0.5
            
            influence[(r, c)] = score
    
    # Find best move by influence
    if influence:
        best_moves = sorted(influence.items(), key=lambda x: x[1], reverse=True)
        # Add some randomness to top moves to avoid predictability
        top_n = min(5, len(best_moves))
        if top_n > 0 and best_moves[0][1] > 0:
            return random.choice(best_moves[:top_n])[0]
    
    # Fallback: find any legal move
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if (r, c) not in occupied:
                return (r, c)
    
    # Pass if no legal moves
    return (0, 0)
