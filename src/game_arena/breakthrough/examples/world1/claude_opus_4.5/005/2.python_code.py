
import time

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    me_set = set(me)
    opp_set = set(opp)
    direction = 1 if color == 'w' else -1
    goal_row = 7 if color == 'w' else 0
    opp_goal = 0 if color == 'w' else 7
    
    def get_moves(my_pieces, opponent_pieces, d):
        my_set = set(my_pieces)
        opp_s = set(opponent_pieces)
        moves = []
        for r, c in my_pieces:
            nr = r + d
            if 0 <= nr <= 7:
                # Forward move
                if (nr, c) not in my_set and (nr, c) not in opp_s:
                    moves.append(((r, c), (nr, c)))
                # Diagonal moves
                for dc in [-1, 1]:
                    nc = c + dc
                    if 0 <= nc <= 7:
                        if (nr, nc) in opp_s:
                            moves.append(((r, c), (nr, nc)))
                        elif (nr, nc) not in my_set:
                            moves.append(((r, c), (nr, nc)))
        return moves
    
    def evaluate(my_pieces, opponent_pieces, my_dir, my_goal):
        if not opponent_pieces:
            return 100000
        if not my_pieces:
            return -100000
        
        for r, c in my_pieces:
            if r == my_goal:
                return 100000
        for r, c in opponent_pieces:
            if r == (0 if my_goal == 7 else 7):
                return -100000
        
        score = 0
        score += (len(my_pieces) - len(opponent_pieces)) * 100
        
        for r, c in my_pieces:
            progress = r if my_dir == 1 else (7 - r)
            score += progress * progress * 5
            score += (3.5 - abs(c - 3.5)) * 2
        
        for r, c in opponent_pieces:
            progress = (7 - r) if my_dir == 1 else r
            score -= progress * progress * 5
            score -= (3.5 - abs(c - 3.5)) * 2
        
        return score
    
    def minimax(my_pieces, opp_pieces, depth, alpha, beta, maximizing, my_dir, my_goal):
        if depth == 0:
            return evaluate(my_pieces, opp_pieces, my_dir, my_goal), None
        
        if maximizing:
            moves = get_moves(my_pieces, opp_pieces, my_dir)
            if not moves:
                return -50000, None
            
            # Move ordering: prioritize captures and goal-reaching moves
            moves.sort(key=lambda m: (m[1][0] == my_goal, m[1] in opp_pieces), reverse=True)
            
            best_val = -float('inf')
            best_move = moves[0]
            
            for move in moves:
                new_my = [p for p in my_pieces if p != move[0]] + [move[1]]
                new_opp = [p for p in opp_pieces if p != move[1]]
                
                if move[1][0] == my_goal:
                    return 100000, move
                
                val, _ = minimax(new_opp, new_my, depth - 1, -beta, -alpha, False, -my_dir, 7 - my_goal)
                val = -val
                
                if val > best_val:
                    best_val = val
                    best_move = move
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return best_val, best_move
        else:
            return minimax(my_pieces, opp_pieces, depth, alpha, beta, True, my_dir, my_goal)
    
    # Iterative deepening
    start_time = time.time()
    best_move = None
    
    moves = get_moves(me, opp, direction)
    if not moves:
        return ((0, 0), (0, 0))  # Should never happen
    
    best_move = moves[0]
    
    # Check for immediate wins
    for move in moves:
        if move[1][0] == goal_row:
            return move
    
    for depth in range(1, 10):
        if time.time() - start_time > 0.8:
            break
        _, move = minimax(list(me), list(opp), depth, -float('inf'), float('inf'), True, direction, goal_row)
        if move:
            best_move = move
    
    return best_move
