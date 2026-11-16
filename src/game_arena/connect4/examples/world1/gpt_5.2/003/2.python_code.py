
import time
from typing import List, Tuple, Dict

# ----------------------------
# Bitboard-based Connect 4 AI
# Board: 6 rows x 7 cols
# We are always player "1" in the input (current player), opponent is "-1".
# ----------------------------

ROWS, COLS = 6, 7

# Bitboard mapping (classic 7-bits-per-column with a sentinel bit):
# bit index = col*7 + row, where row=0 is the bottom playable cell, row=5 top playable, row=6 sentinel.
BOTTOM_MASK = [1 << (c * 7) for c in range(COLS)]
TOP_MASK = [1 << (c * 7 + (ROWS - 1)) for c in range(COLS)]
COLUMN_MASK = [((1 << ROWS) - 1) << (c * 7) for c in range(COLS)]
FULL_MASK = 0
for c in range(COLS):
    FULL_MASK |= COLUMN_MASK[c]

CENTER_COL = 3
CENTER_MASK = COLUMN_MASK[CENTER_COL]

MOVE_ORDER = [3, 2, 4, 1, 5, 0, 6]

WIN_SCORE = 1_000_000
INF = 10**18

# Precompute all 4-in-a-row line masks (69 total).
LINES_4 = []
for c in range(COLS):
    for r in range(ROWS):
        # Horizontal
        if c <= COLS - 4:
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * 7 + r)
            LINES_4.append(m)
        # Vertical
        if r <= ROWS - 4:
            m = 0
            for i in range(4):
                m |= 1 << (c * 7 + (r + i))
            LINES_4.append(m)
        # Diagonal \
        if c <= COLS - 4 and r <= ROWS - 4:
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * 7 + (r + i))
            LINES_4.append(m)
        # Diagonal /
        if c <= COLS - 4 and r >= 3:
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * 7 + (r - i))
            LINES_4.append(m)


def _is_win(bb: int) -> bool:
    """Check whether bb has a connect-4."""
    # Vertical (shift 1), horizontal (shift 7), diagonals (shift 6 and 8)
    for shift in (1, 7, 6, 8):
        m = bb & (bb >> shift)
        if (m & (m >> (2 * shift))) != 0:
            return True
    return False


def _valid_columns(mask: int) -> List[int]:
    """Return list of columns that are not full."""
    # Column is full if top playable cell is occupied.
    return [c for c in MOVE_ORDER if (mask & TOP_MASK[c]) == 0]


def _play_mask(mask: int, col: int) -> int:
    """
    Return new mask after dropping a disc into col.
    Uses classic bitboard trick: add bottom mask within column mask.
    """
    return mask | ((mask + BOTTOM_MASK[col]) & COLUMN_MASK[col])


def _added_bit(mask: int, col: int) -> Tuple[int, int]:
    """Return (added_bit, new_mask) after playing in col."""
    new_mask = _play_mask(mask, col)
    return (new_mask ^ mask), new_mask


def _board_to_bitboards(board: List[List[int]]) -> Tuple[int, int]:
    """
    Convert 6x7 board (top row index 0) into (position, mask) bitboards.
    position: current player's stones (board value 1)
    mask: all occupied stones
    """
    position = 0
    mask = 0
    for r_top in range(ROWS):
        for c in range(COLS):
            v = board[r_top][c]
            if v == 0:
                continue
            r = (ROWS - 1) - r_top  # convert to bottom-based
            bit = 1 << (c * 7 + r)
            mask |= bit
            if v == 1:
                position |= bit
    return position, mask


def _evaluate(position: int, mask: int) -> int:
    """Static evaluation from the current player's perspective."""
    opp = mask ^ position

    # Center preference
    score = 3 * ((position & CENTER_MASK).bit_count() - (opp & CENTER_MASK).bit_count())

    # Window scoring
    # Weights tuned for fast/robust play; search does the heavy lifting.
    w1, w2, w3 = 1, 10, 60
    for line in LINES_4:
        cp = (position & line).bit_count()
        if cp:
            if (opp & line) != 0:
                continue
            if cp == 1:
                score += w1
            elif cp == 2:
                score += w2
            elif cp == 3:
                score += w3
        else:
            co = (opp & line).bit_count()
            if co == 0:
                continue
            if co == 1:
                score -= w1
            elif co == 2:
                score -= w2
            elif co == 3:
                score -= w3

    return score


