
import numpy as np

DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

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

def get_legal(me, opp):
    moves = []
    for r in range(8):
        for c in range(8):
            if me[r][c] or opp[r][c]: continue
            for dr,dc in DIRS:
                nr,nc=r+dr,c+dc
                found=False
                while 0<=nr<8 and 0<=nc<8 and opp[nr][nc]:
                    nr+=dr;nc+=dc
                    found=True
                if found and 0<=nr<8 and 0<=nc<8 and me[nr][nc]:
                    moves.append((r,c)); break
    return moves

def do_move(me, opp, r, c):
    me2=me.copy(); opp2=opp.copy()
    me2[r][c]=1
    for dr,dc in DIRS:
        nr,nc=r+dr,c+dc
        flips=[]
        while 0<=nr<8 and 0<=nc<8 and opp2[nr][nc]:
            flips.append((nr,nc)); nr+=dr;nc+=dc
        if flips and 0<=nr<8 and 0<=nc<8 and me2[nr][nc]:
            for fr,fc in flips: me2[fr][fc]=1;opp2[fr][fc]=0
    return me2,opp2

def evaluate(me, opp):
    return float(np.sum(me*WEIGHTS) - np.sum(opp*WEIGHTS))

def minimax(me, opp, depth, alpha, beta, maximizing):
    if depth==0:
        return evaluate(me,opp),None
    moves = get_legal(me,opp) if maximizing else get_legal(opp,me)
    if not moves:
        opp_moves = get_legal(opp,me) if maximizing else get_legal(me,opp)
        if not opp_moves:
            diff=float(np.sum(me)-np.sum(opp))
            return (1000 if diff>0 else -1000 if diff<0 else 0),None
        val,_=minimax(me,opp,depth-1,alpha,beta,not maximizing)
        return val,None
    best_move=moves[0]
    if maximizing:
        val=-1e9
        for r,c in moves:
            me2,opp2=do_move(me,opp,r,c)
            v,_=minimax(me2,opp2,depth-1,alpha,beta,False)
            if v>val: val=v;best_move=(r,c)
            alpha=max(alpha,v)
            if alpha>=beta: break
    else:
        val=1e9
        for r,c in moves:
            opp2,me2=do_move(opp,me,r,c)
            v,_=minimax(me2,opp2,depth-1,alpha,beta,True)
            if v<val: val=v;best_move=(r,c)
            beta=min(beta,v)
            if alpha>=beta: break
    return val,best_move

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    moves = get_legal(you, opponent)
    if not moves: return "pass"
    total = int(np.sum(you)+np.sum(opponent))
    depth = 4 if total < 52 else 8
    _,best = minimax(you,opponent,depth,-1e9,1e9,True)
    if best is None: best=moves[0]
    return chr(ord('a')+best[1])+str(best[0]+1)
