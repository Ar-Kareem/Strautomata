
import time

DIRS8 = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
LINE_DIRS = [(0,1),(1,0),(1,1),(1,-1)]

def get_moves(board, player):
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != player: continue
            for dr, dc in LINE_DIRS:
                n = 1
                rr, cc = r+dr, c+dc
                while 0<=rr<8 and 0<=cc<8:
                    if board[rr][cc] != 0: n += 1
                    rr += dr; cc += dc
                rr, cc = r-dr, c-dc
                while 0<=rr<8 and 0<=cc<8:
                    if board[rr][cc] != 0: n += 1
                    rr -= dr; cc -= dc
                for sign in (1, -1):
                    ddr, ddc = dr*sign, dc*sign
                    tr, tc = r+ddr*n, c+ddc*n
                    if not (0<=tr<8 and 0<=tc<8): continue
                    if board[tr][tc] == player: continue
                    valid = True
                    for i in range(1, n):
                        if board[r+ddr*i][c+ddc*i] == -player:
                            valid = False; break
                    if valid:
                        moves.append((r,c,tr,tc))
    return moves

def is_connected(board, player):
    first = None
    count = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                count += 1
                if first is None:
                    first = (r,c)
    if count == 0: return False
    if count == 1: return True
    visited = [[False]*8 for _ in range(8)]
    visited[first[0]][first[1]] = True
    stack = [first]
    cnt = 1
    while stack:
        r,c = stack.pop()
        for dr,dc in DIRS8:
            rr,cc = r+dr,c+dc
            if 0<=rr<8 and 0<=cc<8 and board[rr][cc]==player and not visited[rr][cc]:
                visited[rr][cc] = True
                cnt += 1
                stack.append((rr,cc))
    return cnt == count

def count_groups(board, player):
    visited = [[False]*8 for _ in range(8)]
    groups = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player and not visited[r][c]:
                groups += 1
                stack = [(r,c)]
                visited[r][c] = True
                while stack:
                    rr, cc = stack.pop()
                    for dr, dc in DIRS8:
                        nr, nc = rr+dr, cc+dc
                        if 0<=nr<8 and 0<=nc<8 and board[nr][nc]==player and not visited[nr][nc]:
                            visited[nr][nc] = True
                            stack.append((nr,nc))
    return groups

def evaluate(board, root):
    my_p = []; opp_p = []
    for r in range(8):
        for c in range(8):
            v = board[r][c]
            if v == root: my_p.append((r,c))
            elif v == -root: opp_p.append((r,c))
    nm = len(my_p); no = len(opp_p)
    if nm == 0: return -100000
    if no == 0: return 100000
    my_g = count_groups(board, root)
    opp_g = count_groups(board, -root)
    cr = sum(p[0] for p in my_p)/nm
    cc = sum(p[1] for p in my_p)/nm
    my_c = sum((p[0]-cr)**2 + (p[1]-cc)**2 for p in my_p)
    cr = sum(p[0] for p in opp_p)/no
    cc = sum(p[1] for p in opp_p)/no
    opp_c = sum((p[0]-cr)**2 + (p[1]-cc)**2 for p in opp_p)
    return 40*(opp_g - my_g) + 0.5*(opp_c - my_c) + 12*(nm - no)

def apply_move(board, m, player):
    r,c,tr,tc = m
    cap = board[tr][tc]
    board[r][c] = 0
    board[tr][tc] = player
    return cap

def undo_move(board, m, cap, player):
    r,c,tr,tc = m
    board[r][c] = player
    board[tr][tc] = cap

class TimeOut(Exception): pass

def search(board, depth, alpha, beta, player, root, deadline):
    if time.time() > deadline:
        raise TimeOut()
    if depth == 0:
        return evaluate(board, root)
    moves = get_moves(board, player)
    if not moves:
        return evaluate(board, root)
    maxer = (player == root)
    if maxer:
        best = -1e9
        for m in moves:
            cap = apply_move(board, m, player)
            mc = is_connected(board, player)
            oc = is_connected(board, -player)
            if mc: v = 90000 + depth
            elif oc: v = -90000 - depth
            else: v = search(board, depth-1, alpha, beta, -player, root, deadline)
            undo_move(board, m, cap, player)
            if v > best: best = v
            if v > alpha: alpha = v
            if beta <= alpha: break
        return best
    else:
        best = 1e9
        for m in moves:
            cap = apply_move(board, m, player)
            mc = is_connected(board, player)
            oc = is_connected(board, -player)
            if mc: v = -90000 - depth
            elif oc: v = 90000 + depth
            else: v = search(board, depth-1, alpha, beta, -player, root, deadline)
            undo_move(board, m, cap, player)
            if v < best: best = v
            if v < beta: beta = v
            if beta <= alpha: break
        return best

def policy(board):
    b = [list(row) for row in board]
    deadline = time.time() + 0.85
    moves = get_moves(b, 1)
    if not moves:
        for r in range(8):
            for c in range(8):
                if b[r][c] == 1:
                    return f"{r},{c}:{r},{c}"
        return "0,0:0,0"
    # Immediate win
    for m in moves:
        cap = apply_move(b, m, 1)
        if is_connected(b, 1):
            undo_move(b, m, cap, 1)
            r,c,tr,tc = m
            return f"{r},{c}:{tr},{tc}"
        undo_move(b, m, cap, 1)
    # Order by shallow eval
    scored = []
    for m in moves:
        cap = apply_move(b, m, 1)
        oc = is_connected(b, -1)
        if oc:
            s = -100000
        else:
            s = evaluate(b, 1)
        undo_move(b, m, cap, 1)
        scored.append((s, m))
    scored.sort(key=lambda x: -x[0])
    moves = [m for _,m in scored]
    best_move = moves[0]
    try:
        for depth in range(2, 6):
            if time.time() > deadline: break
            current_best = moves[0]
            current_best_score = -1e9
            alpha = -1e9; beta = 1e9
            for m in moves:
                cap = apply_move(b, m, 1)
                mc = is_connected(b, 1)
                oc = is_connected(b, -1)
                if mc: v = 90000 + depth
                elif oc: v = -90000 - depth
                else: v = search(b, depth-1, alpha, beta, -1, 1, deadline)
                undo_move(b, m, cap, 1)
                if v > current_best_score:
                    current_best_score = v
                    current_best = m
                if v > alpha: alpha = v
            best_move = current_best
            if current_best in moves:
                moves = [current_best] + [m for m in moves if m != current_best]
            if current_best_score > 80000:
                break
    except TimeOut:
        pass
    r,c,tr,tc = best_move
    return f"{r},{c}:{tr},{tc}"
