
import time

# Precompute board geometry
ROWS, COLS = 5, 6
N = ROWS * COLS
DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

# neighbor[index][dir] = neighbor index or -1
NEIGHBOR = [[-1]*4 for _ in range(N)]
for r in range(ROWS):
    for c in range(COLS):
        idx = r*COLS + c
        for d,(dr,dc,_) in enumerate(DIRS):
            nr, nc = r+dr, c+dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                NEIGHBOR[idx][d] = nr*COLS + nc

def to_bitboard(arr):
    # Accept list of lists or flat list or numpy array
    if hasattr(arr, 'shape'):
        # numpy
        flat = arr.reshape(-1)
        bb = 0
        for i,v in enumerate(flat):
            if int(v) == 1:
                bb |= (1<<i)
        return bb
    if len(arr) == ROWS and hasattr(arr[0], '__len__'):
        bb = 0
        for r in range(ROWS):
            for c in range(COLS):
                if arr[r][c]:
                    bb |= (1<<(r*COLS+c))
        return bb
    # flat list
    bb = 0
    for i,v in enumerate(arr):
        if v:
            bb |= (1<<i)
    return bb

def generate_moves(you, opp):
    moves = []
    y = you
    for idx in range(N):
        if (y >> idx) & 1:
            for d in range(4):
                n = NEIGHBOR[idx][d]
                if n != -1 and ((opp >> n) & 1):
                    moves.append((idx, d))
    return moves

def apply_move(you, opp, move):
    idx, d = move
    n = NEIGHBOR[idx][d]
    new_you = (you ^ (1<<idx)) | (1<<n)
    new_opp = opp ^ (1<<n)
    return new_you, new_opp

def count_moves(you, opp):
    return len(generate_moves(you, opp))

def evaluate(you, opp):
    # Material + mobility evaluation
    my_pieces = you.bit_count()
    op_pieces = opp.bit_count()
    my_moves = count_moves(you, opp)
    op_moves = count_moves(opp, you)
    return (my_moves - op_moves) * 5 + (my_pieces - op_pieces)

INF = 10**9
end_time = 0

def negamax(you, opp, depth, alpha, beta):
    global end_time
    if time.time() > end_time:
        raise TimeoutError
    moves = generate_moves(you, opp)
    if not moves:
        return -INF + 1  # losing
    if depth == 0:
        return evaluate(you, opp)

    best = -INF
    for mv in moves:
        ny, no = apply_move(you, opp, mv)
        score = -negamax(no, ny, depth-1, -beta, -alpha)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(you: list[int], opponent: list[int]) -> str:
    global end_time
    you_bb = to_bitboard(you)
    opp_bb = to_bitboard(opponent)

    moves = generate_moves(you_bb, opp_bb)
    if not moves:
        # No legal move; game should be over, but return dummy legal format
        return "0,0,U"
    if len(moves) == 1:
        idx, d = moves[0]
        r, c = divmod(idx, COLS)
        return f"{r},{c},{DIRS[d][2]}"

    best_move = moves[0]
    best_score = -INF
    start = time.time()
    end_time = start + 0.95  # time budget

    depth = 1
    while True:
        try:
            local_best = -INF
            local_move = best_move
            alpha = -INF
            beta = INF
            for mv in moves:
                ny, no = apply_move(you_bb, opp_bb, mv)
                score = -negamax(no, ny, depth-1, -beta, -alpha)
                if score > local_best:
                    local_best = score
                    local_move = mv
                if score > alpha:
                    alpha = score
            best_move = local_move
            best_score = local_best
            depth += 1
        except TimeoutError:
            break

    idx, d = best_move
    r, c = divmod(idx, COLS)
    return f"{r},{c},{DIRS[d][2]}"
