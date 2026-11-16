
import random
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """
    Hex policy using connectivity analysis and path evaluation.
    """
    BOARD_SIZE = 11
    
    # Convert to sets for O(1) lookup
    my_stones = set(me)
    opp_stones = set(opp)
    occupied = my_stones | opp_stones
    
    # Get all empty cells
    empty_cells = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) 
                   if (r, c) not in occupied]
    
    if not empty_cells:
        return (0, 0)  # Should never happen
    
    # Opening book - prefer center area
    if len(me) == 0:
        return (5, 5)
    if len(me) == 1 and len(opp) == 1:
        # Respond near center
        center_moves = [(4, 5), (5, 4), (5, 6), (6, 5), (4, 4), (6, 6)]
        for move in center_moves:
            if move in empty_cells:
                return move
    
    # Evaluate all empty cells
    best_score = float('-inf')
    best_moves = []
    
    for move in empty_cells:
        score = evaluate_move(move, my_stones, opp_stones, color, BOARD_SIZE)
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)
    
    return random.choice(best_moves) if best_moves else empty_cells[0]


def get_neighbors(r, c, board_size=11):
    """Get all 6 hex neighbors of cell (r, c)."""
    candidates = [
        (r-1, c), (r-1, c+1),  # top two
        (r, c-1), (r, c+1),     # left and right
        (r+1, c-1), (r+1, c)    # bottom two
    ]
    return [(nr, nc) for nr, nc in candidates 
            if 0 <= nr < board_size and 0 <= nc < board_size]


def evaluate_move(move, my_stones, opp_stones, color, board_size):
    """Evaluate the quality of a move."""
    # Simulate placing the stone
    new_my_stones = my_stones | {move}
    new_opp_stones = opp_stones | {move}  # For opponent blocking evaluation
    
    # My score with this move
    my_score = evaluate_position(new_my_stones, opp_stones, color, board_size)
    
    # Opponent's score if they played here (blocking value)
    opp_color = 'w' if color == 'b' else 'b'
    opp_score = evaluate_position(new_opp_stones, my_stones, opp_color, board_size)
    
    # Combined score: value of my position + blocking opponent
    return my_score + 0.7 * opp_score


def evaluate_position(my_stones, opp_stones, color, board_size):
    """Evaluate position strength using shortest path distance."""
    if not my_stones:
        return 0
    
    # Use BFS to find shortest path from one side to the other
    distance = shortest_path_distance(my_stones, opp_stones, color, board_size)
    
    # Lower distance is better (closer to winning)
    # Convert to positive score
    score = 1000.0 / (distance + 1)
    
    # Add bonus for connectivity
    connectivity_bonus = sum(1 for stone in my_stones 
                            for neighbor in get_neighbors(stone[0], stone[1], board_size)
                            if neighbor in my_stones)
    
    return score + connectivity_bonus * 2


def shortest_path_distance(my_stones, opp_stones, color, board_size):
    """Calculate shortest path distance to connect sides using BFS."""
    # For black: connect top (row 0) to bottom (row 10)
    # For white: connect left (col 0) to right (col 10)
    
    if color == 'b':
        start_cells = [(r, c) for r, c in my_stones if r == 0]
        target_row = board_size - 1
    else:
        start_cells = [(r, c) for r, c in my_stones if c == 0]
        target_col = board_size - 1
    
    if not start_cells:
        # No stones on starting edge, find minimum distance to starting edge
        if color == 'b':
            start_dist = min(r for r, c in my_stones) if my_stones else board_size
        else:
            start_dist = min(c for r, c in my_stones) if my_stones else board_size
        return start_dist + board_size
    
    # BFS from start cells
    queue = deque()
    visited = set()
    
    for cell in start_cells:
        queue.append((cell, 0))
        visited.add(cell)
    
    while queue:
        (r, c), dist = queue.popleft()
        
        # Check if we reached target edge
        if color == 'b' and r == target_row:
            return dist
        if color == 'w' and c == target_col:
            return dist
        
        # Explore neighbors
        for nr, nc in get_neighbors(r, c, board_size):
            if (nr, nc) not in visited:
                if (nr, nc) in my_stones:
                    # Already our stone - no cost
                    visited.add((nr, nc))
                    queue.append(((nr, nc), dist))
                elif (nr, nc) not in opp_stones:
                    # Empty cell - costs 1
                    visited.add((nr, nc))
                    queue.append(((nr, nc), dist + 1))
                # Opponent stones are blocked
    
    # No path found
    return board_size * 2