class _Timeout(Exception):
    pass


def _negamax(position: int, mask: int, depth: int, alpha: int, beta: int,
             ply: int, deadline: float,
             tt: Dict[Tuple[int, int, int], int]) -> int:
    """
    Negamax with alpha-beta pruning.
    position: bitboard for player to move
    mask: all stones
    """
    if time.perf_counter() >= deadline:
        raise _Timeout

    opp = mask ^ position
    # If opponent already has a win, current player is losing (previous move ended the game).
    if _is_win(opp):
        return -WIN_SCORE + ply

    if mask == FULL_MASK:
        return 0  # draw

    if depth == 0:
        return _evaluate(position, mask)

    key = (position, mask, depth)
    if key in tt:
        return tt[key]

    best = -INF
    for col in _valid_columns(mask):
        added, new_mask = _added_bit(mask, col)

        # Immediate win for current player by playing here?
        if _is_win(position | added):
            val = WIN_SCORE - ply
        else:
            # After the move, the side to move switches; next position is old opponent stones:
            new_position = position ^ mask
            val = -_negamax(new_position, new_mask, depth - 1, -beta, -alpha, ply + 1, deadline, tt)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    tt[key] = best
    return best


def policy(board: List[List[int]]) -> int:
    position, mask = _board_to_bitboards(board)
    valid = _valid_columns(mask)
    if not valid:
        return 0  # should not happen in normal play

    # 1) Immediate win
    for col in valid:
        added, _ = _added_bit(mask, col)
        if _is_win(position | added):
            return col

    # 2) Immediate block (if opponent would win next move, play that column if possible)
    opp = mask ^ position
    must_block = []
    for col in valid:
        added, _ = _added_bit(mask, col)
        if _is_win(opp | added):
            must_block.append(col)
    if len(must_block) == 1:
        return must_block[0]
    # If multiple threats, search will decide the best defense.

    # 3) Iterative deepening negamax under a strict time budget
    start = time.perf_counter()
    deadline = start + 0.95  # keep margin
    best_move = valid[0]

    # Shallow safety: avoid moves that allow an immediate opponent win if possible.
    # (Search usually covers this, but it helps when time is tight.)
    safe_moves = []
    for col in valid:
        added, new_mask = _added_bit(mask, col)
        new_position = position ^ mask  # opponent to move
        opp_valid = _valid_columns(new_mask)
        loses_immediately = False
        opp_stones = new_mask ^ new_position  # stones for the player who is NOT to move (us after the flip)
        # Actually opponent to play's stones are new_position; their stones after a reply are new_position|added2.
        for oc in opp_valid:
            added2, _ = _added_bit(new_mask, oc)
            if _is_win(new_position | added2):
                loses_immediately = True
                break
        if not loses_immediately:
            safe_moves.append(col)
    root_moves = safe_moves if safe_moves else valid

    tt: Dict[Tuple[int, int, int], int] = {}

    # Increase depth while time remains
    max_depth = 10
    for depth in range(1, max_depth + 1):
        if time.perf_counter() >= deadline:
            break
        alpha, beta = -INF, INF
        best_val = -INF
        current_best = best_move

        try:
            for col in root_moves:
                if time.perf_counter() >= deadline:
                    raise _Timeout

                added, new_mask = _added_bit(mask, col)
                if _is_win(position | added):
                    # Would have been caught above, but keep it here for completeness.
                    current_best = col
                    best_val = WIN_SCORE
                    break

                new_position = position ^ mask  # opponent to move
                val = -_negamax(new_position, new_mask, depth - 1, -beta, -alpha, 1, deadline, tt)

                if val > best_val:
                    best_val = val
                    current_best = col
                if val > alpha:
                    alpha = val
        except _Timeout:
            break

        best_move = current_best

    # Ensure legality
    if (mask & TOP_MASK[best_move]) != 0:
        # Fallback: pick first legal
        for col in MOVE_ORDER:
            if (mask & TOP_MASK[col]) == 0:
                return col
        return valid[0]

    return best_move
