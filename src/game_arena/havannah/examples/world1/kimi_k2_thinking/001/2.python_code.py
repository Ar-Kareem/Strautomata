
import numpy as np

def policy(me, opp, valid_mask):
    """
    Havannah playing policy focusing on:
    1. Central influence
    2. Connection building
    3. Blocking opponent
    4. Edge control for forks/bridges
    """
    board_size = 15
    me_set = set(me)
    opp_set = set(opp)
    
    # Opening: play center
    if not me:
        return (7, 7)
    
    # Find all valid moves
    valid_moves = []
    for r in range(board_size):
        for c in range(board_size):
            if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set:
                valid_moves.append((r, c))
    
    if not valid_moves:
        return (7, 7)
    
    # Precompute neighbor offsets for hex grid
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]
    
    # Score each move
    best_move = None
    best_score = float('-inf')
    
    for r, c in valid_moves:
        score = 0.0
        
        # 1. Center distance (hexagonal)
        dr = abs(r - 7)
        dc = abs(c - 7)
        hex_dist = max(dr, dc, abs(dr - dc))
        score += 1000.0 / (hex_dist + 1.0)
        
        # 2. Adjacent stones
        our_adj = 0
        opp_adj = 0
        for dr, dc in offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < board_size and 0 <= nc < board_size:
                if (nr, nc) in me_set:
                    our_adj += 1
                elif (nr, nc) in opp_set:
                    opp_adj += 1
        
        score += our_adj * 250
        score += opp_adj * 200
        
        # Bonus for connecting multiple groups
        if our_adj >= 2:
            score += 500
        
        # Bonus for blocking strong opponent
        if opp_adj >= 3:
            score += 400
        
        # 3. Second-order connections
        our_2nd = 0
        opp_2nd = 0
        for dr, dc in offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < board_size and 0 <= nc < board_size and (nr, nc) in me_set:
                for dr2, dc2 in offsets:
                    nnr, nnc = nr + dr2, nc + dc2
                    if (0 <= nnr < board_size and 0 <= nnc < board_size and 
                        (nnr, nnc) in me_set and (nnr, nnc) != (r, c)):
                        our_2nd += 1
        
        for dr, dc in offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < board_size and 0 <= nc < board_size and (nr, nc) in opp_set:
                for dr2, dc2 in offsets:
                    nnr, nnc = nr + dr2, nc + dc2
                    if (0 <= nnr < board_size and 0 <= nnc < board_size and 
                        (nnr, nnc) in opp_set and (nnr, nnc) != (r, c)):
                        opp_2nd += 1
        
        score += our_2nd * 40
        score += opp_2nd * 30
        
        # 4. Edge and corner bonuses
        edges = sum([r == 0, r == 14, c == 0, c == 14])
        score += edges * 180
        
        # Special hex corners
        if (r, c) in [(0, 7), (7, 0), (7, 14), (14, 7)]:
            score += 350
        
        # 5. Fork potential (multiple edge threats)
        edge_types = set()
        for dr, dc in offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < board_size and 0 <= nc < board_size and (nr, nc) in me_set:
                if nr == 0: edge_types.add('t')
                elif nr == 14: edge_types.add('b')
                if nc == 0: edge_types.add('l')
                elif nc == 14: edge_types.add('r')
        
        if len(edge_types) >= 2:
            score += 600
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move
