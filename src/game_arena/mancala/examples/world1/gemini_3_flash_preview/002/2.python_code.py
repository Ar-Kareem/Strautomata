
import copy

def simulate_move(you, opponent, move_idx):
    """
    Returns (new_you, new_opponent, extra_turn)
    """
    you = list(you)
    opponent = list(opponent)
    
    seeds = you[move_idx]
    you[move_idx] = 0
    
    curr_side = 'you'
    curr_idx = move_idx + 1
    
    while seeds > 0:
        if curr_side == 'you':
            if curr_idx < 7: # includes store
                you[curr_idx] += 1
                seeds -= 1
                if seeds == 0:
                    # Capture rule
                    if curr_idx < 6 and you[curr_idx] == 1:
                        opp_idx = 5 - curr_idx
                        if opponent[opp_idx] > 0:
                            you[6] += you[curr_idx] + opponent[opp_idx]
                            you[curr_idx] = 0
                            opponent[opp_idx] = 0
                    # Extra turn rule
                    if curr_idx == 6:
                        return you, opponent, True
                curr_idx += 1
            else:
                curr_side = 'opp'
                curr_idx = 0
        else:
            if curr_idx < 6: # skips opponent store
                opponent[curr_idx] += 1
                seeds -= 1
                if seeds == 0:
                    pass # land in opponent's house, no special rule
                curr_idx += 1
            else:
                curr_side = 'you'
                curr_idx = 0
                
    return you, opponent, False

def is_terminal(you, opponent):
    return sum(you[:6]) == 0 or sum(opponent[:6]) == 0

def evaluate(you, opponent):
    if sum(you[:6]) == 0 or sum(opponent[:6]) == 0:
        y_score = you[6] + sum(you[:6])
        o_score = opponent[6] + sum(opponent[:6])
        return 1000 * (y_score - o_score)
    
    # Heuristic: Store difference + small weight for seeds on board
    return (you[6] - opponent[6]) * 10 + (sum(you[:6]) - sum(opponent[:6]))

def minimax(you, opponent, depth, alpha, beta, maximizing_player):
    if depth == 0 or is_terminal(you, opponent):
        return evaluate(you, opponent)
    
    if maximizing_player:
        max_eval = -float('inf')
        moves = [i for i in range(6) if you[i] > 0]
        # Heuristic move ordering: try moves that give extra turns first
        moves.sort(key=lambda i: (you[i] % 13 == (6 - i)), reverse=True)
        
        for move in moves:
            ny, no, extra = simulate_move(you, opponent, move)
            if extra:
                eval = minimax(ny, no, depth - 1, alpha, beta, True)
            else:
                eval = minimax(no, ny, depth - 1, -beta, -alpha, False)
                eval = -eval
            
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        # This branch is handled by the negation in the caller
        return 0

def policy(you: list[int], opponent: list[int]) -> int:
    best_move = -1
    best_value = -float('inf')
    
    legal_moves = [i for i in range(6) if you[i] > 0]
    if len(legal_moves) == 1:
        return legal_moves[0]
        
    # Increasing depth for better precision within time limits
    # Kalah has a small branching factor, depth 8 is usually safe
    depth = 8
    
    for move in legal_moves:
        ny, no, extra = simulate_move(you, opponent, move)
        if extra:
            # If extra turn, we continue to maximize
            val = minimax(ny, no, depth - 1, -float('inf'), float('inf'), True)
        else:
            # If turn ends, we minimize opponent's outcome
            val = -minimax(no, ny, depth - 1, -float('inf'), float('inf'), False)
            
        if val > best_value:
            best_value = val
            best_move = move
            
    return best_move if best_move != -1 else legal_moves[0]
