
import random

def get_liberties(stone, me, opponent, board_size=19):
    stack = [stone]
    visited = {stone}
    liberties = set()
    group = {stone}
    
    # Determine whose group this is
    is_me = stone in me
    friends = me if is_me else opponent
    enemies = opponent if is_me else me
    
    while stack:
        r, c = stack.pop()
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= board_size and 1 <= nc <= board_size:
                if (nr, nc) in friends:
                    if (nr, nc) not in visited:
                        visited.add((nr, nc))
                        group.add((nr, nc))
                        stack.append((nr, nc))
                elif (nr, nc) not in enemies:
                    liberties.add((nr, nc))
    return liberties, group

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    board_size = 19
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set
    
    # 1. Capture opponent stones in Atari
    for stone in opp_set:
        libs, group = get_liberties(stone, me_set, opp_set)
        if len(libs) == 1:
            move = list(libs)[0]
            # Check if this move is legal (not suicide normally, but here it's a capture)
            return move, memory

    # 2. Save own stones in Atari
    for stone in me_set:
        libs, group = get_liberties(stone, me_set, opp_set)
        if len(libs) == 1:
            move = list(libs)[0]
            # Try to save if the move grants more than 1 liberty
            new_me = me_set | {move}
            new_libs, _ = get_liberties(move, new_me, opp_set)
            if len(new_libs) > 1:
                return move, memory

    # 3. Opening moves (Star points)
    star_points = [(4, 4), (4, 16), (16, 4), (16, 16), (4, 10), (10, 4), (10, 16), (16, 10), (10, 10)]
    for pt in star_points:
        if pt not in occupied:
            return pt, memory

    # 4. Greedy search for move with most liberties
    best_move = (0, 0)
    max_libs = -1
    
    # To keep it fast, sample potential moves if many are empty
    possible_moves = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in occupied:
                possible_moves.append((r, c))
    
    if not possible_moves:
        return (0, 0), memory
    
    # Focus on moves near existing stones for better local play
    if occupied:
        nearby_moves = set()
        for r, c in occupied:
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r+dr, c+dc
                if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) not in occupied:
                    nearby_moves.add((nr, nc))
        if nearby_moves:
            search_list = list(nearby_moves)
        else:
            search_list = possible_moves
    else:
        search_list = possible_moves

    random.shuffle(search_list)
    # Check a subset for speed
    for move in search_list[:50]:
        new_me = me_set | {move}
        libs, _ = get_liberties(move, new_me, opp_set)
        l_count = len(libs)
        
        # Simple Ko / Suicide avoidance
        if l_count == 0:
            # Check if it captures anything
            is_capture = False
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = move[0]+dr, move[1]+dc
                if (nr, nc) in opp_set:
                    ol, _ = get_liberties((nr, nc), me_set, opp_set)
                    if len(ol) == 1: # Our move at 'move' would reduce this to 0
                        is_capture = True
                        break
            if not is_capture:
                continue
        
        if l_count > max_libs:
            max_libs = l_count
            best_move = move
            
    if best_move == (0, 0):
        return random.choice(possible_moves) if possible_moves else (0,0), memory

    return best_move, memory
