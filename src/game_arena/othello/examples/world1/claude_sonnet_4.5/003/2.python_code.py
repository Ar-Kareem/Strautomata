
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    legal_moves = get_legal_moves(you, opponent)
    
    if not legal_moves:
        return "pass"
    
    # Use iterative deepening with time consideration
    total_pieces = np.sum(you) + np.sum(opponent)
    
    # Adjust depth based on game phase
    if total_pieces < 20:
        depth = 4
    elif total_pieces < 50:
        depth = 5
    else:
        depth = 6
    
    best_move = None
    best_score = -float('inf')
    
    for move in legal_moves:
        new_you, new_opp = apply_move(you, opponent, move)
        score = -minimax(new_opp, new_you, depth - 1, -float('inf'), float('inf'), False)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return move_to_string(best_move)

def minimax(you, opponent, depth, alpha, beta, maximizing):
    if depth == 0:
        return evaluate_position(you, opponent)
    
    legal_moves = get_legal_moves(you, opponent)
    
    if not legal_moves:
        opp_moves = get_legal_moves(opponent, you)
        if not opp_moves:
            # Game over
            diff = np.sum(you) - np.sum(opponent)
            return diff * 1000
        else:
            # Pass
            return -minimax(opponent, you, depth - 1, -beta, -alpha, not maximizing)
    
    if maximizing:
        max_eval = -float('inf')
        for move in legal_moves:
            new_you, new_opp = apply_move(you, opponent, move)
            eval_score = -minimax(new_opp, new_you, depth - 1, -beta, -alpha, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            new_you, new_opp = apply_move(you, opponent, move)
            eval_score = -minimax(new_opp, new_you, depth - 1, -beta, -alpha, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def evaluate_position(you, opponent):
    total_pieces = np.sum(you) + np.sum(opponent)
    
    # Positional weights
    weights = np.array([
        [100, -25,  10,   5,   5,  10, -25, 100],
        [-25, -25,   2,   2,   2,   2, -25, -25],
        [ 10,   2,   5,   3,   3,   5,   2,  10],
        [  5,   2,   3,   1,   1,   3,   2,   5],
        [  5,   2,   3,   1,   1,   3,   2,   5],
        [ 10,   2,   5,   3,   3,   5,   2,  10],
        [-25, -25,   2,   2,   2,   2, -25, -25],
        [100, -25,  10,   5,   5,  10, -25, 100]
    ])
    
    # Adjust corner-adjacent penalties if corner is taken
    corners = [(0,0), (0,7), (7,0), (7,7)]
    for r, c in corners:
        if you[r, c] == 1 or opponent[r, c] == 1:
            # Corner is taken, adjacent squares are now safer
            if r == 0 and c == 0:
                weights[0,1] = 5; weights[1,0] = 5; weights[1,1] = 5
            elif r == 0 and c == 7:
                weights[0,6] = 5; weights[1,7] = 5; weights[1,6] = 5
            elif r == 7 and c == 0:
                weights[7,1] = 5; weights[6,0] = 5; weights[6,1] = 5
            elif r == 7 and c == 7:
                weights[7,6] = 5; weights[6,7] = 5; weights[6,6] = 5
    
    position_score = np.sum(you * weights) - np.sum(opponent * weights)
    
    # Mobility
    my_mobility = len(get_legal_moves(you, opponent))
    opp_mobility = len(get_legal_moves(opponent, you))
    mobility_score = (my_mobility - opp_mobility) * 3
    
    # Disc count (more important in endgame)
    disc_diff = np.sum(you) - np.sum(opponent)
    if total_pieces > 50:
        disc_weight = 10
    else:
        disc_weight = 2
    
    return position_score + mobility_score + disc_diff * disc_weight

def get_legal_moves(you, opponent):
    moves = []
    for r in range(8):
        for c in range(8):
            if you[r, c] == 0 and opponent[r, c] == 0:
                if is_legal_move(you, opponent, r, c):
                    moves.append((r, c))
    return moves

def is_legal_move(you, opponent, r, c):
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    for dr, dc in directions:
        if check_direction(you, opponent, r, c, dr, dc):
            return True
    return False

def check_direction(you, opponent, r, c, dr, dc):
    nr, nc = r + dr, c + dc
    found_opponent = False
    
    while 0 <= nr < 8 and 0 <= nc < 8:
        if opponent[nr, nc] == 1:
            found_opponent = True
        elif you[nr, nc] == 1:
            return found_opponent
        else:
            return False
        nr += dr
        nc += dc
    return False

def apply_move(you, opponent, move):
    new_you = you.copy()
    new_opp = opponent.copy()
    r, c = move
    new_you[r, c] = 1
    
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    for dr, dc in directions:
        if check_direction(you, opponent, r, c, dr, dc):
            nr, nc = r + dr, c + dc
            while opponent[nr, nc] == 1:
                new_opp[nr, nc] = 0
                new_you[nr, nc] = 1
                nr += dr
                nc += dc
    
    return new_you, new_opp

def move_to_string(move):
    r, c = move
    return chr(ord('a') + c) + str(r + 1)
