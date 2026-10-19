
from math import inf

def policy(me, opp, color):
    state = (set(me), set(opp), 'me')
    depth = 3
    _, move = best_move(state, depth, color)
    return move

def generate_moves(state, my_color):
    my_pieces, opp_pieces, to_move = state
    if to_move == 'me':
        pieces = my_pieces
        current_color = my_color
    else:
        pieces = opp_pieces
        current_color = 'w' if my_color == 'b' else 'b'
    
    moves = []
    for piece in pieces:
        r, c = piece
        if current_color == 'w':
            r_new = r + 1
            if r_new < 8:
                if (r_new, c) not in my_pieces and (r_new, c) not in opp_pieces:
                    moves.append(((r, c), (r_new, c)))
                if c - 1 >= 0 and (r_new, c - 1) in opp_pieces:
                    moves.append(((r, c), (r_new, c - 1)))
                if c + 1 < 8 and (r_new, c + 1) in opp_pieces:
                    moves.append(((r, c), (r_new, c + 1)))
        else:
            r_new = r - 1
            if r_new >= 0:
                if (r_new, c) not in my_pieces and (r_new, c) not in opp_pieces:
                    moves.append(((r, c), (r_new, c)))
                if c - 1 >= 0 and (r_new, c - 1) in opp_pieces:
                    moves.append(((r, c), (r_new, c - 1)))
                if c + 1 < 8 and (r_new, c + 1) in opp_pieces:
                    moves.append(((r, c), (r_new, c + 1)))
    return moves

def apply_move(state, move, my_color):
    from_pos, to_pos = move
    my_pieces, opp_pieces, to_move = state
    if to_move == 'me':
        if from_pos not in my_pieces:
            return state
        my_pieces = set(my_pieces)
        my_pieces.remove(from_pos)
        if to_pos in opp_pieces:
            opp_pieces = set(opp_pieces)
            opp_pieces.remove(to_pos)
        my_pieces.add(to_pos)
        new_to_move = 'opp'
    else:
        if from_pos not in opp_pieces:
            return state
        opp_pieces = set(opp_pieces)
        opp_pieces.remove(from_pos)
        if to_pos in my_pieces:
            my_pieces = set(my_pieces)
            my_pieces.remove(to_pos)
        opp_pieces.add(to_pos)
        new_to_move = 'me'
    return (my_pieces, opp_pieces, new_to_move)

def evaluate_state(state, my_color):
    my_pieces, opp_pieces, to_move = state
    if len(my_pieces) == 0:
        return -1000
    if len(opp_pieces) == 0:
        return 1000
    
    if my_color == 'w':
        if any(p[0] == 7 for p in my_pieces):
            return 1000
        if any(p[0] == 0 for p in opp_pieces):
            return -1000
    else:
        if any(p[0] == 0 for p in my_pieces):
            return 1000
        if any(p[0] == 7 for p in opp_pieces):
            return -1000
    
    moves = generate_moves(state, my_color)
    if len(moves) == 0:
        if to_move == 'me':
            return -1000
        else:
            return 1000
    
    if my_color == 'w':
        my_adv = sum(p[0] for p in my_pieces)
        opp_adv = sum(7 - p[0] for p in opp_pieces)
    else:
        my_adv = sum(7 - p[0] for p in my_pieces)
        opp_adv = sum(p[0] for p in opp_pieces)
    
    return my_adv - opp_adv

def alpha_beta(state, depth, alpha, beta, max_player, my_color):
    value = evaluate_state(state, my_color)
    if depth == 0 or value in [1000, -1000]:
        return value, None
    
    moves = generate_moves(state, my_color)
    if len(moves) == 0:
        if max_player:
            return -1000, None
        else:
            return 1000, None
    
    if max_player:
        value = -inf
        best_move_val = None
        for move in moves:
            new_state = apply_move(state, move, my_color)
            v, _ = alpha_beta(new_state, depth-1, alpha, beta, False, my_color)
            if v > value:
                value = v
                best_move_val = move
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value, best_move_val
    else:
        value = inf
        best_move_val = None
        for move in moves:
            new_state = apply_move(state, move, my_color)
            v, _ = alpha_beta(new_state, depth-1, alpha, beta, True, my_color)
            if v < value:
                value = v
                best_move_val = move
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value, best_move_val

def best_move(state, depth, my_color):
    return alpha_beta(state, depth, -inf, inf, True, my_color)
