
import numpy as np

def policy(state):
    # Get all legal moves
    moves = get_all_legal_moves(state)
    if not moves:
        return "H:P,P"
    
    # Score each move and pick the best one
    best_move = None
    best_score = -float('inf')
    
    for move in moves:
        score = evaluate_move(state, move)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def get_all_legal_moves(state):
    moves = []
    dice = sorted(state['dice'], reverse=True)
    if not dice:
        return ["H:P,P"]
    
    # Handle bar moves first
    if state['my_bar'] > 0:
        return generate_bar_moves(state)
    
    # Generate all possible moves
    if len(dice) == 1:
        # Single die
        moves.extend(generate_single_moves(state, dice[0]))
    else:
        # Two dice - consider both orders
        moves.extend(generate_double_moves(state, dice[0], dice[1]))
        if dice[0] != dice[1]:
            moves.extend(generate_double_moves(state, dice[1], dice[0]))
    
    # Add pass move if no other moves
    if not moves:
        return ["H:P,P"]
    return moves

def generate_bar_moves(state):
    moves = []
    dice = sorted(state['dice'], reverse=True)
    home_board = list(range(18, 24))  # A18-A23 is home board
    
    # Try to enter from bar
    for die in dice:
        target = 23 - die  # Convert to opponent's perspective
        if state['opp_pts'][target] < 2:
            # Can enter here
            moves.append(f"H:B,A{target}")
            break
    
    # If can't enter, return pass
    if not moves:
        return ["H:P,P"]
    return moves

def generate_single_moves(state, die):
    moves = []
    # Check for bearing off first
    if can_bear_off(state):
        for i in range(23, 17, -1):
            if state['my_pts'][i] > 0:
                if i + 1 == 24 or (i + die >= 24):
                    moves.append(f"H:A{i},P")
                    break
        return moves if moves else ["H:P,P"]
    
    # Normal moves
    for i in range(24):
        if state['my_pts'][i] > 0:
            target = i - die
            if target >= 0:
                if state['opp_pts'][target] < 2:
                    moves.append(f"H:A{i},P")
    
    return moves if moves else ["H:P,P"]

def generate_double_moves(state, die1, die2):
    moves = []
    # Check bearing off first
    if can_bear_off(state):
        # Try to bear off two checkers
        for i in range(23, 17, -1):
            if state['my_pts'][i] > 0:
                if i + 1 == 24 or (i + die1 >= 24):
                    for j in range(23, 17, -1):
                        if state['my_pts'][j] > 0 and (j != i or state['my_pts'][i] > 1):
                            if j + 1 == 24 or (j + die2 >= 24):
                                moves.append(f"H:A{i},A{j}")
                    break
        return moves if moves else generate_single_moves(state, die1)
    
    # Normal moves
    for i in range(24):
        if state['my_pts'][i] > 0:
            target1 = i - die1
            if target1 >= 0 and state['opp_pts'][target1] < 2:
                for j in range(24):
                    if state['my_pts'][j] > 0 and (j != i or state['my_pts'][i] > 1):
                        target2 = j - die2
                        if target2 >= 0 and state['opp_pts'][target2] < 2:
                            moves.append(f"H:A{i},A{j}")
    
    return moves if moves else ["H:P,P"]

def can_bear_off(state):
    # Check if all checkers are in home board
    home_board = list(range(18, 24))
    total = sum(state['my_pts'][i] for i in range(18))
    return total == 0 and state['my_bar'] == 0

def evaluate_move(state, move):
    score = 0
    parts = move.split(':')
    order = parts[0]
    from1, from2 = parts[1].split(',')
    
    # Evaluate first move
    if from1 != 'P':
        src = int(from1[1:]) if from1.startswith('A') else None
        die = state['dice'][0] if order == 'H' else state['dice'][-1]
        
        if from1 == 'B':
            # Bar move - always good to get off bar
            score += 50
        else:
            target = src - die
            # Prefer hitting opponent blots
            if target >= 0 and state['opp_pts'][target] == 1:
                score += 30
            # Prefer moving to make points
            if target >= 0 and state['my_pts'][target] == 1 and state['opp_pts'][target] == 0:
                score += 20
            # Prefer moving toward home
            if src >= 18:
                score += 5
            else:
                score += (18 - src) * 2
    
    # Evaluate second move if exists
    if from2 != 'P':
        src = int(from2[1:]) if from2.startswith('A') else None
        die = state['dice'][1] if order == 'H' else state['dice'][0]
        
        if from2 == 'B':
            score += 50
        else:
            target = src - die
            if target >= 0 and state['opp_pts'][target] == 1:
                score += 30
            if target >= 0 and state['my_pts'][target] == 1 and state['opp_pts'][target] == 0:
                score += 20
            if src >= 18:
                score += 5
            else:
                score += (18 - src) * 2
    
    # Prefer bearing off
    if can_bear_off(state):
        if from1.startswith('A') and int(from1[1:]) >= 18:
            score += 40
        if from2.startswith('A') and int(from2[1:]) >= 18:
            score += 40
    
    return score
