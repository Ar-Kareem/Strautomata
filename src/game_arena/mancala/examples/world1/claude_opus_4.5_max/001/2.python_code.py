
def policy(you: list[int], opponent: list[int]) -> int:
    import time
    
    def simulate_move(player, other, move):
        player, other = list(player), list(other)
        seeds, player[move], pos = player[move], 0, move
        while seeds > 0:
            pos = (pos + 1) % 13
            if pos < 7: player[pos] += 1
            else: other[pos - 7] += 1
            seeds -= 1
        if pos == 6: return player, other, True
        if pos <= 5 and player[pos] == 1:
            opp = 5 - pos
            if other[opp] > 0:
                player[6] += 1 + other[opp]
                player[pos], other[opp] = 0, 0
        return player, other, False
    
    def is_over(my, their): return sum(my[:6]) == 0 or sum(their[:6]) == 0
    def final_score(my, their): return (my[6] + sum(my[:6])) - (their[6] + sum(their[:6]))
    
    def evaluate(my, their):
        score = (my[6] - their[6]) * 5 + (sum(my[:6]) - sum(their[:6])) * 0.5
        for i in range(6):
            if my[i] > 0:
                f = (i + my[i]) % 13
                if f == 6: score += 2
                elif f <= 5 and my[i] <= 13 and their[5-f] > 0:
                    if my[i] == 13 or (f != i and my[f] == 0): score += their[5-f] * 0.3
        return score
    
    def get_moves(st): return [i for i in range(6) if st[i] > 0]
    
    def order_moves(my, their, moves):
        def pri(m):
            s, f = my[m], (m + my[m]) % 13
            if f == 6: return 1000
            if f <= 5 and s <= 13 and their[5-f] > 0 and (s == 13 or (f != m and my[f] == 0)):
                return 500 + their[5-f] * 10
            return s
        return sorted(moves, key=pri, reverse=True)
    
    def minimax(my, their, depth, alpha, beta, my_turn, ply):
        if is_over(my, their): return final_score(my, their) * 10000, None
        if depth == 0 or ply > 80: return evaluate(my, their), None
        
        if my_turn:
            moves = get_moves(my)
            if not moves: return final_score(my, their) * 10000, None
            moves = order_moves(my, their, moves)
            best_val, best_move = float('-inf'), moves[0]
            for m in moves:
                new_my, new_their, extra = simulate_move(my, their, m)
                val, _ = minimax(new_my, new_their, depth if extra else depth-1, alpha, beta, extra or not my_turn, ply+1)
                if val > best_val: best_val, best_move = val, m
                alpha = max(alpha, val)
                if beta <= alpha: break
            return best_val, best_move
        else:
            moves = get_moves(their)
            if not moves: return final_score(my, their) * 10000, None
            moves = order_moves(their, my, moves)
            best_val = float('inf')
            for m in moves:
                new_their, new_my, extra = simulate_move(their, my, m)
                val, _ = minimax(new_my, new_their, depth if extra else depth-1, alpha, beta, not extra, ply+1)
                best_val = min(best_val, val)
                beta = min(beta, val)
                if beta <= alpha: break
            return best_val, None
    
    start, best = time.time(), None
    yl, ol = list(you), list(opponent)
    for d in range(1, 30):
        if time.time() - start > 0.7: break
        _, m = minimax(yl, ol, d, float('-inf'), float('inf'), True, 0)
        if m is not None: best = m
    
    if best is None or you[best] == 0:
        best = next(i for i in range(6) if you[i] > 0)
    return best
