
import random

# Constants for the search algorithm
SEARCH_DEPTH = 10
WEIGHT_STORE = 1.0
WEIGHT_SEEDS = 0.5

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Determines the best move for the current player using Minimax with Alpha-Beta pruning.
    """
    # Identify all legal moves (houses with seeds)
    legal_moves = [i for i in range(6) if you[i] > 0]
    
    # If there is only one legal move, take it immediately
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    best_move = -1
    best_value = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    # Shuffle moves to ensure variation if scores are equal
    random.shuffle(legal_moves)
    
    # Iterate through legal moves to find the best one
    for move in legal_moves:
        new_you, new_opp, extra_turn = simulate(you, opponent, move)
        
        # Call minimax
        # If we get an extra turn, we are still the maximizing player, so we pass True.
        # We pass the same depth because we haven't passed the turn to the opponent yet
        # (consuming a ply only when the turn switches).
        if extra_turn:
            value = minimax(new_you, new_opp, SEARCH_DEPTH, alpha, beta, True)
        else:
            value = minimax(new_you, new_opp, SEARCH_DEPTH - 1, alpha, beta, False)
        
        if value > best_value:
            best_value = value
            best_move = move
            
        alpha = max(alpha, value)
        
        # Optimization: If we found a guaranteed winning score (e.g., > 50), stop searching.
        # Maximum score difference is rarely higher than total seeds (usually < 100).
        if best_value > 100:
            return best_move

    return best_move

def simulate(p_board: list[int], o_board: list[int], idx: int):
    """
    Simulates a move for the player 'p_board' against 'o_board'.
    Returns: (new_p_board, new_o_board, extra_turn_bool)
    """
    # Create copies of the boards to avoid mutation
    new_p = list(p_board)
    new_o = list(o_board)
    
    seeds = new_p[idx]
    new_p[idx] = 0
    current_pos = idx
    
    # Sowing loop
    while seeds > 0:
        current_pos += 1
        
        # Logic maps linear index 0-12 to the two boards
        # 0-5: p_board houses
        # 6: p_board store
        # 7-12: o_board houses (skipping o_board store at index 13)
        
        if current_pos == 6:
            new_p[6] += 1
            seeds -= 1
        elif current_pos > 12:
            current_pos = 0
            new_p[0] += 1
            seeds -= 1
        elif 0 <= current_pos <= 5:
            new_p[current_pos] += 1
            seeds -= 1
        elif 7 <= current_pos <= 12:
            opp_idx = current_pos - 7
            new_o[opp_idx] += 1
            seeds -= 1
            
    # Check for extra turn (last seed landed in store)
    if current_pos == 6:
        return new_p, new_o, True
        
    # Check for capture
    # Condition: Last seed landed in own house (0-5), that house was empty before the drop,
    # and opposite house has seeds.
    if 0 <= current_pos <= 5:
        if new_p[current_pos] == 1: # It was empty before we dropped this seed
            opp_idx = 5 - current_pos
            if new_o[opp_idx] > 0:
                # Capture: Move seed from house + opposite house to store
                new_p[6] += new_p[current_pos] + new_o[opp_idx]
                new_p[current_pos] = 0
                new_o[opp_idx] = 0
                
    return new_p, new_o, False

def minimax(you: list[int], opp: list[int], depth: int, alpha: float, beta: float, maximizing: bool):
    """
    Minimax algorithm with Alpha-Beta pruning.
    """
    # Terminal state checks
    my_seeds = sum(you[0:6])
    opp_seeds = sum(opp[0:6])
    
    if my_seeds == 0:
        # I have no seeds, opponent collects their remaining seeds
        return you[6] - (opp[6] + opp_seeds)
        
    if opp_seeds == 0:
        # Opponent has no seeds, I collect my remaining seeds
        return (you[6] + my_seeds) - opp[6]
    
    if depth == 0:
        return evaluate(you, opp)
        
    if maximizing:
        max_eval = -float('inf')
        moves = [i for i in range(6) if you[i] > 0]
        
        for move in moves:
            new_you, new_opp, extra = simulate(you, opp, move)
            
            if extra:
                eval_val = minimax(new_you, new_opp, depth, alpha, beta, True)
            else:
                eval_val = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
                
            max_eval = max(max_eval, eval_val)
            alpha = max(alpha, eval_val)
            
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        moves = [i for i in range(6) if opp[i] > 0]
        
        for move in moves:
            # Opponent is the active player
            new_opp_active, new_you_passive, extra = simulate(opp, you, move)
            
            if extra:
                eval_val = minimax(new_you_passive, new_opp_active, depth, alpha, beta, False)
            else:
                eval_val = minimax(new_you_passive, new_opp_active, depth - 1, alpha, beta, True)
                
            min_eval = min(min_eval, eval_val)
            beta = min(beta, eval_val)
            
            if beta <= alpha:
                break
        return min_eval

def evaluate(you: list[int], opp: list[int]):
    """
    Heuristic evaluation function.
    Positive score is good for 'you'.
    """
    store_diff = you[6] - opp[6]
    seeds_diff = sum(you[0:6]) - sum(opp[0:6])
    
    return WEIGHT_STORE * store_diff + WEIGHT_SEEDS * seeds_diff
