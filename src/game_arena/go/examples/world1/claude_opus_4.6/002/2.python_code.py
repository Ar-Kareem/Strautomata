
import numpy as np
from collections import deque

def policy(me, opponent):
    BOARD_SIZE = 19
    me_set = set(me)
    opp_set = set(opponent)
    all_stones = me_set | opp_set

    def neighbors(r, c):
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                yield nr, nc

    def get_group_and_liberties(r, c, stone_set):
        group = set()
        liberties = set()
        queue = deque([(r, c)])
        group.add((r, c))
        while queue:
            cr, cc = queue.popleft()
            for nr, nc in neighbors(cr, cc):
                if (nr, nc) in stone_set and (nr, nc) not in group:
                    group.add((nr, nc))
                    queue.append((nr, nc))
                elif (nr, nc) not in all_stones:
                    liberties.add((nr, nc))
        return group, liberties

    def get_group_and_liberties_with(r, c, stone_set, extra_stone, extra_opp=None):
        my_stones = stone_set | {extra_stone}
        all_s = all_stones | {extra_stone}
        if extra_opp:
            all_s = all_s - extra_opp
        group = set()
        liberties = set()
        queue = deque([(r, c)])
        group.add((r, c))
        while queue:
            cr, cc = queue.popleft()
            for nr, nc in neighbors(cr, cc):
                if (nr, nc) in my_stones and (nr, nc) not in group:
                    group.add((nr, nc))
                    queue.append((nr, nc))
                elif (nr, nc) not in all_s:
                    liberties.add((nr, nc))
        return group, liberties

    def would_capture(r, c):
        captured = set()
        for nr, nc in neighbors(r, c):
            if (nr, nc) in opp_set and (nr, nc) not in captured:
                g, libs = get_group_and_liberties(nr, nc, opp_set)
                new_libs = libs - {(r, c)}
                if len(new_libs) == 0:
                    captured |= g
        return captured

    def is_suicide(r, c):
        captured = would_capture(r, c)
        _, libs = get_group_and_liberties_with(r, c, me_set, (r, c), captured)
        return len(libs) == 0

    def is_legal(r, c):
        if (r, c) in all_stones:
            return False
        if is_suicide(r, c):
            return False
        return True

    # Find all empty legal moves
    candidates = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if (r, c) not in all_stones:
                candidates.append((r, c))

    legal = [m for m in candidates if is_legal(m[0], m[1])]
    if not legal:
        return (0, 0)

    # Score each move
    best_score = -1e18
    best_move = legal[0]

    # Precompute opponent groups in atari
    opp_visited = set()
    opp_atari_libs = set()
    for s in opp_set:
        if s not in opp_visited:
            g, libs = get_group_and_liberties(s[0], s[1], opp_set)
            opp_visited |= g
            if len(libs) == 1:
                opp_atari_libs |= libs

    # Precompute own groups in atari
    my_visited = set()
    my_atari_save = set()
    my_atari_groups = []
    for s in me_set:
        if s not in my_visited:
            g, libs = get_group_and_liberties(s[0], s[1], me_set)
            my_visited |= g
            if len(libs) == 1:
                my_atari_groups.append((g, libs))
                my_atari_save |= libs

    # Opening: prefer star points and nearby
    star_points = [(4,4),(4,10),(4,16),(10,4),(10,10),(10,16),(16,4),(16,10),(16,16)]
    move_count = len(me) + len(opponent)

    for r, c in legal:
        score = 0.0

        # Capture score
        cap = would_capture(r, c)
        score += len(cap) * 50

        # Atari capture (opponent group with 1 liberty)
        if (r, c) in opp_atari_libs:
            score += 100

        # Save own group in atari
        if (r, c) in my_atari_save:
            for g, libs in my_atari_groups:
                if (r, c) in libs:
                    score += len(g) * 40

        # Check resulting liberties for the new stone's group
        _, new_libs = get_group_and_liberties_with(r, c, me_set, (r, c), cap)
        num_libs = len(new_libs)
        if num_libs <= 1 and len(cap) == 0:
            score -= 200  # self-atari penalty
        else:
            score += num_libs * 2

        # Reduce opponent liberties
        for nr, nc in neighbors(r, c):
            if (nr, nc) in opp_set:
                g, libs = get_group_and_liberties(nr, nc, opp_set)
                remaining = libs - {(r, c)}
                if len(remaining) == 1:
                    score += len(g) * 15  # putting in atari
                elif len(remaining) == 2:
                    score += len(g) * 3

        # Connectivity: bonus for being adjacent to own stones
        own_adj = sum(1 for nr, nc in neighbors(r, c) if (nr, nc) in me_set)
        score += own_adj * 3

        # Avoid filling own eyes
        all_own = all(((nr, nc) in me_set) for nr, nc in neighbors(r, c))
        if all_own and own_adj >= 2:
            score -= 300  # likely an eye

        # Prefer center and strategic positions
        center_dist = abs(r - 10) + abs(c - 10)
        score += max(0, 10 - center_dist) * 0.5

        # Opening preference
        if move_count < 12 and (r, c) in star_points:
            score += 20

        # Edge proximity (slight penalty for 1st/2nd line in opening)
        edge = min(r - 1, BOARD_SIZE - r, c - 1, BOARD_SIZE - c)
        if edge == 0:
            score -= 15
        elif edge == 1:
            score -= 5

        # Influence: count nearby empty and own stones
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                nr, nc = r + dr, c + dc
                if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                    dist = abs(dr) + abs(dc)
                    if dist > 0 and dist <= 3:
                        if (nr, nc) in me_set:
                            score += 1.0 / dist
                        elif (nr, nc) in opp_set:
                            score += 0.5 / dist  # contesting is good

        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
