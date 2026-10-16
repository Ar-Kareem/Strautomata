
import random
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """
    Hex playing policy using virtual connection and resistance-based evaluation.
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
    
    # First move heuristic - play center
    if len(my_stones) == 0:
        return (5, 5)
    
    # Get neighbors function for hex board
    def get_neighbors(r, c):
        """Returns the 6 hexagonal neighbors of cell (r, c)"""
        neighbors = []
        for dr, dc in [(0, -1), (0, 1), (-1, 0), (-1, 1), (1, -1), (1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                neighbors.append((nr, nc))
        return neighbors
    
    # Calculate resistance distance to winning (lower is better)
    def calc_resistance(stones, player_color):
        """Calculate minimum resistance from one edge to opposite edge"""
        # For black: connect top (row 0) to bottom (row 10)
        # For white: connect left (col 0) to right (col 10)
        
        # Build resistance map using BFS with path counting
        if player_color == 'b':
            # Start from top edge
            queue = deque()
            dist = {}
            for c in range(BOARD_SIZE):
                if (0, c) in stones:
                    dist[(0, c)] = 0
                    queue.append((0, c))
                elif (0, c) not in opp_stones:
                    dist[(0, c)] = 1
                    queue.append((0, c))
            
            # BFS to bottom
            while queue:
                r, c = queue.popleft()
                current_dist = dist[(r, c)]
                
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in dist:
                        continue
                    
                    if (nr, nc) in stones:
                        new_dist = current_dist
                    elif (nr, nc) in opp_stones:
                        continue
                    else:
                        new_dist = current_dist + 1
                    
                    dist[(nr, nc)] = new_dist
                    queue.append((nr, nc))
            
            # Find minimum distance to bottom edge
            min_dist = float('inf')
            for c in range(BOARD_SIZE):
                if (10, c) in dist:
                    min_dist = min(min_dist, dist[(10, c)])
            return min_dist
        
        else:  # white
            # Start from left edge
            queue = deque()
            dist = {}
            for r in range(BOARD_SIZE):
                if (r, 0) in stones:
                    dist[(r, 0)] = 0
                    queue.append((r, 0))
                elif (r, 0) not in opp_stones:
                    dist[(r, 0)] = 1
                    queue.append((r, 0))
            
            # BFS to right
            while queue:
                r, c = queue.popleft()
                current_dist = dist[(r, c)]
                
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in dist:
                        continue
                    
                    if (nr, nc) in stones:
                        new_dist = current_dist
                    elif (nr, nc) in opp_stones:
                        continue
                    else:
                        new_dist = current_dist + 1
                    
                    dist[(nr, nc)] = new_dist
                    queue.append((nr, nc))
            
            # Find minimum distance to right edge
            min_dist = float('inf')
            for r in range(BOARD_SIZE):
                if (r, 10) in dist:
                    min_dist = min(min_dist, dist[(r, 10)])
            return min_dist
    
    # Evaluate each empty cell
    best_score = float('-inf')
    best_moves = []
    
    my_resistance = calc_resistance(my_stones, color)
    opp_resistance = calc_resistance(opp_stones, 'w' if color == 'b' else 'b')
    
    for cell in empty_cells:
        # Try placing stone at this cell
        my_new_resistance = calc_resistance(my_stones | {cell}, color)
        opp_new_resistance = calc_resistance(opp_stones | {cell}, 'w' if color == 'b' else 'b')
        
        # Score: how much we improve minus how much we prevent opponent from improving
        my_improvement = my_resistance - my_new_resistance
        opp_blocking = opp_resistance - opp_new_resistance
        
        # Weight defensive play higher if opponent is closer to winning
        if opp_resistance < my_resistance:
            score = my_improvement + 1.5 * opp_blocking
        else:
            score = 1.5 * my_improvement + opp_blocking
        
        # Bonus for being adjacent to our stones (connectivity)
        adjacency_bonus = sum(1 for n in get_neighbors(cell[0], cell[1]) if n in my_stones)
        score += 0.3 * adjacency_bonus
        
        if score > best_score:
            best_score = score
            best_moves = [cell]
        elif score == best_score:
            best_moves.append(cell)
    
    # Return best move (random if tie)
    return random.choice(best_moves) if best_moves else empty_cells[0]
