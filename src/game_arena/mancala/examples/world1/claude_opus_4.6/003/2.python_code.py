
import time

def policy(you: list[int], opponent: list[int]) -> int:
    start_time = time.time()
    time_limit = 0.85
    
    def simulate(you, opp, move):
        y = list(you)
        o = list(opp)
        seeds = y[move]
        y[move] = 0
        pos = move + 1
        side = 0  # 0 = your side, 1 = opponent side
        while seeds > 0:
            if side == 0:
                if pos <= 5:
                    y[pos] += 1
                    seeds -= 1
                    last_side, last_pos = 0, pos
                    pos += 1
                elif pos == 6:
                    y[6] += 1
                    seeds -= 1
                    last_side, last_pos = 0, 6
                    pos = 0
                    side = 1
                else:
                    pos = 0
                    side = 1
            else:
                if pos <= 5:
                    o[pos] += 1
                    seeds -= 1
                    last_side, last_pos = 1, pos
                    pos += 1
                elif pos >= 6:
                    # Skip opponent store
                    pos = 0
                    side = 0
                else:
                    pos += 1
        
        extra_turn = (last_side == 0 and last_pos == 6)
        if last_side == 0 and 0 <= last_pos <= 5 and y[last_pos] == 1 and o[5 - last_pos] > 0:
            y[6] += 1 + o[5 - last_pos]
            y[last_pos] = 0
            o[5 - last_pos] = 0
        
        # Check game end
        if all(y[i] == 0 for i in range(6)):
            for i in range(6):
                o[6] += o[i]
                o[i] = 0
        elif all(o[i] == 0 for i in range(6)):
            for i in range(6):
                y[6] += y[i]
                y[i] = 0
        
        return y, o, extra_turn
    
    def evaluate(y, o):
        return (y[6] - o[6]) * 10 + sum(y[i] for i in range(6)) - sum(o[i] for i in range(6))
    
    def game_over(y, o):
        return all(y[i] == 0 for i in range(6)) or all(o[i] == 0 for i in range(6))
    
    def get_moves(y):
        return [i for i in range(6) if y[i] > 0]
    
    def minimax(y, o, depth, alpha, beta, maximizing):
        if game_over(y, o) or depth == 0:
            return evaluate(y, o), -1
        
        if time.time() - start_time > time_limit:
            return evaluate(y, o), -1
        
        moves = get_moves(y if maximizing else o)
        if not moves:
            return evaluate(y, o), -1
        
        best_move = moves[0]
        if maximizing:
            best_val = -999999
            for m in moves:
                ny, no, extra = simulate(y, o, m)
                if extra:
                    val, _ = minimax(ny, no, depth - 1, alpha, beta, True)
                else:
                    val, _ = minimax(no, ny, depth - 1, alpha, beta, False)
                if val > best_val:
                    best_val = val
                    best_move = m
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return best_val, best_move
        else:
            best_val = 999999
            for m in moves:
                no, ny, extra = simulate(o, y, m)
                if extra:
                    val, _ = minimax(ny, no, depth - 1, alpha, beta, False)
                else:
                    val, _ = minimax(no, ny, depth - 1, alpha, beta, True)
                if val < best_val:
                    best_val = val
                    best_move = m
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return best_val, best_move
    
    legal = get_moves(you)
    best_move = legal[0]
    
    for depth in range(1, 30):
        if time.time() - start_time > time_limit:
            break
        val, move = minimax(you, opponent, depth, -999999, 999999, True)
        if time.time() - start_time <= time_limit and move in legal:
            best_move = move
    
    return best_move
