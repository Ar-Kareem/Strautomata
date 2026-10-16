
import numpy as np

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    my_bar = state['my_bar']
    dice = sorted(state['dice'])
    
    # Handle pass if no dice or no legal moves possible conceptually, but always return something legal
    if not dice:
        return "H:P,P"
    
    len_dice = len(dice)
    order = 'H'  # Default to higher first for doubles or preference
    if len_dice == 2 and dice[0] < dice[1]:
        order = 'H'
    elif len_dice == 1:
        order = 'H'
    else:
        order = 'L'  # For ties or other cases
    
    # Candidate starting points: prioritize bar if present, else scan from farthest (23) down
    move1_from = None
    move2_from = None
    
    if my_bar > 0:
        # Must move from bar first
        move1_from = 'B'
        if len_dice > 1:
            # Find another move from farthest available point
            for p in range(23, -1, -1):
                if my_pts[p] > 0:
                    move2_from = f"A{p}"
                    break
    else:
        # Find up to two moves from farthest points
        moves = []
        for p in range(23, -1, -1):
            if my_pts[p] > 0:
                moves.append(f"A{p}")
                if len(moves) == 2:
                    break
        if moves:
            move1_from = moves[0]
            if len(moves) > 1 and len_dice > 1:
                move2_from = moves[1]
    
    # Default to P if not set
    from1 = move1_from or 'P'
    from2 = (move2_from or 'P') if len_dice > 1 else 'P'
    
    return f"{order}:{from1},{from2}"
