
import math

# Pentago policy
# Returns move string: "row,col,quad,dir"

LINES = []

def _init_lines():
    global LINES
    if LINES:
        return
    # horizontals length 5 and 6 windows represented as full lines for scoring/win checks
    for r in range(6):
        LINES.append([(r, c) for c in range(6)])
    for c in range(6):
        LINES.append([(r, c) for r in range(6)])
    # diagonals \
    for start_c in range(6):
        line = []
        r, c = 0, start_c
        while r < 6 and c < 6:
            line.append((r, c))
            r += 1
            c += 1
        if len(line) >= 5:
            LINES.append(line)
    for start_r in range(1, 6):
        line = []
        r, c = start_r, 0
        while r < 6 and c < 6:
            line.append((r, c))
            r += 1
            c += 1
        if len(line) >= 5:
            LINES.append(line)
    # diagonals /
    for start_c in range(6):
        line = []
        r, c = 0, start_c
        while r < 6 and c >= 0:
            line.append((r, c))
            r += 1
            c -= 1
        if len(line) >= 5:
            LINES.append(line)
    for start_r in range(1, 6):
        line = []
        r, c = start_r, 5
        while r < 6 and c >= 0:
            line.append((r, c))
            r += 1
            c -= 1
        if len(line) >= 5:
            LINES.append(line)

_init_lines()

QUAD_R0 = [0, 0, 3, 3]
QUAD_C0 = [0, 3, 0, 3]

CENTER_WEIGHTS = [
    [0, 1, 1, 1, 1, 0],
    [1, 2, 3, 3, 2, 1],
    [1, 3, 4, 4, 3, 1],
    [1, 3, 4, 4, 3, 1],
    [1, 2, 3, 3, 2, 1],
    [0, 1, 1, 1, 1, 0],
]

def copy_board(b):
    return [row[:] for row in b]

def rotate_sub(board, quad, dirc):
    r0 = QUAD_R0[quad]
    c0 = QUAD_C0[quad]
    sub = [board[r0+i][c0:c0+3] for i in range(3)]
    if dirc == 'R':
        rot = [[sub[2-j][i] for j in range(3)] for i in range(3)]
    else:
        rot = [[sub[j][2-i] for j in range(3)] for i in range(3)]
    for i in range(3):
        for j in range(3):
            board[r0+i][c0+j] = rot[i][j]

def apply_move(you, opp, move):
    r, c, q, d = move
    ny = copy_board(you)
    no = copy_board(opp)
    ny[r][c] = 1
    rotate_sub(ny, q, d)
    rotate_sub(no, q, d)
    return ny, no

def has_five(board):
    for line in LINES:
        vals = [board[r][c] for r, c in line]
        n = len(vals)
        for i in range(n - 4):
            if vals[i] and vals[i+1] and vals[i+2] and vals[i+3] and vals[i+4]:
                return True
    return False

def empties(you, opp):
    out = []
    for r in range(6):
        yr = you[r]
        orow = opp[r]
        for c in range(6):
            if yr[c] == 0 and orow[c] == 0:
                out.append((r, c))
    return out

def legal_moves(you, opp):
    es = empties(you, opp)
    moves = []
    for r, c in es:
        for q in range(4):
            moves.append((r, c, q, 'L'))
            moves.append((r, c, q, 'R'))
    return moves

def immediate_winning_moves(you, opp):
    wins = []
    for mv in legal_moves(you, opp):
        ny, no = apply_move(you, opp, mv)
        yw = has_five(ny)
        ow = has_five(no)
        if yw and not ow:
            wins.append(mv)
    return wins

def count_immediate_wins_for_player_to_move(you, opp, limit=None):
    cnt = 0
    for mv in legal_moves(you, opp):
        ny, no = apply_move(you, opp, mv)
        yw = has_five(ny)
        ow = has_five(no)
        if yw and not ow:
            cnt += 1
            if limit is not None and cnt >= limit:
                return cnt
    return cnt

