
import math

# Precompute all length-5 segments on a 6x6 board
DIRS = [(1,0),(0,1),(1,1),(1,-1)]
SEGMENTS = []
for r in range(6):
    for c in range(6):
        for dr,dc in DIRS:
            r2 = r + 4*dr
            c2 = c + 4*dc
            if 0 <= r2 < 6 and 0 <= c2 < 6:
                SEGMENTS.append([(r+i*dr, c+i*dc) for i in range(5)])

WEIGHTS = [0, 1, 5, 25, 125, 625]

def build_board(you, opponent):
    board = [[0]*6 for _ in range(6)]
    for r in range(6):
        for c in range(6):
            if you[r][c]:
                board[r][c] = 1
            elif opponent[r][c]:
                board[r][c] = 2
    return board

def rotate(board, quad, direction):
    r0 = (quad // 2) * 3
    c0 = (quad % 2) * 3
    sub = [row[c0:c0+3] for row in board[r0:r0+3]]
    if direction == 'R':
        new = [[sub[2-j][i] for j in range(3)] for i in range(3)]
    else:  # 'L'
        new = [[sub[j][2-i] for j in range(3)] for i in range(3)]
    for i in range(3):
        for j in range(3):
            board[r0+i][c0+j] = new[i][j]

def apply_move(board, r, c, quad, direction, player):
    b = [row[:] for row in board]
    b[r][c] = player
    rotate(b, quad, direction)
    return b

def has_five(board, player):
    for r in range(6):
        for c in range(6):
            for dr,dc in DIRS:
                r2 = r + 4*dr
                c2 = c + 4*dc
                if 0 <= r2 < 6 and 0 <= c2 < 6:
                    ok = True
                    for i in range(5):
                        if board[r+i*dr][c+i*dc] != player:
                            ok = False
                            break
                    if ok:
                        return True
    return False

def heuristic(board):
    score = 0
    for seg in SEGMENTS:
        you_count = 0
        opp_count = 0
        for r,c in seg:
            v = board[r][c]
            if v == 1:
                you_count += 1
            elif v == 2:
                opp_count += 1
        if you_count and opp_count:
            continue
        if you_count:
            score += WEIGHTS[you_count]
        elif opp_count:
            score -= WEIGHTS[opp_count]
    return score

def policy(you, opponent) -> str:
    board = build_board(you, opponent)
    empty = [(r,c) for r in range(6) for c in range(6) if board[r][c] == 0]

    best_move = None
    best_score = -10**9

    for (r,c) in empty:
        for quad in range(4):
            for direction in ('L','R'):
                b = apply_move(board, r, c, quad, direction, 1)
                you_win = has_five(b, 1)
                opp_win = has_five(b, 2)
                if you_win and not opp_win:
                    return f"{r+1},{c+1},{quad},{direction}"
                if you_win and opp_win:
                    score = 0
                else:
                    worst = 10**9
                    if len(empty) == 1:
                        worst = 0  # board full after move
                    else:
                        for (r2,c2) in empty:
                            if r2 == r and c2 == c:
                                continue
                            for quad2 in range(4):
                                for direction2 in ('L','R'):
                                    b2 = apply_move(b, r2, c2, quad2, direction2, 2)
                                    y2 = has_five(b2, 1)
                                    o2 = has_five(b2, 2)
                                    if o2 and not y2:
                                        worst = -1000
                                        break
                                    elif o2 and y2:
                                        score2 = 0
                                    elif y2 and not o2:
                                        score2 = 1000
                                    else:
                                        score2 = heuristic(b2)
                                    if score2 < worst:
                                        worst = score2
                                if worst == -1000:
                                    break
                            if worst == -1000:
                                break
                    score = worst

                if score > best_score:
                    best_score = score
                    best_move = (r,c,quad,direction)

    if best_move is None:
        # fallback: first legal move
        r,c = empty[0]
        return f"{r+1},{c+1},0,L"

    r,c,quad,direction = best_move
    return f"{r+1},{c+1},{quad},{direction}"
