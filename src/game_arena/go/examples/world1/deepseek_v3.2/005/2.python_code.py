
import random
import math
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    # Convert to sets for faster lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    all_stones = my_stones.union(opp_stones)
    
    BOARD_SIZE = 19
    # Directions: up, down, left, right
    DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    def is_on_board(pos):
        r, c = pos
        return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE
    
    def get_adjacent(pos):
        r, c = pos
        return [(r + dr, c + dc) for dr, dc in DIRECTIONS]
    
    def count_liberties(group, player_stones, opponent_stones):
        """Count liberties of a connected group."""
        liberties = set()
        for stone in group:
            for adj in get_adjacent(stone):
                if is_on_board(adj) and adj not in player_stones and adj not in opponent_stones:
                    liberties.add(adj)
        return len(liberties)
    
    def find_connected_group(start, stones):
        """BFS to find connected group of same color."""
        visited = set()
        stack = [start]
        group = set()
        while stack:
            stone = stack.pop()
            if stone in visited:
                continue
            visited.add(stone)
            group.add(stone)
            for adj in get_adjacent(stone):
                if adj in stones and adj not in visited:
                    stack.append(adj)
        return group
    
    def find_all_groups(stones):
        """Find all connected groups for a player."""
        groups = []
        visited = set()
        for stone in stones:
            if stone not in visited:
                group = find_connected_group(stone, stones)
                groups.append(group)
                visited.update(group)
        return groups
    
    # 1. Check for immediate captures
    my_groups = find_all_groups(my_stones)
    opp_groups = find_all_groups(opp_stones)
    
    # Capture opponent groups with 1 liberty
    for group in opp_groups:
        if count_liberties(group, opp_stones, my_stones) == 1:
            # Find the liberty
            for stone in group:
                for adj in get_adjacent(stone):
                    if is_on_board(adj) and adj not in all_stones:
                        # Check if move is legal (not suicide)
                        # Simple suicide check: if the move creates a group with at least 1 liberty
                        test_my = my_stones.union({adj})
                        test_group = find_connected_group(adj, test_my)
                        if count_liberties(test_group, test_my, opp_stones) > 0:
                            return adj
    
    # 2. Defend my groups with 1 liberty
    for group in my_groups:
        if count_liberties(group, my_stones, opp_stones) == 1:
            # Find and defend the liberty
            for stone in group:
                for adj in get_adjacent(stone):
                    if is_on_board(adj) and adj not in all_stones:
                        # Check if defense move is legal
                        test_my = my_stones.union({adj})
                        test_group = find_connected_group(adj, test_my)
                        if count_liberties(test_group, test_my, opp_stones) > 0:
                            return adj
    
    # 3. Strategic move selection
    # Generate candidate moves
    candidates = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            pos = (r, c)
            if pos not in all_stones:
                candidates.append(pos)
    
    if not candidates:
        return (0, 0)  # Pass if no legal moves (shouldn't happen)
    
    # Score each candidate
    best_move = None
    best_score = -float('inf')
    
    for move in candidates:
        score = 0
        
        # Base score for being on board
        score += 1
        
        # Prefer center (influence)
        center_r, center_c = 10, 10
        dist_to_center = math.sqrt((move[0] - center_r)**2 + (move[1] - center_c)**2)
        score += (19 - dist_to_center) * 0.5
        
        # Prefer moves near my existing stones (reinforce)
        for my_stone in my_stones:
            dist = abs(move[0] - my_stone[0]) + abs(move[1] - my_stone[1])
            if dist <= 3:
                score += (4 - dist) * 0.3
        
        # Avoid being too close to opponent (unless attacking)
        for opp_stone in opp_stones:
            dist = abs(move[0] - opp_stone[0]) + abs(move[1] - opp_stone[1])
            if dist == 1:  # Direct contact
                score += 2  # Aggressive play
            elif dist <= 2:
                score += 0.5
        
        # Check liberties after move
        test_my = my_stones.union({move})
        test_group = find_connected_group(move, test_my)
        liberties = count_liberties(test_group, test_my, opp_stones)
        score += liberties * 0.8
        
        # Corner/side control in early-mid game
        stone_count = len(my_stones) + len(opp_stones)
        if stone_count < 60:  # Early game
            # Prefer corners and sides
            if move[0] in [1, 19] and move[1] in [1, 19]:
                score += 3  # Corners
            elif move[0] in [1, 19] or move[1] in [1, 19]:
                score += 1.5  # Sides
        
        # Check if move is legal (no suicide)
        if liberties == 0:
            score = -100  # Illegal suicide move
        
        if score > best_score:
            best_score = score
            best_move = move
    
    # Fallback: random legal move
    if best_move is None or best_score <= 0:
        legal_moves = [m for m in candidates if m not in all_stones]
        if legal_moves:
            return random.choice(legal_moves)
        else:
            return (0, 0)
    
    return best_move
