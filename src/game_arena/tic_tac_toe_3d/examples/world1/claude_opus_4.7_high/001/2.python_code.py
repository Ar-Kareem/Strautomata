
import time

def _init_lines():
    lines = []
    for i in range(3):
        for j in range(3):
            lines.append(tuple((i,j,k) for k in range(3)))
            lines.append(tuple((i,k,j) for k in range(3)))
            lines.append(tuple((k,i,j) for k in range(3)))
    for i in range(3):
        lines.append(tuple((i,k,k) for k in range(3)))
        lines.append(tuple((i,k,2-k) for k in range(3)))
        lines.append(tuple((k,i,k) for k in range(3)))
        lines.append(tuple((k,i,2-k) for k in range(3)))
        lines.append(tuple((k,k,i) for k in range(3)))
        lines.append(tuple((k,2-k,i) for k in range(3)))
    lines.append(tuple((k,k,k) for k in range(3)))
    lines.append(tuple((k,k,2-k) for k in range(3)))
    lines.append(tuple((k,2-k,k) for k in range(3)))
    lines.append(tuple((2-k,k,k) for k in range(3)))
    return lines

LINES = _init_lines()
CELL_LINES = {}
for i in range(3):
    for j in range(3):
        for k in range(3):
            CELL_LINES[(i,j,k)] = [l for l in LINES if (i,j,k) in l]

class _Timeout(Exception): pass

def _check_winner(board):
    for line in LINES:
        s = 0
        for (i,j,k) in line:
            s += board[i][j][k]
        if s == 3: return 1
        if s == -3: return -1
    return 0

def _evaluate(board):
    score = 0
    for line in LINES:
        a = b = 0
        for (i,j,k) in line:
            v = board[i][j][k]
            if v == 1: a += 1
            elif v == -1: b += 1
        if a and b: continue
        if a == 3: return 100000
        if b == 3: return -100000
        if a == 2: score += 50
        elif b == 2: score -= 60
        elif a == 1: score += 1
        elif b == 1: score -= 1
    return score

def _minimax(board, depth, alpha, beta, maximizing, deadline):
    if time.time() > deadline:
        raise _Timeout()
    w = _check_winner(board)
    if w != 0:
        return w * (100000 + depth * 100), None
    if depth == 0:
        return _evaluate(board), None
    moves = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    moves.append((i,j,k))
    if not moves:
        return 0, None
    moves.sort(key=lambda m: -len(CELL_LINES[m]))
    best_move = moves[0]
    if maximizing:
        best = -10**9
        for m in moves:
            board[m[0]][m[1]][m[2]] = 1
            val, _ = _minimax(board, depth-1, alpha, beta, False, deadline)
            board[m[0]][m[1]][m[2]] = 0
            if val > best:
                best = val; best_move = m
            if val > alpha: alpha = val
            if alpha >= beta: break
        return best, best_move
    else:
        best = 10**9
        for m in moves:
            board[m[0]][m[1]][m[2]] = -1
            val, _ = _minimax(board, depth-1, alpha, beta, True, deadline)
            board[m[0]][m[1]][m[2]] = 0
            if val < best:
                best = val; best_move = m
            if val < beta: beta = val
            if alpha >= beta: break
        return best, best_move

def policy(board):
    start = time.time()
    deadline = start + 0.85
    moves = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    moves.append((i,j,k))
    if not moves:
        return (0,0,0)
    if len(moves) == 27:
        return (1,1,1)
    # Immediate win
    for m in moves:
        board[m[0]][m[1]][m[2]] = 1
        if _check_winner(board) == 1:
            board[m[0]][m[1]][m[2]] = 0
            return m
        board[m[0]][m[1]][m[2]] = 0
    # Block immediate loss
    for m in moves:
        board[m[0]][m[1]][m[2]] = -1
        if _check_winner(board) == -1:
            board[m[0]][m[1]][m[2]] = 0
            return m
        board[m[0]][m[1]][m[2]] = 0
    moves.sort(key=lambda m: -len(CELL_LINES[m]))
    best_move = moves[0]
    for depth in [2, 3, 4, 5, 6, 7]:
        try:
            val, move = _minimax(board, depth, -10**9, 10**9, True, deadline)
            if move is not None:
                best_move = move
            if val > 50000:
                break
        except _Timeout:
            break
        if time.time() - start > 0.6:
            break
    if board[best_move[0]][best_move[1]][best_move[2]] != 0:
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:
                        return (i,j,k)
    return best_move
