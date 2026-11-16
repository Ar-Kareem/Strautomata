
import math
import time

WIN_SCORE = 10**9
INF = 10**18

QUAD_R0 = [0, 0, 3, 3]
QUAD_C0 = [0, 3, 0, 3]

ALL_LINES = []

# 6 horizontal lines
for r in range(6):
    ALL_LINES.append([(r, c) for c in range(6)])
# 6 vertical lines
for c in range(6):
    ALL_LINES.append([(r, c) for r in range(6)])
# diagonals of length >= 5
ALL_LINES.append([(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])
ALL_LINES.append([(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)])
ALL_LINES.append([(1, 0), (2, 1), (3, 2), (4, 3), (5, 4)])
ALL_LINES.append([(0, 5), (1, 4), (2, 3), (3, 2), (4, 1), (5, 0)])
ALL_LINES.append([(0, 4), (1, 3), (2, 2), (3, 1), (4, 0)])
ALL_LINES.append([(1, 5), (2, 4), (3, 3), (4, 2), (5, 1)])

# All contiguous windows of length 5 from each line
LINE_WINDOWS = []
for line in ALL_LINES:
    if len(line) == 5:
        LINE_WINDOWS.append(line)
    elif len(line) == 6:
        LINE_WINDOWS.append(line[:5])
        LINE_WINDOWS.append(line[1:])

CENTER_WEIGHTS = [
    [0, 1, 1, 1, 1, 0],
    [1, 3, 3, 3, 3, 1],
    [1, 3, 4, 4, 3, 1],
    [1, 3, 4, 4, 3, 1],
    [1, 3, 3, 3, 3, 1],
    [0, 1, 1, 1, 1, 0],
]

def copy_board(b):
    return [row[:] for row in b]

def make_board(you, opp):
    board = [[0] * 6 for _ in range(6)]
    for r in range(6):
        yr = you[r]
        orow = opp[r]
        brow = board[r]
        for c in range(6):
            if yr[c]:
                brow[c] = 1
            elif orow[c]:
                brow[c] = -1
    return board

def rotate_quadrant(board, quad, dirc):
    r0 = QUAD_R0[quad]
    c0 = QUAD_C0[quad]
    sub = [board[r0 + i][c0:c0 + 3] for i in range(3)]
    if dirc == 'R':
        rot = [[sub[2 - j][i] for j in range(3)] for i in range(3)]
    else:
        rot = [[sub[j][2 - i] for j in range(3)] for i in range(3)]
    for i in range(3):
        for j in range(3):
            board[r0 + i][c0 + j] = rot[i][j]

def apply_move(board, move, player):
    r, c, q, d = move
    nb = [row[:] for row in board]
    nb[r][c] = player
    rotate_quadrant(nb, q, d)
    return nb

def has_five(board, player):
    target = player
    for window in LINE_WINDOWS:
        ok = True
        for r, c in window:
            if board[r][c] != target:
                ok = False
                break
        if ok:
            return True
    return False

def terminal_value(board):
    my_win = has_five(board, 1)
    op_win = has_five(board, -1)
    if my_win and op_win:
        return 0, True
    if my_win:
        return WIN_SCORE, True
    if op_win:
        return -WIN_SCORE, True
    full = True
    for r in range(6):
        for c in range(6):
            if board[r][c] == 0:
                full = False
                break
        if not full:
            break
    if full:
        return 0, True
    return 0, False

def legal_moves(board):
    moves = []
    empties = []
    for r in range(6):
        for c in range(6):
            if board[r][c] == 0:
                empties.append((r, c))
    for r, c in empties:
        for q in range(4):
            moves.append((r, c, q, 'L'))
            moves.append((r, c, q, 'R'))
    return moves

def move_to_str(move):
    r, c, q, d = move
    return f"{r+1},{c+1},{q},{d}"

def score_window(vals):
    me = vals.count(1)
    op = vals.count(-1)
    emp = vals.count(0)
    if me > 0 and op > 0:
        return 0
    if me == 5:
        return 5000000
    if op == 5:
        return -5000000
    if me == 4 and emp == 1:
        return 50000
    if op == 4 and emp == 1:
        return -70000
    if me == 3 and emp == 2:
        return 3000
    if op == 3 and emp == 2:
        return -4000
    if me == 2 and emp == 3:
        return 200
    if op == 2 and emp == 3:
        return -250
    if me == 1 and emp == 4:
        return 10
    if op == 1 and emp == 4:
        return -12
    return 0

def heuristic(board):
    tval, term = terminal_value(board)
    if term:
        return tval

    score = 0

    # Line windows
    for window in LINE_WINDOWS:
        vals = [board[r][c] for r, c in window]
        score += score_window(vals)

    # 6-cell lines bonus
    for line in ALL_LINES:
        vals = [board[r][c] for r, c in line]
        me = vals.count(1)
        op = vals.count(-1)
        if op == 0:
            score += me * me * 8
        elif me == 0:
            score -= op * op * 10

    # Center control
    for r in range(6):
        for c in range(6):
            if board[r][c] == 1:
                score += CENTER_WEIGHTS[r][c]
            elif board[r][c] == -1:
                score -= CENTER_WEIGHTS[r][c]

    return score

def immediate_winning_moves(board, player):
    wins = []
    for mv in legal_moves(board):
        nb = apply_move(board, mv, player)
        myw = has_five(nb, player)
        opw = has_five(nb, -player)
        if myw and not opw:
            wins.append(mv)
        elif myw and opw:
            # draw move; not an outright win
            pass
    return wins

def count_opponent_immediate_wins_after(board_after_my_move):
    cnt = 0
    for mv in legal_moves(board_after_my_move):
        nb = apply_move(board_after_my_move, mv, -1)
        opw = has_five(nb, -1)
        myw = has_five(nb, 1)
        if opw and not myw:
            cnt += 1
    return cnt

def ordered_moves(board, player, limit=None):
    moves = legal_moves(board)
    scored = []

    for mv in moves:
        nb = apply_move(board, mv, player)
        tv, term = terminal_value(nb)
        if player == 1:
            if term and tv == WIN_SCORE:
                pri = 10**15
            elif term and tv == 0:
                pri = -10**6
            else:
                pri = heuristic(nb)
                if player == 1:
                    threats = count_immediate_threats(nb, player)
                    pri += 15000 * threats
        else:
            # minimizing player ordering
            if term and tv == -WIN_SCORE:
                pri = 10**15
            elif term and tv == 0:
                pri = -10**6
            else:
                pri = -heuristic(nb)
                threats = count_immediate_threats(nb, player)
                pri += 15000 * threats
        scored.append((pri, mv))

    scored.sort(reverse=True, key=lambda x: x[0])
    ordered = [mv for _, mv in scored]
    if limit is not None and len(ordered) > limit:
        ordered = ordered[:limit]
    return ordered

def count_immediate_threats(board, player):
    cnt = 0
    for mv in legal_moves(board):
        nb = apply_move(board, mv, player)
        pw = has_five(nb, player)
        ow = has_five(nb, -player)
        if pw and not ow:
            cnt += 1
    return cnt

def negamax(board, depth, alpha, beta, player, deadline):
    if time.time() >= deadline:
        return player * heuristic(board)

    tv, term = terminal_value(board)
    if term:
        return player * tv
    if depth == 0:
        return player * heuristic(board)

    # Candidate width control
    move_limit = 16 if depth >= 2 else 24
    moves = ordered_moves(board, player, limit=move_limit)
    if not moves:
        return player * heuristic(board)

    best = -INF
    for mv in moves:
        nb = apply_move(board, mv, player)
        val = -negamax(nb, depth - 1, -beta, -alpha, -player, deadline)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
        if time.time() >= deadline:
            break
    return best

def choose_move(board, deadline):
    all_moves = legal_moves(board)
    fallback = all_moves[0]

    # 1. Immediate outright win
    for mv in all_moves:
        nb = apply_move(board, mv, 1)
        myw = has_five(nb, 1)
        opw = has_five(nb, -1)
        if myw and not opw:
            return mv

    # 2. If opponent has immediate wins now, prefer moves that eliminate all of them,
    # or at least avoid loss / create draw.
    opp_now_wins = immediate_winning_moves(board, -1)
    if opp_now_wins:
        safe = []
        drawing = []
        for mv in all_moves:
            nb = apply_move(board, mv, 1)
            tv, term = terminal_value(nb)
            if term and tv == 0:
                drawing.append(mv)
                continue
            opp_wins = immediate_winning_moves(nb, -1)
            if not opp_wins:
                safe.append(mv)
        if safe:
            # choose best heuristic among safe moves
            best_mv = safe[0]
            best_sc = -INF
            for mv in safe:
                nb = apply_move(board, mv, 1)
                sc = heuristic(nb)
                if sc > best_sc:
                    best_sc = sc
                    best_mv = mv
            return best_mv
        if drawing:
            return drawing[0]

    # 3. Strong tactical filter: avoid giving immediate opponent win if possible
    safe_moves = []
    risky_moves = []
    for mv in all_moves:
        nb = apply_move(board, mv, 1)
        tv, term = terminal_value(nb)
        if term and tv == 0:
            safe_moves.append((mv, heuristic(nb) - 5000))
            continue
        opp_cnt = count_opponent_immediate_wins_after(nb)
        h = heuristic(nb) - opp_cnt * 200000
        if opp_cnt == 0:
            safe_moves.append((mv, h))
        else:
            risky_moves.append((mv, h))

    candidates = safe_moves if safe_moves else risky_moves
    candidates.sort(key=lambda x: x[1], reverse=True)
    candidate_moves = [mv for mv, _ in candidates[:18]]
    if not candidate_moves:
        candidate_moves = [fallback]

    # 4. Iterative deepening minimax
    best_move = candidate_moves[0]
    best_score = -INF

    depth = 1
    while depth <= 3 and time.time() < deadline:
        local_best_move = best_move
        local_best_score = -INF
        alpha = -INF
        beta = INF

        ordered = []
        for mv in candidate_moves:
            nb = apply_move(board, mv, 1)
            pri = heuristic(nb)
            ordered.append((pri, mv))
        ordered.sort(reverse=True, key=lambda x: x[0])

        for _, mv in ordered:
            if time.time() >= deadline:
                break
            nb = apply_move(board, mv, 1)
            val = -negamax(nb, depth - 1, -beta, -alpha, -1, deadline)
            if val > local_best_score:
                local_best_score = val
                local_best_move = mv
            if val > alpha:
                alpha = val

        if time.time() < deadline:
            best_move = local_best_move
            best_score = local_best_score
        depth += 1

    return best_move

def policy(you, opponent) -> str:
    try:
        board = make_board(you, opponent)
        deadline = time.time() + 0.92
        mv = choose_move(board, deadline)

        # Final legality guard
        r, c, q, d = mv
        if not (0 <= r < 6 and 0 <= c < 6 and 0 <= q < 4 and d in ('L', 'R')):
            raise ValueError("invalid move shape")
        if board[r][c] != 0:
            # fallback legal move
            for rr in range(6):
                for cc in range(6):
                    if board[rr][cc] == 0:
                        return f"{rr+1},{cc+1},0,L"
        return move_to_str(mv)
    except Exception:
        # Absolute fallback: first legal move found
        for r in range(6):
            for c in range(6):
                try:
                    if int(you[r][c]) == 0 and int(opponent[r][c]) == 0:
                        return f"{r+1},{c+1},0,L"
                except Exception:
                    pass
        return "1,1,0,L"