def line_windows(line):
    if len(line) == 5:
        return [line]
    return [line[:5], line[1:6]]

def eval_window(window, you, opp):
    yc = 0
    oc = 0
    empty = 0
    for r, c in window:
        if you[r][c]:
            yc += 1
        elif opp[r][c]:
            oc += 1
        else:
            empty += 1
    if yc and oc:
        return 0
    if yc == 5:
        return 1000000
    if oc == 5:
        return -1000000
    if oc == 0:
        if yc == 4 and empty == 1:
            return 15000
        if yc == 3 and empty == 2:
            return 900
        if yc == 2 and empty == 3:
            return 80
        if yc == 1 and empty == 4:
            return 8
    if yc == 0:
        if oc == 4 and empty == 1:
            return -18000
        if oc == 3 and empty == 2:
            return -1100
        if oc == 2 and empty == 3:
            return -90
        if oc == 1 and empty == 4:
            return -8
    return 0

def evaluate(you, opp):
    yw = has_five(you)
    ow = has_five(opp)
    if yw and not ow:
        return 10_000_000
    if ow and not yw:
        return -10_000_000
    if yw and ow:
        return 0

    score = 0

    # positional weight
    for r in range(6):
        for c in range(6):
            if you[r][c]:
                score += CENTER_WEIGHTS[r][c] * 12
            elif opp[r][c]:
                score -= CENTER_WEIGHTS[r][c] * 12

    # line pattern scoring
    for line in LINES:
        for window in line_windows(line):
            score += eval_window(window, you, opp)

    # mobility/threat bonus: number of immediate wins available next move
    my_wins = count_immediate_wins_for_player_to_move(you, opp, limit=3)
    op_wins = count_immediate_wins_for_player_to_move(opp, you, limit=3)
    score += my_wins * 25000
    score -= op_wins * 30000

    return score

def move_to_str(mv):
    r, c, q, d = mv
    return f"{r+1},{c+1},{q},{d}"

def policy(you, opponent) -> str:
    you = [list(map(int, row)) for row in you]
    opponent = [list(map(int, row)) for row in opponent]

    moves = legal_moves(you, opponent)
    if not moves:
        return "1,1,0,L"  # should never happen per prompt

    # 1) Immediate winning move
    best_draw_win = None
    for mv in moves:
        ny, no = apply_move(you, opponent, mv)
        yw = has_five(ny)
        ow = has_five(no)
        if yw and not ow:
            return move_to_str(mv)
        if yw and ow and best_draw_win is None:
            best_draw_win = mv

    # 2) Filter for moves that do not allow opponent immediate win
    safe_moves = []
    best_safe = None
    best_safe_score = -10**18

    best_unsafe = None
    best_unsafe_score = -10**18

    for mv in moves:
        ny, no = apply_move(you, opponent, mv)
        yw = has_five(ny)
        ow = has_five(no)

        # terminal after our move
        if yw and ow:
            sc = 0
            if sc > best_unsafe_score:
                best_unsafe_score = sc
                best_unsafe = mv
            continue

        opp_can_win = False
        # opponent to move on swapped boards: no is them, ny is us
        for omv in legal_moves(no, ny):
            nny, nno = apply_move(no, ny, omv)
            opw = has_five(nny)
            myw = has_five(nno)
            if opw and not myw:
                opp_can_win = True
                break

        sc = evaluate(ny, no)

        if not opp_can_win:
            safe_moves.append(mv)
            if sc > best_safe_score:
                best_safe_score = sc
                best_safe = mv
        else:
            # prefer unsafe moves that at least maximize eval
            if sc > best_unsafe_score:
                best_unsafe_score = sc
                best_unsafe = mv

    if best_safe is not None:
        return move_to_str(best_safe)

    if best_draw_win is not None:
        return move_to_str(best_draw_win)

    if best_unsafe is not None:
        return move_to_str(best_unsafe)

    # Fallback: guaranteed legal
    return move_to_str(moves[0])
