
import numpy as np
from typing import List, Tuple, Dict

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    # Convert lists to sets for faster lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    all_stones = my_stones | opp_stones

    # Board size
    BOARD_SIZE = 19

    # Helper function to get neighbors
    def get_neighbors(r, c):
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                neighbors.append((nr, nc))
        return neighbors

    # Helper function to count liberties of a group (connected component)
    def count_liberties(stone_set, group_stones):
        liberties = set()
        for r, c in group_stones:
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in all_stones:
                    liberties.add((nr, nc))
        return len(liberties), liberties

    # Helper function to get connected group (flood fill)
    def get_group(stone, stone_set, visited):
        group = set()
        stack = [stone]
        visited.add(stone)
        while stack:
            r, c = stack.pop()
            group.add((r, c))
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in stone_set and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    stack.append((nr, nc))
        return group

    # Find all opponent groups and their liberties
    opp_visited = set()
    opp_groups = []
    for stone in opp_stones:
        if stone not in opp_visited:
            group = get_group(stone, opp_stones, opp_visited)
            liberties, _ = count_liberties(opp_stones, group)
            opp_groups.append((group, liberties))

    # Find all my groups and their liberties
    my_visited = set()
    my_groups = []
    for stone in my_stones:
        if stone not in my_visited:
            group = get_group(stone, my_stones, my_visited)
            liberties, _ = count_liberties(my_stones, group)
            my_groups.append((group, liberties))

    # Candidate moves: empty intersections adjacent to any stone
    candidate_moves = set()
    all_empty = [(r, c) for r in range(1, BOARD_SIZE + 1) for c in range(1, BOARD_SIZE + 1) if (r, c) not in all_stones]

    # First, check for immediate capture moves: any move that removes last liberty of opponent group
    for opp_group, opp_liberties in opp_groups:
        if opp_liberties == 1:
            # Find the single liberty
            for r, c in opp_group:
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) not in all_stones:
                        # Check if playing here captures the group
                        # Temporarily add this move
                        temp_board = all_stones | {(nr, nc)}
                        # Check if the group still has liberties after move
                        new_liberties = 0
                        for gr, gc in opp_group:
                            for ngr, ngc in get_neighbors(gr, gc):
                                if (ngr, ngc) not in temp_board:
                                    new_liberties += 1
                        if new_liberties == 0:
                            # This move captures
                            return ((nr, nc), memory)

    # Check for moves that give opponent 1 liberty (set up for next turn capture)
    # But only if we are not putting ourselves in atari
    for opp_group, opp_liberties in opp_groups:
        if opp_liberties == 2:
            # Try to fill one liberty, see if we leave them with only 1
            for r, c in opp_group:
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) not in all_stones:
                        # Simulate playing here
                        temp_board = all_stones | {(nr, nc)}
                        # Recompute liberties for this group
                        new_liberties = 0
                        for gr, gc in opp_group:
                            for ngr, ngc in get_neighbors(gr, gc):
                                if (ngr, ngc) not in temp_board:
                                    new_liberties += 1
                        if new_liberties == 1:
                            # Check if our own group that we're adding to is not in atari
                            # Find our group if this move connects to one
                            new_group = set()
                            stack = [(nr, nc)]
                            visited_temp = set()
                            visited_temp.add((nr, nc))
                            while stack:
                                cr, cc = stack.pop()
                                new_group.add((cr, cc))
                                for ncr, ncc in get_neighbors(cr, cc):
                                    if (ncr, ncc) in my_stones and (ncr, ncc) not in visited_temp:
                                        visited_temp.add((ncr, ncc))
                                        stack.append((ncr, ncc))
                                    elif (ncr, ncc) == (nr, nc):
                                        pass  # already added
                            # Check liberties of the new group
                            if len(new_group) > 0:
                                temp_my_stones = my_stones | {(nr, nc)}
                                group_liberties, _ = count_liberties(temp_my_stones, new_group)
                                # Avoid putting ourselves in atari unless it's a capturing move
                                if group_liberties >= 2:
                                    candidate_moves.add((nr, nc))
    
    # Look for moves that threaten to capture (two liberties now, will be one after move)
    # Check opponent groups with 2 liberties and see if we can reduce it

    # Check for self-atari avoidance
    for r, c in all_empty:
        # Try playing here and see if any of our groups go into atari
        temp_stones = my_stones | {(r, c)}
        # Find all connected groups that include (r,c) or neighbors
        group_to_check = set()
        stack = [(r, c)]
        visited = set()
        visited.add((r, c))
        while stack:
            cr, cc = stack.pop()
            group_to_check.add((cr, cc))
            for nr, nc in get_neighbors(cr, cc):
                if (nr, nc) in my_stones and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    stack.append((nr, nc))
        
        # Count liberties of this new group
        if len(group_to_check) > 0:
            liberties, _ = count_liberties(temp_stones, group_to_check)
            if liberties == 0:
                # This move puts our own group in atari (self-atari) without capture - illegal
                continue
            # Also, if liberties == 1, check if any of the opponent stones it attacks are capturable
            # We already checked for capture above, so we're just avoiding self-atari unless it captures
            # But we already check for capture first, so if we get here and liberties==1 and no capture, then skip
            # So we continue to allow only moves that don't cause self-atari unless already captured
            # But our capture check above already handled captures, so now:
            # if liberties == 1: then we are in atari, which we avoid unless it's the only move
            # We'll record it but rank it low
            # For now, we'll just include it as candidate but with low priority
            candidate_moves.add((r, c))
        else:
            candidate_moves.add((r, c))

    # If there are no candidate moves, just pass
    if not candidate_moves and not all_empty:
        return ((0, 0), memory)

    # If no capture moves found, use tactical priority:
    # 1. Moves that reduce opponent liberties (especially to 1)
    # 2. Moves that build eyes or connect groups
    # 3. Corner and edge play
    # 4. Center influence
    # 5. Random safe move

    # Evaluate each candidate
    scores = {}
    for move in candidate_moves:
        r, c = move
        score = 0
        
        # Bonus for corner and edge
        if (r in [1, 19] and c in [1, 19]):
            score += 10  # Corner
        elif r in [1, 19] or c in [1, 19]:
            score += 5   # Edge
        
        # Bonus for center (influence)
        if 8 <= r <= 12 and 8 <= c <= 12:
            score += 3

        # Check how many opponent liberties this move reduces
        opp_liberties_reduced = 0
        opp_groups_affected = 0
        for opp_group, opp_liberties in opp_groups:
            if (r, c) in [n for gr, gc in opp_group for n in get_neighbors(gr, gc)]:
                opp_groups_affected += 1
                # Simulate move and count new liberties
                temp_board = all_stones | {(r, c)}
                new_liberties = 0
                for gr, gc in opp_group:
                    for ngr, ngc in get_neighbors(gr, gc):
                        if (ngr, ngc) not in temp_board:
                            new_liberties += 1
                opp_liberties_reduced += (opp_liberties - new_liberties)

        # Add score for reducing liberties
        score += opp_liberties_reduced * 5

        # Check if this move helps form eye or connect
        # Look at adjacent my stones
        my_adjacent = [n for n in get_neighbors(r, c) if n in my_stones]
        if len(my_adjacent) > 0:
            # Connect to existing group
            score += 4
            
            # Check if this move helps form potential eye
            # If surrounded by 3+ my stones (in corners or edges) and empty around
            my_neighbors = []  # my stones in neighbors
            opp_neighbors = [] # opponent stones in neighbors
            empty_neighbors = [] # empty in neighbors
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in my_stones:
                    my_neighbors.append((nr, nc))
                elif (nr, nc) in opp_stones:
                    opp_neighbors.append((nr, nc))
                else:
                    empty_neighbors.append((nr, nc))
            
            # In corner: if 2 my, 1 opp, and 1 empty -> this could form eye
            if r in [1,19] and c in [1,19]:
                if len(my_neighbors) >= 2 and len(opp_neighbors) <= 1:
                    score += 8
            # In edge: if 3 my, no opp -> high eye potential
            elif r in [1,19] or c in [1,19]:
                if len(my_neighbors) >= 3 and len(opp_neighbors) == 0:
                    score += 6
            # In center: if 3 or more my stones, and <=1 opponent, and 1 empty, then eye potential
            else:
                if len(my_neighbors) >= 3 and len(opp_neighbors) <= 1:
                    score += 5
        
        scores[move] = score

    # Sort candidates by score descending
    if scores:
        best_move = max(scores, key=scores.get)
        return (best_move, memory)
    else:
        # Fallback: play a random empty point if no candidates (shouldn't happen)
        if all_empty:
            return (all_empty[0], memory)
        else:
            # Pass if board is full
            return ((0, 0), memory)
