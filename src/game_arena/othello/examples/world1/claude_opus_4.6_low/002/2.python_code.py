
import numpy as np

DIRECTIONS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

WEIGHTS = np.array([
    [100,-20,10, 5, 5,10,-20,100],
    [-20,-50,-2,-2,-2,-2,-50,-20],
    [ 10, -2, 1, 1, 1, 1, -2, 10],
    [  5, -2, 1, 0, 0, 1, -2,  5],
    [  5, -2, 1, 0, 0, 1, -2,  5],
    [ 10, -2, 1, 1, 1, 1, -2, 10],
    [-20,-50,-2,-2,-2,-2,-50,-20],
    [100,-20,10, 5, 5,10,-20,100],
])

def get_legal_moves(me, opp):
    moves = []
    for r in range(8):
        for c in range(8):
            if me[r][c] or opp[r][c]:
                continue
            if is_valid(me, opp, r, c):
                moves.append((r, c))
    return moves

def is_valid(me, opp, r, c):
    for dr, dc in DIRECTIONS:
        nr, nc = r+dr, c+dc
        found = False
        while 0<=nr<8 and 0<=nc<8 and opp[nr][nc]:
            nr+=dr; nc+=dc; found=True
        if found and 0<=nr<8 and 0<=nc<8 and me[nr][nc]:
            return True
    return False

def do_move(me, opp, r, c):
    me2=me.copy(); opp2=opp.copy()
    me2[r][c]=1
    for dr,dc in DIRECTIONS:
        nr,nc=r+dr,c+dc
        flip=[]
        while 0<=nr<8 and 0<=nc<8 and opp2[nr][nc]:
            flip.append((nr,nc)); nr+=dr; nc+=dc
        if flip and 0<=nr<8 and 0<=nc<8 and me2[nr][nc]:
            for fr,fc in flip:
                me2[fr][fc]=1; opp2[fr][fc]=0
    return me2, opp2

def evaluate(me, opp):
    total = np.sum(me) + np.sum(opp)
    if total > 55:
        return np.sum(me) - np.sum(opp)
    score = np.sum(WEIGHTS * me) - np.sum(WEIGHTS * opp)
    my_moves = len(get_legal_moves(me, opp))
    opp_moves = len(get_legal_moves(opp, me))
    score += 5 * (my_moves - opp_moves)
    return score

def minimax(me, opp, depth, alpha, beta, maximizing):
    if depth == 0:
        return evaluate(me, opp), None
    moves = get_legal_moves(me, opp) if maximizing else get_legal_moves(opp, me)
    if not moves:
        # pass
        other_moves = get_legal_moves(opp, me) if maximizing else get_legal_moves(me, opp)
        if not other_moves:
            diff = np.sum(me) - np.sum(opp)
            return (1000 if diff>0 else -1000 if diff<0 else 0), None
        val, _ = minimax(me, opp, depth-1, alpha, beta, not maximizing)
        return val, None
    best_move = moves[0]
    if maximizing:
        val = -9999
        for move in moves:
            me2, opp2 = do_move(me, opp, *move)
            v, _ = minimax(me2, opp2, depth-1, alpha, beta, False)
            if v > val:
                val = v; best_move = move
            alpha = max(alpha, v)
            if alpha >= beta: break
        return val, best_move
    else:
        val = 9999
        for move in moves:
            opp2, me2 = do_move(opp, me, *move)
            v, _ = minimax(me2, opp2, depth-1, alpha, beta, True)
            if v < val:
                val = v; best_move = move
            beta = min(beta, v)
            if alpha >= beta: break
        return val, best_move

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    moves = get_legal_moves(you, opponent)
    if not moves:
        return "pass"
    total = np.sum(you) + np.sum(opponent)
    depth = 4 if total < 52 else 8
    _, best = minimax(you, opponent, depth, -99999, 99999, True)
    if best is None:
        best = moves[0]
    r, c = best
    return chr(ord('a')+c) + str(r+1)
