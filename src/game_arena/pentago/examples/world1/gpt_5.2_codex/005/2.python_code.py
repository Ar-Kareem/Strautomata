
import math

# Precompute all 5-length lines on 6x6 board
LINES = []
for r in range(6):
    for c in range(2):
        LINES.append([(r, c+i) for i in range(5)])
for c in range(6):
    for r in range(2):
        LINES.append([(r+i, c) for i in range(5)])
for r in range(2):
    for c in range(2):
        LINES.append([(r+i, c+i) for i in range(5)])
for r in range(2):
    for c in range(4,6):
        LINES.append([(r+i, c-i) for i in range(5)])

WEIGHTS = [0, 1, 5, 25, 200, 10000]

def rotate_quadrant(board, r0, c0, dirc):
    # Extract
    temp = [[board[r0+i][c0+j] for j in range(3)] for i in range(3)]
    if dirc == 'R':
        for i in range(3):
            for j in range(3):
                board[r0+i][c0+j] = temp[2-j][i]
    else:  # 'L'
        for i in range(3):
            for j in range(3):
                board[r0+i][c0+j] = temp[j][2-i]

def apply_move(you, opp, r, c, quad, dirc, turn_you=True):
    # Copy boards
    nyou = [row[:] for row in you]
    nopp = [row[:] for row in opp]
    if turn_you:
        nyou[r][c] = 1
    else:
        nopp[r][c] = 1
    r0 = 0 if quad in (0,1) else 3
    c0 = 0 if quad in (0,2) else 3
    rotate_quadrant(nyou, r0, c0, dirc)
    rotate_quadrant(nopp, r0, c0, dirc)
    return nyou, nopp

def check_wins(you, opp):
    you_win = False
    opp_win = False
    for line in LINES:
        yc = 0
        oc = 0
        for r,c in line:
            yc += you[r][c]
            oc += opp[r][c]
        if yc == 5:
            you_win = True
        if oc == 5:
            opp_win = True
        if you_win and opp_win:
            break
    return you_win, opp_win

def heuristic(you, opp):
    score = 0
    for line in LINES:
        yc = 0
        oc = 0
        for r,c in line:
            yc += you[r][c]
            oc += opp[r][c]
        if oc == 0:
            score += WEIGHTS[yc]
        if yc == 0:
            score -= WEIGHTS[oc]
    return score

def generate_moves(you, opp):
    moves = []
    for r in range(6):
        for c in range(6):
            if you[r][c]==0 and opp[r][c]==0:
                for quad in range(4):
                    for dirc in ('L','R'):
                        moves.append((r,c,quad,dirc))
    return moves

def minimax(you, opp, depth, alpha, beta, turn_you):
    you_win, opp_win = check_wins(you, opp)
    if you_win and not opp_win:
        return 100000 + depth
    if opp_win and not you_win:
        return -100000 - depth
    if you_win and opp_win:
        return 0
    # check full
    full = True
    for r in range(6):
        for c in range(6):
            if you[r][c]==0 and opp[r][c]==0:
                full = False
                break
        if not full:
            break
    if full:
        return 0
    if depth == 0:
        return heuristic(you, opp)

    moves = generate_moves(you, opp)

    # Simple ordering: for us, evaluate each move quickly
    if turn_you:
        moves.sort(key=lambda m: heuristic(*apply_move(you, opp, *m, True)), reverse=True)
        best = -math.inf
        for m in moves:
            ny, no = apply_move(you, opp, *m, True)
            val = minimax(ny, no, depth-1, alpha, beta, False)
            if val > best:
                best = val
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        moves.sort(key=lambda m: heuristic(*apply_move(you, opp, *m, False)))
        best = math.inf
        for m in moves:
            ny, no = apply_move(you, opp, *m, False)
            val = minimax(ny, no, depth-1, alpha, beta, True)
            if val < best:
                best = val
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best

def policy(you, opponent) -> str:
    # Convert to lists (in case array-like)
    you = [list(row) for row in you]
    opponent = [list(row) for row in opponent]

    moves = generate_moves(you, opponent)
    best_move = moves[0]
    best_val = -math.inf

    for m in moves:
        ny, no = apply_move(you, opponent, *m, True)
        val = minimax(ny, no, 1, -math.inf, math.inf, False)
        if val > best_val:
            best_val = val
            best_move = m

    r,c,quad,dirc = best_move
    return f"{r+1},{c+1},{quad},{dirc}"
