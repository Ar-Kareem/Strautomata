
import random

def get_liberties(stones, all_stones):
    liberties = set()
    for r, c in stones:
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if (nr, nc) not in all_stones:
                    liberties.add((nr, nc))
    return liberties

def get_group(start_pos, player_stones):
    group = {start_pos}
    stack = [start_pos]
    while stack:
        r, c = stack.pop()
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in player_stones and (nr, nc) not in group:
                group.add((nr, nc))
                stack.append((nr, nc))
    return group

def is_legal(move, me, opponent):
    if move == (0, 0): return True
    r, c = move
    if not (1 <= r <= 19 and 1 <= c <= 19): return False
    all_stones = set(me) | set(opponent)
    if move in all_stones: return False
    
    # Check if move has immediate liberties
    test_me = set(me) | {move}
    if get_liberties({move}, all_stones | {move}):
        return True
    
    # Check if move captures any opponent groups
    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nr, nc = r + dr, c + dc
        if (nr, nc) in opponent:
            group = get_group((nr, nc), opponent)
            if not get_liberties(group, all_stones | {move}):
                return True
                
    # Check if move connects to a group that has liberties
    group = get_group(move, test_me)
    if get_liberties(group, all_stones | {move}):
        return True
        
    return False

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    me_set = set(me)
    opp_set = set(opponent)
    all_stones = me_set | opp_set
    
    # 1. Opening: Play star points and komoku
    stars = [(4, 4), (4, 16), (16, 4), (16, 16), (4, 10), (10, 4), (10, 16), (16, 10), (10, 10)]
    random.shuffle(stars)
    for s in stars:
        if s not in all_stones:
            return s, memory

    # 2. Tactical: Look for Atari - Capture or Save
    # Try to capture
    for stone in opponent:
        group = get_group(stone, opp_set)
        libs = get_liberties(group, all_stones)
        if len(libs) == 1:
            move = list(libs)[0]
            if is_legal(move, me, opponent):
                return move, memory
                
    # Try to save own
    for stone in me:
        group = get_group(stone, me_set)
        libs = get_liberties(group, all_stones)
        if len(libs) == 1:
            move = list(libs)[0]
            if is_legal(move, me, opponent):
                # Only move if it actually increases liberties
                test_me = me_set | {move}
                new_group = get_group(move, test_me)
                if len(get_liberties(new_group, all_stones | {move})) > 1:
                    return move, memory

    # 3. Simple Heuristic: Play near existing stones with most liberties
    candidates = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in all_stones:
                # Basic legality check
                if is_legal((r, c), me, opponent):
                    # Scoring
                    score = 0
                    # Bias towards center-ish and away from first line
                    if 3 <= r <= 17 and 3 <= c <= 17: score += 2
                    if r == 1 or r == 19 or c == 1 or c == 19: score -= 5
                    
                    # Proximity to own stones (connectivity)
                    for dr, dc in [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
                        if (r+dr, c+dc) in me_set: score += 3
                        if (r+dr, c+dc) in opp_set: score += 2
                    
                    candidates.append(((r, c), score))

    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        # Choose from top 5 to avoid being too predictable
        best_move = random.choice(candidates[:min(5, len(candidates))])[0]
        return best_move, memory

    return (0, 0), memory
