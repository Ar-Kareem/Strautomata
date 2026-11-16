
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    BOARD_SIZE = 19
    my_stones = set(me)
    opp_stones = set(opponent)
    occupied = my_stones | opp_stones

    def get_liberties(r, c, stones_set):
        liberties = set()
        stack = [(r, c)]
        visited = {(r, c)}
        while stack:
            curr_r, curr_c = stack.pop()
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = curr_r + dr, curr_c + dc
                if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                    if (nr, nc) not in occupied:
                        liberties.add((nr, nc))
                    elif (nr, nc) in stones_set and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        stack.append((nr, nc))
        return liberties

    def is_legal(r, c):
        if (r, c) in occupied:
            return False
        # Check for suicide
        temp_occupied = occupied | {(r, c)}
        temp_me = my_stones | {(r, c)}
        
        # If it captures opponent, it's legal
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in opp_stones:
                if len(get_liberties(nr, nc, opp_stones)) == 0:
                    # This is actually checked after placement logic, 
                    # but effectively if we remove the group, we are safe.
                    return True
                    
        # Check if placement has liberties
        has_liberty = False
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                if (nr, nc) not in temp_occupied:
                    has_liberty = True
                    break
                if (nr, nc) in my_stones:
                    # If connecting to a group that has other liberties
                    if len(get_liberties(nr, nc, my_stones)) > 1:
                        has_liberty = True
                        break
        return has_liberty

    # 1. Capture opponent in Atari
    for r, c in opp_stones:
        libs = get_liberties(r, c, opp_stones)
        if len(libs) == 1:
            move = list(libs)[0]
            if is_legal(move[0], move[1]):
                return move

    # 2. Save own stones in Atari
    for r, c in my_stones:
        libs = get_liberties(r, c, my_stones)
        if len(libs) == 1:
            move = list(libs)[0]
            if is_legal(move[0], move[1]):
                return move

    # 3. Opening Moves (Star Points)
    stars = [(4, 4), (4, 16), (16, 4), (16, 16), (4, 10), (10, 4), (10, 16), (16, 10), (10, 10)]
    for move in stars:
        if is_legal(move[0], move[1]):
            return move

    # 4. Smart Search: Try moves near existing stones
    potential_moves = set()
    for (r, c) in occupied:
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                nr, nc = r + dr, c + dc
                if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                    if (nr, nc) not in occupied:
                        potential_moves.add((nr, nc))
    
    scored_moves = []
    for move in potential_moves:
        if is_legal(move[0], move[1]):
            # Simple heuristic: favor moves with more liberties
            score = 0
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = move[0] + dr, move[1] + dc
                if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE and (nr, nc) not in occupied:
                    score += 1
            scored_moves.append((score, move))
            
    if scored_moves:
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        return scored_moves[0][1]

    # 5. Last Resort: Random Legal Move
    all_coords = [(r, c) for r in range(1, 20) for c in range(1, 20)]
    random.shuffle(all_coords)
    for r, c in all_coords:
        if is_legal(r, c):
            return (r, c)

    return (0, 0)
