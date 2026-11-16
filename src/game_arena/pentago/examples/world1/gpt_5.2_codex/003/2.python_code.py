
import math

# Precompute all 5-length segments on a 6x6 board
SEGMENTS = []
DIRS = [(1,0),(0,1),(1,1),(1,-1)]
for r in range(6):
    for c in range(6):
        for dr, dc in DIRS:
            if 0 <= r + 4*dr < 6 and 0 <= c + 4*dc < 6:
                SEGMENTS.append([(r+i*dr, c+i*dc) for i in range(5)])

SCORES = [0, 1, 10, 50, 200, 10000]

def check_win(board, player):
    for seg in SEGMENTS:
        for r,c in seg:
            if board[r][c] != player:
                break
        else:
            return True
    return False

def evaluate(board):
    total = 0
    for seg in SEGMENTS:
        cnt = 0
        cnto = 0
        for r,c in seg:
            v = board[r][c]
            if v == 1:
                cnt += 1
            elif v == -1:
                cnto += 1
        if cnt and cnto:
            continue
        if cnt:
            total += SCORES[cnt]
        elif cnto:
            total -= SCORES[cnto]
    return total

def rotate(board, quad, dirc):
    r0 = 0 if quad < 2 else 3
    c0 = 0 if quad % 2 == 0 else 3
    sub = [[board[r0+i][c0+j] for j in range(3)] for i in range(3)]
    if dirc == 'R':
        for i in range(3):
            for j in range(3):
                board[r0+i][c0+j] = sub[2-j][i]
    else:  # 'L'
        for i in range(3):
            for j in range(3):
                board[r0+i][c0+j] = sub[j][2-i]

def apply_move(board, r, c, quad, dirc, player):
    newb = [row[:] for row in board]
    newb[r][c] = player
    rotate(newb, quad, dirc)
    return newb

def policy(you, opponent) -> str:
    board = [[you[r][c] - opponent[r][c] for c in range(6)] for r in range(6)]
    empties = [(r,c) for r in range(6) for c in range(6) if board[r][c] == 0]

    best_move = None
    best_score = -1e9
    alpha = -1e9

    for (r,c) in empties:
        for quad in range(4):
            for dirc in ('L','R'):
                b1 = apply_move(board, r, c, quad, dirc, 1)
                win_us = check_win(b1, 1)
                win_opp = check_win(b1, -1)

                if win_us and not win_opp:
                    return f"{r+1},{c+1},{quad},{dirc}"
                if win_opp and not win_us:
                    score = -100000
                elif win_us and win_opp:
                    score = 0
                else:
                    score = 1e9
                    opp_empties = [(rr,cc) for rr in range(6) for cc in range(6) if b1[rr][cc] == 0]
                    prune = False
                    for (rr,cc) in opp_empties:
                        for q2 in range(4):
                            for d2 in ('L','R'):
                                b2 = apply_move(b1, rr, cc, q2, d2, -1)
                                win_o = check_win(b2, -1)
                                win_u = check_win(b2, 1)
                                if win_o and not win_u:
                                    val = -100000
                                elif win_o and win_u:
                                    val = 0
                                elif win_u and not win_o:
                                    val = 100000
                                else:
                                    val = evaluate(b2)
                                if val < score:
                                    score = val
                                if score <= alpha:
                                    prune = True
                                    break
                            if prune:
                                break
                        if prune:
                            break

                if score > best_score:
                    best_score = score
                    best_move = (r,c,quad,dirc)
                    alpha = best_score

    if best_move is None:
        r,c = empties[0]
        return f"{r+1},{c+1},0,L"
    r,c,quad,dirc = best_move
    return f"{r+1},{c+1},{quad},{dirc}"
