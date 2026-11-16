
def policy(you: list[int], opponent: list[int]) -> int:
    """
    Kalah AI Policy using Minimax with a depth of 4.
    Heuristics:
    1. Store count (primary).
    2. Extra moves (landing in store).
    3. Captures (landing in empty house with opposite occupied).
    4. Side seed count (secondary).
    """
    
    # Constants
    DEPTH = 4
    HOUSES = 6
    
    def is_terminal(state):
        y, o = state
        return sum(y[:HOUSES]) == 0 or sum(o[:HOUSES]) == 0

    def get_final_score(state):
        y, o = state
        y_seeds = sum(y)
        o_seeds = sum(o)
        if y_seeds > o_seeds:
            return 100000
        elif y_seeds < o_seeds:
            return -100000
        else:
            return 0

    def evaluate(state, is_maximizing):
        y, o = state
        
        if is_terminal(state):
            return get_final_score(state)
        
        # Heuristics
        y_store = y[6]
        o_store = o[6]
        y_seeds = sum(y[:HOUSES])
        o_seeds = sum(o[:HOUSES])
        
        # Weighted score
        # 1. Store difference is most important
        # 2. Seed difference on side
        # 3. Small bonus for having seeds to move
        
        score = (y_store - o_store) * 100
        score += (y_seeds - o_seeds) * 10
        
        # If it's max's turn, positive score is good.
        # If it's min's turn, positive score is bad (from min's perspective).
        # The return value of evaluate should always be from max's perspective.
        
        return score

    def simulate_move(move, state, player):
        y, o = state
        if player == 'max': # You
            if y[move] == 0: return None
            seeds = y[move]
            new_y = y[:]
            new_o = o[:]
            new_y[move] = 0
            idx = move
            last_seed_loc = None
            
            for _ in range(seeds):
                idx += 1
                if idx < HOUSES:
                    new_y[idx] += 1
                    last_seed_loc = ('y', idx)
                elif idx == HOUSES:
                    new_y[6] += 1
                    last_seed_loc = ('y_store', None)
                elif idx < HOUSES * 2 + 1:
                    # Opponent houses
                    o_idx = idx - HOUSES - 1
                    new_o[o_idx] += 1
                    last_seed_loc = ('o', o_idx)
                else:
                    # Wrap around to own houses
                    wrap_idx = idx - (HOUSES * 2 + 1)
                    new_y[wrap_idx] += 1
                    last_seed_loc = ('y', wrap_idx)
            
            extra_turn = False
            if last_seed_loc[0] == 'y_store':
                extra_turn = True
            
            # Capture
            if not extra_turn and last_seed_loc[0] == 'y':
                l_idx = last_seed_loc[1]
                if new_y[l_idx] == 1: # Was empty (now has 1)
                    opp_idx = 5 - l_idx
                    if new_o[opp_idx] > 0:
                        # Capture
                        new_y[6] += new_y[l_idx] + new_o[opp_idx]
                        new_y[l_idx] = 0
                        new_o[opp_idx] = 0
            
            return (new_y, new_o, extra_turn)
            
        else: # Opponent (Min)
            if o[move] == 0: return None
            seeds = o[move]
            new_y = y[:]
            new_o = o[:]
            new_o[move] = 0
            idx = move
            last_seed_loc = None
            
            for _ in range(seeds):
                idx += 1
                if idx < HOUSES:
                    new_o[idx] += 1
                    last_seed_loc = ('o', idx)
                elif idx == HOUSES:
                    new_o[6] += 1
                    last_seed_loc = ('o_store', None)
                elif idx < HOUSES * 2 + 1:
                    # Opponent houses (which are your houses relative to them)
                    y_idx = idx - HOUSES - 1
                    new_y[y_idx] += 1
                    last_seed_loc = ('y', y_idx)
                else:
                    # Wrap around to own houses
                    wrap_idx = idx - (HOUSES * 2 + 1)
                    new_o[wrap_idx] += 1
                    last_seed_loc = ('o', wrap_idx)
            
            extra_turn = False
            if last_seed_loc[0] == 'o_store':
                extra_turn = True
            
            # Capture
            if not extra_turn and last_seed_loc[0] == 'o':
                l_idx = last_seed_loc[1]
                if new_o[l_idx] == 1:
                    opp_idx = 5 - l_idx
                    if new_y[opp_idx] > 0:
                        new_o[6] += new_o[l_idx] + new_y[opp_idx]
                        new_o[l_idx] = 0
                        new_y[opp_idx] = 0
            
            return (new_y, new_o, extra_turn)

    def minimax(state, depth, alpha, beta, maximizing_player, skip_turn=False):
        if depth == 0 or is_terminal(state):
            return evaluate(state, maximizing_player)

        if maximizing_player:
            max_eval = -float('inf')
            moves = [i for i in range(HOUSES) if state[0][i] > 0]
            # Heuristic move ordering: prioritize moves that might give extra turns or captures
            # We can sort moves simply by seed count (more seeds = more options usually) or check simple conditions
            # For simplicity, we process in order.
            
            for move in moves:
                result = simulate_move(move, state, 'max')
                if result is None: continue
                
                new_y, new_o, extra_turn = result
                next_state = (new_y, new_o)
                
                # If extra turn, depth does not decrease for the same player
                new_depth = depth - 1 if not extra_turn else depth
                
                eval_val = minimax(next_state, new_depth, alpha, beta, True if extra_turn else False, skip_turn=False)
                
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval

        else: # Minimizing player
            min_eval = float('inf')
            moves = [i for i in range(HOUSES) if state[1][i] > 0]
            
            for move in moves:
                result = simulate_move(move, state, 'min')
                if result is None: continue
                
                new_y, new_o, extra_turn = result
                next_state = (new_y, new_o)
                
                new_depth = depth - 1 if not extra_turn else depth
                
                eval_val = minimax(next_state, new_depth, alpha, beta, False if extra_turn else True, skip_turn=False)
                
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # Main Logic
    best_move = -1
    best_value = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    moves = [i for i in range(HOUSES) if you[i] > 0]
    
    # If only one move, take it
    if len(moves) == 1:
        return moves[0]
        
    # Sort moves to improve pruning (simple heuristic: more seeds first)
    moves.sort(key=lambda i: you[i], reverse=True)

    for move in moves:
        result = simulate_move(move, (you, opponent), 'max')
        if result is None: continue
        
        new_y, new_o, extra_turn = result
        next_state = (new_y, new_o)
        
        # Start minimax
        # If extra turn, we keep depth, but it's still "our turn".
        # Minimax signature: minimax(state, depth, alpha, beta, maximizing_player)
        # If we get extra turn, we are still maximizing.
        # However, usually in games, "extra turn" just means the turn repeats.
        # So if extra_turn is True, we call minimax with maximizing_player=True and depth unchanged (or decremented if we count moves strictly).
        # Strict depth counting:
        new_depth = DEPTH - 1 if not extra_turn else DEPTH
        
        eval_val = minimax(next_state, new_depth, alpha, beta, True if extra_turn else False)
        
        if eval_val > best_value:
            best_value = eval_val
            best_move = move
        
        alpha = max(alpha, best_value)
        if beta <= alpha:
            break
            
    if best_move == -1:
        # Fallback
        return moves[0] if moves else 0
        
    return best_move
