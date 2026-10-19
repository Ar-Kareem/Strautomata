
import time

DIRS = [(0,1),(1,0),(1,1),(1,-1)]
NEIGHBORS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def count_line(board, r, c, dr, dc):
    count = 1
    rr, cc = r+dr, c+dc
    while 0 <= rr < 8 and 0 <= cc < 8:
        if board[rr][cc] != 0: count += 1
        rr += dr; cc += dc
    rr, cc = r-dr, c-dc
    while 0 <= rr < 8 and 0 <= cc < 8:
        if board[rr][cc] != 0: count += 1
        rr -= dr; cc -= dc
    return count

def gen_moves(board, player):
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != player: continue
            for dr, dc in DIRS:
                n = count_line(board, r, c, dr, dc)
                for sign in (1, -1):
                    sdr, sdc = sign*dr, sign*dc
                    nr, nc = r + sdr*n, c + sdc*n
                    if not (0<=nr<8 and 0<=nc<8): continue
                    if board[nr][nc] == player: continue
                    ok = True
                    for i in range(1, n):
                        ir, ic = r + sdr*i, c + sdc*i
                        if board[ir][ic] == -player:
                            ok = False; break
                    if ok:
                        moves.append((r, c, nr, nc))
    return moves

def components_info(board, player):
    seen = [[False]*8 for _ in range(8)]
    comps = 0
    largest = 0
    total = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player and not seen[r][c]:
                comps += 1
                stack = [(r,c)]
                seen[r][c] = True
                size = 0
                while stack:
                    x, y = stack.pop()
                    size += 1
                    total += 1
                    for dx, dy in NEIGHBORS:
                        nx, ny = x+dx, y+dy
                        if 0<=nx<8 and 0<=ny<8 and board[nx][ny]==player and not seen[nx][ny]:
                            seen[nx][ny] = True
                            stack.append((nx,ny))
                if size > largest: largest = size
    return comps, largest, total

def evaluate(board, root_player):
    my_c, my_l, my_t = components_info(board, root_player)
    opp_c, opp_l, opp_t = components_info(board, -root_player)
    if my_t == 0: return -1000000
    if opp_t == 0: return 1000000
    score = (my_t - opp_t) * 15
    score += (opp_c - my_c) * 100
    score += (my_l - opp_l) * 25
    my_cent = 0; opp_cent = 0
    for r in range(8):
        for c in range(8):
            v = board[r][c]
            if v == 0: continue
            d = max(abs(r-3.5), abs(c-3.5))
            if v == root_player: my_cent += d
            else: opp_cent += d
    score += int((opp_cent - my_cent) * 3)
    return score

def make_move(board, move, player):
    r1, c1, r2, c2 = move
    cap = board[r2][c2]
    board[r1][c1] = 0
    board[r2][c2] = player
    return cap

def undo_move(board, move, player, cap):
    r1, c1, r2, c2 = move
    board[r1][c1] = player
    board[r2][c2] = cap

def alphabeta(board, depth, alpha, beta, player, root_player, deadline):
    if time.time() > deadline:
        return None, None
    moves = gen_moves(board, player)
    if not moves:
        return (-1000000 if player == root_player else 1000000), None
    # order: captures first
    moves.sort(key=lambda m: 0 if board[m[2]][m[3]] == 0 else -1)
    if depth == 0:
        return evaluate(board, root_player), None
    
    maximizing = (player == root_player)
    best_move = moves[0]
    best_score = -float('inf') if maximizing else float('inf')
    
    for mv in moves:
        cap = make_move(board, mv, player)
        my_c, _, my_t = components_info(board, root_player)
        opp_c, _, opp_t = components_info(board, -root_player)
        my_win = my_c == 1 and my_t > 0
        opp_win = opp_c == 1 and opp_t > 0
        # Mover wins ties
        if maximizing:
            if my_win: score = 1000000
            elif opp_win: score = -1000000
            else:
                res, _ = alphabeta(board, depth-1, alpha, beta, -player, root_player, deadline)
                if res is None:
                    undo_move(board, mv, player, cap); break
                score = res
        else:
            if opp_win: score = -1000000
            elif my_win: score = 1000000
            else:
                res, _ = alphabeta(board, depth-1, alpha, beta, -player, root_player, deadline)
                if res is None:
                    undo_move(board, mv, player, cap); break
                score = res
        undo_move(board, mv, player, cap)
        if maximizing:
            if score > best_score:
                best_score = score; best_move = mv
            if score > alpha: alpha = score
        else:
            if score < best_score:
                best_score = score; best_move = mv
            if score < beta: beta = score
        if beta <= alpha: break
        if time.time() > deadline: break
    return best_score, best_move

def policy(board):
    b = [[int(board[r][c]) for c in range(8)] for r in range(8)]
    deadline = time.time() + 0.75
    moves = gen_moves(b, 1)
    if not moves:
        for r in range(8):
            for c in range(8):
                if b[r][c] == 1:
                    return f"{r},{c}:{r},{c}"
        return "0,0:0,0"
    best_move = moves[0]
    for depth in range(1, 5):
        if time.time() > deadline: break
        score, mv = alphabeta(b, depth, -float('inf'), float('inf'), 1, 1, deadline)
        if mv is not None:
            best_move = mv
        if score is not None and abs(score) >= 900000:
            break
    r1, c1, r2, c2 = best_move
    return f"{r1},{c1}:{r2},{c2}"
