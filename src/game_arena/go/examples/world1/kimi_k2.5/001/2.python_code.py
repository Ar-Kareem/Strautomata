
import numpy as np
from collections import deque
from typing import Set, Tuple, List

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    my_set: Set[Tuple[int, int]] = set(me)
    opp_set: Set[Tuple[int, int]] = set(opponent)
    occupied: Set[Tuple[int, int]] = my_set | opp_set
    
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    
    def in_bounds(r: int, c: int) -> bool:
        return 1 <= r <= 19 and 1 <= c <= 19
    
    def get_neighbors(r: int, c: int) -> List[Tuple[int, int]]:
        return [(r + dr, c + dc) for dr, dc in directions if in_bounds(r + dr, c + dc)]
    
    def get_group_and_liberties(start_r: int, start_c: int, stone_set: Set[Tuple[int, int]]) -> Tuple[Set[Tuple[int, int]], int]:
        """BFS to find connected group and count liberties."""
        if (start_r, start_c) not in stone_set:
            return set(), 0
        
        group = set()
        liberties = set()
        queue = deque([(start_r, start_c)])
        group.add((start_r, start_c))
        
        while queue:
            r, c = queue.popleft()
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in stone_set and (nr, nc) not in group:
                    group.add((nr, nc))
                    queue.append((nr, nc))
                elif (nr, nc) not in occupied:
                    liberties.add((nr, nc))
        return group, len(liberties)
    
    def is_legal(move_r: int, move_c: int) -> bool:
        """Check if move is legal (not occupied, not suicide unless capturing)."""
        if (move_r, move_c) in occupied:
            return False
        
        # Check if this move captures any opponent stones
        will_capture = False
        for nr, nc in get_neighbors(move_r, move_c):
            if (nr, nc) in opp_set:
                _, libs = get_group_and_liberties(nr, nc, opp_set)
                if libs == 1:  # This move removes last liberty
                    will_capture = True
                    break
        
        if will_capture:
            return True
        
        # Check for suicide (new group must have liberties)
        temp_my = my_set | {(move_r, move_c)}
        _, libs = get_group_and_liberties(move_r, move_c, temp_my)
        return libs > 0
    
    def evaluate_move(move_r: int, move_c: int) -> float:
        """Score a legal move."""
        score = 0.0
        temp_my = my_set | {(move_r, move_c)}
        
        # 1. Capture bonus (highest priority)
        capture_count = 0
        for nr, nc in get_neighbors(move_r, move_c):
            if (nr, nc) in opp_set:
                group, libs = get_group_and_liberties(nr, nc, opp_set)
                if libs == 1:
                    capture_count += len(group)
        if capture_count > 0:
            score += 1000 * capture_count
        
        # 2. Save own stones in atari (high priority)
        saved_count = 0
        for nr, nc in get_neighbors(move_r, move_c):
            if (nr, nc) in my_set:
                group, libs = get_group_and_liberties(nr, nc, my_set)
                if libs == 1:
                    saved_count += len(group)
        if saved_count > 0:
            score += 800 * saved_count
        
        # 3. Self-atari penalty (avoid playing into atari unless capturing)
        _, new_libs = get_group_and_liberties(move_r, move_c, temp_my)
        if new_libs <= 1 and capture_count == 0:
            score -= 500
        
        # 4. Eye filling penalty (don't fill obvious eyes)
        # Simple eye check: surrounded by own stones
        own_neighbors = sum(1 for nr, nc in get_neighbors(move_r, move_c) if (nr, nc) in my_set)
        if own_neighbors >= 3:  # Likely an eye or almost eye
            score -= 200
        
        # 5. Connectivity bonus
        score += 15 * own_neighbors
        
        # 6. Liberty expansion
        score += 10 * new_libs
        
        # 7. Line preference (3rd and 4th line best for territory/influence)
        dist_top = move_r - 1
        dist_bot = 19 - move_r
        dist_left = move_c - 1
        dist_right = 19 - move_c
        dist_edge = min(dist_top, dist_bot, dist_left, dist_right)
        
        if dist_edge == 0:  # 1st line
            score -= 100
        elif dist_edge == 1:  # 2nd line
            score -= 40
        elif dist_edge == 2:  # 3rd line (good for territory)
            score += 50
        elif dist_edge == 3:  # 4th line (good for influence)
            score += 40
        else:
            score += 10  # Center
        
        # 8. Pressure on opponent
        for nr, nc in get_neighbors(move_r, move_c):
            if (nr, nc) in opp_set:
                _, libs = get_group_and_liberties(nr, nc, opp_set)
                if libs == 2:  # Putting in atari is good
                    score += 30
                elif libs == 3:
                    score += 10
        
        # 9. Opening preference (star points)
        if not me:
            stars = {(4,4), (4,10), (4,16), (10,4), (10,10), (10,16), (16,4), (16,10), (16,16)}
            if (move_r, move_c) in stars:
                score += 200
        
        return score
    
    best_move = (0, 0)
    best_score = -float('inf')
    
    # Search all intersections
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) in occupied:
                continue
            if is_legal(r, c):
                score = evaluate_move(r, c)
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    
    return best_move
