
from collections import deque
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    BOARD_SIZE = 19
    my_stones = set(me)
    opp_stones = set(opponent)
    occupied = my_stones | opp_stones
    
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    def get_neighbors(r, c):
        neighbors = []
        for dr, dc in deltas:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                neighbors.append((nr, nc))
        return neighbors
    
    def get_liberties(group, occupied_set):
        liberties = set()
        for r, c in group:
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in occupied_set:
                    liberties.add((nr, nc))
        return liberties
    
    def find_groups(stones, occupied_set):
        groups = []
        visited = set()
        for stone in stones:
            if stone not in visited:
                group = set()
                queue = deque([stone])
                visited.add(stone)
                group.add(stone)
                while queue:
                    r, c = queue.popleft()
                    for nr, nc in get_neighbors(r, c):
                        if (nr, nc) in stones and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            group.add((nr, nc))
                            queue.append((nr, nc))
                groups.append(group)
        return groups
    
    opp_groups = find_groups(opp_stones, occupied)
    
    all_moves = [(r, c) for r in range(1, BOARD_SIZE + 1) for c in range(1, BOARD_SIZE + 1) if (r, c) not in occupied]
    
    best_move = None
    best_score = -float('inf')
    
    for r, c in all_moves:
        my_neighbors = 0
        opp_neighbors = 0
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in my_stones:
                my_neighbors += 1
            elif (nr, nc) in opp_stones:
                opp_neighbors += 1
        
        captures = 0
        for group in opp_groups:
            liberties = get_liberties(group, occupied)
            if len(liberties) == 1 and next(iter(liberties)) == (r, c):
                captures += len(group)
        
        # Check for suicide
        temp_my_stones = my_stones | {(r, c)}
        temp_occupied = occupied | {(r, c)}
        my_groups = find_groups(temp_my_stones, temp_occupied)
        suicidal = any(len(get_liberties(g, temp_occupied)) == 0 for g in my_groups)
        
        if suicidal:
            score = -10000  # Invalid move
        else:
            # Score: captures * 1000, my neighbors * 10, opp neighbors * 5, distance from center penalty
            center_penalty = (r - 10)**2 + (c - 10)**2
            score = captures * 1000 + my_neighbors * 10 + opp_neighbors * 5 - center_penalty
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    # If no good moves, pass
    if best_move is None or best_score <= -9999:
        return ((0, 0), memory)
    
    return (best_move, memory)
