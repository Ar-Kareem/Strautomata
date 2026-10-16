
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    import random
    
    BOARD_SIZE = 19
    
    # Convert to sets for faster lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    all_stones = my_stones | opp_stones
    
    def is_valid(row, col):
        return 1 <= row <= BOARD_SIZE and 1 <= col <= BOARD_SIZE
    
    def is_empty(row, col):
        return (row, col) not in all_stones
    
    def get_neighbors(row, col):
        neighbors = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = row + dr, col + dc
            if is_valid(nr, nc):
                neighbors.append((nr, nc))
        return neighbors
    
    def count_liberties(row, col, stone_set):
        """Count liberties of a group containing stone at (row, col)"""
        if (row, col) not in stone_set:
            return 0
        
        group = set()
        liberties = set()
        stack = [(row, col)]
        
        while stack:
            r, c = stack.pop()
            if (r, c) in group:
                continue
            group.add((r, c))
            
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in stone_set and (nr, nc) not in group:
                    stack.append((nr, nc))
                elif (nr, nc) not in all_stones:
                    liberties.add((nr, nc))
        
        return len(liberties), liberties, group
    
    def find_atari_defense():
        """Find if any of my groups are in atari and need defense"""
        checked = set()
        for r, c in my_stones:
            if (r, c) in checked:
                continue
            lib_count, liberties, group = count_liberties(r, c, my_stones)
            checked.update(group)
            if lib_count == 1:
                liberty = list(liberties)[0]
                if is_empty(liberty[0], liberty[1]):
                    return liberty
        return None
    
    def find_capture_move():
        """Find if we can capture any opponent groups"""
        checked = set()
        for r, c in opp_stones:
            if (r, c) in checked:
                continue
            lib_count, liberties, group = count_liberties(r, c, opp_stones)
            checked.update(group)
            if lib_count == 1:
                liberty = list(liberties)[0]
                if is_empty(liberty[0], liberty[1]):
                    return liberty
        return None
    
    def evaluate_position(row, col):
        """Evaluate how good a position is"""
        if not is_empty(row, col):
            return -1000
        
        score = 0
        
        # Corner and edge values
        dist_from_edge = min(row - 1, BOARD_SIZE - row, col - 1, BOARD_SIZE - col)
        if dist_from_edge == 3:  # 4-4 points and similar
            score += 15
        elif dist_from_edge == 2:  # 3-3 points
            score += 12
        elif dist_from_edge <= 4:
            score += 8
        
        # Proximity to own stones (extending/connecting)
        min_dist_to_mine = BOARD_SIZE
        for mr, mc in my_stones:
            dist = abs(row - mr) + abs(col - mc)
            min_dist_to_mine = min(min_dist_to_mine, dist)
            if dist == 1:
                score += 20  # Adjacent to own stone
            elif dist == 2:
                score += 10  # Knight's move or one space away
            elif dist == 3:
                score += 5
        
        # Distance from opponent stones
        min_dist_to_opp = BOARD_SIZE
        for or_, oc in opp_stones:
            dist = abs(row - or_) + abs(col - oc)
            min_dist_to_opp = min(min_dist_to_opp, dist)
            if dist == 1:
                score += 8  # Can pressure opponent
            elif dist == 2:
                score += 4
        
        # Avoid overcrowding
        if min_dist_to_mine < 2 and len(my_stones) > 5:
            score -= 5
        
        return score
    
    # Opening book - first few moves
    star_points = [(4, 4), (4, 16), (16, 4), (16, 16)]
    if len(all_stones) < 8:
        random.shuffle(star_points)
        for r, c in star_points:
            if is_empty(r, c):
                return (r, c)
    
    # Tactical: Defend against atari
    defense = find_atari_defense()
    if defense:
        return defense
    
    # Tactical: Capture opponent stones
    capture = find_capture_move()
    if capture:
        return capture
    
    # Strategic: Find best position
    candidates = []
    for row in range(1, BOARD_SIZE + 1):
        for col in range(1, BOARD_SIZE + 1):
            if is_empty(row, col):
                score = evaluate_position(row, col)
                if score > 0:
                    candidates.append((score, row, col))
    
    if candidates:
        candidates.sort(reverse=True)
        # Add some randomness among top moves
        top_candidates = [c for c in candidates if c[0] >= candidates[0][0] - 5]
        if top_candidates:
            _, row, col = random.choice(top_candidates[:min(5, len(top_candidates))])
            return (row, col)
    
    # Fallback: find any legal move
    for row in range(1, BOARD_SIZE + 1):
        for col in range(1, BOARD_SIZE + 1):
            if is_empty(row, col):
                return (row, col)
    
    # Last resort: pass
    return (0, 0)
