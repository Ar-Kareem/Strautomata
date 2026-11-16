
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(you, opponent, move):
        you = list(you)
        opponent = list(opponent)
        seeds = you[move]
        you[move] = 0
        
        pos = move
        while seeds > 0:
            pos += 1
            if pos == 13:
                pos = 0
            if pos < 6:
                you[pos] += 1
            elif pos == 6:
                you[6] += 1
            else:
                opponent[pos - 7] += 1
            seeds -= 1
        
        extra_move = (pos == 6)
        
        # Capture: last seed in my empty house, opposite has seeds
        if pos < 6 and you[pos] == 1:
            opposite = 5 - pos
            if opponent[opposite] > 0:
                you[6] += 1 + opponent[opposite]
                you[pos] = 0
                opponent[opposite] = 0
        
        return tuple(you), tuple(opponent), extra_move
    
    def evaluate(you, opponent):
        # Score difference plus small bonus for seeds on my side
        return you[6] - opponent[6] + 0.1 * (sum(you[:6]) - sum(opponent[:6]))
    
    def minimax(you, opponent, depth, alpha, beta, is_my_turn, memo):
        key = (you, opponent, depth, is_my_turn)
        if key in memo:
            return memo[key]
        
        my_sum = sum(you[:6])
        opp_sum = sum(opponent[:6])
        
        # Terminal state
        if my_sum == 0 or opp_sum == 0:
            final_diff = (you[6] + my_sum) - (opponent[6] + opp_sum)
            result = (final_diff * 1000, None)
            memo[key] = result
            return result
        
        if depth == 0:
            result = (evaluate(you, opponent), None)
            memo[key] = result
            return result
        
        if is_my_turn:
            best_value = -float('inf')
            best_move = None
            # Order moves: prefer moves that land in store (extra turn)
            moves = [(you[i], -(6 - i - you[i] % 13), i) for i in range(6) if you[i] > 0]
            moves.sort(reverse=True)
            
            for _, _, move in moves:
                new_you, new_opp, extra = simulate_move(you, opponent, move)
                if extra:
                    value, _ = minimax(new_you, new_opp, depth, alpha, beta, True, memo)
                else:
                    value, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, False, memo)
                if value > best_value:
                    best_value = value
                    best_move = move
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            result = (best_value, best_move)
        else:
            best_value = float('inf')
            for move in range(6):
                if opponent[move] > 0:
                    new_opp, new_you, extra = simulate_move(opponent, you, move)
                    if extra:
                        value, _ = minimax(new_you, new_opp, depth, alpha, beta, False, memo)
                    else:
                        value, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, True, memo)
                    best_value = min(best_value, value)
                    beta = min(beta, value)
                    if beta <= alpha:
                        break
            result = (best_value, None)
        
        memo[key] = result
        return result
    
    # Iterative deepening with time limit
    import time
    start = time.time()
    best_move = None
    
    # Find first legal move as fallback
    for i in range(6):
        if you[i] > 0:
            best_move = i
            break
    
    for depth in range(1, 16):
        if time.time() - start > 0.85:
            break
        memo = {}
        _, move = minimax(tuple(you), tuple(opponent), depth, -float('inf'), float('inf'), True, memo)
        if move is not None:
            best_move = move
    
    return best_move
