
def _build_lines():
    lines = []
    for a in range(3):
        for b in range(3):
            lines.append([(a,b,c) for c in range(3)])
            lines.append([(a,c,b) for c in range(3)])
            lines.append([(c,a,b) for c in range(3)])
    for i in range(3):
        lines.append([(i,c,c) for c in range(3)])
        lines.append([(i,c,2-c) for c in range(3)])
        lines.append([(c,i,c) for c in range(3)])
        lines.append([(c,i,2-c) for c in range(3)])
        lines.append([(c,c,i) for c in range(3)])
        lines.append([(c,2-c,i) for c in range(3)])
    lines.append([(c,c,c) for c in range(3)])
    lines.append([(c,c,2-c) for c in range(3)])
    lines.append([(c,2-c,c) for c in range(3)])
    lines.append([(2-c,c,c) for c in range(3)])
    return lines

LINES = _build_lines()
CELL_WEIGHTS = {}
for line in LINES:
    for cell in line:
        CELL_WEIGHTS[cell] = CELL_WEIGHTS.get(cell, 0) + 1

def _check_win(b, p):
    for line in LINES:
        if (b[line[0][0]][line[0][1]][line[0][2]] == p and
            b[line[1][0]][line[1][1]][line[1][2]] == p and
            b[line[2][0]][line[2][1]][line[2][2]] == p):
            return True
    return False

def _evaluate(b):
    score = 0
    for line in LINES:
        v0 = b[line[0][0]][line[0][1]][line[0][2]]
        v1 = b[line[1][0]][line[1][1]][line[1][2]]
        v2 = b[line[2][0]][line[2][1]][line[2][2]]
        s = v0 + v1 + v2
        has_me = v0 == 1 or v1 == 1 or v2 == 1
        has_opp = v0 == -1 or v1 == -1 or v2 == -1
        if has_me and has_opp:
            continue
        if s == 3: return 100000
        if s == -3: return -100000
        if s == 2: score += 50
        elif s == -2: score -= 60
        elif s == 1: score += 5
        elif s == -1: score -= 5
    return score

def _minimax(b, depth, alpha, beta, maximizing):
    score = _evaluate(b)
    if score >= 100000 or score <= -100000 or depth == 0:
        return score
    moves = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if b[i][j][k] == 0:
                    moves.append((i,j,k))
    if not moves:
        return score
    moves.sort(key=lambda m: -CELL_WEIGHTS[m])
    if maximizing:
        best = -10**9
        for i,j,k in moves:
            b[i][j][k] = 1
            val = _minimax(b, depth-1, alpha, beta, False)
            b[i][j][k] = 0
            if val > best: best = val
            if val > alpha: alpha = val
            if beta <= alpha: break
        return best
    else:
        best = 10**9
        for i,j,k in moves:
            b[i][j][k] = -1
            val = _minimax(b, depth-1, alpha, beta, True)
            b[i][j][k] = 0
            if val < best: best = val
            if val < beta: beta = val
            if beta <= alpha: break
        return best

def policy(board):
    b = [[[board[i][j][k] for k in range(3)] for j in range(3)] for i in range(3)]
    moves = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if b[i][j][k] == 0:
                    moves.append((i,j,k))
    if not moves:
        return (0,0,0)
    # Immediate win
    for i,j,k in moves:
        b[i][j][k] = 1
        if _check_win(b, 1):
            b[i][j][k] = 0
            return (i,j,k)
        b[i][j][k] = 0
    # Block
    for i,j,k in moves:
        b[i][j][k] = -1
        if _check_win(b, -1):
            b[i][j][k] = 0
            return (i,j,k)
        b[i][j][k] = 0
    # Center
    if b[1][1][1] == 0:
        return (1,1,1)
    n = len(moves)
    if n >= 22: depth = 3
    elif n >= 16: depth = 4
    elif n >= 10: depth = 5
    else: depth = 7
    moves.sort(key=lambda m: -CELL_WEIGHTS[m])
    best_val = -10**9
    best_move = moves[0]
    alpha = -10**9
    beta = 10**9
    for i,j,k in moves:
        b[i][j][k] = 1
        val = _minimax(b, depth-1, alpha, beta, False)
        b[i][j][k] = 0
        if val > best_val:
            best_val = val
            best_move = (i,j,k)
            if val > alpha: alpha = val
    return best_move
