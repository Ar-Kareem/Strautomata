
import numpy as np
from functools import lru_cache

def policy(board):
    b = np.array(board, dtype=np.int8)
    
    # All 49 winning lines
    lines = []
    for i in range(3):
        for j in range(3):
            lines.append([(i,j,0),(i,j,1),(i,j,2)])
            lines.append([(i,0,k) for k in range(3) for _ in [None] if True] if False else [(i,0,j),(i,1,j),(i,2,j)])
            lines.append([(0,i,j),(1,i,j),(2,i,j)])
    # Fix line generation
    lines = []
    # Lines along each axis
    for i in range(3):
        for j in range(3):
            lines.append([(i,j,0),(i,j,1),(i,j,2)])  # along k
            lines.append([(i,0,j),(i,1,j),(i,2,j)])  # along j
            lines.append([(0,i,j),(1,i,j),(2,i,j)])  # along i
    # Face diagonals
    for i in range(3):
        lines.append([(i,0,0),(i,1,1),(i,2,2)])
        lines.append([(i,0,2),(i,1,1),(i,2,0)])
        lines.append([(0,i,0),(1,i,1),(2,i,2)])
        lines.append([(0,i,2),(1,i,1),(2,i,0)])
        lines.append([(0,0,i),(1,1,i),(2,2,i)])
        lines.append([(0,2,i),(1,1,i),(2,0,i)])
    # Space diagonals
    lines.append([(0,0,0),(1,1,1),(2,2,2)])
    lines.append([(0,0,2),(1,1,1),(2,2,0)])
    lines.append([(0,2,0),(1,1,1),(2,0,2)])
    lines.append([(0,2,2),(1,1,1),(2,0,0)])

    def evaluate(b):
        score = 0
        for line in lines:
            vals = [b[p] for p in line]
            s = sum(vals)
            zeros = vals.count(0)
            if s == 3: return 10000
            if s == -3: return -10000
            if s == 2 and zeros == 1: score += 50
            elif s == -2 and zeros == 1: score -= 50
            elif s == 1 and zeros == 2: score += 5
            elif s == -1 and zeros == 2: score -= 5
        if b[1,1,1] == 1: score += 20
        elif b[1,1,1] == -1: score -= 20
        return score

    empty = list(zip(*np.where(b == 0)))
    
    def minimax(b, depth, alpha, beta, maximizing):
        e = evaluate(b)
        if abs(e) >= 10000 or depth == 0:
            return e, None
        moves = list(zip(*np.where(b == 0)))
        if not moves:
            return 0, None
        # Move ordering: center first, then by heuristic
        moves.sort(key=lambda m: -abs(sum(x-1 for x in m)))
        best_move = moves[0]
        if maximizing:
            val = -100000
            for m in moves:
                b[m] = 1
                v, _ = minimax(b, depth-1, alpha, beta, False)
                b[m] = 0
                if v > val:
                    val, best_move = v, m
                alpha = max(alpha, v)
                if beta <= alpha: break
            return val, best_move
        else:
            val = 100000
            for m in moves:
                b[m] = -1
                v, _ = minimax(b, depth-1, alpha, beta, True)
                b[m] = 0
                if v < val:
                    val, best_move = v, m
                beta = min(beta, v)
                if beta <= alpha: break
            return val, best_move

    n_empty = len(empty)
    depth = min(n_empty, 5 if n_empty > 15 else 6 if n_empty > 10 else 8 if n_empty > 6 else n_empty)
    _, move = minimax(b, depth, -100000, 100000, True)
    if move is None or b[move] != 0:
        move = empty[0]
    return tuple(int(x) for x in move)
