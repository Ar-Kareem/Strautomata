
def policy(you, opponent):
    def simulate(you, opp, move):
        y = you[:]
        o = opp[:]
        seeds = y[move]
        y[move] = 0
        pos = move + 1
        side = 0  # 0=you, 1=opp
        while seeds:
            if side == 0:
                if pos <= 5:
                    y[pos] += 1
                    seeds -= 1
                    if seeds == 0:
                        if y[pos] == 1 and o[5 - pos] > 0:
                            y[6] += 1 + o[5 - pos]
                            y[pos] = 0
                            o[5 - pos] = 0
                        return y, o, False
                    pos += 1
                elif pos == 6:
                    y[6] += 1
                    seeds -= 1
                    if seeds == 0:
                        return y, o, True
                    pos = 0
                    side = 1
                else:
                    pos = 0
                    side = 1
            else:
                if pos <= 5:
                    o[pos] += 1
                    seeds -= 1
                    if seeds == 0:
                        return y, o, False
                    pos += 1
                else:
                    pos = 0
                    side = 0
        return y, o, False

    def evaluate(y, o):
        return y[6] - o[6]

    def minimax(y, o, depth, alpha, beta, maximizing):
        if all(v == 0 for v in y[:6]):
            return y[6] - (o[6] + sum(o[:6]))
        if all(v == 0 for v in o[:6]):
            return (y[6] + sum(y[:6])) - o[6]
        if depth == 0:
            return evaluate(y, o)
        if maximizing:
            val = -100
            for m in range(6):
                if y[m] == 0:
                    continue
                ny, no, extra = simulate(y, o, m)
                if extra:
                    v = minimax(ny, no, depth - 1, alpha, beta, True)
                else:
                    v = minimax(no, ny, depth - 1, alpha, beta, False)
                if v > val:
                    val = v
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return val
        else:
            val = 100
            for m in range(6):
                if y[m] == 0:
                    continue
                ny, no, extra = simulate(y, o, m)
                if extra:
                    v = minimax(ny, no, depth - 1, alpha, beta, False)
                else:
                    v = minimax(no, ny, depth - 1, alpha, beta, True)
                if v < val:
                    val = v
                beta = min(beta, val)
                if alpha >= beta:
                    break
            return val

    best_move = -1
    best_val = -200
    for m in range(6):
        if you[m] == 0:
            continue
        ny, no, extra = simulate(you, opponent, m)
        if extra:
            v = minimax(ny, no, 9, -200, 200, True)
        else:
            v = minimax(no, ny, 9, -200, 200, False)
        if v > best_val:
            best_val = v
            best_move = m
    return best_move
