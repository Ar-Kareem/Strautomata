
import numpy as np
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    # Convert to sets for fast lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    all_stones = my_stones | opp_stones
    
    # Define the 19x19 board boundaries
    BOARD_SIZE = 19
    
    # Get all empty intersections
    empty_intersections = set()
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if (r, c) not in all_stones:
                empty_intersections.add((r, c))
    
    # If board is empty, play center (10,10) or 4-4 point
    if len(all_stones) == 0:
        return (10, 10)
    
    # Function to get adjacent points
    def get_neighbors(r, c):
        neighbors = []
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                neighbors.append((nr, nc))
        return neighbors
    
    # Function to count liberties of a group
    def count_liberties(group: set) -> int:
        liberties = set()
        for r, c in group:
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in all_stones:
                    liberties.add((nr, nc))
        return len(liberties)
    
    # Function to find connected group containing a stone
    def find_group(stone, group_stones, opponent_group):
        stack = [stone]
        visited = set()
        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            group_stones.add((r, c))
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in opponent_group and (nr, nc) not in visited:
                    stack.append((nr, nc))
        return visited
    
    # Identify opponent groups and their liberties
    opp_groups = []
    visited_opp = set()
    
    for stone in opp_stones:
        if stone not in visited_opp:
            group = set()
            find_group(stone, group, opp_stones)
            visited_opp.update(group)
            liberties = count_liberties(group)
            opp_groups.append((group, liberties))
    
    # Identify my groups and their liberties (for defense)
    my_groups = []
    visited_my = set()
    
    for stone in my_stones:
        if stone not in visited_my:
            group = set()
            find_group(stone, group, my_stones)
            visited_my.update(group)
            liberties = count_liberties(group)
            my_groups.append((group, liberties))
    
    # Candidate moves: empty intersections adjacent to opponent or my stones
    candidate_moves = set()
    
    # Add empty intersections adjacent to opponent stones
    for r, c in opp_stones:
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in empty_intersections:
                candidate_moves.add((nr, nc))
    
    # Add empty intersections adjacent to my stones
    for r, c in my_stones:
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in empty_intersections:
                candidate_moves.add((nr, nc))
    
    # Also consider center and corner if no candidates
    if not candidate_moves:
        # Try center and 4-4 points
        center_candidates = [(10, 10), (10, 9), (9, 10), (10, 11), (11, 10)]
        corner_candidates = [(4, 4), (4, 16), (16, 4), (16, 16)]
        for cand in center_candidates + corner_candidates:
            if cand in empty_intersections:
                candidate_moves.add(cand)
    
    # If still no candidates, consider any empty space
    if not candidate_moves:
        candidate_moves = empty_intersections
    
    # Evaluate each candidate move
    best_move = (0, 0)  # Default: pass
    best_score = -float('inf')
    
    for move in candidate_moves:
        r, c = move
        
        # Skip if this move would be suicidal (unless it captures)
        temp_my = my_stones | {move}
        temp_all = temp_my | opp_stones
        
        # Check if move would have liberties (not suicidal)
        move_liberties = 0
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) not in temp_all:
                move_liberties += 1
        
        # Check if this move captures any opponent group
        captured = False
        capture_count = 0
        for group, liberties in opp_groups:
            if move in group:
                continue
            # Simulate adding our stone and check opponent group liberties
            group_liberties = 0
            for gr, gc in group:
                for nr, nc in get_neighbors(gr, gc):
                    if (nr, nc) not in temp_all:
                        group_liberties += 1
            # Check if the opponent group would have exactly 0 liberties
            # This is a simplified version: we check if move reduces liberties to 0
            # We do it more accurately by checking the specific group
            if move in [n for gr, gc in group for n in get_neighbors(gr, gc)]:
                # This move is adjacent to the group
                # Recalculate the liberty count assuming this move is placed
                group_liberties = 0
                for gr, gc in group:
                    for nr, nc in get_neighbors(gr, gc):
                        if (nr, nc) not in temp_all:
                            group_liberties += 1
                if group_liberties == 0:
                    captured = True
                    capture_count += len(group)
                    break
        
        # Scoring function
        score = 0
        
        # High priority: capture opponent stones
        if captured:
            score += 1000 * capture_count
        
        # Medium priority: prevent opponent capture
        for group, liberties in opp_groups:
            if liberties == 1:
                # If opponent group has only one liberty and we don't play there,
                # it might get captured in next move (but we're not directly preventing)
                if move in [n for gr, gc in group for n in get_neighbors(gr, gc)]:
                    score += 500
        
        # Medium priority: connect or extend my groups
        for group, liberties in my_groups:
            if move in [n for gr, gc in group for n in get_neighbors(gr, gc)]:
                score += 200
        
        # Small priority: reduce opponent liberties
        for group, liberties in opp_groups:
            if move in [n for gr, gc in group for n in get_neighbors(gr, gc)]:
                score += 50
        
        # Small priority: increase own liberties
        for group, liberties in my_groups:
            if move in [n for gr, gc in group for n in get_neighbors(gr, gc)]:
                # If this move increases our group's potential liberties
                score += 20
        
        # Small priority: play in corner/edge/center based on board position
        if move in [(1, 1), (1, 19), (19, 1), (19, 19)]:
            score += 10
        elif move[0] in [1, 19] or move[1] in [1, 19]:
            score += 8
        elif 5 <= move[0] <= 15 and 5 <= move[1] <= 15:
            score += 5
        
        # Avoid suicidal moves (unless they capture)
        if not captured and move_liberties == 0:
            score = -float('inf')  # Don't play suicidal moves
        
        # Prefer moves that don't create weaknesses (no easy opponent captures)
        # Check if our own group after placing stone has few liberties
        # Find my group that includes this stone
        if move in my_stones:
            continue  # This shouldn't happen but just in case
        
        # Check if this stone creates a weak group for me
        temp_my_group = set()
        stack = [move]
        visited = set([move])
        while stack:
            curr = stack.pop()
            temp_my_group.add(curr)
            for nr, nc in get_neighbors(curr[0], curr[1]):
                if (nr, nc) in temp_my and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    stack.append((nr, nc))
        
        my_liberties_after = 0
        for gr, gc in temp_my_group:
            for nr, nc in get_neighbors(gr, gc):
                if (nr, nc) not in temp_all:
                    my_liberties_after += 1
        
        # Penalize if our new group has only 1 liberty and it's not capturing
        # and the opponent can immediately play there next
        if not captured and my_liberties_after == 1:
            # Check if opponent can play at any liberty next turn
            for gr, gc in temp_my_group:
                for nr, nc in get_neighbors(gr, gc):
                    if (nr, nc) not in temp_all:
                        # This is a liberty of our group
                        # Check if opponent has a group adjacent to this liberty
                        opponent_adjacent = False
                        for opp_gr, opp_gc in opp_stones:
                            for opp_nr, opp_nc in get_neighbors(opp_gr, opp_gc):
                                if (opp_nr, opp_nc) == (nr, nc):
                                    opponent_adjacent = True
                                    break
                            if opponent_adjacent:
                                break
                        if opponent_adjacent:
                            score -= 100
                            break
        
        # If score beats best, record
        if score > best_score:
            best_score = score
            best_move = move
    
    # If best_move has negative score and we have no good moves, pass
    # But if we have at least one legal move with score > -10000, use it
    # Only pass if really nothing better
    if best_score < -10000 and len(empty_intersections) > 0:
        # Try a non-dangerous move
        for move in empty_intersections:
            r, c = move
            is_dangerous = False
            # Check if it captures opponent
            temp_my = my_stones | {move}
            temp_all = temp_my | opp_stones
            
            # Check for capture
            for group, liberties in opp_groups:
                if move in [n for gr, gc in group for n in get_neighbors(gr, gc)]:
                    # Recalculate liberties for this group
                    group_liberties = 0
                    for gr, gc in group:
                        for nr, nc in get_neighbors(gr, gc):
                            if (nr, nc) not in temp_all:
                                group_liberties += 1
                    if group_liberties == 0:
                        return move  # Capture move is always safe
            
            # Check if this move is suicidal
            self_liberties = 0
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in temp_all:
                    self_liberties += 1
            if self_liberties > 0:
                return move  # Safe and legal
            
        # If nothing, return pass
        return (0, 0)
    
    return best_move
