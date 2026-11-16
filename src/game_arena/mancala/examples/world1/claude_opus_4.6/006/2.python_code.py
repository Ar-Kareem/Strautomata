
import time

def policy(you: list[int], opponent: list[int]) -> int:
    start_time = time.time()
    time_limit = 0.90  # conservative limit
    
    def simulate_move(you, opp, move):
        """Simulate a move. Returns (new_you, new_opp, extra_turn)."""
        y = list(you)
        o = list(opp)
        seeds = y[move]
        y[move] = 0
        pos = move  # current position index
        # positions: 0-5 = your houses, 6 = your store, 7-12 = opp houses (skip opp store)
        # Total cycle length = 13
        idx = move  # in the 0-12 cycle
        for _ in range(seeds):
            idx = (idx + 1) % 13
            if idx <= 5:
                y[idx] += 1
            elif idx == 6:
                y[6] += 1
            else:  # 7-12 -> opponent houses 0-5
                o[idx - 7] += 1
        
        extra_turn = False
        if idx == 6:
            extra_turn = True
        elif 0 <= idx <= 5:
            # Check capture
            if y[idx] == 1:  # was empty before (we just placed 1)
                opp_idx = 5 - idx
                if o[opp_idx] > 0:
                    y[6] += y[idx] + o[opp_idx]
                    y[idx] = 0
                    o[opp_idx] = 0
        
        return y, o, extra_turn
    
    def game_over(y, o):
        return all(s == 0 for s in y[:6]) or all(s == 0 for s in o[:6])
    
    def finalize(y, o):
        y = list(y)
        o = list(o)
        y[6] += sum(y[:6])
        o[6] += sum(o[:6])
        for i in range(6):
            y[i] = 0
            o[i] = 0
        return y, o
    
    def evaluate(y, o):
        if game_over(y, o):
            y, o = finalize(y, o)
            diff = y[6] - o[6]
            if diff > 0: return 1000 + diff
            elif diff < 0: return -1000 + diff
            else: return 0
        return (y[6] - o[6]) * 10 + sum(y[:6]) - sum(o[:6])
    
    def get_moves(y):
        moves = []
        for i in range(6):
            if y[i] > 0:
                moves.append(i)
        return moves
    
    def alphabeta(y, o, depth, alpha, beta, maximizing):
        if time.time() - start_time > time_limit:
            return evaluate(y, o)
        if game_over(y, o) or depth == 0:
            return evaluate(y, o)
        
        if maximizing:
            moves = get_moves(y)
            if not moves:
                return evaluate(y, o)
            # Order: extra turns first, then by seeds descending
            moves.sort(key=lambda m: (0 if (y[m] == 6 - m) else 1, -y[m]))
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
            moves = get_moves(y)
            if not moves:
                return evaluate(o, y)  # Note: evaluate from maximizer's perspective
            moves.sort(key=lambda m: (0 if (y[m] == 6 - m) else 1, -y[m]))
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
    
    # Prioritize extra turns immediately
    for m in legal:
        if you[m] == 6 - m:
            best_move = m
            break
    
    for depth in range(1, 40):
        if time.time() - start_time > time_limit:
            break
        best_val = -100000
        current_best = legal[0]
        # Sort moves
        sorted_moves = sorted(legal, key=lambda m: (0 if (you[m] == 6 - m) else 1, -you[m]))
        for m in sorted_moves:
            if time.time() - start_time > time_limit:
                break
            ny, no, extra = simulate_move(you, opponent, m)
            if extra:
                val = alphabeta(ny, no, depth - 1, -100000, 100000, True)
            else:
                val = alphabeta(no, ny, depth - 1, -100000, 100000, False)
            if val > best_val:
                best_val = val
                current_best = m
        if time.time() - start_time <= time_limit:
            best_move = current_best
    
    return best_move
