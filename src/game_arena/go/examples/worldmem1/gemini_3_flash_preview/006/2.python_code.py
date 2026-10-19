
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    SIZE = 19
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set

    def get_neighbors(r, c):
        res = []
        if r > 1: res.append((r - 1, c))
        if r < SIZE: res.append((r + 1, c))
        if c > 1: res.append((r, c - 1))
        if c < SIZE: res.append((r, c + 1))
        return res

    def get_liberties(stone, my_stones, opponent_stones):
        stack = [stone]
        visited = {stone}
        liberties = set()
        color_set = my_stones if stone in my_stones else opponent_stones
        
        while stack:
            curr = stack.pop()
            for nb in get_neighbors(*curr):
                if nb in color_set:
                    if nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
                elif nb not in (my_stones | opponent_stones):
                    liberties.add(nb)
        return liberties

    # 1. Capture opponent stones in Atari
    for move in opponent:
        libs = get_liberties(move, opp_set, me_set)
        if len(libs) == 1:
            target = list(libs)[0]
            if target not in occupied:
                return target, memory

    # 2. Save own stones in Atari
    for move in me:
        libs = get_liberties(move, me_set, opp_set)
        if len(libs) == 1:
            escape_spots = list(libs)
            for spot in escape_spots:
                # Check if move is legal (not self-capture)
                if spot not in occupied:
                    # Simple check: would it have > 1 liberty after moving?
                    temp_me = me_set | {spot}
                    if len(get_liberties(spot, temp_me, opp_set)) > 1:
                        return spot, memory

    # 3. Strategic moves (Good Shapes)
    # Try Keima (knight's move) or Ikken Tobi (one-point jump)
    shapes = [(2, 1), (1, 2), (-2, 1), (1, -2), (2, -1), (-1, 2), (-2, -1), (-1, -2), (2, 0), (0, 2), (-2, 0), (0, -2)]
    if me:
        random_me = list(me)
        random.shuffle(random_me)
        for my_stone in random_me:
            for dr, dc in shapes:
                nr, nc = my_stone[0] + dr, my_stone[1] + dc
                if 1 <= nr <= SIZE and 1 <= nc <= SIZE and (nr, nc) not in occupied:
                    # Ensure move isn't suicidal
                    if len(get_liberties((nr, nc), me_set | {(nr, nc)}, opp_set)) > 0:
                        return (nr, nc), memory

    # 4. Opening / Basic expansion (3rd and 4th lines)
    preferred = [3, 4, 16, 17]
    valid_starts = []
    for r in preferred:
        for c in preferred:
            if (r, c) not in occupied:
                valid_starts.append((r, c))
    if valid_starts:
        move = random.choice(valid_starts)
        return move, memory

    # 5. Fallback: Any legal move
    all_coords = [(r, c) for r in range(1, SIZE + 1) for c in range(1, SIZE + 1)]
    random.shuffle(all_coords)
    for r, c in all_coords:
        if (r, c) not in occupied:
            # Check for suicide
            if len(get_liberties((r, c), me_set | {(r, c)}, opp_set)) > 0:
                return (r, c), memory

    return (0, 0), memory
