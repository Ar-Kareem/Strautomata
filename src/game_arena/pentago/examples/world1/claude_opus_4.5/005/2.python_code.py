
import numpy as np
from copy import deepcopy

def policy(you, opponent) -> str:
    you = np.array(you, dtype=np.int8)
    opponent = np.array(opponent, dtype=np.int8)
    
    def get_empty_cells(y, o):
        empty = []
        for r in range(6):
            for c in range(6):
                if y[r][c] == 0 and o[r][c] == 0:
                    empty.append((r, c))
        return empty
    
    def rotate_quad(board, quad, direction):
        b = board.copy()
        r_start = 0 if quad < 2 else 3
        c_start = 0 if quad % 2 == 0 else 3
        sub = b[r_start:r_start+3, c_start:c_start+3].copy()
        if direction == 'L':
            sub = np.rot90(sub, 1)
        else:
            sub = np.rot90(sub, -1)
        b[r_start:r_start+3, c_start:c_start+3] = sub
        return b
    
    def check_win(board):
        for r in range(6):
            for c in range(2):
                if np.all(board[r, c:c+5] == 1):
                    return True
        for c in range(6):
            for r in range(2):
                if np.all(board[r:r+5, c] == 1):
                    return True
        for r in range(2):
            for c in range(2):
                if all(board[r+i, c+i] == 1 for i in range(5)):
                    return True
        for r in range(2):
            for c in range(4, 6):
                if all(board[r+i, c-i] == 1 for i in range(5)):
                    return True
        return False
    
    def apply_move(y, o, r, c, quad, d):
        ny, no = y.copy(), o.copy()
        ny[r, c] = 1
        ny = rotate_quad(ny, quad, d)
        no = rotate_quad(no, quad, d)
        return ny, no
    
    def evaluate(y, o):
        def count_lines(board):
            score = 0
            weights = {2: 1, 3: 10, 4: 100, 5: 10000}
            lines = []
            for r in range(6):
                for c in range(2):
                    lines.append(board[r, c:c+5])
            for c in range(6):
                for r in range(2):
                    lines.append(board[r:r+5, c])
            for r in range(2):
                for c in range(2):
                    lines.append([board[r+i, c+i] for i in range(5)])
            for r in range(2):
                for c in range(4, 6):
                    lines.append([board[r+i, c-i] for i in range(5)])
            for line in lines:
                cnt = sum(line)
                if cnt >= 2:
                    score += weights.get(cnt, 0)
            return score
        return count_lines(y) - count_lines(o) * 1.1
    
    dirs = ['L', 'R']
    quads = [0, 1, 2, 3]
    empty = get_empty_cells(you, opponent)
    
    best_move = None
    best_score = float('-inf')
    
    # Sort empty cells by centrality
    empty.sort(key=lambda x: abs(x[0]-2.5) + abs(x[1]-2.5))
    
    for r, c in empty:
        for q in quads:
            for d in dirs:
                ny, no = apply_move(you, opponent, r, c, q, d)
                if check_win(ny):
                    return f"{r+1},{c+1},{q},{d}"
                if check_win(no):
                    continue
                score = evaluate(ny, no)
                if score > best_score:
                    best_score = score
                    best_move = (r, c, q, d)
    
    if best_move is None:
        for r, c in empty:
            for q in quads:
                for d in dirs:
                    return f"{r+1},{c+1},{q},{d}"
    
    r, c, q, d = best_move
    return f"{r+1},{c+1},{q},{d}"
