
import time

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Returns the best move using iterative deepening negamax with alpha-beta pruning.
    """
    
    def simulate_move(you, opponent, move):
        """Simulate a move and return the new state and whether we get another turn."""
        you = you[:]
        opponent = opponent[:]
        
        seeds = you[move]
        you[move] = 0
        
        pos = move + 1
        side = 'you'
        last_side = None
        last_pos = None
        
        while seeds > 0:
            if side == 'you':
                if pos <= 6:
                    you[pos] += 1
                    last_side = 'you'
                    last_pos = pos
                    seeds -= 1
                    pos += 1
                else:
                    side = 'opponent'
                    pos = 0
            else:
                if pos <= 5:
                    opponent[pos] += 1
                    last_side = 'opponent'
                    last_pos = pos
                    seeds -= 1
                    pos += 1
                else:
                    side = 'you'
                    pos = 0
        
        extra_turn = (last_side == 'you' and last_pos == 6)
        
        if (last_side == 'you' and 0 <= last_pos <= 5 and 
            you[last_pos] == 1 and opponent[5 - last_pos] > 0):
            you[6] += you[last_pos] + opponent[5 - last_pos]
            you[last_pos] = 0
            opponent[5 - last_pos] = 0
        
        return you, opponent, extra_turn
    
    def is_terminal(you, opponent):
        """Check if the game is over."""
        return sum(you[0:6]) == 0 or sum(opponent[0:6]) == 0
    
    def get_legal_moves(you):
        """Get all legal moves."""
        return [i for i in range(6) if you[i] > 0]
    
    def evaluate(you, opponent):
        """Evaluate the current position."""
        you_seeds = sum(you[0:6])
        opp_seeds = sum(opponent[0:6])
        
        if you_seeds == 0 or opp_seeds == 0:
            final_you = you[6] + you_seeds
            final_opp = opponent[6] + opp_seeds
            diff = final_you - final_opp
            if diff > 0:
                return 100000
            elif diff < 0:
                return -100000
            else:
                return 0
        
        score = (you[6] - opponent[6]) * 100
        score += (you_seeds - opp_seeds) * 5
        
        for i in range(6):
            if you[i] > 0 and you[i] == 6 - i:
                score += 30
            if opponent[i] > 0 and opponent[i] == 6 - i:
                score -= 20
        
        return score
    
    def negamax(you, opponent, depth, alpha, beta):
        """Negamax with alpha-beta pruning."""
        if depth == 0 or is_terminal(you, opponent):
            return evaluate(you, opponent), None
        
        legal_moves = get_legal_moves(you)
        
        if not legal_moves:
            return evaluate(you, opponent), None
        
        legal_moves.sort(key=lambda m: (-1000 if you[m] == 6 - m else -you[m]))
        
        max_eval = float('-inf')
        best_move = legal_moves[0]
        
        for move in legal_moves:
            new_you, new_opp, extra_turn = simulate_move(you, opponent, move)
            
            if extra_turn:
                eval_score, _ = negamax(new_you, new_opp, depth - 1, alpha, beta)
            else:
                eval_score, _ = negamax(new_opp, new_you, depth - 1, -beta, -alpha)
                eval_score = -eval_score
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            
            alpha = max(alpha, eval_score)
            if alpha >= beta:
                break
        
        return max_eval, best_move
    
    legal_moves = get_legal_moves(you)
    if not legal_moves:
        return 0
    
    best_move = legal_moves[0]
    start_time = time.time()
    time_limit = 0.9
    
    try:
        for depth in range(1, 30):
            if time.time() - start_time > time_limit:
                break
            
            _, move = negamax(you, opponent, depth, float('-inf'), float('inf'))
            best_move = move
    except:
        pass
    
    return best_move
