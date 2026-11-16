
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Convert to sets for faster lookup
    me_set = set(me)
    opponent_set = set(opponent)
    board = [[0 for _ in range(20)] for _ in range(20)]  # 1-indexed
    
    # Mark positions on board: 1 for me, 2 for opponent
    for r, c in me:
        board[r][c] = 1
    for r, c in opponent:
        board[r][c] = 2
    
    def is_on_board(r, c):
        return 1 <= r <= 19 and 1 <= c <= 19
    
    def get_neighbors(r, c):
        return [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
    
    def count_liberties(stone_list):
        """Count liberties for a group of stones"""
        group = set(stone_list)
        liberties = set()
        for r, c in group:
            for nr, nc in get_neighbors(r, c):
                if is_on_board(nr, nc) and (nr, nc) not in me_set and (nr, nc) not in opponent_set:
                    liberties.add((nr, nc))
        return liberties
    
    def get_group(r, c, player_set):
        """Get connected group of stones"""
        if (r, c) not in player_set:
            return set()
        
        group = set()
        stack = [(r, c)]
        
        while stack:
            current = stack.pop()
            if current in group:
                continue
            group.add(current)
            
            for nr, nc in get_neighbors(current[0], current[1]):
                if (nr, nc) in player_set and (nr, nc) not in group:
                    stack.append((nr, nc))
        
        return group
    
    def get_opponent_groups():
        """Get all opponent groups"""
        visited = set()
        groups = []
        for r, c in opponent:
            if (r, c) not in visited:
                group = get_group(r, c, opponent_set)
                groups.append(group)
                visited.update(group)
        return groups
    
    def get_my_groups():
        """Get all my groups"""
        visited = set()
        groups = []
        for r, c in me:
            if (r, c) not in visited:
                group = get_group(r, c, me_set)
                groups.append(group)
                visited.update(group)
        return groups
    
    # 1. Check for captures
    opponent_groups = get_opponent_groups()
    for group in opponent_groups:
        liberties = count_liberties(group)
        if len(liberties) == 1:
            # Capture move available
            move = list(liberties)[0]
            return move
    
    # 2. Check for own groups in atari
    my_groups = get_my_groups()
    for group in my_groups:
        liberties = count_liberties(group)
        if len(liberties) == 1:
            # Save own group
            move = list(liberties)[0]
            return move
    
    # 3. Strategic move - expand toward center
    # Score potential moves based on distance to center and existing stones
    best_move = None
    best_score = -1
    
    # Generate candidate moves near our stones
    candidate_moves = set()
    for r, c in me:
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                nr, nc = r + dr, c + dc
                if is_on_board(nr, nc) and (nr, nc) not in me_set and (nr, nc) not in opponent_set:
                    candidate_moves.add((nr, nc))
    
    # If no candidates near our stones, consider all empty positions
    if not candidate_moves:
        for r in range(1, 20):
            for c in range(1, 20):
                if (r, c) not in me_set and (r, c) not in opponent_set:
                    candidate_moves.add((r, c))
    
    # Score candidate moves
    center_r, center_c = 10, 10
    for r, c in candidate_moves:
        # Distance to center (lower is better)
        dist_to_center = abs(r - center_r) + abs(c - center_c)
        score = 20 - dist_to_center  # Prefer center positions
        
        # Bonus for being near own stones
        for mr, mc in me:
            dist = abs(r - mr) + abs(c - mc)
            if dist == 1:  # Directly adjacent
                score += 3
            elif dist == 2:  # One space away
                score += 1
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    if best_move:
        return best_move
    
    # 4. Fallback: random legal move
    legal_moves = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in me_set and (r, c) not in opponent_set:
                legal_moves.append((r, c))
    
    if legal_moves:
        return random.choice(legal_moves)
    
    # 5. Final fallback: pass
    return (0, 0)
