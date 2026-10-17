
import numpy as np
from collections import defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Convert to sets for fast lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    all_stones = my_stones | opp_stones
    
    # If board is empty, play center (10,10) or a corner for 3-3
    if len(all_stones) == 0:
        return (10, 10)  #center is generally good, but 4-4 or 3-3 also valid
    
    # Define possible moves (19x19 board) and candidate moves
    candidate_moves = []
    
    # Generate all possible moves within 2 stones of existing stones
    for r, c in all_stones:
        for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) not in all_stones:
                candidate_moves.append((nr, nc))
    
    # Also add center if not taken (encourage control)
    center_candidates = [(10,10), (9,9), (11,11), (9,11), (11,9)]
    for cand in center_candidates:
        if cand not in all_stones:
            candidate_moves.append(cand)
    
    # Remove duplicates
    candidate_moves = list(set(candidate_moves))
    
    # If no candidates (super rare), pass
    if not candidate_moves:
        return (0, 0)
    
    # Evaluate each candidate move
    move_scores = []
    
    for move in candidate_moves:
        score = 0
        
        # Check if move captures opponent stones
        captured = get_captures(move, my_stones, opp_stones)
        score += len(captured) * 10.0  # High reward for capture
        
        # Check if move is vital point to prevent opponent capture
        if is_vital_point(move, opp_stones, my_stones):
            score += 5.0
            
        # Check liberties of our new group (after playing move)
        new_my_stones = my_stones | {move}
        new_group = get_connected_group(move, new_my_stones)
        liberties = count_liberties(new_group, new_my_stones, opp_stones)
        score += liberties * 0.5
        
        # Check if move reduces opponent liberties
        for opp_stone in opp_stones:
            if distance(move, opp_stone) <= 2:  # Check adjacent affected groups
                opp_group = get_connected_group(opp_stone, opp_stones)
                opp_liberties = count_liberties(opp_group, opp_stones, new_my_stones)
                # If opponent group had 1 liberty and now has 0, it's a capture (already counted)
                if opp_liberties == 1 and len(opp_group) > 1:
                    score += 3.0  # Threatening capture
                elif opp_liberties == 2 and len(opp_group) > 1:
                    score += 1.0  # Reducing liberties
        
        # Check if move is in a corner or edge - traditionally good for foundation
        if move[0] in [1, 19] or move[1] in [1, 19]:
            score += 0.5
        
        # Avoid suicide moves
        if is_suicide(move, new_my_stones, opp_stones):
            score = -1000.0  # Very bad
            
        # Prefer moves that don't connect to weak groups
        # We can add connection bonus if we link stones
        connected_count = count_adjacent_stones(move, my_stones)
        if connected_count >= 2:
            score += 1.0  # Good for forming shape
        
        move_scores.append((move, score))
    
    # Sort by score, pick best
    move_scores.sort(key=lambda x: x[1], reverse=True)
    best_move = move_scores[0][0]
    
    # Ensure we don't return an illegal move
    # Double-check legality
    if is_suicide(best_move, my_stones | {best_move}, opp_stones):
        # Try next best
        for move, score in move_scores[1:]:
            if not is_suicide(move, my_stones | {move}, opp_stones):
                return move
        # If all possible moves are suicide, pass
        return (0, 0)
    
    # If the best move would capture, we're done
    captured = get_captures(best_move, my_stones, opp_stones)
    if len(captured) > 0:
        return best_move
    
    return best_move

def get_captures(move, my_stones, opp_stones):
    """Return set of opponent stones captured by playing move"""
    new_my_stones = my_stones | {move}
    captured = set()
    
    for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
        nr, nc = move[0] + dr, move[1] + dc
        if (nr, nc) in opp_stones:
            opp_group = get_connected_group((nr, nc), opp_stones)
            if count_liberties(opp_group, opp_stones, new_my_stones) == 0:
                captured.update(opp_group)
                
    return captured

def get_connected_group(start_stone, stones):
    """Get all stones in the connected group containing start_stone"""
    group = set()
    stack = [start_stone]
    group.add(start_stone)
    
    while stack:
        stone = stack.pop()
        r, c = stone
        for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
            neighbor = (r + dr, c + dc)
            if neighbor in stones and neighbor not in group:
                group.add(neighbor)
                stack.append(neighbor)
    
    return group

def count_liberties(group, my_stones, opp_stones):
    """Count liberties of a group of stones"""
    liberties = set()
    for r, c in group:
        for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
            neighbor = (r + dr, c + dc)
            if 1 <= neighbor[0] <= 19 and 1 <= neighbor[1] <= 19:
                if neighbor not in my_stones and neighbor not in opp_stones:
                    liberties.add(neighbor)
    return len(liberties)

def is_suicide(move, new_my_stones, opp_stones):
    """Check if playing move results in self-capture"""
    # Play the move and check if the new group has zero liberties
    new_group = get_connected_group(move, new_my_stones)
    return count_liberties(new_group, new_my_stones, opp_stones) == 0

def is_vital_point(move, opp_stones, my_stones):
    """Check if move is a vital point for opponent (prevents eye formation)"""
    # This is a simplified check: look for potential eyes or shapes
    # If a move blocks the opponent from making an eye-like shape, it's vital
    for opp_stone in opp_stones:
        if distance(move, opp_stone) == 1:
            opp_group = get_connected_group(opp_stone, opp_stones)
            if len(opp_group) <= 3:  # Small group
                # Check if this move would prevent eye formation
                potential_eye_points = get_nearby_empty_spots(opp_group, opp_stones | my_stones)
                # If this move fills a potential eye point, it's vital
                if move in potential_eye_points and len(potential_eye_points) <= 2:
                    return True
    return False

def distance(point1, point2):
    """Manhattan distance"""
    return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])

def get_nearby_empty_spots(group, all_stones):
    """Get empty points adjacent to group"""
    spots = set()
    for r, c in group:
        for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
            neighbor = (r + dr, c + dc)
            if 1 <= neighbor[0] <= 19 and 1 <= neighbor[1] <= 19 and neighbor not in all_stones:
                spots.add(neighbor)
    return spots

def count_adjacent_stones(move, my_stones):
    """Count how many of my stones are adjacent to the move"""
    count = 0
    r, c = move
    for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
        neighbor = (r + dr, c + dc)
        if neighbor in my_stones:
            count += 1
    return count
