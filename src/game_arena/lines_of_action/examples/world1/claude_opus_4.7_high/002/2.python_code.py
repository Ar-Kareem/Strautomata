
import time

DIRS = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]

def policy(board):
    if hasattr(board, 'tolist'):
        b = board.tolist()
    else:
        b = [list(row) for row in board]
    b = [[int(x) for x in row] for row in b]

    start = time.time()
    TIME_LIMIT = 0.85

    def line_count(r, c, dr, dc):
        sr, sc = r, c
        while 0 <= sr - dr < 8 and 0 <= sc - dc < 8:
            sr -= dr; sc -= dc
        cnt = 0
        cr, cc = sr, sc
        while 0 <= cr < 8 and 0 <= cc < 8:
            if b[cr][cc] != 0:
                cnt += 1
            cr += dr; cc += dc
        return cnt

    def legal_moves(player):
        moves = []
        for r in range(8):
            for c in range(8):
                if b[r][c] != player: continue
                for dr, dc in DIRS:
                    n = line_count(r, c, dr, dc)
                    tr, tc = r + dr*n, c + dc*n
                    if not (0 <= tr < 8 and 0 <= tc < 8): continue
                    if b[tr][tc] == player: continue
                    blocked = False
                    for i in range(1, n):
                        if b[r+dr*i][c+dc*i] == -player:
                            blocked = True; break
                    if blocked: continue
                    moves.append((r,c,tr,tc))
        return moves

    def is_connected(player):
        pieces = []
        for r in range(8):
            for c in range(8):
                if b[r][c] == player: pieces.append((r,c))
        if len(pieces) <= 1: return True
        visited = {pieces[0]}
        stack = [pieces[0]]
        while stack:
            r,c = stack.pop()
            for dr,dc in DIRS:
                nr,nc = r+dr, c+dc
                if 0<=nr<8 and 0<=nc<8 and b[nr][nc]==player and (nr,nc) not in visited:
                    visited.add((nr,nc))
                    stack.append((nr,nc))
        return len(visited) == len(pieces)

    def count_groups(player):
        visited = set()
        groups = 0
        max_size = 0
        for r in range(8):
            for c in range(8):
                if b[r][c] == player and (r,c) not in visited:
                    groups += 1
                    stack = [(r,c)]
                    visited.add((r,c))
                    size = 0
                    while stack:
                        cr,cc = stack.pop()
                        size += 1
                        for dr,dc in DIRS:
                            nr,nc = cr+dr, cc+dc
                            if 0<=nr<8 and 0<=nc<8 and b[nr][nc]==player and (nr,nc) not in visited:
                                visited.add((nr,nc))
                                stack.append((nr,nc))
                    if size > max_size: max_size = size
        return groups, max_size

    def evaluate():
        mg, mm = count_groups(1)
        og, om = count_groups(-1)
        mc = 0; oc = 0
        m_cent = 0.0; o_cent = 0.0
        for r in range(8):
            for c in range(8):
                v = b[r][c]
                if v == 1:
                    mc += 1
                    m_cent += max(abs(r-3.5), abs(c-3.5))
                elif v == -1:
                    oc += 1
                    o_cent += max(abs(r-3.5), abs(c-3.5))
        score = 0
        score += (og - mg) * 35
        score += (mm - om) * 8
        score += (mc - oc) * 3
        score -= m_cent * 1.0
        score += o_cent * 1.0
        return score

    def apply_move(m):
        r,c,tr,tc = m
        cap = b[tr][tc]
        b[tr][tc] = b[r][c]
        b[r][c] = 0
        return cap

    def undo_move(m, cap):
        r,c,tr,tc = m
        b[r][c] = b[tr][tc]
        b[tr][tc] = cap

    timeout = [False]

    def search(depth, alpha, beta, player):
        if timeout[0]: return 0
        if time.time() - start > TIME_LIMIT:
            timeout[0] = True
            return 0
        if depth == 0:
            return evaluate()
        moves = legal_moves(player)
        if not moves:
            return -999999 if player == 1 else 999999
        moves.sort(key=lambda m: 0 if b[m[2]][m[3]] == 0 else -1)
        if player == 1:
            best = -10**9
            for m in moves:
                cap = apply_move(m)
                if is_connected(1):
                    val = 900000 + depth
                elif is_connected(-1):
                    val = -900000 - depth
                else:
                    val = search(depth-1, alpha, beta, -1)
                undo_move(m, cap)
                if timeout[0]: return 0
                if val > best: best = val
                if best > alpha: alpha = best
                if alpha >= beta: break
            return best
        else:
            best = 10**9
            for m in moves:
                cap = apply_move(m)
                if is_connected(-1):
                    val = -900000 - depth
                elif is_connected(1):
                    val = 900000 + depth
                else:
                    val = search(depth-1, alpha, beta, 1)
                undo_move(m, cap)
                if timeout[0]: return 0
                if val < best: best = val
                if best < beta: beta = best
                if alpha >= beta: break
            return best

    moves = legal_moves(1)
    if not moves:
        return "0,0:0,0"

    best_move = moves[0]
    # order root moves: captures first
    moves.sort(key=lambda m: 0 if b[m[2]][m[3]] == 0 else -1)

    for depth in range(1, 6):
        if time.time() - start > TIME_LIMIT * 0.5:
            break
        current_best = None
        current_val = -10**9
        alpha = -10**9
        beta = 10**9
        sorted_moves = list(moves)
        if best_move in sorted_moves:
            sorted_moves.remove(best_move)
            sorted_moves.insert(0, best_move)
        aborted = False
        for m in sorted_moves:
            cap = apply_move(m)
            if is_connected(1):
                val = 900000 + depth
            elif is_connected(-1):
                val = -900000 - depth
            else:
                val = search(depth-1, alpha, beta, -1)
            undo_move(m, cap)
            if timeout[0]:
                aborted = True
                break
            if val > current_val:
                current_val = val
                current_best = m
                if val > alpha: alpha = val
        if not aborted and current_best is not None:
            best_move = current_best
            if current_val > 500000:
                break

    r,c,tr,tc = best_move
    return f"{r},{c}:{tr},{tc}"
