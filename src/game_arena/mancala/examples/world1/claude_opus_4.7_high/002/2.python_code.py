
import time

def policy(you, opponent):
    my0 = list(you[:6])
    ms0 = you[6]
    op0 = list(opponent[:6])
    os0 = opponent[6]
    
    start = time.time()
    time_limit = 0.75

    def make_move(my, ms, op, os, move):
        my = list(my); op = list(op)
        seeds = my[move]
        my[move] = 0
        pos = move
        while seeds > 0:
            pos = (pos + 1) % 13
            if pos < 6:
                my[pos] += 1
            elif pos == 6:
                ms += 1
            else:
                op[pos - 7] += 1
            seeds -= 1
        extra = (pos == 6)
        if (not extra) and pos < 6 and my[pos] == 1 and op[5 - pos] > 0:
            ms += 1 + op[5 - pos]
            my[pos] = 0
            op[5 - pos] = 0
        return my, ms, op, os, extra

    def search(my, ms, op, os, depth, alpha, beta):
        sm = sum(my); so = sum(op)
        if sm == 0 or so == 0:
            return (ms + sm) - (os + so)
        if depth <= 0:
            return (ms - os)
        
        if time.time() - start > time_limit:
            raise TimeoutError
        
        best = -10**9
        moved = False
        for m in range(5, -1, -1):
            if my[m] == 0: 
                continue
            moved = True
            nm, nms, no, nos, extra = make_move(my, ms, op, os, m)
            if extra:
                val = search(nm, nms, no, nos, depth - 1, alpha, beta)
            else:
                val = -search(no, nos, nm, nms, depth - 1, -beta, -alpha)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        if not moved:
            return (ms + sm) - (os + so)
        return best

    # find a fallback legal move
    best_move = 0
    for i in range(6):
        if my0[i] > 0:
            best_move = i
            break

    # Iterative deepening
    try:
        for depth in range(2, 30):
            if time.time() - start > time_limit * 0.5:
                break
            current_best = best_move
            current_val = -10**9
            alpha = -10**9
            beta = 10**9
            # try previous best first for better pruning
            order = [best_move] + [m for m in range(5, -1, -1) if m != best_move]
            for m in order:
                if my0[m] == 0:
                    continue
                nm, nms, no, nos, extra = make_move(my0, ms0, op0, os0, m)
                if extra:
                    val = search(nm, nms, no, nos, depth - 1, alpha, beta)
                else:
                    val = -search(no, nos, nm, nms, depth - 1, -beta, -alpha)
                if val > current_val:
                    current_val = val
                    current_best = m
                if current_val > alpha:
                    alpha = current_val
            best_move = current_best
    except TimeoutError:
        pass
    except Exception:
        pass
    
    # Safety check
    if my0[best_move] == 0:
        for i in range(6):
            if my0[i] > 0:
                best_move = i
                break
    
    return best_move
