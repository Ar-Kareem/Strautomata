
import time
from functools import lru_cache

N = 4
FULL_MASK = (1 << 16) - 1
INF = 10**9

EXACT = 0
LOWER = 1
UPPER = 2

# Precompute row/col/diag win masks for 4-in-a-row on a 4x4 board.
WIN_MASKS = []

# Rows
for r in range(4):
    m = 0
    for c in range(4):
        m |= 1 << (4 * r + c)
    WIN_MASKS.append(m)

# Cols
for c in range(4):
    m = 0
    for r in range(4):
        m |= 1 << (4 * r + c)
    WIN_MASKS.append(m)

# Main diagonal
m = 0
for i in range(4):
    m |= 1 << (4 * i + i)
WIN_MASKS.append(m)

# Anti-diagonal
m = 0
for i in range(4):
    m |= 1 << (4 * i + (3 - i))
WIN_MASKS.append(m)

IDX_TO_RC = [(i // 4, i % 4) for i in range(16)]
BIT_TO_IDX = {1 << i: i for i in range(16)}

CELL_MASKS = [[] for _ in range(16)]
for mask in WIN_MASKS:
    bits = mask
    while bits:
        b = bits & -bits
        bits -= b
        CELL_MASKS[BIT_TO_IDX[b]].append(mask)

# Piece-square values: prefer inner 2x2, then corners, then edges.
POS_SCORES = []
for i in range(16):
    r, c = IDX_TO_RC[i]
    if 0 < r < 3 and 0 < c < 3:
        POS_SCORES.append(7)   # inner 2x2
    elif r in (0, 3) and c in (0, 3):
        POS_SCORES.append(6)   # corners
    else:
        POS_SCORES.append(3)   # edges

LOCAL_ATTACK = (0, 6, 25, 120, 0)
LOCAL_BLOCK = (0, 5, 22, 110, 0)
LINE_VALUES = (0, 4, 18, 120, 0)

ROOT_EXACT_THRESHOLD = 11


class SearchTimeout(Exception):
    pass


def has_win(bits: int) -> bool:
    for mask in WIN_MASKS:
        if bits & mask == mask:
            return True
    return False


def winning_moves_bits(player: int, opponent: int) -> int:
    occ = player | opponent
    result = 0
    for mask in WIN_MASKS:
        if opponent & mask:
            continue
        if (player & mask).bit_count() == 3:
            result |= mask & ~occ
    return result


def board_to_bits(board: list[list[int]]) -> tuple[int, int]:
    cur = 0
    opp = 0
    for r in range(4):
        row = board[r]
        for c in range(4):
            v = row[c]
            bit = 1 << (4 * r + c)
            if v == 1:
                cur |= bit
            elif v == -1:
                opp |= bit
    return cur, opp


def first_empty(board: list[list[int]]) -> tuple[int, int]:
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)


def ordered_moves(cur: int, opp: int, hint: int = 0) -> list[int]:
    occ = cur | opp
    empty = FULL_MASK ^ occ
    opp_wins_now = winning_moves_bits(opp, cur)
    moves = []

    bits = empty
    while bits:
        bit = bits & -bits
        bits -= bit
        idx = BIT_TO_IDX[bit]
        score = POS_SCORES[idx]

        if bit == hint:
            score += 1_000_000

        my2 = cur | bit

        if has_win(my2):
            score += 500_000

        if opp_wins_now & bit:
            score += 200_000

        # Reward moves that create one or more direct threats next turn.
        score += 30_000 * winning_moves_bits(my2, opp).bit_count()

        # Local line potential and blocking value.
        for mask in CELL_MASKS[idx]:
            myc = (cur & mask).bit_count()
            opc = (opp & mask).bit_count()
            if opc == 0:
                score += LOCAL_ATTACK[myc]
            elif myc == 0:
                score += LOCAL_BLOCK[opc]

        moves.append((score, bit))

    moves.sort(key=lambda x: x[0], reverse=True)
    return [bit for _, bit in moves]


@lru_cache(maxsize=300000)
def solve(cur: int, opp: int) -> int:
    """
    Exact minimax score from the perspective of side-to-move = cur.
    Larger is better for cur.
    """
    occ = cur | opp
    rem = 16 - occ.bit_count()

    if has_win(opp):
        return -10000 - rem
    if occ == FULL_MASK:
        return 0

    wins = winning_moves_bits(cur, opp)
    if wins:
        return 10000 + rem - 1

    best = -20000
    for bit in ordered_moves(cur, opp):
        score = -solve(opp, cur | bit)
        if score > best:
            best = score
    return best


def choose_exact_move(cur: int, opp: int) -> int:
    moves = ordered_moves(cur, opp)
    best_bit = moves[0]
    best_score = -20000
    for bit in moves:
        score = -solve(opp, cur | bit)
        if score > best_score:
            best_score = score
            best_bit = bit
    return best_bit


def evaluate(cur: int, opp: int) -> int:
    occ = cur | opp
    rem = 16 - occ.bit_count()

    if has_win(cur):
        return 100000 + rem
    if has_win(opp):
        return -100000 - rem

    score = 0

    my_wins = winning_moves_bits(cur, opp).bit_count()
    opp_wins = winning_moves_bits(opp, cur).bit_count()

    score += 1200 * my_wins
    score -= 1300 * opp_wins

    if my_wins >= 2:
        score += 3000
    if opp_wins >= 2:
        score -= 3200

    for mask in WIN_MASKS:
        myc = (cur & mask).bit_count()
        opc = (opp & mask).bit_count()
        if myc and opc:
            continue
        if opc == 0:
            score += LINE_VALUES[myc]
        else:
            score -= LINE_VALUES[opc]

    bits = cur
    while bits:
        b = bits & -bits
        bits -= b
        score += POS_SCORES[BIT_TO_IDX[b]]

    bits = opp
    while bits:
        b = bits & -bits
        bits -= b
        score -= POS_SCORES[BIT_TO_IDX[b]]

    return score


def negamax(cur: int, opp: int, depth: int, alpha: int, beta: int,
            deadline: float, tt: dict) -> int:
    if time.perf_counter() >= deadline:
        raise SearchTimeout

    occ = cur | opp
    rem = 16 - occ.bit_count()

    if has_win(opp):
        return -100000 - rem
    if occ == FULL_MASK:
        return 0
    if depth == 0:
        return evaluate(cur, opp)

    key = (cur, opp, depth)
    alpha_orig = alpha
    beta_orig = beta
    hint = 0

    entry = tt.get(key)
    if entry is not None:
        val, flag, move = entry
        hint = move
        if flag == EXACT:
            return val
        elif flag == LOWER:
            if val > alpha:
                alpha = val
        else:
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    best = -INF
    best_move = 0

    for bit in ordered_moves(cur, opp, hint):
        score = -negamax(opp, cur | bit, depth - 1, -beta, -alpha, deadline, tt)
        if score > best:
            best = score
            best_move = bit
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    tt[key] = (best, flag, best_move)
    return best


def search_root(cur: int, opp: int, depth: int, deadline: float,
                tt: dict, best_hint: int = 0) -> tuple[int, int]:
    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = 0

    for bit in ordered_moves(cur, opp, best_hint):
        if time.perf_counter() >= deadline:
            raise SearchTimeout
        score = -negamax(opp, cur | bit, depth - 1, -beta, -alpha, deadline, tt)
        if score > best_score:
            best_score = score
            best_move = bit
        if score > alpha:
            alpha = score

    return best_move, best_score


def policy(board: list[list[int]]) -> tuple[int, int]:
    fallback = first_empty(board)

    try:
        cur, opp = board_to_bits(board)
        occ = cur | opp
        rem = 16 - occ.bit_count()

        if rem <= 0:
            return fallback

        # Immediate win.
        my_wins = winning_moves_bits(cur, opp)
        if my_wins:
            for bit in ordered_moves(cur, opp):
                if my_wins & bit:
                    move = IDX_TO_RC[BIT_TO_IDX[bit]]
                    if board[move[0]][move[1]] == 0:
                        return move
            bit = my_wins & -my_wins
            move = IDX_TO_RC[BIT_TO_IDX[bit]]
            if board[move[0]][move[1]] == 0:
                return move

        # Mandatory block if opponent has exactly one immediate winning move.
        opp_wins = winning_moves_bits(opp, cur)
        if opp_wins and opp_wins.bit_count() == 1:
            bit = opp_wins & -opp_wins
            move = IDX_TO_RC[BIT_TO_IDX[bit]]
            if board[move[0]][move[1]] == 0:
                return move

        # Opening book: choose a strong central square.
        if rem == 16:
            if board[1][1] == 0:
                return (1, 1)
            return fallback

        # Exact play in the late game.
        if rem <= ROOT_EXACT_THRESHOLD:
            bit = choose_exact_move(cur, opp)
            move = IDX_TO_RC[BIT_TO_IDX[bit]]
            if board[move[0]][move[1]] == 0:
                return move
            return fallback

        # Earlier game: iterative-deepening alpha-beta.
        deadline = time.perf_counter() + 0.90
        tt = {}

        moves = ordered_moves(cur, opp)
        best_bit = moves[0]
        best_hint = best_bit

        max_depth = min(8, rem)

        for depth in range(1, max_depth + 1):
            try:
                bit, score = search_root(cur, opp, depth, deadline, tt, best_hint)
                best_bit = bit
                best_hint = bit
                if abs(score) >= 90000:
                    break
            except SearchTimeout:
                break

        move = IDX_TO_RC[BIT_TO_IDX[best_bit]]
        if board[move[0]][move[1]] == 0:
            return move
        return fallback

    except Exception:
        return fallback
