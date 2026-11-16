
import random

def policy(me, opponent, memory):
    size = 19
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set

    def get_liberties(stones):
        liberties = set()
        for r, c in stones:
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= size and 1 <= nc <= size:
                    if (nr, nc) not in occupied:
                        liberties.add((nr, nc))
        return liberties

    def get_group(start_pos, current_me, current_opp):
        color_set = current_me if start_pos in current_me else current_opp
        group = {start_pos}
        stack = [start_pos]
        while stack:
            r, c = stack.pop()
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in color_set and (nr, nc) not in group:
                    group.add((nr, nc))
                    stack.append((nr, nc))
        return group

    # 1. Capture opponent if possible (Atari)
    checked_opp = set()
    for r, c in opponent:
        if (r, c) not in checked_opp:
            group = get_group((r, c), me_set, opp_set)
            libs = get_liberties(group)
            if len(libs) == 1:
                move = list(libs)[0]
                return move, memory
            checked_opp.update(group)

    # 2. Save own stones if in Atari
    checked_me = set()
    for r, c in me:
        if (r, c) not in checked_me:
            group = get_group((r, c), me_set, opp_set)
            libs = get_liberties(group)
            if len(libs) == 1:
                escape_move = list(libs)[0]
                # Simple suicide check
                test_occupied = occupied | {escape_move}
                surrounding = 0
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = escape_move[0]+dr, escape_move[1]+dc
                    if not (1 <= nr <= size and 1 <= nc <= size) or (nr, nc) in test_occupied:
                        surrounding += 1
                if surrounding < 4:
                    return escape_move, memory
            checked_me.update(group)

    # 3. Opening Strategy: Star points and 3-4 points
    star_points = [
        (4, 4), (4, 16), (16, 4), (16, 16), (4, 10), (10, 4), (10, 16), (16, 10), (10, 10),
        (3, 4), (4, 3), (3, 16), (16, 3), (17, 4), (4, 17), (17, 16), (16, 17)
    ]
    for sp in star_points:
        if sp not in occupied:
            return sp, memory

    # 4. Heuristic: Play near existing stones but maintain liberties
    best_move = None
    max_adj = -1
    
    # Sample some random legal squares to find a decent heuristic move
    possible_moves = []
    for _ in range(100):
        r, c = random.randint(1, size), random.randint(1, size)
        if (r, c) not in occupied:
            # Avoid immediate suicide
            adj_me = 0
            adj_opp = 0
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in me_set: adj_me += 1
                if (nr, nc) in opp_set: adj_opp += 1
            
            score = adj_me * 2 + adj_opp
            possible_moves.append(((r, c), score))

    if possible_moves:
        possible_moves.sort(key=lambda x: x[1], reverse=True)
        return possible_moves[0][0], memory

    # 5. Last resort: Pass
    return (0, 0), memory
