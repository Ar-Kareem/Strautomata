
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    direction = 1 if color == 'w' else -1
    goal_row = 0 if color == 'b' else 7
    my_set = set(me)
    opp_set = set(opp)

    def get_legal_moves(current_me, current_opp, current_color):
        moves = []
        d = 1 if current_color == 'w' else -1
        c_me = set(current_me)
        c_opp = set(current_opp)
        
        for r, c in current_me:
            # Straight move
            nr, nc = r + d, c
            if 0 <= nr <= 7 and (nr, nc) not in c_me and (nr, nc) not in c_opp:
                moves.append(((r, c), (nr, nc)))
            # Diagonal moves
            for dc in [-1, 1]:
                nr, nc = r + d, c + dc
                if 0 <= nr <= 7 and 0 <= nc <= 7:
                    if (nr, nc) not in c_me:
                        moves.append(((r, c), (nr, nc)))
        return moves

    def evaluate(current_me, current_opp, current_color, original_color):
        score = 0
        target_row = 7 if original_color == 'w' else 0
        
        # Check for immediate wins
        for r, c in current_me:
            if r == target_row: return 10000
        for r, c in current_opp:
            if r == (0 if target_row == 7 else 7): return -10000

        # Material and Position
        if original_color == 'w':
            for r, c in current_me: score += (10 + r)
            for r, c in current_opp: score -= (10 + (7 - r))
        else:
            for r, c in current_me: score += (10 + (7 - r))
            for r, c in current_opp: score -= (10 + r)
            
        return score

    def minimax(c_me, c_opp, depth, alpha, beta, is_maximizing, p_color):
        # Quick win check
        target_row = 7 if (p_color == 'w' if is_maximizing else ('b' if p_color == 'w' else 'w')) == 'w' else 0
        
        if depth == 0:
            return evaluate(c_me, c_opp, p_color, color)

        legal_moves = get_legal_moves(c_me, c_opp, p_color)
        if not legal_moves: return -9999 if is_maximizing else 9999
        
        # Move ordering: captures and goal-reaching first
        opp_set_cur = set(c_opp)
        legal_moves.sort(key=lambda m: (m[1][0] == goal_row, m[1] in opp_set_cur), reverse=True)

        if is_maximizing:
            max_eval = -float('inf')
            for move in legal_moves:
                new_me = [p if p != move[0] else move[1] for p in c_me]
                new_opp = [p for p in c_opp if p != move[1]]
                if move[1][0] == goal_row: return 10000 # Direct win
                eval = minimax(new_me, new_opp, depth - 1, alpha, beta, False, 'b' if p_color == 'w' else 'w')
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                new_me = [p if p != move[0] else move[1] for p in c_me]
                new_opp = [p for p in c_opp if p != move[1]]
                if move[1][0] == (0 if goal_row == 7 else 7): return -10000 # Opponent win
                eval = minimax(new_me, new_opp, depth - 1, alpha, beta, True, 'b' if p_color == 'w' else 'w')
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

    # Root logic
    best_move = None
    best_value = -float('inf')
    all_moves = get_legal_moves(me, opp, color)
    
    # Priority 1: Instant Win
    for move in all_moves:
        if move[1][0] == goal_row:
            return move

    # Alpha-Beta Search
    random.shuffle(all_moves)
    for move in all_moves:
        new_me = [p if p != move[0] else move[1] for p in me]
        new_opp = [p for p in opp if p != move[1]]
        val = minimax(new_me, new_opp, 3, -float('inf'), float('inf'), False, 'b' if color == 'w' else 'w')
        if val > best_value:
            best_value = val
            best_move = move

    return best_move if best_move else all_moves[0]
