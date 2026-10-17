
import numpy as np
from collections import defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Convert to sets for O(1) lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    occupied = my_stones | opp_stones
    
    # If board is empty, play 4-4 in corner (standard opening)
    if not occupied:
        return (4, 4)
    
    # Board boundaries
    BOARD_SIZE = 19
    
    # Generate all possible moves (all empty intersections)
    all_moves = [(r, c) for r in range(1, BOARD_SIZE + 1) for c in range(1, BOARD_SIZE + 1) 
                 if (r, c) not in occupied]
    
    if not all_moves:
        return (0, 0)  # Pass if no legal moves (shouldn't happen normally)
    
    # Check for immediate capture (winning move)
    for move in all_moves:
        if is_capture(move, my_stones, opp_stones):
            return move
    
    # Check for moves that prevent immediate capture of own groups
    for move in all_moves:
        # Temporarily add this move to my stones
        temp_my = my_stones | {move}
        # Check if any of my groups would be in atari after this move
        if is_self_atari(move, temp_my, opp_stones):
            # But check if it captures opponent - already handled above
            # Otherwise, avoid moves that put own group in atari unless necessary
            continue
        # Check if this move saves a group with only one liberty left
        if saves_group(move, my_stones, opp_stones):
            return move
    
    # Evaluate potential eye spaces and dame points
    # Consider moves that create two eyes or prevent opponent from making eyes
    eye_candidate = find_eye_move(my_stones, opp_stones, occupied)
    if eye_candidate:
        return eye_candidate
    
    # Heuristic scoring of remaining moves
    move_scores = []
    
    for move in all_moves:
        score = evaluate_move(move, my_stones, opp_stones, occupied)
        move_scores.append((score, move))
    
    # Sort by score descending
    move_scores.sort(reverse=True)
    
    # Return best move, or pass if all moves are bad (unlikely)
    if move_scores:
        return move_scores[0][1]
    else:
        return (0, 0)


def is_capture(move, my_stones, opp_stones):
    """Check if playing move captures any opponent group."""
    temp_opp = opp_stones.copy()
    # Temporarily place the move (it belongs to us)
    temp_my = my_stones | {move}
    # Find all opponent groups adjacent to this move
    adjacent_opp = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        r, c = move[0] + dr, move[1] + dc
        if 1 <= r <= 19 and 1 <= c <= 19 and (r, c) in opp_stones:
            adjacent_opp.append((r, c))
    
    for opp_stone in adjacent_opp:
        # Find the whole group containing this stone
        group = find_group(opp_stone, opp_stones)
        # Check liberties of this group
        liberties = count_liberties(group, temp_my, opp_stones)
        if liberties == 0:
            return True
    return False


def is_self_atari(move, temp_my, opp_stones):
    """Check if placing move puts any of my groups in atari (one liberty left)."""
    # Find all my stones adjacent to the move
    adjacent_my = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        r, c = move[0] + dr, move[1] + dc
        if 1 <= r <= 19 and 1 <= c <= 19 and (r, c) in temp_my:
            adjacent_my.append((r, c))
    
    # We need to check groups formed by combining move with adjacent my stones
    if not adjacent_my:
        # Move is isolated - check if it has any liberties
        liberties = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r, c = move[0] + dr, move[1] + dc
            if 1 <= r <= 19 and 1 <= c <= 19 and (r, c) not in (temp_my | opp_stones):
                liberties += 1
        return liberties == 0
    
    # Find the group that includes the move and adjacent my stones
    group = find_group_with_additional(move, adjacent_my, temp_my)
    liberties = count_liberties(group, temp_my, opp_stones)
    return liberties == 0


def saves_group(move, my_stones, opp_stones):
    """Check if this move saves a group of mine that has only one liberty."""
    # Find all my stones adjacent to move
    adjacent_my = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        r, c = move[0] + dr, move[1] + dc
        if 1 <= r <= 19 and 1 <= c <= 19 and (r, c) in my_stones:
            adjacent_my.append((r, c))
    
    # Group the adjacent stones with the move
    temp_my = my_stones | {move}
    for stone in adjacent_my:
        # Find the group containing this stone
        group = find_group(stone, my_stones)
        # Count liberties of this group without the move
        liberties = count_liberties(group, my_stones, opp_stones)
        # If group has exactly one liberty and the move fills that liberty (and doesn't create self-atari),
        # then it's a saving move
        if liberties == 1:
            # Check if the move removes the last liberty from the group - meaning it would capture opponent?
            # But we need to check if by adding the move, we're filling the last liberty of the group we're trying to save
            # Actually, if a group has one liberty, and we place a stone there, then that group is saved
            return True
    return False


def find_group(start_stone, stones):
    """Find all stones in the group connected to start_stone using BFS."""
    group = set()
    queue = [start_stone]
    visited = set([start_stone])
    
    while queue:
        stone = queue.pop(0)
        group.add(stone)
        
        r, c = stone
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) in stones and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc))
    
    return group


def find_group_with_additional(new_stone, adjacent_stones, all_my_stones):
    """Find group that includes new_stone and all adjacent_stones (which are in all_my_stones)."""
    group = {new_stone}
    visited = set([new_stone])
    queue = list(adjacent_stones)
    all_set = set(all_my_stones)
    
    for stone in queue:
        if stone not in visited:
            visited.add(stone)
            group.add(stone)
    
    # BFS from all adjacent stones
    queue_extended = list(adjacent_stones)
    while queue_extended:
        stone = queue_extended.pop(0)
        r, c = stone
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) in all_set and (nr, nc) not in visited:
                visited.add((nr, nc))
                group.add((nr, nc))
                queue_extended.append((nr, nc))
    
    return group


