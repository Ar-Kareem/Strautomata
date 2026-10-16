
_LINES = None
_CELL_LINES = None

def _init():
    global _LINES, _CELL_LINES
    lines = []
    for a in range(3):
        for b in range(3):
            lines.append(((0,a,b),(1,a,b),(2,a,b)))
            lines.append(((a,0,b),(a,1,b),(a,2,b)))
            lines.append(((a,b,0),(a,b,1),(a,b,2)))
    for a in range(3):
        lines.append(((a,0,0),(a,1,1),(a,2,2)))
        lines.append(((a,0,2),(a,1,1),(a,2,0)))
        lines.append(((0,a,0),(1,a,1),(2,a,2)))
        lines.append(((0,a,2),(1,a,1),(2,a,0)))
        lines.append(((0,0,a),(1,1,a),(2,2,a)))
        lines.append(((0,2,a),(1,1,a),(2,0,a)))
    lines.append(((0,0,0),(1,1,1),(2,2,2)))
    lines.append(((0,0,2),(1,1,1),(2,2,0)))
    lines.append(((0,2,0),(1,1,1),(2,0,2)))
    lines.append(((2,0,0),(1,1,1),(0,2,2)))
    _LINES = lines
    cl = {}
    for i in range(3):
        for j in range(3):
            for k in range(3):
                cl[(i,j,k)] = tuple(l for l in lines if (i,j,k) in l)
    _CELL_LINES = cl

def _evaluate(board):
    score = 0
    for line in _LINES:
        my = opp = 0
        for (i,j,k) in line:
            v = board[i][j][k]
            if v == 1: my += 1
            elif v == -1: opp += 1
        if my and opp:
            continue
        if my == 3: return 100000
        if opp == 3: return -100000
        if my == 2: score += 50
        elif my == 1: score += 1
        if opp == 2: score -= 50
        elif opp == 1: score -= 1
    return score

def _move_wins(board, move, player):
    for line in _CELL_LINES[move]:
        if all(board[i][j][k] == player for (i,j,k) in line):
            return True
    return False

def _get_moves(board):
    return [(i,j,k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]

def _negamax(board, depth, alpha, beta, player):
    if depth == 0:
        return _evaluate(board) * player
    moves = _get_moves(board)
    if not moves:
        return 0
    moves.sort(key=lambda m: -len(_CELL_LINES[m]))
    best = -10**9
    for m in moves:
        board[m[0]][m[1]][m[2]] = player
        if _move_wins(board, m, player):
            board[m[0]][m[1]][m[2]] = 0
            return 100000 + depth
        val = -_negamax(board, depth-1, -beta, -alpha, -player)
        board[m[0]][m[1]][m[2]] = 0
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(board):
    if _LINES is None:
        _init()
    b = [[list(board[i][j]) for j in range(3)] for i in range(3)]
    count = sum(1 for i in range(3) for j in range(3) for k in range(3) if b[i][j][k] != 0)
    if count == 0:
        return (1,1,1)
    moves = _get_moves(b)
    # Immediate win
    for m in moves:
        b[m[0]][m[1]][m[2]] = 1
        if _move_wins(b, m, 1):
            b[m[0]][m[1]][m[2]] = 0
            return m
        b[m[0]][m[1]][m[2]] = 0
    # Immediate block
    for m in moves:
        b[m[0]][m[1]][m[2]] = -1
        if _move_wins(b, m, -1):
            b[m[0]][m[1]][m[2]] = 0
            return m
        b[m[0]][m[1]][m[2]] = 0
    # Take center early if available
    if b[1][1][1] == 0 and count <= 2:
        return (1,1,1)
    remaining = 27 - count
    if remaining <= 8:
        depth = remaining
    elif remaining <= 14:
        depth = 6
    elif remaining <= 20:
        depth = 5
    else:
        depth = 4
    moves.sort(key=lambda m: -len(_CELL_LINES[m]))
    best_move = moves[0]
    best_val = -10**9
    alpha = -10**9
    beta = 10**9
    for m in moves:
        b[m[0]][m[1]][m[2]] = 1
        if _move_wins(b, m, 1):
            b[m[0]][m[1]][m[2]] = 0
            return m
        val = -_negamax(b, depth-1, -beta, -alpha, -1)
        b[m[0]][m[1]][m[2]] = 0
        if val > best_val:
            best_val = val
            best_move = m
        if val > alpha:
            alpha = val
    return best_move
