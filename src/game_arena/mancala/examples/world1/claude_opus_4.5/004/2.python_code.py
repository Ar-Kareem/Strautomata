
def policy(you: list[int], opponent: list[int]) -> int:
    import time
    start_time = time.time()
    time_limit = 0.85
    
    def simulate(you_s, opp_s, move, is_you_moving):
        if is_you_moving:
            mover = list(you_s)
            other = list(opp_s)
        else:
            mover = list(opp_s)
            other = list(you_s)
        
        seeds = mover[move]
        mover[move] = 0
        pos = move
        
        while seeds > 0:
            pos = (pos + 1) % 13  # 0-5: mover houses, 6: mover store, 7-12: other houses
            if pos <= 5:
                mover[pos] += 1
            elif pos == 6:
                mover[6] += 1
            else:
                other[pos - 7] += 1
            seeds -= 1
        
        extra = (pos == 6)
        captured = 0
        
        if pos <= 5 and mover[pos] == 1:
            opposite = 5 - pos
            if other[opposite] > 0:
                captured = 1 + other[opposite]
                mover[6] += captured
                mover[pos] = 0
                other[opposite] = 0
        
        if is_you_moving:
            return tuple(mover), tuple(other), extra, captured
        else:
            return tuple(other), tuple(mover), extra, captured

    def evaluate(you_s, opp_s):
        return you_s[6] - opp_s[6]

    def final_score(you_s, opp_s):
        you_final = you_s[6] + sum(you_s[:6])
        opp_final = opp_s[6] + sum(opp_s[:6])
        return (you_final - opp_final) * 100

    def get_ordered_moves(you_s, opp_s, is_you_turn):
        mover = you_s if is_you_turn else opp_s
        moves = []
        for i in range(6):
            if mover[i] > 0:
                _, _, extra, captured = simulate(you_s, opp_s, i, is_you_turn)
                priority = extra * 1000 + captured * 10 + (5 - i)
                moves.append((priority, i))
        moves.sort(reverse=True)
        return [m[1] for m in moves]

    def minimax(you_s, opp_s, depth, alpha, beta, is_you_turn):
        you_sum = sum(you_s[:6])
        opp_sum = sum(opp_s[:6])
        
        if you_sum == 0 or opp_sum == 0:
            return final_score(you_s, opp_s), None
        
        if depth == 0:
            return evaluate(you_s, opp_s), None
        
        moves = get_ordered_moves(you_s, opp_s, is_you_turn)
        
        if not moves:
            return final_score(you_s, opp_s), None
        
        if is_you_turn:
            max_eval = float('-inf')
            best_move = moves[0]
            for i in moves:
                new_you, new_opp, extra, _ = simulate(you_s, opp_s, i, True)
                if extra:
                    ev, _ = minimax(new_you, new_opp, depth, alpha, beta, True)
                else:
                    ev, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
                if ev > max_eval:
                    max_eval = ev
                    best_move = i
                alpha = max(alpha, ev)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = moves[0]
            for i in moves:
                new_you, new_opp, extra, _ = simulate(you_s, opp_s, i, False)
                if extra:
                    ev, _ = minimax(new_you, new_opp, depth, alpha, beta, False)
                else:
                    ev, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
                if ev < min_eval:
                    min_eval = ev
                    best_move = i
                beta = min(beta, ev)
                if beta <= alpha:
                    break
            return min_eval, best_move

    best_move = None
    you_tuple = tuple(you)
    opp_tuple = tuple(opponent)
    
    # Iterative deepening
    for depth in range(1, 30):
        if time.time() - start_time > time_limit * 0.7:
            break
        _, move = minimax(you_tuple, opp_tuple, depth, float('-inf'), float('inf'), True)
        if move is not None:
            best_move = move
    
    # Fallback
    if best_move is None:
        for i in range(6):
            if you[i] > 0:
                return i
    
    return best_move
