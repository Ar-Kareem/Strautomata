
import itertools
import time

def policy(board):
    # All 49 winning lines in 3x3x3
    lines = []
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, 0), (i, j, 1), (i, j, 2)])
            lines.append([(i, 0, j), (i, 1, j), (i, 2, j)])
            lines.append([(0, i, j), (1, i, j), (2, i, j)])
    for i in range(3):
        lines.append([(i, 0, 0), (i, 1, 1), (i, 2, 2)])
        lines.append([(i, 0, 2), (i, 1, 1), (i, 2, 0)])
        lines.append([(0, i, 0), (1, i, 1), (2, i, 2)])
        lines.append([(0, i, 2), (1, i, 1), (2, i, 0)])
        lines.append([(0, 0, i), (1, 1, i), (2, 2, i)])
        lines.append([(0, 2, i), (1, 1, i), (2, 0, i)])
    lines.append([(0,0,0),(1,1,1),(2,2,2)])
    lines.append([(0,0,2),(1,1,1),(2,2,0)])
    lines.append([(0,2,0),(1,1,1),(2,0,2)])
    lines.append([(2,0,0),(1,1,1),(0,2,2)])

    def get_empty(b):
        return [(i,j,k) for i in range(3) for j in range(3) for k in range(3) if b[i][j][k]==0]

    def check_win(b, player):
        for line in lines:
            if all(b[x][y][z]==player for x,y,z in line):
                return True
        return False

    def evaluate(b):
        score = 0
        for line in lines:
            vals = [b[x][y][z] for x,y,z in line]
            s = sum(vals)
            if -1 not in [v for v in vals if v != 0] and s > 0:
                score += s * s * 10
            if 1 not in [v for v in vals if v != 0] and s < 0:
                score += s * abs(s) * 10
        return score

    def minimax(b, depth, alpha, beta, maximizing, deadline):
        if check_win(b, 1): return 10000 + depth
        if check_win(b, -1): return -10000 - depth
        empty = get_empty(b)
        if not empty or depth == 0: return evaluate(b)
        if time.time() > deadline: return evaluate(b)

        if maximizing:
            val = -float('inf')
            for move in sorted(empty, key=lambda m: abs(m[0]-1)+abs(m[1]-1)+abs(m[2]-1)):
                b[move[0]][move[1]][move[2]] = 1
                val = max(val, minimax(b, depth-1, alpha, beta, False, deadline))
                b[move[0]][move[1]][move[2]] = 0
                alpha = max(alpha, val)
                if alpha >= beta or time.time() > deadline: break
            return val
        else:
            val = float('inf')
            for move in sorted(empty, key=lambda m: abs(m[0]-1)+abs(m[1]-1)+abs(m[2]-1)):
                b[move[0]][move[1]][move[2]] = -1
                val = min(val, minimax(b, depth-1, alpha, beta, True, deadline))
                b[move[0]][move[1]][move[2]] = 0
                beta = min(beta, val)
                if alpha >= beta or time.time() > deadline: break
            return val

    import copy
    b = copy.deepcopy(board)
    empty = get_empty(b)
    if not empty: return (0,0,0)

    deadline = time.time() + 0.85
    best_move = empty[0]
    best_val = -float('inf')
    
    for depth in range(1, 27):
        if time.time() > deadline: break
        current_best = best_move
        current_val = -float('inf')
        for move in sorted(empty, key=lambda m: abs(m[0]-1)+abs(m[1]-1)+abs(m[2]-1)):
            b[move[0]][move[1]][move[2]] = 1
            val = minimax(b, depth-1, -float('inf'), float('inf'), False, deadline)
            b[move[0]][move[1]][move[2]] = 0
            if val > current_val:
                current_val = val
                current_best = move
            if time.time() > deadline: break
        if time.time() < deadline or current_val > best_val:
            best_val = current_val
            best_move = current_best
        if best_val >= 10000: break

    return best_move
