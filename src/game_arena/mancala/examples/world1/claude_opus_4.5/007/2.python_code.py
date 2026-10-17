
import time

def policy(you: list[int], opponent: list[int]) -> int:
    start_time = time.time()
    time_limit = 0.9
    
    def simulate(player, other, move):
        p = list(player)
        o = list(other)
        
        seeds = p[move]
        p[move] = 0
        pos = move
        
        while seeds > 0:
            pos = (pos + 1) % 13
            if pos <= 5:
                p[pos] += 1
            elif pos == 6:
                p[6] += 1
            else:
                o[pos - 7] += 1
            seeds -= 1
        
        extra_turn = (pos == 6)
        
        if pos <= 5 and p[pos] == 1:
            opp_idx = 5 - pos
            if o[opp_idx] > 0:
                p[6] += 1 + o[opp_idx]
                p[pos] = 0
                o[opp_idx] = 0
        
        return tuple(p), tuple(o), extra_turn
    
    def game_ended(player, other):
        return sum(player[:6]) == 0 or sum(other[:6]) == 0
    
    def final_score(player, other):
        return (player[6] + sum(player[:6])) - (other[6] + sum(other[:6]))
    
    def get_moves(player):
        return [i for i in range(6) if player[i] > 0]
    
    abort = [False]
    
    def negamax(player, other, depth, alpha, beta):
        if time.time() - start_time > time_limit:
            abort[0] = True
            return 0, None
        
        if game_ended(player, other):
            return final_score(player, other), None
        
        moves = get_moves(player)
        if not moves:
            return final_score(player, other), None
        
        if depth <= 0:
            return player[6] - other[6], None
        
        def priority(m):
            seeds = player[m]
            dist = 6 - m
            extra = seeds >= dist and (seeds - dist) % 13 == 0
            return (extra, seeds)
        moves.sort(key=priority, reverse=True)
        
        best_val = float('-inf')
        best_move = moves[0]
        
        for move in moves:
            new_p, new_o, extra = simulate(player, other, move)
            
            if game_ended(new_p, new_o):
                val = final_score(new_p, new_o)
            elif extra:
                val, _ = negamax(new_p, new_o, depth, alpha, beta)
            else:
                val, _ = negamax(new_o, new_p, depth - 1, -beta, -alpha)
                val = -val
            
            if abort[0]:
                return 0, None
            
            if val > best_val:
                best_val = val
                best_move = move
            
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        
        return best_val, best_move
    
    you_t = tuple(you)
    opp_t = tuple(opponent)
    
    moves = get_moves(you_t)
    if len(moves) == 1:
        return moves[0]
    
    best_move = moves[0]
    
    for depth in range(1, 40):
        if time.time() - start_time > time_limit * 0.7:
            break
        abort[0] = False
        val, move = negamax(you_t, opp_t, depth, float('-inf'), float('inf'))
        if not abort[0] and move is not None:
            best_move = move
    
    return best_move
