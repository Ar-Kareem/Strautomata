
def policy(board):
    lines_set = set()
    for a in range(3):
        for b in range(3):
            lines_set.add(tuple((a,b,c) for c in range(3)))
            lines_set.add(tuple((a,c,b) for c in range(3)))
            lines_set.add(tuple((c,a,b) for c in range(3)))
    for a in range(3):
        lines_set.add(tuple((a,c,c) for c in range(3)))
        lines_set.add(tuple((a,c,2-c) for c in range(3)))
        lines_set.add(tuple((c,a,c) for c in range(3)))
        lines_set.add(tuple((c,a,2-c) for c in range(3)))
        lines_set.add(tuple((c,c,a) for c in range(3)))
        lines_set.add(tuple((c,2-c,a) for c in range(3)))
    lines_set.add(tuple((c,c,c) for c in range(3)))
    lines_set.add(tuple((c,c,2-c) for c in range(3)))
    lines_set.add(tuple((c,2-c,c) for c in range(3)))
    lines_set.add(tuple((2-c,c,c) for c in range(3)))

    line_idxs = [[p[0]*9+p[1]*3+p[2] for p in line] for line in lines_set]
    N = len(line_idxs)
    cell_to_lines = [[] for _ in range(27)]
    for li, line in enumerate(line_idxs):
        for ci in line:
            cell_to_lines[ci].append(li)

    flat = [board[i][j][k] for i in range(3) for j in range(3) for k in range(3)]
    if not any(flat):
        return (1, 1, 1)

    line_my = [0]*N
    line_opp = [0]*N
    for li, line in enumerate(line_idxs):
        for ci in line:
            if flat[ci] == 1: line_my[li] += 1
            elif flat[ci] == -1: line_opp[li] += 1

    def find_win(player):
        if player == 1:
            for li in range(N):
                if line_my[li] == 2 and line_opp[li] == 0:
                    for ci in line_idxs[li]:
                        if flat[ci] == 0: return ci
        else:
            for li in range(N):
                if line_opp[li] == 2 and line_my[li] == 0:
                    for ci in line_idxs[li]:
                        if flat[ci] == 0: return ci
        return -1

    def make_move(ci, player):
        flat[ci] = player
        if player == 1:
            for li in cell_to_lines[ci]: line_my[li] += 1
        else:
            for li in cell_to_lines[ci]: line_opp[li] += 1

    def undo_move(ci, player):
        flat[ci] = 0
        if player == 1:
            for li in cell_to_lines[ci]: line_my[li] -= 1
        else:
            for li in cell_to_lines[ci]: line_opp[li] -= 1

    def evaluate():
        s = 0
        for li in range(N):
            my = line_my[li]; opp = line_opp[li]
            if my and opp: continue
            if my == 2: s += 20
            elif my == 1: s += 1
            if opp == 2: s -= 20
            elif opp == 1: s -= 1
        return s

    def order_moves(moves, player):
        scored = []
        for ci in moves:
            s = 0
            for li in cell_to_lines[ci]:
                my = line_my[li]; opp = line_opp[li]
                if player == 1:
                    if opp == 0: s += (my+1)*(my+1)
                    if my == 0 and opp == 2: s += 100
                else:
                    if my == 0: s += (opp+1)*(opp+1)
                    if opp == 0 and my == 2: s += 100
            scored.append((-s, ci))
        scored.sort()
        return [ci for _, ci in scored]

    def negamax(depth, alpha, beta, player):
        w = find_win(player)
        if w >= 0:
            return 50000 + depth, w
        moves = [i for i in range(27) if flat[i] == 0]
        if not moves:
            return 0, -1
        if depth == 0:
            return player * evaluate(), -1
        moves = order_moves(moves, player)
        best = -10**9
        best_move = moves[0]
        for m in moves:
            make_move(m, player)
            val, _ = negamax(depth-1, -beta, -alpha, -player)
            val = -val
            undo_move(m, player)
            if val > best:
                best = val; best_move = m
            if val > alpha: alpha = val
            if alpha >= beta: break
        return best, best_move

    ec = sum(1 for v in flat if v == 0)
    if ec > 22: d = 3
    elif ec > 16: d = 4
    elif ec > 10: d = 5
    else: d = 7

    _, move = negamax(d, -10**9, 10**9, 1)
    if move < 0 or flat[move] != 0:
        for i in range(27):
            if flat[i] == 0:
                move = i; break
    return (move // 9, (move // 3) % 3, move % 3)
