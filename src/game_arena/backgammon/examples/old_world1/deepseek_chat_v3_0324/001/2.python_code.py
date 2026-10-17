
import numpy as np

def policy(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    dice = sorted(state['dice'], reverse=True)
    
    if not dice:
        return "H:P,P"
    
    # Generate all possible moves
    possible_moves = []
    
    # Handle bar moves first if any
    if my_bar > 0:
        for die in dice:
            target = 23 - die if die <= 23 else None
            if target is not None and opp_pts[target] < 2:
                possible_moves.append(('B', die))
        if not possible_moves:
            return "H:P,P"
    
    # Generate all possible non-bar moves
    else:
        used_dice = set()
        for i in range(24):
            if my_pts[i] == 0:
                continue
            for die in dice:
                if die in used_dice:
                    continue
                target = i - die if i - die >= 0 else None
                if target is not None and opp_pts[target] < 2:
                    possible_moves.append((f"A{i}", die))
                    used_dice.add(die)
    
    # Evaluate moves
    best_score = -float('inf')
    best_move = None
    
    for move in possible_moves:
        from_pos, die = move
        score = 0
        
        # Entering from bar is highest priority
        if from_pos == 'B':
            score += 1000
        
        # Hitting opponent blot
        target = 23 - die if from_pos == 'B' else int(from_pos[1:]) - die
        if opp_pts[target] == 1:
            score += 500
        
        # Making a point in home board (last 6 points)
        if from_pos != 'B' and 18 <= int(from_pos[1:]) <= 23:
            new_count = my_pts[int(from_pos[1:]) - die] + 1
            if new_count >= 2:
                score += 300
        
        # Moving toward home
        if from_pos != 'B':
            score += (23 - int(from_pos[1:])) * 10
        
        # Avoid leaving blots
        if from_pos != 'B' and my_pts[int(from_pos[1:])] == 1:
            score -= 200
        
        if score > best_score:
            best_score = score
            best_move = move
    
    # Handle case where only one die can be played
    if len(dice) == 2 and len(possible_moves) == 1:
        die = possible_moves[0][1]
        if die == dice[0]:
            return f"H:{possible_moves[0][0]},P"
        else:
            return f"L:{possible_moves[0][0]},P"
    
    # Generate final move string
    if not possible_moves:
        return "H:P,P"
    
    if len(dice) == 1:
        return f"H:{possible_moves[0][0]},P"
    
    # For two dice, we need to find two moves
    if len(possible_moves) >= 2:
        # Sort moves by score
        scored_moves = []
        for move in possible_moves:
            from_pos, die = move
            score = 0
            
            if from_pos == 'B':
                score += 1000
            target = 23 - die if from_pos == 'B' else int(from_pos[1:]) - die
            if opp_pts[target] == 1:
                score += 500
            if from_pos != 'B' and 18 <= int(from_pos[1:]) <= 23:
                new_count = my_pts[int(from_pos[1:]) - die] + 1
                if new_count >= 2:
                    score += 300
            if from_pos != 'B':
                score += (23 - int(from_pos[1:])) * 10
            if from_pos != 'B' and my_pts[int(from_pos[1:])] == 1:
                score -= 200
                
            scored_moves.append((score, from_pos, die))
        
        scored_moves.sort(reverse=True, key=lambda x: x[0])
        
        # Try to find two distinct moves
        for i in range(len(scored_moves)):
            for j in range(i+1, len(scored_moves)):
                if scored_moves[i][2] != scored_moves[j][2]:
                    if scored_moves[i][2] == dice[0]:
                        return f"H:{scored_moves[i][1]},{scored_moves[j][1]}"
                    else:
                        return f"L:{scored_moves[j][1]},{scored_moves[i][1]}"
        
        # If we can't find two distinct moves, play the best single move
        return f"H:{scored_moves[0][1]},P"
    
    return "H:P,P"
