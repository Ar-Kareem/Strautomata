
import sys
from collections import deque

def policy(me, opponent, memory):
    me_set = set(me)
    opponent_set = set(opponent)
    
    empty_positions = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in me_set and (r, c) not in opponent_set:
                empty_positions.append((r, c))
    
    if not empty_positions:
        return ((0, 0), memory)
    
    best_score = -float('inf')
    best_moves = []
    
    for (r, c) in empty_positions:
        me_plus = me_set.copy()
        me_plus.add((r, c))
        
        # Check if the new group has liberties
        group_me = set()
        queue_me = deque([(r, c)])
        group_me.add((r, c))
        while queue_me:
            curr_r, curr_c = queue_me.popleft()
            for dr2, dc2 in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = curr_r + dr2, curr_c + dc2
                if (1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) in me_plus and (nr, nc) not in group_me):
                    group_me.add((nr, nc))
                    queue_me.append((nr, nc))
        
        has_liberty_me = False
        for gr, gc in group_me:
            for dr2, dc2 in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                lr, lc = gr + dr2, gc + dc2
                if 1 <= lr <= 19 and 1 <= lc <= 19:
                    if (lr, lc) not in me_plus and (lr, lc) not in opponent_set:
                        has_liberty_me = True
                        break
            if has_liberty_me:
                break
        
        capture_bonus = 0
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            ar, ac = r + dr, c + dc
            if 1 <= ar <= 19 and 1 <= ac <= 19 and (ar, ac) in opponent_set:
                # Find opponent group
                group = set()
                queue = deque()
                group.add((ar, ac))
                queue.append((ar, ac))
                while queue:
                    curr_r, curr_c = queue.popleft()
                    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nr, nc = curr_r + dx, curr_c + dy
                        if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) in opponent_set and (nr, nc) not in group:
                            group.add((nr, nc))
                            queue.append((nr, nc))
                # Check if this group has liberties
                has_liberty = False
                for gr, gc in group:
                    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                        lr, lc = gr + dx, gc + dy
                        if 1 <= lr <= 19 and 1 <= lc <= 19:
                            if (lr, lc) not in me_plus and (lr, lc) not in opponent_set:
                                has_liberty = True
                                break
                    if has_liberty:
                        break
                if not has_liberty:
                    capture_bonus += 1000
        
        if not has_liberty_me and capture_bonus == 0:
            continue
        
        # Count adjacent mines and theirs
        adjacent_mines = sum(1 for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)] 
                             if (r + dr, c + dc) in me_set)
        adjacent_theirs = sum(1 for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)] 
                             if (r + dr, c + dc) in opponent_set)
        
        # Position-based score
        def base_score(r, c):
            if (r in [1, 19] and c in [1, 19]):
                return 100
            elif r in [1, 19] or c in [1, 19]:
                return 50
            else:
                return 10
        
        total_score = capture_bonus + (adjacent_mines * 10) + (adjacent_theirs * 5) + base_score(r, c)
        
        if total_score > best_score:
            best_score = total_score
            best_moves = [(r, c)]
        elif total_score == best_score:
            best_moves.append((r, c))
    
    return (best_moves[0] if best_moves else (0, 0), memory)
