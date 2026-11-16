
import time
from typing import List, Tuple, Dict, Optional

# Connect-4 bitboard engine (7x6) using 7 bits per column (6 playable + 1 sentinel)
WIDTH = 7
HEIGHT = 6
H1 = HEIGHT + 1  # 7

# Precompute masks
BOTTOM_MASK = [1 << (c * H1) for c in range(WIDTH)]
TOP_PLAYABLE_MASK = [1 << (c * H1 + (HEIGHT - 1)) for c in range(WIDTH)]  # row 5 (0-based from bottom)
COLUMN_MASK = [((1 << H1) - 1) << (c * H1) for c in range(WIDTH)]  # includes sentinel bit

# Center column playable cells mask (col 3, rows 0..5)
CENTER_COL = 3
CENTER_MASK = sum(1 << (CENTER_COL * H1 + r) for r in range(HEIGHT))

# Move ordering: center first (strong heuristic in Connect-4)
MOVE_ORDER = (3, 4, 2, 5, 1, 6, 0)

WIN_SCORE = 1_000_000
INF = 10**18

# Precompute all 4-in-a-row window masks over playable cells
WINDOWS = []
def _bit_at(r_from_bottom: int, c: int) -> int:
    return 1 << (c * H1 + r_from_bottom)

def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < HEIGHT and 0 <= c < WIDTH

for r in range(HEIGHT):
    for c in range(WIDTH):
        for dr, dc in ((1, 0), (0, 1), (1, 1), (1, -1)):
            rr = r + 3 * dr
            cc = c + 3 * dc
            if _in_bounds(rr, cc):
                m = 0
                for k in range(4):
                    m |= _bit_at(r + k * dr, c + k * dc)
                WINDOWS.append(m)

# Transposition entry: (depth, value, flag, best_col)
# flag: 0 exact, -1 upperbound, +1 lowerbound
TT: Dict[int, Tuple[int, int, int, int]] = {}

def _pack_key(curr: int, opp: int) -> int:
    # 49 bits per bitboard is enough; pack into a single python int
    return curr | (opp << 49)

def _is_win(pos: int) -> bool:
    # Check alignments using bit shifts on the 7-bit-per-column representation
    # Vertical
    m = pos & (pos >> 1)
    if m & (m >> 2):
        return True
    # Horizontal
    m = pos & (pos >> H1)
    if m & (m >> (2 * H1)):
        return True
    # Diagonal /
    d = H1 - 1  # 6
    m = pos & (pos >> d)
    if m & (m >> (2 * d)):
        return True
    # Diagonal \
    d = H1 + 1  # 8
    m = pos & (pos >> d)
    if m & (m >> (2 * d)):
        return True
    return False

def _is_legal(mask: int, col: int) -> bool:
    return (mask & TOP_PLAYABLE_MASK[col]) == 0

def _play_move(curr: int, opp: int, col: int) -> Tuple[int, int]:
    # Returns (new_curr, new_opp) where new_curr is the side to move after the move (roles swapped).
    mask = curr | opp
    move = (mask + BOTTOM_MASK[col]) & COLUMN_MASK[col]  # next empty bit in the column (or sentinel if full)
    # Caller must ensure legality (top playable not occupied)
    new_opp = curr | move
    new_curr = opp
    return new_curr, new_opp

def _legal_moves(mask: int) -> List[int]:
    return [c for c in MOVE_ORDER if _is_legal(mask, c)]

def _evaluate(curr: int, opp: int) -> int:
    # Heuristic: score all 4-cell windows; reward center control.
    score = 0
    # Center control
    score += 6 * ((curr & CENTER_MASK).bit_count() - (opp & CENTER_MASK).bit_count())

    # Window scoring weights
    # (0 is unused; 4 is handled as win/loss by search but kept safe)
    w = [0, 1, 10, 80, WIN_SCORE]

    for m in WINDOWS:
        a = (curr & m).bit_count()
        b = (opp & m).bit_count()
        if a and b:
            continue
        if a:
            score += w[a]
        elif b:
            score -= w[b]
    return score

class _Timeout(Exception):
    pass

