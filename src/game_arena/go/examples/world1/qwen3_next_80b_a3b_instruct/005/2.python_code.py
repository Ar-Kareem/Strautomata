
import numpy as np
from typing import List, Tuple, Set

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    # Convert to sets for O(1) lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    all_stones = my_stones | opp_stones
    
    # Define 4-directional neighbors (up, down, left, right)
    neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    def is_on_board(r, c):
        return 1 <= r <= 19 and 1 <= c <= 19
    
    def get_liberties(group):
        """Return set of liberties for a group of stones."""
        liberties = set()
        for r, c in group:
            for dr, dc in neighbors:
                nr, nc = r + dr, c + dc
                if is_on_board(nr, nc) and (nr, nc) not in all_stones:
                    liberties.add((nr, nc))
        return liberties
    
    def get_group(stone, visited=None):
        """Return the group of connected stones of same color, starting from stone."""
        if visited is None:
            visited = set()
        r, c = stone
        group = {stone}
        visited.add(stone)
        for dr, dc in neighbors:
            nr, nc = r + dr, c + dc
            if is_on_board(nr, nc) and (nr, nc) not in visited and (nr, nc) in my_stones:
                if (nr, nc) not in visited:
                    group.update(get_group((nr, nc), visited))
        return group
    
    def get_opponent_group(stone, visited=None):
        """Return the group of connected opponent stones."""
        if visited is None:
            visited = set()
        r, c = stone
        group = {stone}
        visited.add(stone)
        for dr, dc in neighbors:
            nr, nc = r + dr, c + dc
            if is_on_board(nr, nc) and (nr, nc) not in visited and (nr, nc) in opp_stones:
                if (nr, nc) not in visited:
                    group.update(get_opponent_group((nr, nc), visited))
        return group

    # Check for immediate captures (target opponent groups with 1 liberty)
    for opp_stone in opp_stones:
        opp_group = get_opponent_group(opp_stone)
        opp_liberties = get_liberties(opp_group)
        if len(opp_liberties) == 1:
            capture_point = list(opp_liberties)[0]
            # Check if placing here is legal (would not be suicide)
            test_my_stones = my_stones | {capture_point}
            test_all_stones = test_my_stones | opp_stones
            # Simulate placing stone and check if our own group has liberties
            # But note: we are capturing opponent, so we only need to check that capture_point is not suicide
            # A move is suicide if after placing, the group of that stone has no liberties AND no capture occurs
            # But since we're capturing an opponent group, we already know opponent group will be removed
            # We only need to check that the stone placed doesn't form a group with 0 liberties after capture
            group_at_capture = get_group(capture_point, set())
            group_liberties = get_liberties(group_at_capture)
            # After capturing opponent, remove the opponent group from all_stones temporarily
            remaining_opponent = opp_stones - opp_group
            test_all_after_capture = test_my_stones | remaining_opponent
            # Now recompute liberties for our group with opponent group removed
            our_liberties_after_capture = set()
            for r, c in group_at_capture:
                for dr, dc in neighbors:
                    nr, nc = r + dr, c + dc
                    if is_on_board(nr, nc) and (nr, nc) not in test_all_after_capture:
                        our_liberties_after_capture.add((nr, nc))
            if len(our_liberties_after_capture) > 0:
                return capture_point  # Capturing move is legal and optimal

    # Look for moves that reduce opponent liberties (2-liberty groups)
    for opp_stone in opp_stones:
        opp_group = get_opponent_group(opp_stone)
        opp_liberties = get_liberties(opp_group)
        if len(opp_liberties) == 2:
            # Try playing on one of the liberties to threaten capture
            for liberty in opp_liberties:
                # Check if we can play here without suicide
                test_my_stones = my_stones | {liberty}
                test_all_stones = test_my_stones | opp_stones
                # Check if the stone we play has any liberties after placement (ignoring opponent capture for now)
                group_at_liberty = get_group(liberty, set())
                liberties_of_new_group = get_liberties(group_at_liberty)
                # Check liberties excluding the one we're about to fill
                remaining_liberties = liberties_of_new_group - {liberty}
                # Also, check after removing opponent group if it would be captured
                if len(remaining_liberties) > 0:  # not suicide
                    # Also, check if this move causes opponent capture
                    captured = False
                    for r, c in neighbors:
                        nr, nc = liberty[0] + r, liberty[1] + c
                        if (nr, nc) in opp_stones:
                            opp_neighbor_group = get_opponent_group((nr, nc))
                            opp_neighbor_liberties = get_liberties(opp_neighbor_group)
                            if len(opp_neighbor_liberties) == 1 and liberty in opp_neighbor_liberties:
                                captured = True
                                break
                    if captured or len(remaining_liberties) > 0:
                        return liberty  # Strong move to threaten capture

    # Evaluate moves based on territory and influence
    # Priority: corners, edges, center
    # Generate candidate moves: empty points adjacent to our stones or opponent stones
    candidate_moves = set()
    
    # Add points adjacent to our stones
    for r, c in my_stones:
        for dr, dc in neighbors:
            nr, nc = r + dr, c + dc
            if is_on_board(nr, nc) and (nr, nc) not in all_stones:
                candidate_moves.add((nr, nc))
    
    # Add points adjacent to opponent stones (defensive)
    for r, c in opp_stones:
        for dr, dc in neighbors:
            nr, nc = r + dr, c + dc
            if is_on_board(nr, nc) and (nr, nc) not in all_stones:
                candidate_moves.add((nr, nc))
    
    # If no candidate moves found (rare), consider any empty point
    if not candidate_moves:
        for r in range(1, 20):
            for c in range(1, 20):
                if (r, c) not in all_stones:
                    candidate_moves.add((r, c))
    
    # Heuristic scoring for candidate moves
    best_move = None
    best_score = -float('inf')
    
    for move in candidate_moves:
        r, c = move
        score = 0
        
        # 1. Corner priority (3-3, 4-4, 3-4 points)
        if (r, c) in [(3,3), (3,4), (4,3), (4,4), (17,3), (17,4), (16,3), (16,4),
                      (3,17), (3,16), (4,17), (4,16), (17,17), (17,16), (16,17), (16,16)]:
            score += 10
        # 2. Edge priority (not corner)
        elif r == 1 or r == 19 or c == 1 or c == 19:
            score += 5
        # 3. Center bonus
        elif 7 <= r <= 13 and 7 <= c <= 13:
            score += 3
        
        # 4. Liberty gain for our group
        test_my_stones = my_stones | {move}
        test_all_stones = test_my_stones | opp_stones
        
        our_group_at_move = get_group(move, set())
        our_liberties_after = get_liberties(our_group_at_move)
        score += len(our_liberties_after) * 1.5
        
        # 5. Reduce opponent liberties
        opp_reduced_liberties = 0
        for dr, dc in neighbors:
            nr, nc = r + dr, c + dc
            if (nr, nc) in opp_stones:
                opp_group = get_opponent_group((nr, nc))
                opp_liberties = get_liberties(opp_group)
                # If this move removes one liberty
                if move in opp_liberties:
                    opp_reduced_liberties += 1
        score += opp_reduced_liberties * 2
        
        # 6. Avoid moves that make our group weak (few liberties)
        # Don't create groups with < 2 liberties unless capturing
        
        # 7. Check if move is suicidal (without capture)
        group_after = get_group(move, set())
        liberties_after = get_liberties(group_after)
        # Simulate opponent group captures
        removed_opponents = set()
        for dr, dc in neighbors:
            nr, nc = r + dr, c + dc
            if (nr, nc) in opp_stones:
                opp_group = get_opponent_group((nr, nc))
                opp_liberties = get_liberties(opp_group)
                if len(opp_liberties) == 1 and move in opp_liberties:
                    removed_opponents.update(opp_group)
        
        # If we capture opponent, then we're fine even if our group has no liberties (after capture)
        if len(removed_opponents) == 0 and len(liberties_after) == 0:
            continue  # Suicide move, skip

        # If we capture, we definitely want this move (already checked earlier, but double-check)
        if len(removed_opponents) > 0:
            score += 100  # Huge bonus for capture
        
        if score > best_score:
            best_score = score
            best_move = move
    
    # If we found a move, return it
    if best_move is not None:
        return best_move
    
    # If no move found (should not happen), pass
    return (0, 0)
