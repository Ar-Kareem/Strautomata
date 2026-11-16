
def policy(you, opponent):
    def simulate(you, opp, move):
        y = you[:]
        o = opp[:]
        seeds = y[move]
        y[move] = 0
        pos = move + 1
        side = 0  # 0=your side, 1=opp side
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
        if depth == 0:
            return evaluate(y, o)
        if maximizing:
            moves = [i for i in range(6) if y[i] > 0]
            if not moves:
                return y[6] + sum(y[:6]) - (o[6] + sum(o[:6]))
            val = -100
            for m in moves:
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
            moves = [i for i in range(6) if y[i] > 0]
            if not moves:
                return -(y[6] + sum(y[:6])) + (o[6] + sum(o[:6]))
            val = 100
            for m in moves:
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

    legal = [i for i in range(6) if you[i] > 0]
    best_move = legal[0]
    best_val = -200
    for depth in [8, 10, 12]:
        bm = legal[0]
        bv = -200
        for m in legal:
            ny, no, extra = simulate(you, opponent, m)
            if extra:
                v = minimax(ny, no, depth - 1, -200, 200, True)
            else:
                v = minimax(no, ny, depth - 1, -200, 200, False)
            if v > bv:
                bv = v
                bm = m
        best_move = bm
        best_val = bv
    return best_move