def count_liberties(group, my_stones, opp_stones):
    """Count the number of vacant adjacent points to a group."""
    liberties = set()
    for stone in group:
        r, c = stone
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) not in (my_stones | opp_stones):
                liberties.add((nr, nc))
    return len(liberties)


def find_eye_move(my_stones, opp_stones, occupied):
    """Find a move that helps form an eye or prevents opponent from forming an eye."""
    # For each empty point, check if playing there creates a potential eye
    for move in [(r, c) for r in range(1, 20) for c in range(1, 20) if (r, c) not in occupied]:
        # Check what kind of eye shape this would create
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = move[0] + dr, move[1] + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if (nr, nc) in my_stones:
                    neighbors.append((nr, nc))
                elif (nr, nc) in opp_stones:
                    neighbors.append((-nr, -nc))  # mark as opponent
        
        # Count my stones around the potential eye point
        my_adjacent = sum(1 for nb in neighbors if nb[0] > 0)
        
        # Simple heuristic: if 3 or 4 of the 4 adjacent points are my stones,
        # then this might be a potential eye (or point we should take to prevent eye)
        
        # But we are more concerned about points that are "dame" (neutral) or
        # points that are vital to eye shapes
        
        # Try a simple heuristic: points surrounded by 3 my stones are good for eye shape
        # Points surrounded by 3 opponent stones are bad (opponent eye)
        if my_adjacent >= 3:
            # Check if this move forms an eye shape
            if is_pseudo_eye(move, my_stones, opp_stones):
                return move
    
    return None


def is_pseudo_eye(point, my_stones, opp_stones):
    """Check if this point is a potential eye for my group (surrounded by mostly my stones)."""
    r, c = point
    adjacent = [(r+dr, c+dc) for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]]
    my_count = 0
    opp_count = 0
    for adj in adjacent:
        if 1 <= adj[0] <= 19 and 1 <= adj[1] <= 19:
            if adj in my_stones:
                my_count += 1
            elif adj in opp_stones:
                opp_count += 1
    # If at least 3 of 4 are my stones, consider it a pseudo-eye point
    return my_count >= 3 and opp_count == 0


def evaluate_move(move, my_stones, opp_stones, occupied):
    """Heuristic evaluation of a move."""
    score = 0
    r, c = move
    
    # Proximity to corner (prioritize corners)
    corner_bonus = 0
    if (r == 4 and c == 4) or (r == 4 and c == 16) or (r == 16 and c == 4) or (r == 16 and c == 16):
        corner_bonus = 20
    elif (r == 3 and c == 3) or (r == 3 and c == 17) or (r == 17 and c == 3) or (r == 17 and c == 17):
        corner_bonus = 15
    elif (r == 4 and c == 10) or (r == 10 and c == 4) or (r == 10 and c == 16) or (r == 16 and c == 10):
        corner_bonus = 10
    elif r == 10 and c == 10:
        corner_bonus = 5  # Center is less important
    score += corner_bonus
    
    # Count liberties gained
    temp_my = my_stones | {move}
    # Find group this stone connects to (if any)
    adjacent_my = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) in temp_my:
            adjacent_my.append((nr, nc))
    
    if adjacent_my:
        # This stone extends an existing group
        group = find_group_with_additional(move, adjacent_my, temp_my)
        original_liberties = count_liberties(group - {move}, my_stones, opp_stones)
        new_liberties = count_liberties(group, temp_my, opp_stones)
        liberty_gain = max(0, new_liberties - original_liberties)
        score += liberty_gain * 3
    else:
        # New isolated stone - check its liberties
        liberties = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) not in occupied:
                liberties += 1
        score += liberties * 2
    
    # Threat to opponent's groups
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) in opp_stones:
            opp_group = find_group((nr, nc), opp_stones)
            opp_liberties = count_liberties(opp_group, temp_my, opp_stones)
            if opp_liberties == 1:
                score += 30  # Very strong: immediate capture
            elif opp_liberties == 2:
                score += 10  # Reduces liberties
    
    # Prevent opponent eye formation
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) in opp_stones:
            # Look at the 4 adjacent points to opponent's stone
            opp_adjacent = [(nr+dr2, nc+dc2) for dr2,dc2 in [(-1,0),(1,0),(0,-1),(0,1)]]
            opp_own_adjacent = [p for p in opp_adjacent if 1<=p[0]<=19 and 1<=p[1]<=19 and p in opp_stones]
            opp_empty_adjacent = [p for p in opp_adjacent if 1<=p[0]<=19 and 1<=p[1]<=19 and p not in opp_stones and p not in temp_my]
            
            # If opponent has 3 adjacent stones and only one liberty left, 
            # then we are starting to prevent their eye
            if len(opp_own_adjacent) >= 3 and len(opp_empty_adjacent) == 1:
                # We are playing on that liberty
                score += 15
    
    # Avoid edges if no benefit (somewhat reduced value in center)
    if r in [1, 19] or c in [1, 19]:
        score -= 2
    
    # Avoid placing stones too close to opponent groups unless beneficial
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) in opp_stones:
            # We are adjacent to opponent - if we are surrounded by opponent, it's bad
            opp_adj_count = 0
            for dr2, dc2 in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                n2r, n2c = r + dr2, c + dc2
                if 1 <= n2r <= 19 and 1 <= n2c <= 19 and (n2r, n2c) in opp_stones:
                    opp_adj_count += 1
            if opp_adj_count >= 3:
                # We're surrounded by opponent stones - very bad, penalty
                score -= 20
    
    return score
