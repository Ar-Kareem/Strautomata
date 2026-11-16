
import time

def policy(you: list[int], opponent: list[int]) -> int:
    start_time = time.time()
    time_limit = 0.85  # conservative time limit
    
    def simulate_move(you, opponent, move):
        """Simulate a move. Returns (new_you, new_opponent, extra_turn)."""
        y = list(you)
        o = list(opponent)
        seeds = y[move]
        y[move] = 0
        pos = move + 1  # start sowing from next position
        # Positions 0-5: your houses, 6: your store, 7-12: opponent houses 0-5
        # Skip opponent store (position 13)
        idx = pos
        while seeds > 0:
            if idx < 6:
                y[idx] += 1
            elif idx == 6:
                y[6] += 1
            elif idx < 13:
                o[idx - 7] += 1
            else:
                idx = 0
                continue
            seeds -= 1
            if seeds > 0:
                idx += 1
                if idx >= 13:
                    idx = 0
            else:
                break  # last seed placed at idx
        
        last_pos = idx
        extra_turn = (last_pos == 6)
        
        # Capture
        if 0 <= last_pos <= 5 and y[last_pos] == 1:
            opp_idx = 5 - last_pos
            if o[opp_idx] > 0:
                y[6] += y[last_pos] + o[opp_idx]
                y[last_pos] = 0
                o[opp_idx] = 0
        
        # Check game end
        if all(s == 0 for s in y[:6]):
            o[6] += sum(o[:6])
            for i in range(6): o[i] = 0
        elif all(s == 0 for s in o[:6]):
            y[6] += sum(y[:6])
            for i in range(6): y[i] = 0
        
        return y, o, extra_turn
    
    def evaluate(y, o):
        score = y[6] - o[6]
        score += 0.1 * (sum(y[:6]) - sum(o[:6]))
        return score
    
    def get_legal_moves(houses):
        return [i for i in range(6) if houses[i] > 0]
    
    def order_moves(y, o):
        moves = get_legal_moves(y)
        scored = []
        for m in moves:
            seeds = y[m]
            landing = m + seeds
            priority = 0
            if landing == 6:
                priority = 100  # extra turn
            elif landing <= 5 and y[landing] == 0 and o[5 - landing] > 0:
                priority = 50 + o[5 - landing]  # capture
            scored.append((-priority, m))
        scored.sort()
        return [m for _, m in scored]
    
    def alphabeta(y, o, depth, alpha, beta, maximizing):
        if time.time() - start_time > time_limit:
            return evaluate(y, o), -1
        
        if depth == 0 or (all(s == 0 for s in y[:6]) or all(s == 0 for s in o[:6])):
            return evaluate(y, o), -1
        
        if maximizing:
            moves = order_moves(y, o)
            if not moves:
                return evaluate(y, o), -1
            best_move = moves[0]
            best_val = -1000
            for m in moves:
                ny, no, extra = simulate_move(y, o, m)
                if extra:
                    val, _ = alphabeta(ny, no, depth - 1, alpha, beta, True)
                else:
                    val, _ = alphabeta(no, ny, depth - 1, alpha, beta, False)
                if val > best_val:
                    best_val = val
                    best_move = m
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return best_val, best_move
        else:
            moves = order_moves(y, o)
            if not moves:
                return evaluate(o, y), -1
            best_move = moves[0]
            best_val = 1000
            for m in moves:
                ny, no, extra = simulate_move(y, o, m)
                if extra:
                    val, _ = alphabeta(ny, no, depth - 1, alpha, beta, False)
                else:
                    val, _ = alphabeta(no, ny, depth - 1, alpha, beta, True)
                if val < best_val:
                    best_val = val
                    best_move = m
                beta = min(beta, val)
                if alpha >= beta:
                    break
            return best_val, best_move
    
    best_move = get_legal_moves(you)[0]
    
    for depth in range(1, 40):
        if time.time() - start_time > time_limit * 0.7:
            break
        val, move = alphabeta(you, opponent, depth, -1000, 1000, True)
        if time.time() - start_time > time_limit:
            break
        if move >= 0:
            best_move = move
    
    # Safety fallback
    if you[best_move] == 0:
        for i in range(6):
            if you[i] > 0:
                best_move = i
                break
    
    return best_move
