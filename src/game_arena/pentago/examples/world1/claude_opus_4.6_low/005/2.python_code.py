
import numpy as np

def policy(you, opponent) -> str:
    you = np.array(you, dtype=np.int8)
    opponent = np.array(opponent, dtype=np.int8)
    
    QUADS = [(0,0),(0,3),(3,0),(3,3)]
    
    def rotate(board, q, d):
        b = board.copy()
        r0,c0 = QUADS[q]
        sub = b[r0:r0+3, c0:c0+3].copy()
        if d == 'L':
            b[r0:r0+3, c0:c0+3] = np.rot90(sub, 1)
        else:
            b[r0:r0+3, c0:c0+3] = np.rot90(sub, -1)
        return b
    
    def has_five(board):
        for r in range(6):
            for c in range(6):
                if board[r][c] == 0: continue
                # right
                if c+4 < 6 and all(board[r][c+i] for i in range(5)): return True
                # down
                if r+4 < 6 and all(board[r+i][c] for i in range(5)): return True
                # diag down-right
                if r+4 < 6 and c+4 < 6 and all(board[r+i][c+i] for i in range(5)): return True
                # diag down-left
                if r+4 < 6 and c-4 >= 0 and all(board[r+i][c-i] for i in range(5)): return True
        return False
    
    def score_board(y, o):
        # count lines of various lengths for heuristic
        lines = []
        for r in range(6):
            for c in range(6):
                if c+4<6: lines.append([(r,c+i) for i in range(5)])
                if r+4<6: lines.append([(r+i,c) for i in range(5)])
                if r+4<6 and c+4<6: lines.append([(r+i,c+i) for i in range(5)])
                if r+4<6 and c-4>=0: lines.append([(r+i,c-i) for i in range(5)])
        s = 0
        for line in lines:
            yc = sum(y[r][c] for r,c in line)
            oc = sum(o[r][c] for r,c in line)
            if oc == 0 and yc > 0:
                s += 10**yc
            if yc == 0 and oc > 0:
                s -= 10**oc * 0.9
        return s
    
    empties = [(r,c) for r in range(6) for c in range(6) if you[r][c]==0 and opponent[r][c]==0]
    rotations = [(q,d) for q in range(4) for d in ['L','R']]
    
    best_move = None
    best_score = -float('inf')
    
    # First pass: find winning moves
    for r,c in empties:
        y2 = you.copy(); y2[r][c] = 1
        for q,d in rotations:
            yr = rotate(y2, q, d)
            opr = rotate(opponent, q, d)
            if has_five(yr):
                if has_five(opr):
                    # draw - still consider
                    if best_score < 0:
                        best_move = f"{r+1},{c+1},{q},{d}"
                        best_score = 0
                else:
                    return f"{r+1},{c+1},{q},{d}"
    
    # Score all moves
    for r,c in empties:
        y2 = you.copy(); y2[r][c] = 1
        for q,d in rotations:
            yr = rotate(y2, q, d)
            opr = rotate(opponent, q, d)
            if has_five(opr) and not has_five(yr):
                sc = -100000
            else:
                sc = score_board(yr, opr)
            if sc > best_score:
                best_score = sc
                best_move = f"{r+1},{c+1},{q},{d}"
    
    if best_move is None:
        r,c = empties[0]
        best_move = f"{r+1},{c+1},0,L"
    
    return best_move
