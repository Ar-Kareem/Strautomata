
import heapq
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Define the six neighbor offsets for hex grid (even-r layout)
    neighbors_offsets = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
    
    # Create set for faster lookup
    occupied = set(me + opp)
    board_size = 11
    
    # Helper: check if a cell is within bounds
    def in_bounds(r, c):
        return 0 <= r < board_size and 0 <= c < board_size
    
    # Helper: get all valid neighbors of a cell
    def get_neighbors(r, c):
        return [(r + dr, c + dc) for dr, dc in neighbors_offsets 
                if in_bounds(r + dr, c + dc)]
    
    # Helper: check if we can win immediately
    def can_win_immediately(stones):
        empty_cells = [(r, c) for r in range(board_size) for c in range(board_size) 
                       if (r, c) not in occupied]
        for cell in empty_cells:
            new_stones = stones + [cell]
            if is_winning_position(new_stones, color):
                return cell
        return None
    
    # Helper: check if a set of stones connects the target sides
    def is_winning_position(stones, color):
        if not stones:
            return False
            
        if color == 'b':  # black: top to bottom
            start_side = {(r, c) for r, c in stones if r == 0}
            end_side = {(r, c) for r, c in stones if r == 10}
            if not start_side or not end_side:
                return False
                
            # BFS from all top row stones
            queue = deque(start_side)
            visited = set(start_side)
            
            while queue:
                r, c = queue.popleft()
                if r == 10:
                    return True
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in stones and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            return False
            
        else:  # white: left to right
            start_side = {(r, c) for r, c in stones if c == 0}
            end_side = {(r, c) for r, c in stones if c == 10}
            if not start_side or not end_side:
                return False
                
            queue = deque(start_side)
            visited = set(start_side)
            
            while queue:
                r, c = queue.popleft()
                if c == 10:
                    return True
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in stones and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            return False
    
    # Check for immediate win
    immediate_win = can_win_immediate(me)
    if immediate_win is not None:
        return immediate_win
    
    # Check for opponent's immediate win and block it
    opponent_color = 'w' if color == 'b' else 'b'
    opponent_can_win = can_win_immediate(opp)
    if opponent_can_win is not None:
        return opponent_can_win
    
    # If no immediate win or block, use A* to find best move
    # Generate all empty cells
    empty_cells = [(r, c) for r in range(board_size) for c in range(board_size) 
                   if (r, c) not in occupied]
    
    if not empty_cells:
        # Should not happen, but safety
        return (5, 5)
    
    # Evaluate each empty cell with a scoring system
    best_move = None
    best_score = -float('inf')
    
    for cell in empty_cells:
        score = evaluate_move(cell, me, color, get_neighbors)
        if score > best_score:
            best_score = score
            best_move = cell
    
    return best_move


def can_win_immediate(stones):
    """Check if adding any single stone to the stones set can create a win."""
    # This is a helper function - use same logic as in policy
    # Assume the board is 11x11, and we don't have access to global occupied here
    # We need to simulate adding one stone to see if it wins
    
    # Create a set of all occupied cells (assume this is called from context where opp is also known)
    # But since we don't have the full state, we'll need to pass occupied
    # Actually we'll refactor: we need to make this internal
    
    # Instead, let's rewrite this as an internal function with access to occupied
    # But for clarity, we'll inline this in the main function and avoid this helper
    # We already did that in main - no need for separate function if we're rewriting
    pass  # We'll delete this helper - we moved the logic to main

# Instead, let's just re-implement everything cleanly without helper functions that are confusing

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Define the six hex neighbor offsets
    neighbors_offsets = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
    
    # Create set for O(1) lookup
    occupied = set(me + opp)
    board_size = 11
    
    def in_bounds(r, c):
        return 0 <= r < board_size and 0 <= c < board_size
    
    def get_neighbors(r, c):
        return [(r + dr, c + dc) for dr, dc in neighbors_offsets 
                if in_bounds(r + dr, c + dc)]
    
    # Determine target sides based on color
    if color == 'b':
        # Black connects top (row 0) and bottom (row 10)
        def is_winning_path(stones):
            # BFS from all top row stones to bottom
            start = {(r, c) for r, c in stones if r == 0}
            if not start:
                return False
            visited = set(start)
            queue = deque(start)
            
            while queue:
                r, c = queue.popleft()
                if r == 10:
                    return True
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in stones and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            return False
        
        # For threat: opponent is white, connects left and right
        opp_color = 'w'
    else:
        # White connects left (col 0) and right (col 10)
        def is_winning_path(stones):
            # BFS from all left column stones to right
            start = {(r, c) for r, c in stones if c == 0}
            if not start:
                return False
            visited = set(start)
            queue = deque(start)
            
            while queue:
                r, c = queue.popleft()
                if c == 10:
                    return True
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in stones and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            return False
        
        opp_color = 'b'
    
    # Check for immediate win
    empty_cells = [(r, c) for r in range(board_size) for c in range(board_size) 
                   if (r, c) not in occupied]
    
    # Try each empty cell: if placing here wins, play it
    for cell in empty_cells:
        test_me = me + [cell]
        if is_winning_path(test_me):
            return cell
    
    # Check if opponent can win on next move
    for cell in empty_cells:
        test_opp = opp + [cell]
        if is_winning_path(test_opp):
            return cell  # Block this move
    
    # No immediate win or block: use A* to find best proactive move
    # Heuristic: prioritize moves that are near own edges and connected to existing stones
    # Create a scoring function
    
    def evaluate_move(cell):
        # Scoring criteria:
        # 1. Connected to existing stones (higher = better)
        # 2. Distance to target edge (closer = better)
        # 3. For black: if row=0 or row=10, bonus
        #    For white: if col=0 or col=10, bonus
        # 4. Also consider connectivity to other stones (degree of existing connections)
        
        score = 0
        my_stones_set = set(me)
        
        # Check how many neighbors are already ours
        neighbors = get_neighbors(cell[0], cell[1])
        own_neighbors = sum(1 for n in neighbors if n in my_stones_set)
        score += own_neighbors * 5  # Strong preference for connecting
        
        # Edge proximity bonus
        r, c = cell
        if color == 'b':
            # Black wants top/bottom
            edge_dist = min(r, board_size - 1 - r)
            # More bonus if already on edge
            if r == 0 or r == 10:
                score += 20
            # Bonus for being near edge
            score += (10 - edge_dist)  # higher score if closer to top/bottom
        else:
            # White wants left/right
            edge_dist = min(c, board_size - 1 - c)
            if c == 0 or c == 10:
                score += 20
            score += (10 - edge_dist)
        
        # Bonus for being central if no edge advantage? Not ideal, but sometimes good
        # We can reduce score for being too central if already connected, but for now, keep it as is
        
        # Avoid moves that are isolated and far from edges
        if own_neighbors == 0:
            # If no connection to own stones, discount if far from edge
            if color == 'b':
                if r > 2 and r < 8:
                    score -= 5  # penalty for middle if not connected
            else:
                if c > 2 and c < 8:
                    score -= 5
        
        return score
    
    # If there are very few stones on board, prioritize center
    if len(me) == 0:
        # First move: take center
        return (5, 5)
    
    # Evaluate all empty cells
    best_cell = None
    best_score = -float('inf')
    
    for cell in empty_cells:
        score = evaluate_move(cell)
        if score > best_score:
            best_score = score
            best_cell = cell
    
    # If all scores are negative or equal, pick the first one
    if best_cell is None:
        return empty_cells[0]
    
    return best_cell
