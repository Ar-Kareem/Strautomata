
import numpy as np

def apply_move(state, move, player):
    horizontal, vertical, capture = state
    row, col, dir = move
    new_h = horizontal.copy()
    new_v = vertical.copy()
    new_c = capture.copy()
    boxes_completed = 0
    
    if dir == 'H':
        if new_h[row, col] != 0:
            return None
        new_h[row, col] = player
        
        if row < 4 and col < 4:
            if new_h[row+1, col] != 0 and new_v[row, col] != 0 and new_v[row, col+1] != 0:
                if new_c[row, col] == 0:
                    new_c[row, col] = player
                    boxes_completed += 1
        
        if row-1 >= 0 and row-1 < 4 and col < 4:
            if new_h[row-1, col] != 0 and new_v[row-1, col] != 0 and new_v[row-1, col+1] != 0:
                if new_c[row-1, col] == 0:
                    new_c[row-1, col] = player
                    boxes_completed += 1
                    
    elif dir == 'V':
        if new_v[row, col] != 0:
            return None
        new_v[row, col] = player
        
        if row < 4 and col < 4:
            if new_h[row, col] != 0 and new_h[row+1, col] != 0 and new_v[row, col+1] != 0:
                if new_c[row, col] == 0:
                    new_c[row, col] = player
                    boxes_completed += 1
                    
        if row < 4 and col-1 >= 0 and col-1 < 4:
            if new_h[row, col-1] != 0 and new_h[row+1, col-1] != 0 and new_v[row, col-1] != 0:
                if new_c[row, col-1] == 0:
                    new_c[row, col-1] = player
                    boxes_completed += 1
                    
    return (new_h, new_v, new_c), (boxes_completed > 0)

def generate_legal_moves(state):
    horizontal, vertical, _ = state
    legal_moves = []
    for row in range(5):
        for col in range(4):
            if horizontal[row, col] == 0:
                legal_moves.append((row, col, 'H'))
    for row in range(4):
        for col in range(5):
            if vertical[row, col] == 0:
                legal_moves.append((row, col, 'V'))
    return legal_moves

def policy(horizontal, vertical, capture):
    state = (horizontal, vertical, capture)
    legal_moves = generate_legal_moves(state)
    
    if not legal_moves:
        return "0,0,H"
    
    best_move = None
    best_gain = -1
    for move in legal_moves:
        new_state, _ = apply_move(state, move, 1)
        if new_state is None:
            continue
        new_h, new_v, new_c = new_state
        gain_us = np.sum((new_c == 1) & (capture == 0))
        if gain_us > best_gain:
            best_gain = gain_us
            best_move = move
            
    if best_gain >= 1:
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"
    
    best_move2 = None
    best_score = -10000
    for move in legal_moves:
        new_state, _ = apply_move(state, move, 1)
        if new_state is None:
            continue
        new_h, new_v, new_c = new_state
        gain_us = np.sum((new_c == 1) & (capture == 0))
        if gain_us > 0:
            continue
        opp_moves = generate_legal_moves((new_h, new_v, new_c))
        min_gain = 10000
        for opp_move in opp_moves:
            state2, _ = apply_move((new_h, new_v, new_c), opp_move, -1)
            if state2 is None:
                continue
            _, _, state2_c = state2
            gain_opp = np.sum((state2_c == -1) & (new_c == 0))
            if gain_opp < min_gain:
                min_gain = gain_opp
        score = -min_gain
        if score > best_score:
            best_score = score
            best_move2 = move
            
    if best_move2 is not None:
        return f"{best_move2[0]},{best_move2[1]},{best_move2[2]}"
    else:
        return f"{legal_moves[0][0]},{legal_moves[0][1]},{legal_moves[0][2]}"
