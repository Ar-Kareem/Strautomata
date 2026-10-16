
import random
import time

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Calculates the best move for the Breakthrough game using Minimax with Alpha-Beta pruning.
    """
    
    # Determine direction and goal row based on color
    # White moves up (increasing row), Black moves down (decreasing row)
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
    
    # Precompute opponent goal row logic
    # If I am White (Goal 7), Opponent is Black (Goal 0).
    # If I am Black (Goal 0), Opponent is White (Goal 7).
    
    # Helper to generate legal moves for a player
    def get_moves(p_pieces, e_pieces, dr, goal):
        moves = []
        for r, c in p_pieces:
            # Straight move
            nr, nc = r + dr, c
            if 0 <= nr < 8 and 0 <= nc < 8:
                if (nr, nc) not in p_pieces and (nr, nc) not in e_pieces:
                    # Winning move is prioritized by returning immediately or flagged
                    moves.append(((r, c), (nr, nc), nr == goal))
            
            # Diagonal moves
            for dc in [-1, 1]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    # Can move diagonally if empty or capture
                    if (nr, nc) not in p_pieces:
                        is_capture = (nr, nc) in e_pieces
                        moves.append(((r, c), (nr, nc), nr == goal, is_capture))
        return moves

    # Heuristic evaluation function
    def evaluate(my_p, opp_p):
        score = 0
        # Material weight
        mat_weight = 100
        
        # Advancement weights: exponential value for distance covered
        # dist_to_goal: 7 -> 0.
        # If dist is 7 (start), value 0.
        # If dist is 1 (one step from win), high value.
        
        for r, c in my_p:
            dist = abs(r - my_goal)
            # Value increases as distance decreases
            # (8 - dist)^2 gives significant value to advanced pieces
            score += mat_weight + (8 - dist) ** 2 * 20
            
            # Safety penalty: if opponent can capture this piece
            # Opponent attacks from (r + my_dr, c +/- 1)?
            # Wait, opponent moves with opp_dr.
            # If I am White (dr=1), opponent is Black (dr=-1).
            # Opponent at (r+1, c-1) or (r+1, c+1) attacks (r,c).
            # Logic check: Black at r+1 moves to (r+1)-1 = r.
            # Correct.
            if (r + my_dr, c - 1) in opp_p or (r + my_dr, c + 1) in opp_p:
                score -= 50 # Penalty for being threatened

        for r, c in opp_p:
            dist = abs(r - opp_goal)
            score -= mat_weight + (8 - dist) ** 2 * 20
            
            # Bonus for threatening opponent
            if (r - my_dr, c - 1) in my_p or (r - my_dr, c + 1) in my_p:
                score += 50
                
        return score

    # Minimax with Alpha-Beta Pruning
    def minimax(my_p, opp_p, depth, alpha, beta, maximizing_player):
        # Check for terminal states (Win/Loss)
        for r, c in my_p:
            if r == my_goal:
                return 100000
        for r, c in opp_p:
            if r == opp_goal:
                return -100000
        
        if depth == 0:
            return evaluate(my_p, opp_p)
        
        if maximizing_player:
            max_eval = -float('inf')
            moves = get_moves(my_p, opp_p, my_dr, my_goal)
            
            # Move ordering: prioritize wins, then captures, then others
            # Sorting tuple: (is_win, is_capture) -> sorts descending bools
            moves.sort(key=lambda x: (x[2], x[3] if len(x) > 3 else False), reverse=True)
            
            for m in moves:
                fr, to, is_win = m[0], m[1], m[2]
                
                # Apply move
                new_my_p = set(my_p)
                new_opp_p = set(opp_p)
                new_my_p.remove(fr)
                new_my_p.add(to)
                if to in new_opp_p:
                    new_opp_p.remove(to)
                
                # Recurse
                eval_val = minimax(new_my_p, new_opp_p, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            # Opponent moves
            moves = get_moves(opp_p, my_p, opp_dr, opp_goal)
            moves.sort(key=lambda x: (x[2], x[3] if len(x) > 3 else False), reverse=True)
            
            for m in moves:
                fr, to, is_win = m[0], m[1], m[2]
                
                # Apply move
                new_my_p = set(my_p)
                new_opp_p = set(opp_p)
                new_opp_p.remove(fr)
                new_opp_p.add(to)
                if to in new_my_p:
                    new_my_p.remove(to)
                    
                eval_val = minimax(new_my_p, new_opp_p, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # Main logic
    # 1. Check for immediate winning moves
    all_moves = get_moves(me_set, opp_set, my_dr, my_goal)
    random.shuffle(all_moves) # Introduce randomness for equal moves
    
    for m in all_moves:
        if m[2]: # is_win
            return (m[0], m[1])
            
    # 2. Search for best move
    best_score = -float('inf')
    best_move = all_moves[0][:2] # Default
    
    # Sorting root moves can improve pruning efficiency
    all_moves.sort(key=lambda x: (x[3] if len(x) > 3 else False), reverse=True)
    
    start_time = time.time()
    # Depth 3 is safe for 1 second. Depth 4 might timeout in complex positions.
    search_depth = 3
    
    # Optional: Iterative deepening if time permits (skipped for strict safety)
    
    for m in all_moves:
        # Check timeout (rough check)
        if time.time() - start_time > 0.8:
            break
            
        fr, to = m[0], m[1]
        
        # Apply move
        new_me = set(me_set)
        new_opp = set(opp_set)
        new_me.remove(fr)
        new_me.add(to)
        if to in new_opp:
            new_opp.remove(to)
            
        current_score = minimax(new_me, new_opp, search_depth - 1, -float('inf'), float('inf'), False)
        
        if current_score > best_score:
            best_score = current_score
            best_move = (fr, to)
            
    return best_move
