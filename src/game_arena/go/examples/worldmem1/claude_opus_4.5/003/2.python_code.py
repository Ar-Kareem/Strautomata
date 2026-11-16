
import random

def policy(me, opponent, memory):
    BOARD_SIZE = 19
    me_set = set(me)
    opp_set = set(opponent)
    all_stones = me_set | opp_set
    
    def neighbors(r, c):
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                yield (nr, nc)
    
    def get_group_and_liberties(r, c, player_set):
        group = set()
        liberties = set()
        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in group:
                continue
            group.add((cr, cc))
            for nr, nc in neighbors(cr, cc):
                if (nr, nc) in player_set and (nr, nc) not in group:
                    stack.append((nr, nc))
                elif (nr, nc) not in all_stones:
                    liberties.add((nr, nc))
        return group, liberties
    
    def count_liberties_after_move(r, c, player_set, enemy_set):
        new_player = player_set | {(r, c)}
        new_enemy = set(enemy_set)
        new_all = new_player | new_enemy
        
        # Check captures
        for nr, nc in neighbors(r, c):
            if (nr, nc) in new_enemy:
                grp, libs = get_group_and_liberties_with_sets(nr, nc, new_enemy, new_all)
                if len(libs) == 0:
                    new_enemy -= grp
                    new_all = new_player | new_enemy
        
        # Count liberties of our new group
        _, libs = get_group_and_liberties_with_sets(r, c, new_player, new_all)
        return len(libs), len(enemy_set) - len(new_enemy)
    
    def get_group_and_liberties_with_sets(r, c, player_set, all_set):
        group = set()
        liberties = set()
        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in group:
                continue
            group.add((cr, cc))
            for nr, nc in neighbors(cr, cc):
                if (nr, nc) in player_set and (nr, nc) not in group:
                    stack.append((nr, nc))
                elif (nr, nc) not in all_set:
                    liberties.add((nr, nc))
        return group, liberties
    
    def is_legal(r, c):
        if (r, c) in all_stones:
            return False
        libs, caps = count_liberties_after_move(r, c, me_set, opp_set)
        return libs > 0 or caps > 0
    
    def score_move(r, c):
        score = 0
        libs, caps = count_liberties_after_move(r, c, me_set, opp_set)
        score += caps * 50
        score += libs * 2
        
        # Prefer moves near existing stones
        for nr, nc in neighbors(r, c):
            if (nr, nc) in me_set:
                score += 5
            if (nr, nc) in opp_set:
                score += 3
        
        # Prefer center-ish and star points early
        center_dist = abs(r - 10) + abs(c - 10)
        score += max(0, 10 - center_dist // 2)
        
        if (r, c) in [(4,4),(4,10),(4,16),(10,4),(10,10),(10,16),(16,4),(16,10),(16,16)]:
            score += 8
        
        # Avoid edges early
        if r in [1, 19] or c in [1, 19]:
            score -= 5
        
        return score
    
    # Find all legal moves
    candidates = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if is_legal(r, c):
                candidates.append((r, c))
    
    if not candidates:
        return ((0, 0), memory)
    
    # Score and sort candidates
    scored = [(score_move(r, c), r, c) for r, c in candidates]
    scored.sort(reverse=True)
    
    best_move = (scored[0][1], scored[0][2])
    return (best_move, memory)
