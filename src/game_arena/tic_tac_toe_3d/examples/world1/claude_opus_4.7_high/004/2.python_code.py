
import time

def _make_data():
    lines = []
    for a in range(3):
        for b_ in range(3):
            lines.append([(a,b_,c) for c in range(3)])
            lines.append([(a,c,b_) for c in range(3)])
            lines.append([(c,a,b_) for c in range(3)])
    for a in range(3):
        lines.append([(a,c,c) for c in range(3)])
        lines.append([(a,c,2-c) for c in range(3)])
        lines.append([(c,a,c) for c in range(3)])
        lines.append([(c,a,2-c) for c in range(3)])
        lines.append([(c,c,a) for c in range(3)])
        lines.append([(c,2-c,a) for c in range(3)])
    lines.append([(c,c,c) for c in range(3)])
    lines.append([(c,c,2-c) for c in range(3)])
    lines.append([(c,2-c,c) for c in range(3)])
    lines.append([(2-c,c,c) for c in range(3)])
    line_cells = [[i*9+j*3+k for (i,j,k) in line] for line in lines]
    cell_lines = [[] for _ in range(27)]
    for li, cells in enumerate(line_cells):
        for c in cells:
            cell_lines[c].append(li)
    return line_cells, cell_lines

LINE_CELLS, CELL_LINES = _make_data()
NUM_LINES = len(LINE_CELLS)
CELL_PRIO = sorted(range(27), key=lambda c: -len(CELL_LINES[c]))
VAL = [0, 1, 25, 1000]

def search(flat, line_sum, line_cnt, depth, alpha, beta, turn, deadline):
    if time.time() > deadline:
        raise TimeoutError()
    empty = [c for c in CELL_PRIO if flat[c] == 0]
    if not empty:
        return 0, None
    if depth == 0:
        score = 0
        for li in range(NUM_LINES):
            s = line_sum[li]; cnt = line_cnt[li]
            if cnt == 0: continue
            if s == cnt: score += VAL[cnt]
            elif s == -cnt: score -= VAL[cnt]
        return score, None
    best_move = empty[0]
    if turn == 1:
        best = -10**9
        for c in empty:
            flat[c] = 1; win = False
            for li in CELL_LINES[c]:
                line_sum[li] += 1; line_cnt[li] += 1
                if line_sum[li] == 3: win = True
            if win: score = 10000 + depth
            else: score, _ = search(flat, line_sum, line_cnt, depth-1, alpha, beta, -1, deadline)
            flat[c] = 0
            for li in CELL_LINES[c]:
                line_sum[li] -= 1; line_cnt[li] -= 1
            if score > best:
                best = score; best_move = c
            if best > alpha: alpha = best
            if alpha >= beta: break
        return best, best_move
    else:
        best = 10**9
        for c in empty:
            flat[c] = -1; win = False
            for li in CELL_LINES[c]:
                line_sum[li] -= 1; line_cnt[li] += 1
                if line_sum[li] == -3: win = True
            if win: score = -(10000 + depth)
            else: score, _ = search(flat, line_sum, line_cnt, depth-1, alpha, beta, 1, deadline)
            flat[c] = 0
            for li in CELL_LINES[c]:
                line_sum[li] += 1; line_cnt[li] -= 1
            if score < best:
                best = score; best_move = c
            if best < beta: beta = best
            if alpha >= beta: break
        return best, best_move

def policy(board):
    flat = [0]*27
    for i in range(3):
        for j in range(3):
            for k in range(3):
                flat[i*9+j*3+k] = board[i][j][k]
    line_sum = [0]*NUM_LINES
    line_cnt = [0]*NUM_LINES
    for li, cells in enumerate(LINE_CELLS):
        for c in cells:
            if flat[c] != 0:
                line_sum[li] += flat[c]; line_cnt[li] += 1
    empty = [c for c in range(27) if flat[c] == 0]
    if len(empty) == 27:
        return (1,1,1)
    # Immediate win
    for c in empty:
        for li in CELL_LINES[c]:
            if line_sum[li] == 2 and line_cnt[li] == 2:
                return (c//9, (c//3)%3, c%3)
    # Forced block (only if exactly one threat)
    opp_threats = []
    for c in empty:
        for li in CELL_LINES[c]:
            if line_sum[li] == -2 and line_cnt[li] == 2:
                opp_threats.append(c); break
    if len(opp_threats) == 1:
        c = opp_threats[0]
        return (c//9, (c//3)%3, c%3)
    # Alpha-beta iterative deepening
    start = time.time()
    deadline = start + 0.85
    best_move = empty[0]
    for depth in range(2, 15):
        try:
            score, move = search(flat, line_sum, line_cnt, depth, -10**9, 10**9, 1, deadline)
            if move is not None:
                best_move = move
            if abs(score) >= 10000:
                break
        except TimeoutError:
            break
        if time.time() - start > 0.5:
            break
    return (best_move//9, (best_move//3)%3, best_move%3)
