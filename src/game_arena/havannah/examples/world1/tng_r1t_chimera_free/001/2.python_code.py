
import numpy as np

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    # Predefined corner positions (approximation)
    corners = [(0,7), (7,0), (14,0), (14,7), (7,14), (0,14)]
    
    def get_neighbors(r, c):
        """Returns valid hexagonal neighbors for a given cell"""
        neighbors = [
            (r-1, c), (r+1, c),       # Same column
            (r, c-1), (r-1, c-1),     # Left column
            (r, c+1), (r-1, c+1),     # Right column
        ]
        return [(nr, nc) for nr, nc in neighbors if 0 <= nr < 15 and 0 <= nc < 15]
    
    # Generate all valid moves
    valid_moves = []
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c] and (r,c) not in me and (r,c) not in opp:
                valid_moves.append((r,c))
    
    if not valid_moves:
        return (0,0)  # Should never occur
    
    # Precompute sets for faster lookup
    me_set = set(me)
    opp_set = set(opp)
    max_score = -np.inf
    best_move = valid_moves[0]
    
    for r, c in valid_moves:
        score = 0
        
        # Connection strength
        connections = sum(1 for neighbor in get_neighbors(r,c) if neighbor in me_set)
        score += 10 * connections
        
        # Proximity to corners
        corner_bonus = sum(5 - max(abs(r-cr), abs(c-cc)) for cr, cc in corners 
                          if max(abs(r-cr), abs(c-cc)) <= 2)
        score += corner_bonus
        
        # Edge proximity
        edge_dist = min(r, 14-r, c, 14-c)
        if edge_dist <= 2:
            score += 3 - edge_dist
        
        # Block opponent's potential
        opp_block = sum(1 for neighbor in get_neighbors(r,c) if neighbor in opp_set)
        score += 5 * opp_block
        
        # Central control
        center_dist = abs(r-7) + abs(c-7)
        score += (14 - center_dist)/2
        
        # Update best move
        if score > max_score:
            max_score = score
            best_move = (r, c)
    
    return best_move
