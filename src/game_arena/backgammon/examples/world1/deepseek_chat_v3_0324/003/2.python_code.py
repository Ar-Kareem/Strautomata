
import numpy as np

def policy(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    dice = state['dice']
    
    if not dice:
        return "H:P,P"
    
    # Handle cases where we have checkers on the bar
    if my_bar > 0:
        return handle_bar(state)
    
    # Check if we're in bear-off phase
    if can_bear_off(my_pts):
        return handle_bear_off(state)
    
    # Normal move phase
    return handle_normal_move(state)

def handle_bar(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    dice = sorted(state['dice'], reverse=True)
    possible_entries = []
    
    for die in dice:
        target = 23 - die  # Convert to our point numbering
        if target < 0 or target >= 24:
            continue
        if opp_pts[target] <= 1:  # Can enter here
            possible_entries.append((die, target))
    
    if not possible_entries:
        return "H:P,P"
    
    # Prefer higher die first
    possible_entries.sort(reverse=True)
    die1, target1 = possible_entries[0]
    
    if len(dice) == 1:
        return f"H:B,A{target1}"
    
    # Try to use both dice
    remaining_die = dice[1] if dice[0] == die1 else dice[0]
    second_move = find_legal_move(state, remaining_die, exclude_bar=True)
    
    if second_move:
        if die1 > remaining_die:
            return f"H:B,A{second_move}"
        else:
            return f"L:B,A{second_move}"
    else:
        return f"H:B,A{target1}"

def handle_bear_off(state):
    my_pts = state['my_pts']
    dice = sorted(state['dice'], reverse=True)
    moves = []
    
    for die in dice:
        # Find highest point with checkers that can bear off
        for point in range(min(23, die-1), -1, -1):
            if my_pts[point] > 0:
                if point + 1 == die or (point < die and is_highest_checker(my_pts, point)):
                    moves.append((die, point))
                    break
    
    if not moves:
        return "H:P,P"
    
    if len(moves) == 1:
        die, point = moves[0]
        return f"H:A{point},P"
    
    die1, point1 = moves[0]
    die2, point2 = moves[1]
    
    if die1 > die2:
        return f"H:A{point1},A{point2}"
    else:
        return f"L:A{point2},A{point1}"

def handle_normal_move(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    dice = sorted(state['dice'], reverse=True)
    possible_moves = []
    
    # Generate all possible single moves
    for die in dice:
        for src in range(23, -1, -1):
            if my_pts[src] > 0:
                dest = src - die
                if dest >= 0:
                    if opp_pts[dest] <= 1:  # Legal move
                        safety = 0 if opp_pts[dest] == 1 else 1
                        progress = (23 - src) + die  # How much closer to bear off
                        possible_moves.append((die, src, dest, safety, progress))
    
    if not possible_moves:
        return "H:P,P"
    
    # Try to find best combination of moves
    if len(dice) == 2:
        best_score = -1
        best_move = None
        
        # Try all combinations of the two dice
        for move1 in [m for m in possible_moves if m[0] == dice[0]]:
            for move2 in [m for m in possible_moves if m[0] == dice[1] and m[1] != move1[1]]:
                score = move1[3] + move2[3] + move1[4] + move2[4]
                if score > best_score:
                    best_score = score
                    if dice[0] > dice[1]:
                        best_move = f"H:A{move1[1]},A{move2[1]}"
                    else:
                        best_move = f"L:A{move2[1]},A{move1[1]}"
        
        if best_move:
            return best_move
    
    # Fall back to best single move
    possible_moves.sort(key=lambda x: (-x[3], -x[4]))
    die, src, dest, safety, progress = possible_moves[0]
    return f"H:A{src},P"

def can_bear_off(my_pts):
    total_checkers = sum(my_pts[:6]) + sum(my_pts[6:])
    return sum(my_pts[6:]) == 0

def is_highest_checker(my_pts, point):
    for higher_point in range(point + 1, 6):
        if my_pts[higher_point] > 0:
            return False
    return True

def find_legal_move(state, die, exclude_bar=False):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    
    for src in range(23, -1, -1):
        if my_pts[src] > 0 and (not exclude_bar or src != 'B'):
            dest = src - die
            if dest >= 0 and opp_pts[dest] <= 1:
                return src
    return None
