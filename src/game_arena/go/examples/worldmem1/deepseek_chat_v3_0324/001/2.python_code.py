
import random
from collections import defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Initialize memory if empty
    if not memory:
        memory = {
            'last_move': None,
            'move_history': [],
            'territory': defaultdict(int)
        }
    
    # Convert positions to sets for faster lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    all_stones = my_stones.union(opp_stones)
    
    # Helper function to get liberties of a stone or group
    def get_liberties(group, all_stones):
        liberties = set()
        for (r, c) in group:
            for (dr, dc) in [(0,1), (1,0), (0,-1), (-1,0)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) not in all_stones:
                    liberties.add((nr, nc))
        return liberties
    
    # Helper function to find all connected stones
    def find_group(start, stones):
        group = set()
        queue = [start]
        while queue:
            stone = queue.pop()
            if stone not in group:
                group.add(stone)
                r, c = stone
                for (dr, dc) in [(0,1), (1,0), (0,-1), (-1,0)]:
                    neighbor = (r + dr, c + dc)
                    if neighbor in stones:
                        queue.append(neighbor)
        return group
    
    # 1. Check for opponent stones we can capture
    for stone in opp_stones:
        group = find_group(stone, opp_stones)
        liberties = get_liberties(group, all_stones)
        if len(liberties) == 1:
            capture_move = liberties.pop()
            if capture_move not in all_stones:
                memory['last_move'] = capture_move
                memory['move_history'].append(capture_move)
                return (capture_move, memory)
    
    # 2. Check if any of our groups are in atari
    for stone in my_stones:
        group = find_group(stone, my_stones)
        liberties = get_liberties(group, all_stones)
        if len(liberties) == 1:
            defense_move = liberties.pop()
            if defense_move not in all_stones:
                memory['last_move'] = defense_move
                memory['move_history'].append(defense_move)
                return (defense_move, memory)
    
    # 3. Try to expand in corners/sides if no urgent moves
    preferred_locations = [
        (1,1), (1,19), (19,1), (19,19),  # Corners
        (1,10), (19,10), (10,1), (10,19)  # Side centers
    ]
    
    for loc in preferred_locations:
        if loc not in all_stones:
            # Check if move is legal (not suicide)
            temp_stones = all_stones.copy()
            temp_stones.add(loc)
            liberties = get_liberties({loc}, temp_stones)
            if liberties or any(find_group(n, my_stones.union({loc})) != {loc} for n in [(loc[0]+dr, loc[1]+dc) for (dr,dc) in [(0,1),(1,0),(0,-1),(-1,0)]] if n in my_stones):
                memory['last_move'] = loc
                memory['move_history'].append(loc)
                return (loc, memory)
    
    # 4. Fall back to random legal move
    legal_moves = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in all_stones:
                # Check if move is legal (not suicide)
                temp_stones = all_stones.copy()
                temp_stones.add((r, c))
                liberties = get_liberties({(r, c)}, temp_stones)
                if liberties or any(find_group(n, my_stones.union({(r,c)})) != {(r,c)} for n in [(r+dr, c+dc) for (dr,dc) in [(0,1),(1,0),(0,-1),(-1,0)]] if n in my_stones):
                    legal_moves.append((r, c))
    
    if legal_moves:
        move = random.choice(legal_moves)
        memory['last_move'] = move
        memory['move_history'].append(move)
        return (move, memory)
    
    # If no legal moves (shouldn't happen), pass
    return ((0, 0), memory)
