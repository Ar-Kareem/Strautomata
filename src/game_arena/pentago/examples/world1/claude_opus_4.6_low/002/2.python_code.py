
import numpy as np
from copy import deepcopy

def policy(you, opponent) -> str:
    you = [list(row) for row in you]
    opponent = [list(row) for row in opponent]
    
    QUADS = [(0,0),(0,3),(3,0),(3,3)]
    
    def rotate(board, q, d):
        b = [r[:] for r in board]
        r0,c0 = QUADS[q]
        sub = [[b[r0+i][c0+j] for j in range(3)] for i in range(3)]
        if d == 'R':
            rot = [[sub[2-j][i] for j in range(3)] for i in range(3)]
        else:
            rot = [[sub[j][2-i] for j in range(3)] for i in range(3)]
        for i in range(3):
            for j in range(3):
                b[r0+i][c0+j] = rot[i][j]
        return b
    
    def check_win(b):
        for r in range(6):
            for c in range(2):
                if all(b[r][c+k] for k in range(5)): return True
        for c in range(6):
            for r in range(2):
                if all(b[r+k][c] for k in range(5)): return True
        for r in range(2):
            for c in range(2):
                if all(b[r+k][c+k] for k in range(5)): return True
        for r in range(2):
            for c in range(4,6):
                if all(b[r+k][c-k] for k in range(5)): return True
        return False
    
    def count_lines(b, ob):
        score = 0
        lines = []
        for r in range(6):
            for c in range(2):
                lines.append([(r,c+k) for k in range(5)])
        for c in range(6):
            for r in range(2):
                lines.append([(r+k,c) for k in range(5)])
        for r in range(2):
            for c in range(2):
                lines.append([(r+k,c+k) for k in range(5)])
        for r in range(2):
            for c in range(4,6):
                lines.append([(r+k,c-k) for k in range(5)])
        for line in lines:
            mine = sum(b[r][c] for r,c in line)
            theirs = sum(ob[r][c] for r,c in line)
            if theirs == 0 and mine > 0:
                score += [0,1,10,100,10000][mine]
            if mine == 0 and theirs > 0:
                score -= [0,1,10,100,10000][theirs] * 1.1
        return score
    
    empty = [(r,c) for r in range(6) for c in range(6) if you[r][c]==0 and opponent[r][c]==0]
    rotations = [(q,d) for q in range(4) for d in ['L','R']]
    
    best_move = None
    best_score = -1e18
    
    for r,c in empty:
        you[r][c] = 1
        for q,d in rotations:
            ny = rotate(you, q, d)
            no = rotate(opponent, q, d)
            my_win = check_win(ny)
            op_win = check_win(no)
            if my_win and not op_win:
                you[r][c] = 0
                return f"{r+1},{c+1},{q},{d}"
            if my_win and op_win:
                sc = 500000  # draw better than loss
            elif op_win:
                sc = -1e9
            else:
                sc = count_lines(ny, no)
            if sc > best_score:
                best_score = sc
                best_move = (r,c,q,d)
        you[r][c] = 0
    
    r,c,q,d = best_move
    return f"{r+1},{c+1},{q},{d}"
