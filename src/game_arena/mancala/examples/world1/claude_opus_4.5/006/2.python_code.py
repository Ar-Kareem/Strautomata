
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate(player, other, move):
        player = list(player)
        other = list(other)
        seeds = player[move]
        player[move] = 0
        pos = move
        while seeds > 0:
            pos = (pos + 1) % 13
            if pos < 6:
                player[pos] += 1
            elif pos == 6:
                player[6] += 1
            else:
                other[pos - 7] += 1
            seeds -= 1
        extra_turn = (pos == 6)
        if pos < 6 and player[pos] == 1:
            opposite = 5 - pos
            if other[opposite] > 0:
                player[6] += player[pos] + other[opposite]
                player[pos] = 0
                other[opposite] = 0
        return tuple(player), tuple(other), extra_turn
    
    def evaluate(my_pits, opp_pits):
        return my_pits[6] - opp_pits[6] + 0.05 * (sum(my_pits[:6]) - sum(opp_pits[:6]))
    
    def minimax(my_pits, opp_pits, depth, alpha, beta, is_my_turn):
        my_sum = sum(my_pits[:6])
        opp_sum = sum(opp_pits[:6])
        
        if my_sum == 0 or opp_sum == 0:
            final_my = my_pits[6] + my_sum
            final_opp = opp_pits[6] + opp_sum
            diff = final_my - final_opp
            if diff > 0:
                return 1000 + diff
            elif diff < 0:
                return -1000 + diff
            return 0
        
        if depth == 0:
            return evaluate(my_pits, opp_pits)
        
        if is_my_turn:
            max_eval = float('-inf')
            moves = [i for i in range(6) if my_pits[i] > 0]
            # Prioritize moves that end in store (extra turn)
            moves.sort(key=lambda i: -1 if (my_pits[i] + i) % 13 == 6 else i)
            for i in moves:
                new_my, new_opp, extra = simulate(my_pits, opp_pits, i)
                if extra:
                    ev = minimax(new_my, new_opp, depth, alpha, beta, True)
                else:
                    ev = minimax(new_my, new_opp, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, ev)
                alpha = max(alpha, ev)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            moves = [i for i in range(6) if opp_pits[i] > 0]
            moves.sort(key=lambda i: -1 if (opp_pits[i] + i) % 13 == 6 else i)
            for i in moves:
                new_opp, new_my, extra = simulate(opp_pits, my_pits, i)
                if extra:
                    ev = minimax(new_my, new_opp, depth, alpha, beta, False)
                else:
                    ev = minimax(new_my, new_opp, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, ev)
                beta = min(beta, ev)
                if beta <= alpha:
                    break
            return min_eval
    
    you_t = tuple(you)
    opp_t = tuple(opponent)
    
    best_move = -1
    best_score = float('-inf')
    
    valid_moves = [i for i in range(6) if you[i] > 0]
    
    # Check for immediate extra turns first
    for i in valid_moves:
        if (you[i] + i) % 13 == 6:
            new_you, new_opp, extra = simulate(you_t, opp_t, i)
            if extra:
                score = minimax(new_you, new_opp, 10, float('-inf'), float('inf'), True)
                if score > best_score:
                    best_score = score
                    best_move = i
    
    # Then check other moves
    for i in valid_moves:
        if (you[i] + i) % 13 != 6:
            new_you, new_opp, extra = simulate(you_t, opp_t, i)
            score = minimax(new_you, new_opp, 10, float('-inf'), float('inf'), False)
            if score > best_score:
                best_score = score
                best_move = i
    
    # Fallback if somehow nothing was selected
    if best_move == -1:
        best_move = valid_moves[0]
    
    return best_move
