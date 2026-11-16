
import random

def policy(me, opp, color):
    """
    Calculates the next move for the Breakthrough game using Minimax with Alpha-Beta pruning.
    """
    # Define directions and goals based on color
    if color == 'w':
        my_dr = 1
        my_goal = 7
        opp_dr = -1
        opp_goal = 0
    else:
        my_dr = -1
        my_goal = 0
        opp_dr = 1
        opp_goal = 7

    # Convert lists to sets for O(1) lookups
    me_set = set(me)
    opp_set = set(opp)

    # Generate initial moves for the root node
    # Format: (is_win, is_capture, from_pos, to_pos)
    initial_moves = []
    for r, c in me_set:
        nr = r + my_dr
        if 0 <= nr <= 7:
            # Forward move
            target = (nr, c)
            if target not in me_set and target not in opp_set:
                is_win = (nr == my_goal)
                initial_moves.append((is_win, False, (r, c), target))
            
            # Diagonal moves
            for dc in [-1, 1]:
                nc = c + dc
                if 0 <= nc <= 7:
                    target = (nr, nc)
                    is_capture = target in opp_set
                    is_empty = target not in me_set and not is_capture
                    
                    if is_capture or is_empty:
                        is_win = (nr == my_goal)
                        initial_moves.append((is_win, is_capture, (r, c), target))

    # Sort moves: Wins first, then captures, then others.
    # This improves alpha-beta pruning efficiency.
    initial_moves.sort(key=lambda x: (x[0], x[1]), reverse=True)

    # If we can win immediately, do it.
    for move in initial_moves:
        if move[0]:
            return (move[2], move[3])

    # If no moves available (should not happen in a normal game state), return None or handle error
    if not initial_moves:
        return None 

    best_score = -2000000
    best_move = (initial_moves[0][2], initial_moves[0][3])
    
    depth = 4

    # Iterate through moves to start the search
    for is_win, is_capture, fr, to in initial_moves:
        # Apply move to create new state
        new_me = set(me_set)
        new_opp = set(opp_set)
        
        new_me.remove(fr)
        new_me.add(to)
        if is_capture:
            new_opp.remove(to)
            
        # Start Minimax (Minimizing opponent's turn next)
        score = minimax(new_me, new_opp, depth - 1, -2000000, 2000000, False, 
                        my_dr, my_goal, opp_dr, opp_goal)
        
        if score > best_score:
            best_score = score
            best_move = (fr, to)
            
    return best_move

def minimax(me, opp, depth, alpha, beta, is_maximizing, my_dr, my_goal, opp_dr, opp_goal):
    # Terminal state checks
    # Did I win? (Reached opponent home row)
    for p in me:
        if p[0] == my_goal:
            return 100000
    # Did Opponent win?
    for p in opp:
        if p[0] == opp_goal:
            return -100000
            
    if depth == 0:
        return evaluate(me, opp, my_dr)

    if is_maximizing:
        max_eval = -2000000
        moves = get_moves(me, opp, my_dr, my_goal)
        
        if not moves: return -100000 # Stuck is a loss
        
        # Optimization: If the first sorted move is a win, we can return immediately
        if moves[0][0]: return 100000

        for is_win, is_capture, fr, to in moves:
            new_me = set(me)
            new_opp = set(opp)
            new_me.remove(fr)
            new_me.add(to)
            if is_capture:
                new_opp.remove(to)
            
            eval_val = minimax(new_me, new_opp, depth - 1, alpha, beta, False, 
                               my_dr, my_goal, opp_dr, opp_goal)
            if eval_val > max_eval: max_eval = eval_val
            if max_eval > alpha: alpha = max_eval
            if beta <= alpha: break
        return max_eval
    else:
        min_eval = 2000000
        moves = get_moves(opp, me, opp_dr, opp_goal)
        
        if not moves: return 100000 # Opponent stuck is my win
        
        # Optimization: If opponent can win immediately
        if moves[0][0]: return -100000

        for is_win, is_capture, fr, to in moves:
            new_opp = set(opp)
            new_me = set(me)
            new_opp.remove(fr)
            new_opp.add(to)
            if is_capture:
                new_me.remove(to)
            
            eval_val = minimax(new_me, new_opp, depth - 1, alpha, beta, True, 
                               my_dr, my_goal, opp_dr, opp_goal)
            if eval_val < min_eval: min_eval = eval_val
            if min_eval < beta: beta = min_eval
            if beta <= alpha: break
        return min_eval

def get_moves(pieces, opp_pieces, dr, goal):
    moves = []
    for r, c in pieces:
        nr = r + dr
        if 0 <= nr <= 7:
            # Forward
            if (nr, c) not in opp_pieces and (nr, c) not in pieces:
                moves.append((nr == goal, False, (r, c), (nr, c)))
            # Diagonals
            for dc in [-1, 1]:
                nc = c + dc
                if 0 <= nc <= 7:
                    target = (nr, nc)
                    is_capture = target in opp_pieces
                    is_empty = target not in pieces and not is_capture
                    if is_capture or is_empty:
                        moves.append((nr == goal, is_capture, (r, c), target))
    
    # Sort by Win status then Capture status
    moves.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return moves

def evaluate(me, opp, my_dr):
    # Material score
    score = len(me) * 100 - len(opp) * 100
    
    # Positional score (progress)
    if my_dr == 1: # White (moving up)
        for r, c in me:
            score += r * 10
        for r, c in opp:
            score -= (7 - r) * 10
    else: # Black (moving down)
        for r, c in me:
            score += (7 - r) * 10
        for r, c in opp:
            score -= r * 10
            
    return score
