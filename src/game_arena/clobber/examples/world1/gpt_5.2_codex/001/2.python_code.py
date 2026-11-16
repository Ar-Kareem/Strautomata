
import numpy as np

# Precompute board geometry
ROWS, COLS = 5, 6
N = ROWS * COLS

# Directions and deltas
DIRS = [('U', -1, 0), ('R', 0, 1), ('D', 1, 0), ('L', 0, -1)]
# For each index, store neighbor index or -1 for each direction
NEIGH = [[-1]*4 for _ in range(N)]
for r in range(ROWS):
    for c in range(COLS):
        idx = r*COLS + c
        for d,(ch,dr,dc) in enumerate(DIRS):
            nr,nc = r+dr, c+dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                NEIGH[idx][d] = nr*COLS + nc

IDX_TO_RC = [(i//COLS, i%COLS) for i in range(N)]

def flatten_board(board):
    # Supports 5x6 list of lists or flat length-30 list/array
    if len(board) == ROWS and isinstance(board[0], (list, tuple, np.ndarray)):
        flat = []
        for r in range(ROWS):
            flat.extend(board[r])
        return flat
    return list(board)

def board_to_bit(board):
    flat = flatten_board(board)
    b = 0
    for i,v in enumerate(flat):
        if v:
            b |= (1 << i)
    return b

def gen_moves(you, opp):
    moves = []
    y = you
    while y:
        lsb = y & -y
        frm = (lsb.bit_length()-1)
        y ^= lsb
        for d in range(4):
            to = NEIGH[frm][d]
            if to != -1 and (opp >> to) & 1:
                moves.append((frm, to, d))
    return moves

def apply_move(you, opp, frm, to):
    new_you = you ^ (1 << frm)
    new_you |= (1 << to)
    new_opp = opp ^ (1 << to)
    return new_you, new_opp

def mobility(you, opp):
    return len(gen_moves(you, opp))

def evaluate(you, opp):
    # Heuristic: piece diff + mobility diff
    pc_diff = you.bit_count() - opp.bit_count()
    mob_diff = mobility(you, opp) - mobility(opp, you)
    return pc_diff + 3*mob_diff

def negamax(you, opp, depth, alpha, beta, memo):
    key = (you, opp, depth)
    if key in memo:
        return memo[key]
    moves = gen_moves(you, opp)
    if not moves:
        # current player loses
        return -10000 - depth
    if depth == 0:
        return evaluate(you, opp)
    best = -10**9
    for frm,to,d in moves:
        ny,no = apply_move(you, opp, frm, to)
        score = -negamax(no, ny, depth-1, -beta, -alpha, memo)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    memo[key] = best
    return best

def policy(you: list[int], opponent: list[int]) -> str:
    you_b = board_to_bit(you)
    opp_b = board_to_bit(opponent)

    moves = gen_moves(you_b, opp_b)
    if not moves:
        # No legal move (should not be called in terminal), return a placeholder
        return "0,0,U"

    best_move = moves[0]
    best_score = -10**9
    depth = 4  # adjustable depth
    memo = {}
    # Simple move ordering: try captures that reduce opponent mobility
    def move_order(m):
        frm,to,d = m
        ny,no = apply_move(you_b, opp_b, frm, to)
        return -mobility(no, ny)
    moves.sort(key=move_order)

    alpha, beta = -10**9, 10**9
    for frm,to,d in moves:
        ny,no = apply_move(you_b, opp_b, frm, to)
        score = -negamax(no, ny, depth-1, -beta, -alpha, memo)
        if score > best_score:
            best_score = score
            best_move = (frm,to,d)
        if score > alpha:
            alpha = score

    frm,to,d = best_move
    r,c = IDX_TO_RC[frm]
    dir_char = DIRS[d][0]
    return f"{r},{c},{dir_char}"
