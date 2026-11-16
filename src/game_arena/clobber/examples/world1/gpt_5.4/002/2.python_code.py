
from typing import List, Tuple

ROWS = 5
COLS = 6
DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

# Mild center preference
CENTER_WEIGHT = [
    [0, 1, 1, 1, 1, 0],
    [1, 2, 2, 2, 2, 1],
    [1, 2, 3, 3, 2, 1],
    [1, 2, 2, 2, 2, 1],
    [0, 1, 1, 1, 1, 0],
]

WIN_SCORE = 10**9


def _to_masks(you: List[List[int]], opp: List[List[int]]) -> Tuple[int, int]:
    ym = 0
    om = 0
    bit = 1
    for r in range(ROWS):
        rowy = you[r]
        rowo = opp[r]
        for c in range(COLS):
            if rowy[c]:
                ym |= bit
            elif rowo[c]:
                om |= bit
            bit <<= 1
    return ym, om


def _idx(r: int, c: int) -> int:
    return r * COLS + c


def _bit(i: int) -> int:
    return 1 << i


def _popcount(x: int) -> int:
    return x.bit_count()


def _neighbors(i: int):
    r, c = divmod(i, COLS)
    out = []
    if r > 0:
        out.append((i - COLS, 'U'))
    if c < COLS - 1:
        out.append((i + 1, 'R'))
    if r < ROWS - 1:
        out.append((i + COLS, 'D'))
    if c > 0:
        out.append((i - 1, 'L'))
    return out


# Precompute neighbors
NEI = [_neighbors(i) for i in range(ROWS * COLS)]


def legal_moves(you_mask: int, opp_mask: int):
    moves = []
    y = you_mask
    while y:
        lsb = y & -y
        i = lsb.bit_length() - 1
        for j, d in NEI[i]:
            if (opp_mask >> j) & 1:
                moves.append((i, j, d))
        y ^= lsb
    return moves


def apply_move(you_mask: int, opp_mask: int, move):
    i, j, _ = move
    # Current player moves from i to j, capturing opponent on j.
    you_mask ^= _bit(i)
    opp_mask ^= _bit(j)
    you_mask |= _bit(j)
    # Swap sides: next player to move is previous opponent.
    return opp_mask, you_mask


def square_attack_count(pos: int, opp_mask: int) -> int:
    cnt = 0
    for j, _ in NEI[pos]:
        cnt += (opp_mask >> j) & 1
    return cnt


def mobility(you_mask: int, opp_mask: int) -> int:
    total = 0
    y = you_mask
    while y:
        lsb = y & -y
        i = lsb.bit_length() - 1
        for j, _ in NEI[i]:
            total += (opp_mask >> j) & 1
        y ^= lsb
    return total


def evaluate(you_mask: int, opp_mask: int) -> int:
    my_moves = legal_moves(you_mask, opp_mask)
    if not my_moves:
        return -WIN_SCORE
    opp_moves = legal_moves(opp_mask, you_mask)
    if not opp_moves:
        return WIN_SCORE

    my_mob = len(my_moves)
    opp_mob = len(opp_moves)

    my_pieces = _popcount(you_mask)
    opp_pieces = _popcount(opp_mask)

    score = 0
    score += 120 * (my_mob - opp_mob)
    score += 18 * (my_pieces - opp_pieces)

    # Positional and tactical local features
    y = you_mask
    while y:
        lsb = y & -y
        i = lsb.bit_length() - 1
        r, c = divmod(i, COLS)
        score += 4 * CENTER_WEIGHT[r][c]
        score += 10 * square_attack_count(i, opp_mask)
        y ^= lsb

    o = opp_mask
    while o:
        lsb = o & -o
        i = lsb.bit_length() - 1
        r, c = divmod(i, COLS)
        score -= 4 * CENTER_WEIGHT[r][c]
        score -= 10 * square_attack_count(i, you_mask)
        o ^= lsb

    return score


def move_order_key(you_mask: int, opp_mask: int, move):
    i, j, _ = move
    new_you, new_opp = apply_move(you_mask, opp_mask, move)

    # After apply_move, sides are swapped; from original perspective:
    # opponent to move has masks (new_you, new_opp)
    opp_mob_after = len(legal_moves(new_you, new_opp))
    my_mob_after = len(legal_moves(new_opp, new_you))

    rj, cj = divmod(j, COLS)
    ri, ci = divmod(i, COLS)

    val = 0
    val -= 100 * opp_mob_after
    val += 60 * my_mob_after
    val += 12 * CENTER_WEIGHT[rj][cj]
    val -= 3 * CENTER_WEIGHT[ri][ci]
    val += 15 * square_attack_count(j, new_you)  # our moved piece attacks their pieces after swap-adjusted board
    return val


TT = {}


def alphabeta(you_mask: int, opp_mask: int, depth: int, alpha: int, beta: int) -> int:
    key = (you_mask, opp_mask, depth)
    if key in TT:
        return TT[key]

    moves = legal_moves(you_mask, opp_mask)
    if not moves:
        return -WIN_SCORE + (20 - depth)

    if depth == 0:
        val = evaluate(you_mask, opp_mask)
        TT[key] = val
        return val

    moves.sort(key=lambda mv: move_order_key(you_mask, opp_mask, mv), reverse=True)

    best = -10**18
    for mv in moves:
        ny, no = apply_move(you_mask, opp_mask, mv)
        val = -alphabeta(ny, no, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    TT[key] = best
    return best


def choose_depth(you_mask: int, opp_mask: int, num_moves: int) -> int:
    total_pieces = _popcount(you_mask | opp_mask)

    if total_pieces <= 8:
        return 12
    if total_pieces <= 12:
        return 10
    if num_moves <= 4:
        return 9
    if num_moves <= 7:
        return 8
    if total_pieces <= 18:
        return 7
    return 6


def policy(you: list[list[int]], opponent: list[list[int]]) -> str:
    you_mask, opp_mask = _to_masks(you, opponent)
    moves = legal_moves(you_mask, opp_mask)

    # Safety: if somehow no legal moves, return a syntactically valid string.
    # Arena spec says legal move required; normally this case should not be queried.
    if not moves:
        return "0,0,R"

    # Strong heuristic ordering first
    moves.sort(key=lambda mv: move_order_key(you_mask, opp_mask, mv), reverse=True)

    depth = choose_depth(you_mask, opp_mask, len(moves))

    # Clear transposition table each call to control memory/time.
    global TT
    TT = {}

    best_move = moves[0]
    best_val = -10**18
    alpha = -10**18
    beta = 10**18

    for mv in moves:
        ny, no = apply_move(you_mask, opp_mask, mv)
        val = -alphabeta(ny, no, depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val

    i, _, d = best_move
    r, c = divmod(i, COLS)
    return f"{r},{c},{d}"
