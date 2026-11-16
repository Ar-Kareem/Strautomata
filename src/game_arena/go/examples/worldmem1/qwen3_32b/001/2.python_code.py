
import numpy as np

BOARD_SIZE = 19
CENTER = (9, 9)

def is_in_bounds(position):
    return 1 <= position[0] <= BOARD_SIZE and 1 <= position[1] <= BOARD_SIZE

def get_neighbors(position):
    r, c = position
    neighbors = [(r-1,c), (r+1,c), (r,c-1), (r,c+1)]
    return [n for n in neighbors if is_in_bounds(n)]

def has_liberty(stone, me, opponent, visited=None):
    if visited is None:
        visited = set()
    if stone in visited:
        return False
    visited.add(stone)
    
    for neighbor in get_neighbors(stone):
        if neighbor not in opponent:
            return True
        if neighbor in me and has_liberty(neighbor, me, opponent, visited):
            return True
    return False

def is_dead_group(stone, me, opponent):
    # Check if a stone is part of a group without liberties
    visited = set()
    group = []
    stack = [stone]
    visited.add(stone)
    
    while stack:
        current = stack.pop()
        group.append(current)
        for neighbor in get_neighbors(current):
            if neighbor in me and neighbor not in visited:
                visited.add(neighbor)
                stack.append(neighbor)
    
    return not any(has_liberty(g, me, opponent) for g in group)

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    me_set = set(me)
    opponent_set = set(opponent)
    
    # 1. Check for immediate captures (opponent stones with only one liberty)
    for o in opponent_set:
        neighbors = get_neighbors(o)
        me_neighbors = [n for n in neighbors if n in me_set]
        if len(neighbors) - len(me_neighbors) == 1:
            for n in neighbors:
                if n not in me_set and n not in opponent_set:
                    # Check if this move would capture opponent stones
                    new_me = me + [n]
                    new_me_set = me_set | {n}
                    
                    # Find captured stones
                    captured = []
                    for o_stone in opponent:
                        if o_stone not in captured and not has_liberty(o_stone, new_me, opponent_set):
                            # Find entire group
                            group = []
                            stack = [o_stone]
                            visited = set()
                            while stack:
                                current = stack.pop()
                                if current in visited or current not in opponent_set:
                                    continue
                                visited.add(current)
                                group.append(current)
                                for neighbor in get_neighbors(current):
                                    if neighbor in opponent_set and neighbor not in visited:
                                        stack.append(neighbor)
                            captured.extend(group)
                    if captured:
                        return (n, memory)
    
    # 2. Avoid moves that would put our stones in atari (immediate capture)
    for m in me_set:
        neighbors = get_neighbors(m)
        o_neighbors = [n for n in neighbors if n in opponent_set]
        if len(neighbors) == len(o_neighbors):
            for n in neighbors:
                if n not in me_set and n not in opponent_set:
                    # Check if this move would save our stones
                    new_me = me + [n]
                    new_me_set = me_set | {n}
                    
                    # Check if all new stones have liberties
                    safe = True
                    for s in new_me:
                        if not has_liberty(s, new_me, opponent_set):
                            safe = False
                            break
                    
                    if safe:
                        return (n, memory)
    
    # 3. Check for eye shapes that can be filled
    for m in me_set:
        for n in get_neighbors(m):
            if n not in me_set and n not in opponent_set:
                # Check if this position is part of an eye shape
                eye_neighbors = get_neighbors(n)
                me_eye_neighbors = [e for e in eye_neighbors if e in me_set]
                if len(me_eye_neighbors) >= 3:
                    return (n, memory)
    
    # 4. Look for central control
    center_area = [(r, c) for r in range(7, 12) for c in range(7, 12)]
    center_candidates = [c for c in center_area if c not in me_set and c not in opponent_set]
    if center_candidates:
        # Choose the candidate with the highest number of empty neighbors
        if center_candidates:
            # Sort by potential for expansion
            center_candidates.sort(key=lambda x: sum(1 for n in get_neighbors(x) if n not in me_set and n not in opponent_set), reverse=True)
            return (center_candidates[0], memory)
    
    # 5. Evaluate expansion candidates using a utility function
    candidates = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            pos = (r, c)
            if pos in me_set or pos in opponent_set:
                continue
            
            # Calculate number of adjacent empty points and opponent stones
            empty_neighbors = [n for n in get_neighbors(pos) if n not in me_set and n not in opponent_set]
            opponent_neighbors = [n for n in get_neighbors(pos) if n in opponent_set]
            
            # Calculate distance from our stones
            my_distance = 100  # Default large distance
            for m in me_set:
                my_distance = min(my_distance, abs(m[0] - pos[0]) + abs(m[1] - pos[1]))
            
            # Calculate utility score
            utility = len(empty_neighbors) * 2 + len(opponent_neighbors) * 1.5 - my_distance
            
            # Bonus for positions that connect our stones
            connecting = 0
            for n1 in get_neighbors(pos):
                for n2 in get_neighbors(pos):
                    if n1 != n2 and n1 in me_set and n2 in me_set:
                        connecting += 1
            utility += connecting * 2
            
            # Penalty for being near our stones (prevents unnecessary clustering)
            if my_distance < 2:
                utility -= len(empty_neighbors)
                
            candidates.append((pos, utility))
    
    # 6. Sort candidates and choose the best move
    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        for candidate, _ in candidates:
            # Check if this move is safe
            new_me = me + [candidate]
            new_me_set = me_set | {candidate}
            
            safe = True
            for s in new_me:
                if not has_liberty(s, new_me, opponent_set):
                    safe = False
                    break
                    
            if safe:
                return (candidate, memory)
    
    # 7. If no good move found, pass
    return ((0, 0), memory)
