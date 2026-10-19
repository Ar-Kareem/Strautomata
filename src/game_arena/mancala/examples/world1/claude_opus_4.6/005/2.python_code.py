
import time

def policy(you: list[int], opponent: list[int]) -> int:
    start_time = time.time()
    TIME_LIMIT = 0.9  # seconds, leave some margin
    
    def simulate_move(you, opp, move):
        y = list(you)
        o = list(opp)
        seeds = y[move]
        y[move] = 0
        pos = move + 1
        # Sowing: y[0..5], y[6]=store, o[0..5], skip o[6], repeat
        # Total positions in cycle: 13 (6 your houses + 1 your store + 6 opp houses)
        while seeds > 0:
            if pos <= 5:
                y[pos] += 1
                seeds -= 1
                if seeds == 0:
                    # Last seed in your house
                    if y[pos] == 1 and o[5 - pos] > 0:
                        y[6] += y[pos] + o[5 - pos]
                        y[pos] = 0
                        o[5 - pos] = 0
                    break
                pos += 1
            elif pos == 6:
                y[6] += 1
                seeds -= 1
                if seeds == 0:
                    # Extra turn
                    return y, o, True
                pos = 7
            elif pos <= 12:
                idx = pos - 7
                o[idx] += 1
                seeds -= 1
                pos += 1
            else:
                pos = 0
        
        return y, o, False
    
    def game_over(y, o):
        return all(s == 0 for s in y[:6]) or all(s == 0 for s in o[:6])
    
    def finalize(y, o):
        y = list(y); o = list(o)
        y[6] += sum(y[:6]); y[:6] = [0]*6
        o[6] += sum(o[:6]); o[:6] = [0]*6
        return y[6] - o[6]
    
    def evaluate(y, o):
        if game_over(y, o):
            return finalize(y, o)
        return (y[6] - o[6]) * 4 + (sum(y[:6]) - sum(o[:6]))
    
    def get_moves(y):
        moves = []
        for i in range(6):
            if y[i] > 0:
                moves.append(i)
        return moves
    
    def order_moves(y, o):
        moves = get_moves(y)
        scored = []
        for m in moves:
            ny, no, extra = simulate_move(y, o, m)
            s = 0
            if extra: s += 1000
            if game_over(ny, no): s += 500
            s += ny[6] - y[6]
            scored.append((-s, m))
        scored.sort()
        return [m for _, m in scored]
    
    def alphabeta(y, o, depth, alpha, beta, maximizing):
        if time.time() - start_time > TIME_LIMIT:
            raise TimeoutError
        if game_over(y, o):
            return finalize(y, o)
        if depth == 0:
            return evaluate(y, o)
        
        if maximizing:
            moves = order_moves(y, o)
            val = -10000
            for m in moves:
                ny, no, extra = simulate_move(y, o, m)
                if extra:
                    v = alphabeta(ny, no, depth - 1, alpha, beta, True)
                else:
                    v = alphabeta(no, ny, depth - 1, alpha, beta, False)
                val = max(val, v)
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return val
        else:
            moves = order_moves(y, o)
            val = 10000
            for m in moves:
                ny, no, extra = simulate_move(y, o, m)
                if extra:
                    v = alphabeta(ny, no, depth - 1, alpha, beta, False)
                else:
                    v = alphabeta(no, ny, depth - 1, alpha, beta, True)
                val = min(val, v)
                beta = min(beta, val)
                if alpha >= beta:
                    break
            return val
    
    legal = [i for i in range(6) if you[i] > 0]
    best_move = legal[0]
    
    # Quick check for extra turn moves
    for m in legal:
        if you[m] == 6 - m:
            best_move = m
            break
    
    try:
        for depth in range(1, 30):
            if time.time() - start_time > TIME_LIMIT:
                break
            best_val = -100000
            moves = order_moves(you, opponent)
            current_best = moves[0]
            for m in moves:
                ny, no, extra = simulate_move(you, opponent, m)
                if extra:
                    v = alphabeta(ny, no, depth - 1, -100000, 100000, True)
                else:
                    v = alphabeta(no, ny, depth - 1, -100000, 100000, False)
                if v > best_val:
                    best_val = v
                    current_best = m
            best_move = current_best
    except TimeoutError:
        pass
    
    return best_move
