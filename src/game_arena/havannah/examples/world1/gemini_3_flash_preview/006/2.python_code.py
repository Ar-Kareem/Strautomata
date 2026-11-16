
import numpy as np

def get_neighbors(r, c, board_size=15):
    """Hexagonal neighbors for Havannah given the 2D grid representation."""
    # Based on: (4,1) touches (5,1), (3,1), (3,0), (4,0), (4,2), (3,2)
    # Pattern: Same col (+-1), Left col (0, -1), Right col (0, +1)
    # The specific instructions imply:
    # (r+1, c), (r-1, c)
    # (r, c-1), (r-1, c-1)
    # (r, c+1), (r+1, c+1) (to match the logic of the example)
    candidates = [
        (r + 1, c), (r - 1, c),
        (r, c - 1), (r - 1, c - 1),
        (r, c + 1), (r + 1, c + 1)
    ]
    return [(nr, nc) for nr, nc in candidates if 0 <= nr < board_size and 0 <= nc < board_size]

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    board_size = 15
    my_set = set(me)
    opp_set = set(opp)
    occupied = my_set.union(opp_set)
    
    # 1. Identify all legal moves
    legal_moves = []
    for r in range(board_size):
        for c in range(board_size):
            if valid_mask[r][c] and (r, c) not in occupied:
                legal_moves.append((r, c))
    
    if not legal_moves:
        return (0, 0) # Should not happen

    # 2. Distance from center (for general positioning)
    center = board_size // 2
    
    def score_move(move):
        r, c = move
        score = 0
        
        # Priority 1: Adjacency to own pieces (building chains)
        neighbors = get_neighbors(r, c)
        my_neighs = 0
        opp_neighs = 0
        for nr, nc in neighbors:
            if (nr, nc) in my_set:
                my_neighs += 1
            if (nr, nc) in opp_set:
                opp_neighs += 1
        
        # Encourage bridging existing stones
        if my_neighs >= 2:
            score += 50
        elif my_neighs == 1:
            score += 20
            
        # Defense: Block opponent chains
        if opp_neighs >= 2:
            score += 40
        elif opp_neighs == 1:
            score += 10

        # Priority 2: Corner/Edge proximity (Havannah goals)
        # Corners: (0,0), (0,7), (7,0), (7,14), (14,7), (14,14) roughly
        # For a 15x15 board mask, edges are wherever total neighbors < 6
        if len(neighbors) < 6:
            score += 5 
            
        # Priority 3: Centrality
        dist_center = abs(r - center) + abs(c - center)
        score -= dist_center * 2
        
        return score

    # Sort moves by score
    best_move = max(legal_moves, key=score_move)
    
    # Safety Check: If it's the very first move, take the center
    if not me and valid_mask[center][center] and (center, center) not in occupied:
        return (center, center)

    return best_move
