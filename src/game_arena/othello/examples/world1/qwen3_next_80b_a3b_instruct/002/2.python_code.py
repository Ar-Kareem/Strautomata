
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Convert board to a combined representation for easier manipulation
    board = you + opponent
    empty_mask = (you == 0) & (opponent == 0)
    
    # Find all legal moves
    legal_moves = []
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    for r in range(8):
        for c in range(8):
            if empty_mask[r][c]:  # Empty cell
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    opponent_discs = 0
                    # Follow the direction until we hit a boundary or our own disc
                    while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc] == 1:
                        opponent_discs += 1
                        nr += dr
                        nc += dc
                    # If we found at least one opponent disc and then our disc
                    if opponent_discs > 0 and 0 <= nr < 8 and 0 <= nc < 8 and you[nr][nc] == 1:
                        legal_moves.append((r, c))
                        break  # Found at least one valid direction, no need to check others
                        
    # If no legal moves, return "pass"
    if len(legal_moves) == 0:
        return "pass"
    
    # Precompute scoring function for each legal move
    def evaluate_move(r, c):
        # Calculate immediate flip count
        flip_count = 0
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            temp_flips = 0
            while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc] == 1:
                temp_flips += 1
                nr += dr
                nc += dc
            if 0 <= nr < 8 and 0 <= nc < 8 and you[nr][nc] == 1:
                flip_count += temp_flips
        
        # Check if move is a corner
        corner_bonus = 0
        if (r, c) in [(0, 0), (0, 7), (7, 0), (7, 7)]:
            corner_bonus = 1000
        
        # Check if move is on edges but not adjacent to corners (safe edge)
        edge_bonus = 0
        if r == 0 or r == 7 or c == 0 or c == 7:
            # Avoid squares adjacent to corners if they are not corners themselves (risky)
            if (r, c) not in [(0,1), (1,0), (0,6), (1,7), (6,0), (7,1), (6,7), (7,6)]:
                edge_bonus = 200
        
        # Calculate potential mobility (next player moves) after making this move
        # Simulate the move and count opponent's future moves
        temp_you = you.copy()
        temp_opponent = opponent.copy()
        temp_you[r][c] = 1
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            discs_to_flip = []
            while 0 <= nr < 8 and 0 <= nc < 8 and temp_opponent[nr][nc] == 1:
                discs_to_flip.append((nr, nc))
                nr += dr
                nc += dc
            if 0 <= nr < 8 and 0 <= nc < 8 and temp_you[nr][nc] == 1:
                for fr, fc in discs_to_flip:
                    temp_you[fr][fc] = 1
                    temp_opponent[fr][fc] = 0
        
        # Count opponent's legal moves after our move
        opponent_mobility = 0
        for or_ in range(8):
            for oc in range(8):
                if (temp_you[or_][oc] == 0) and (temp_opponent[or_][oc] == 0):
                    for ddr, ddc in directions:
                        nrr, ncc = or_ + ddr, oc + ddc
                        opp_discs = 0
                        while 0 <= nrr < 8 and 0 <= ncc < 8 and temp_you[nrr][ncc] == 1:
                            opp_discs += 1
                            nrr += ddr
                            ncc += ddc
                        if opp_discs > 0 and 0 <= nrr < 8 and 0 <= ncc < 8 and temp_opponent[nrr][ncc] == 1:
                            opponent_mobility += 1
                            break
        
        # Stability consideration: avoid disc placements that are easily flippable
        # (this is heuristic since full stability requires lookahead)
        instability_penalty = 0
        if (r, c) in [(0,1), (1,0), (0,6), (1,7), (6,0), (7,1), (6,7), (7,6)]:
            instability_penalty = -150
        # Also penalize moves that expose corners
        corner_exposure = 0
        if (r, c) in [(0,1), (0,6), (1,0), (1,7), (6,0), (6,7), (7,1), (7,6)]:
            # Check if the adjacent corner is empty
            adj_corners = []
            if r == 0 and c == 1: adj_corners = [(0,0)]
            elif r == 0 and c == 6: adj_corners = [(0,7)]
            elif r == 1 and c == 0: adj_corners = [(0,0)]
            elif r == 1 and c == 7: adj_corners = [(0,7)]
            elif r == 6 and c == 0: adj_corners = [(7,0)]
            elif r == 6 and c == 7: adj_corners = [(7,7)]
            elif r == 7 and c == 1: adj_corners = [(7,0)]
            elif r == 7 and c == 6: adj_corners = [(7,7)]
            
            for cr, cc in adj_corners:
                if you[cr][cc] == 0 and opponent[cr][cc] == 0:  # corner is empty
                    corner_exposure = -200
        
        # Combine all factors
        score = flip_count * 10 + corner_bonus + edge_bonus - opponent_mobility * 5 + instability_penalty + corner_exposure
        
        return score
    
    # Evaluate all legal moves
    move_scores = [(r, c, evaluate_move(r, c)) for r, c in legal_moves]
    
    # Sort by score in descending order
    move_scores.sort(key=lambda x: x[2], reverse=True)
    
    # Best move
    best_move = move_scores[0]
    
    # Format move to algebraic notation
    col_map = "abcdefgh"
    return f"{col_map[best_move[1]]}{best_move[0] + 1}"
