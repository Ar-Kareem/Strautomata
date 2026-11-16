
import numpy as np
from collections import deque
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board_size = 19
    # Convert positions to sets for faster lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    all_stones = my_stones.union(opp_stones)
    
    # Check all possible moves for legality and strategic value
    candidates = []
    
    # First priority: capture opponent groups with 1 liberty
    capture_move = find_capture_move(opp_stones, my_stones, board_size)
    if capture_move:
        return capture_move
    
    # Second priority: defend our groups with 1 liberty
    defense_move = find_defense_move(my_stones, opp_stones, board_size)
    if defense_move:
        return defense_move
    
    # Third priority: play in corners/sides if available
    corner_move = find_corner_move(my_stones, opp_stones, board_size)
    if corner_move:
        return corner_move
    
    # Fourth priority: play near existing stones for influence
    influence_move = find_influence_move(my_stones, opp_stones, board_size)
    if influence_move:
        return influence_move
    
    # Fallback: random legal move
    return find_random_move(my_stones, opp_stones, board_size)

def find_capture_move(opp_stones, my_stones, board_size):
    # Check for opponent groups with exactly 1 liberty
    for stone in opp_stones:
        group, liberties = find_group_and_liberties(stone, opp_stones, my_stones, board_size)
        if len(liberties) == 1:
            return liberties.pop()
    return None

def find_defense_move(my_stones, opp_stones, board_size):
    # Check for our groups with exactly 1 liberty
    for stone in my_stones:
        group, liberties = find_group_and_liberties(stone, my_stones, opp_stones, board_size)
        if len(liberties) == 1:
            return liberties.pop()
    return None

def find_corner_move(my_stones, opp_stones, board_size):
    # Prefer corners and sides
    corners = [(1,1), (1,19), (19,1), (19,19)]
    sides = []
    for i in range(2, 19):
        sides.extend([(1,i), (i,1), (19,i), (i,19)])
    
    # Check corners first
    for move in corners:
        if move not in my_stones and move not in opp_stones:
            if is_legal_move(move, my_stones, opp_stones, board_size):
                return move
    
    # Then check sides
    for move in sides:
        if move not in my_stones and move not in opp_stones:
            if is_legal_move(move, my_stones, opp_stones, board_size):
                return move
    return None

def find_influence_move(my_stones, opp_stones, board_size):
    # Simple influence calculation - prefer moves near our stones
    influence = np.zeros((board_size+2, board_size+2))
    
    for stone in my_stones:
        r, c = stone
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= board_size and 1 <= nc <= board_size:
                    if (nr, nc) not in my_stones and (nr, nc) not in opp_stones:
                        influence[nr][nc] += 1
    
    # Find the move with highest influence that's legal
    best_score = -1
    best_move = None
    for r in range(1, board_size+1):
        for c in range(1, board_size+1):
            if influence[r][c] > best_score and (r,c) not in my_stones and (r,c) not in opp_stones:
                if is_legal_move((r,c), my_stones, opp_stones, board_size):
                    best_score = influence[r][c]
                    best_move = (r,c)
    
    return best_move

def find_random_move(my_stones, opp_stones, board_size):
    # Try random moves until we find a legal one
    for _ in range(1000):
        r = random.randint(1, board_size)
        c = random.randint(1, board_size)
        if (r,c) not in my_stones and (r,c) not in opp_stones:
            if is_legal_move((r,c), my_stones, opp_stones, board_size):
                return (r,c)
    return (0, 0)  # pass if no legal moves found (shouldn't happen)

def is_legal_move(move, my_stones, opp_stones, board_size):
    if move == (0, 0):  # pass is always legal
        return True
    
    r, c = move
    if r < 1 or r > board_size or c < 1 or c > board_size:
        return False
    if move in my_stones or move in opp_stones:
        return False
    
    # Temporarily place the stone
    new_my_stones = my_stones.union({move})
    
    # Check liberties of the new stone's group
    group, liberties = find_group_and_liberties(move, new_my_stones, opp_stones, board_size)
    if len(liberties) > 0:
        return True
    
    # Check if it captures any opponent stones
    for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
        nr, nc = r + dr, c + dc
        if (nr, nc) in opp_stones:
            opp_group, opp_liberties = find_group_and_liberties((nr,nc), opp_stones, new_my_stones, board_size)
            if len(opp_liberties) == 0:
                return True
    
    return False

def find_group_and_liberties(stone, group_stones, other_stones, board_size):
    visited = set()
    group = set()
    liberties = set()
    queue = deque([stone])
    
    while queue:
        r, c = queue.popleft()
        if (r,c) in visited:
            continue
        visited.add((r,c))
        group.add((r,c))
        
        for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= board_size and 1 <= nc <= board_size:
                if (nr, nc) not in group_stones and (nr, nc) not in other_stones:
                    liberties.add((nr, nc))
                elif (nr, nc) in group_stones and (nr, nc) not in visited:
                    queue.append((nr, nc))
    
    return group, liberties
