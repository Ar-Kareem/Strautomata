
import random
from typing import List, Tuple, Set, Dict, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Advanced Battleship targeting policy using hit tracking, probability weighting,
    and pattern-based search to maximize ship cell hits.
    """
    n = 10
    # Track all unshot positions
    available_moves = []
    hit_positions = []
    max_prob = 0
    best_move = (0, 0)
    
    # First, collect all unshot positions and hit positions
    for i in range(n):
        for j in range(n):
            if board[i][j] == 0:
                available_moves.append((i, j))
            elif board[i][j] == 1:
                hit_positions.append((i, j))
    
    # If no hits yet, use probability-based search with checkerboard pattern
    if not hit_positions:
        # Use checkerboard pattern to cover maximum uncertainty
        # Focus on every other square to efficiently cover ship possibilities
        corner_moves = [(0,0), (0,9), (9,0), (9,9)]
        for move in corner_moves:
            if move in available_moves:
                return move
                
        # Use weighted probability based on ship placement possibilities
        prob_board = [[0 for _ in range(n)] for _ in range(n)]
        ships = [5, 4, 3, 3, 2]
        
        # Calculate placement possibilities for each ship
        for ship_size in ships:
            # Horizontal placements
            for r in range(n):
                for c in range(n - ship_size + 1):
                    if all(board[r][c + i] != -1 for i in range(ship_size)):
                        for i in range(ship_size):
                            prob_board[r][c + i] += 1
            
            # Vertical placements
            for r in range(n - ship_size + 1):
                for c in range(n):
                    if all(board[r + i][c] != -1 for i in range(ship_size)):
                        for i in range(ship_size):
                            prob_board[r + i][c] += 1
        
        # Find the highest probability unshot position
        for i in range(n):
            for j in range(n):
                if board[i][j] == 0 and prob_board[i][j] > max_prob:
                    max_prob = prob_board[i][j]
                    best_move = (i, j)
                    
        return best_move if max_prob > 0 else random.choice(available_moves)
    
    # If we have hits, focus on finishing off ships
    # Group hits that are connected (likely part of same ship)
    hit_groups = []
    visited = set()
    
    for hit in hit_positions:
        if hit not in visited:
            # Find connected hits (same row or column, adjacent)
            group = []
            stack = [hit]
            while stack:
                r, c = stack.pop()
                if (r, c) not in visited:
                    visited.add((r, c))
                    group.append((r, c))
                    # Check neighbors
                    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < n and 0 <= nc < n and 
                            board[nr][nc] == 1 and (nr, nc) not in visited):
                            stack.append((nr, nc))
            hit_groups.append(group)
    
    # For each hit group, try to extend in possible directions
    for group in hit_groups:
        if len(group) == 1:
            # Single hit - check all four directions
            r, c = group[0]
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            possible_extensions = []
            
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if (0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0):
                    # Check if this extension is viable based on ship constraints
                    if is_valid_extension(board, nr, nc, dr, dc, True):
                        possible_extensions.append((nr, nc))
            
            if possible_extensions:
                # Prefer extensions that maintain alignment with other hits if possible
                return random.choice(possible_extensions)
        else:
            # Multiple hits - determine orientation and extend
            group.sort()  # Sort to determine orientation
            r0, c0 = group[0]
            r1, c1 = group[-1]
            
            # Determine if horizontal or vertical
            if r0 == r1:  # Horizontal
                # Try to extend left
                if c0 > 0 and board[r0][c0-1] == 0:
                    if is_valid_extension(board, r0, c0-1, 0, -1, True):
                        return (r0, c0-1)
                # Try to extend right
                if c1 < n-1 and board[r0][c1+1] == 0:
                    if is_valid_extension(board, r0, c1+1, 0, 1, True):
                        return (r0, c1+1)
            else:  # Vertical
                # Try to extend up
                if r0 > 0 and board[r0-1][c0] == 0:
                    if is_valid_extension(board, r0-1, c0, -1, 0, True):
                        return (r0-1, c0)
                # Try to extend down
                if r1 < n-1 and board[r1+1][c0] == 0:
                    if is_valid_extension(board, r1+1, c0, 1, 0, True):
                        return (r1+1, c0)
    
    # If we can't extend any groups, use weighted probabilities focused near hits
    prob_board = [[0 for _ in range(n)] for _ in range(n)]
    ships = [5, 4, 3, 3, 2]
    
    for ship_size in ships:
        # Horizontal placements
        for r in range(n):
            for c in range(n - ship_size + 1):
                valid = True
                for i in range(ship_size):
                    if board[r][c + i] == -1:
                        valid = False
                        break
                if valid:
                    for i in range(ship_size):
                        if board[r][c + i] == 0:  # Only score unshot positions
                            # Boost probability near existing hits
                            for hit_r, hit_c in hit_positions:
                                dist = abs(r - hit_r) + abs(c + i - hit_c)
                                if dist <= ship_size:
                                    prob_board[r][c + i] += 1 + (ship_size - dist)
        
        # Vertical placements
        for r in range(n - ship_size + 1):
            for c in range(n):
                valid = True
                for i in range(ship_size):
                    if board[r + i][c] == -1:
                        valid = False
                        break
                if valid:
                    for i in range(ship_size):
                        if board[r + i][c] == 0:  # Only score unshot positions
                            # Boost probability near existing hits
                            for hit_r, hit_c in hit_positions:
                                dist = abs(r + i - hit_r) + abs(c - hit_c)
                                if dist <= ship_size:
                                    prob_board[r + i][c] += 1 + (ship_size - dist)
    
    # Find the highest probability unshot position
    for i in range(n):
        for j in range(n):
            if board[i][j] == 0 and prob_board[i][j] > max_prob:
                max_prob = prob_board[i][j]
                best_move = (i, j)
    
    return best_move if max_prob > 0 else random.choice(available_moves)

def is_valid_extension(board: List[List[int]], r: int, c: int, dr: int, dc: int, check_back: bool = False) -> bool:
    """
    Check if extending in a direction is valid based on ship constraints.
    """
    n = 10
    # Check if we can place a ship in either direction
    for length in [5, 4, 3, 3, 2]:
        # Check forward (direction of dr, dc)
        valid_forward = True
        for i in range(length):
            nr, nc = r + dr * i, c + dc * i
            if not (0 <= nr < n and 0 <= nc < n):
                valid_forward = False
                break
            if board[nr][nc] == -1:
                valid_forward = False
                break
        
        # If checking backward too, verify both directions
        if check_back and valid_forward:
            # Check backward (opposite direction)
            valid_backward = True
            for i in range(1, length):  # Don't recheck origin
                nr, nc = r - dr * i, c - dc * i
                if not (0 <= nr < n and 0 <= nc < n):
                    valid_backward = False
                    break
                if board[nr][nc] == -1:
                    valid_backward = False
                    break
            if valid_forward or valid_backward:
                return True
        elif valid_forward:
            return True
    
    return False
