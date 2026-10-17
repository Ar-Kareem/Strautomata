
import numpy as np

def policy(board):
    # Locate the player's and opponent's amazons
    my_amazons = list(zip(*np.where(board == 1)))
    opponent_amazons = list(zip(*np.where(board == 2)))
    directions = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr != 0 or dc != 0]
    all_moves = []
    
    # Generate all possible moves for each amazon
    for (from_r, from_c) in my_amazons:
        moves = []
        for dr, dc in directions:
            step = 1
            while True:
                to_r, to_c = from_r + dr * step, from_c + dc * step
                if not (0 <= to_r < 6 and 0 <= to_c < 6) or board[to_r, to_c] != 0:
                    break
                moves.append((to_r, to_c))
                step += 1
        # Generate arrow shots for each valid move
        for (to_r, to_c) in moves:
            arrows = []
            for dr, dc in directions:
                step = 1
                while True:
                    arrow_r, arrow_c = to_r + dr * step, to_c + dc * step
                    if not (0 <= arrow_r < 6 and 0 <= arrow_c):
                        break
                    # Arrow can pass through the vacated 'from' square
                    if (arrow_r, arrow_c) == (from_r, from_c):
                        arrows.append((arrow_r, arrow_c))
                        step += 1
                    elif board[arrow_r, arrow_c] != 0:
                        break
                    else:
                        arrows.append((arrow_r, arrow_c))
                        step += 1
            for (arrow_r, arrow_c) in arrows:
                all_moves.append((from_r, from_c, to_r, to_c, arrow_r, arrow_c))
    
    # Fallback if no moves (should not occur per problem constraints)
    if not all_moves:
        return "0,0:0,0:0,0"
    
    # Score moves based on centrality and arrow proximity to opponents
    center = (2.5, 2.5)
    best_score = -float('inf')
    best_move = None
    for move in all_moves:
        fr, fc, tr, tc, ar, ac = move
        # Centrality of the move's destination
        to_score = -((tr - center[0])**2 + (tc - center[1])**2)
        # Arrow proximity to nearest opponent amazon
        arrow_score = 0
        if opponent_amazons:
            min_dist = min((ar - opp_r)**2 + (ac - opp_c)**2 for opp_r, opp_c in opponent_amazons)
            arrow_score = -min_dist
        total_score = to_score + 0.5 * arrow_score
        if total_score > best_score:
            best_score = total_score
            best_move = move
    
    # Format the selected move
    fr, fc, tr, tc, ar, ac = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