def _negamax(curr: int, opp: int, depth: int, alpha: int, beta: int, ply: int,
             end_time: float) -> Tuple[int, int]:
    # Returns (value, best_col)
    if time.perf_counter() >= end_time:
        raise _Timeout()

    # If opponent already has a 4-in-a-row, current player is losing
    if _is_win(opp):
        return (-WIN_SCORE + ply), -1

    mask = curr | opp
    moves = _legal_moves(mask)
    if not moves:
        return 0, -1  # draw (or game over)

    if depth == 0:
        return _evaluate(curr, opp), -1

    key = _pack_key(curr, opp)
    tt = TT.get(key)
    if tt is not None:
        tt_depth, tt_val, tt_flag, tt_best = tt
        if tt_depth >= depth:
            if tt_flag == 0:
                return tt_val, tt_best
            elif tt_flag < 0:
                beta = min(beta, tt_val)
            else:
                alpha = max(alpha, tt_val)
            if alpha >= beta:
                return tt_val, tt_best

    # If TT suggests a best move, search it first
    ordered = moves
    if tt is not None and tt[3] in moves:
        bm = tt[3]
        ordered = [bm] + [c for c in moves if c != bm]

    best_val = -INF
    best_col = ordered[0]
    orig_alpha = alpha

    for col in ordered:
        # Extra time check in loop
        if time.perf_counter() >= end_time:
            raise _Timeout()

        new_curr, new_opp = _play_move(curr, opp, col)

        # Immediate win after making this move (i.e., new_opp has our stones including the placed one)
        if _is_win(new_opp):
            val = WIN_SCORE - ply
        else:
            val, _ = _negamax(new_curr, new_opp, depth - 1, -beta, -alpha, ply + 1, end_time)
            val = -val

        if val > best_val:
            best_val = val
            best_col = col

        if best_val > alpha:
            alpha = best_val
        if alpha >= beta:
            break

    # Store TT
    flag = 0
    if best_val <= orig_alpha:
        flag = -1  # upperbound
    elif best_val >= beta:
        flag = +1  # lowerbound
    TT[key] = (depth, best_val, flag, best_col)

    return best_val, best_col

def policy(board: List[List[int]]) -> int:
    # Convert 6x7 (row 0 top) to bitboards (row 0 bottom in bitboard)
    curr = 0
    opp = 0
    for r in range(HEIGHT):
        rr = HEIGHT - 1 - r  # bottom-based row index
        row = board[r]
        for c in range(WIDTH):
            v = row[c]
            if v == 0:
                continue
            bit = 1 << (c * H1 + rr)
            if v == 1:
                curr |= bit
            else:
                opp |= bit

    mask = curr | opp
    legal = _legal_moves(mask)
    if not legal:
        return 0  # no legal moves; game should be over

    # 1) Immediate winning move
    for col in legal:
        new_curr, new_opp = _play_move(curr, opp, col)
        if _is_win(new_opp):  # our move created a win
            return col

    # 2) Immediate block: if opponent can win next in some column, try to play there
    # (If multiple, just take one; search will handle deeper tactics.)
    for col in legal:
        # Simulate opponent playing in this column (without changing turn for real)
        if not _is_legal(mask, col):
            continue
        opp_mask = (mask + BOTTOM_MASK[col]) & COLUMN_MASK[col]
        if opp_mask and _is_win(opp | opp_mask):
            return col

    # 3) Iterative deepening alpha-beta
    end_time = time.perf_counter() + 0.98  # stay under 1s budget
    best_col = legal[0]

    # Slightly clear TT if it grows too large (keeps memory bounded)
    if len(TT) > 300_000:
        TT.clear()

    try:
        for depth in range(1, 10):  # up to 9 plies; iterative deepening will stop by time
            val, col = _negamax(curr, opp, depth, -INF, INF, 0, end_time)
            if col != -1 and _is_legal(mask, col):
                best_col = col
            # If we found a forced win, stop early
            if val >= WIN_SCORE - 50:
                break
    except _Timeout:
        pass
    except Exception:
        # Safety: never crash; always return a legal move
        pass

    if not _is_legal(mask, best_col):
        # Fallback safety
        return legal[0]
    return best_col
