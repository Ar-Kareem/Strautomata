
import numpy as np
from collections import deque

def policy(me, opponent):
    BOARD_SIZE = 19
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set
    
    def neighbors(r, c):
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                yield nr, nc
    
    def get_group_and_liberties(r, c, board_set, opp_set_local):
        group = set()
        liberties = set()
        queue = deque([(r, c)])
        group.add((r, c))
        while queue:
            cr, cc = queue.popleft()
            for nr, nc in neighbors(cr, cc):
                if (nr, nc) in group:
                    continue
                if (nr, nc) in board_set:
                    group.add((nr, nc))
                    queue.append((nr, nc))
                elif (nr, nc) not in opp_set_local:
                    liberties.add((nr, nc))
        return group, liberties
    
    def would_be_captured(r, c, my_stones, opp_stones):
        # Simulate placing stone at (r,c) for my_stones
        new_my = my_stones | {(r,c)}
        # First check if this captures any opponent groups
        new_opp = set(opp_stones)
        for nr, nc in neighbors(r, c):
            if (nr, nc) in new_opp:
                grp, libs = get_group_and_liberties(nr, nc, new_opp, new_my)
                if len(libs) == 0:
                    new_opp -= grp
        # Now check our group's liberties
        grp, libs = get_group_and_liberties(r, c, new_my, new_opp)
        return len(libs) == 0
    
    def captures_stones(r, c, my_stones, opp_stones):
        new_my = my_stones | {(r,c)}
        captured = set()
        for nr, nc in neighbors(r, c):
            if (nr, nc) in opp_stones and (nr, nc) not in captured:
                grp, libs = get_group_and_liberties(nr, nc, opp_stones, new_my)
                if len(libs) == 0:
                    captured |= grp
        return captured

    # Generate candidate moves
    candidates = set()
    for r, c in occupied:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r+dr, c+dc
                if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE and (nr,nc) not in occupied:
                    candidates.add((nr, nc))
    
    if not candidates:
        # Opening moves - star points
        star_points = [(4,4),(4,16),(16,4),(16,16),(10,10),(4,10),(16,10),(10,4),(10,16)]
        for sp in star_points:
            if sp not in occupied:
                return sp
        candidates = {(r,c) for r in range(1,20) for c in range(1,20) if (r,c) not in occupied}
    
    best_score = -float('inf')
    best_move = (0, 0)
    
    for r, c in candidates:
        if would_be_captured(r, c, me_set, opp_set):
            cap = captures_stones(r, c, me_set, opp_set)
            if not cap:
                continue
        
        score = 0.0
        cap = captures_stones(r, c, me_set, opp_set)
        score += len(cap) * 15
        
        # Reduce opponent liberties
        for nr, nc in neighbors(r, c):
            if (nr, nc) in opp_set:
                _, libs = get_group_and_liberties(nr, nc, opp_set, me_set | {(r,c)})
                if len(libs) == 1:
                    score += 8
                elif len(libs) == 2:
                    score += 3
        
        # Save own groups in atari
        for nr, nc in neighbors(r, c):
            if (nr, nc) in me_set:
                _, libs = get_group_and_liberties(nr, nc, me_set, opp_set)
                if len(libs) == 1:
                    score += 12
        
        # Center preference
        dist_center = abs(r - 10) + abs(c - 10)
        score += max(0, (18 - dist_center)) * 0.15
        
        # Edge penalty for very edge moves
        edge_dist = min(r-1, 19-r, c-1, 19-c)
        if edge_dist == 0:
            score -= 3
        elif edge_dist == 1:
            score -= 1
        
        # Connectivity to own stones
        own_adj = sum(1 for nr,nc in neighbors(r,c) if (nr,nc) in me_set)
        score += own_adj * 0.5
        
        # Empty neighbors (liberties of new stone)
        new_my = me_set | {(r,c)}
        new_opp = opp_set - cap
        _, my_libs = get_group_and_liberties(r, c, new_my, new_opp)
        score += len(my_libs) * 0.3
        
        # Self-atari penalty
        grp, libs = get_group_and_liberties(r, c, new_my, new_opp)
        if len(libs) == 1 and len(cap) == 0:
            score -= 10 * len(grp)
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move
