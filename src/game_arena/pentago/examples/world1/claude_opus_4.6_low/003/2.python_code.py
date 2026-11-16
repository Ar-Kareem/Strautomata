
import numpy as np
from copy import deepcopy

def policy(you, opponent) -> str:
    you = [list(r) for r in you]
    opponent = [list(r) for r in opponent]
    
    QUADS = [(0,0),(0,3),(3,0),(3,3)]
    
    def get_quad(board, q):
        r0,c0 = QUADS[q]
        return [board[r0+i][c0:c0+3] for i in range(3)]
    
    def set_quad(board, q, sub):
        r0,c0 = QUADS[q]
        for i in range(3):
            for j in range(3):
                board[r0+i][c0+j] = sub[i][j]
    
    def rotate(sub, d):
        if d == 'L':
            return [[sub[j][2-i] for j in range(3)] for i in range(3)]
        else:
            return [[sub[2-j][i] for j in range(3)] for i in range(3)]
    
    def apply_move(y, o, r, c, q, d):
        y2 = [row[:] for row in y]
        o2 = [row[:] for row in o]
        y2[r][c] = 1
        ysub = get_quad(y2, q)
        osub = get_quad(o2, q)
        set_quad(y2, q, rotate(ysub, d))
        set_quad(o2, q, rotate(osub, d))
        return y2, o2
    
    def has_five(board):
        for r in range(6):
            for c in range(6):
                if board[r][c] == 0: continue
                # right
                if c <= 1 and all(board[r][c+i] for i in range(5)): return True
                # down
                if r <= 1 and all(board[r+i][c] for i in range(5)): return True
                # diag
                if r <= 1 and c <= 1 and all(board[r+i][c+i] for i in range(5)): return True
                if r <= 1 and c >= 4 and all(board[r+i][c-i] for i in range(5)): return True
        return False
    
    def score_board(y, o):
        return count_lines(y) - 1.5 * count_lines(o)
    
    def count_lines(board):
        score = 0
        lines = []
        for r in range(6):
            for length in [5,6]:
                if length <= 6:
                    for start in range(6-length+1):
                        lines.append([(r, start+i) for i in range(length)])
        for c in range(6):
            for length in [5,6]:
                for start in range(6-length+1):
                    lines.append([(start+i, c) for i in range(length)])
        for r in range(6):
            for c in range(6):
                for dr,dc in [(1,1),(1,-1)]:
                    for length in [5]:
                        cells = [(r+i*dr, c+i*dc) for i in range(length)]
                        if all(0<=rr<6 and 0<=cc<6 for rr,cc in cells):
                            lines.append(cells)
        for line in lines:
            vals = [board[r][c] for r,c in line]
            if sum(vals) >= 2:
                score += sum(vals) ** 2
        return score
    
    empty = [(r,c) for r in range(6) for c in range(6) if you[r][c]==0 and opponent[r][c]==0]
    rotations = [(q,d) for q in range(4) for d in ['L','R']]
    
    best_move = None
    best_score = -1e9
    
    for r,c in empty:
        for q,d in rotations:
            y2, o2 = apply_move(you, opponent, r, c, q, d)
            yw = has_five(y2)
            ow = has_five(o2)
            if yw and not ow:
                return f"{r+1},{c+1},{q},{d}"
            if yw and ow:
                s = 50000
            elif ow:
                s = -100000
            else:
                s = score_board(y2, o2)
            if s > best_score:
                best_score = s
                best_move = f"{r+1},{c+1},{q},{d}"
    
    return best_move
