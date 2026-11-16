
import time
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional

# Connect4 bitboard implementation (7 columns, 6 rows) using 7 bits per column (extra sentinel bit).
# Bit index = col*7 + row, where row=0 is bottom playable cell, row=5 is top playable cell, row=6 sentinel.

COLS = 7
ROWS = 6

MOVE_ORDER = [3, 4, 2, 5, 1, 6, 0]  # center-first

WIN_SCORE = 1_000_000
INF = 10_000_000

# Heuristic weights for windows with N stones and 0 opponent stones.
WINDOW_WEIGHTS = {0: 0, 1: 1, 2: 12, 3: 80, 4: WIN_SCORE}


class _Timeout(Exception):
    pass


@dataclass
class TTEntry:
    depth: int
    value: int
    flag: int  # 0 exact, 1 lowerbound, 2 upperbound


# Precomputed bit masks
BOTTOM_MASK = [1 << (c * 7) for c in range(COLS)]
TOP_MASK = [1 << (c * 7 + (ROWS - 1)) for c in range(COLS)]
COLUMN_MASK = []
for c in range(COLS):
    m = 0
    for r in range(ROWS):
        m |= 1 << (c * 7 + r)
    COLUMN_MASK.append(m)

# Precompute all 4-in-a-row winning masks (69 total in standard Connect4)
WIN_MASKS: List[int] = []
# Horizontal
for r in range(ROWS):
    for c in range(COLS - 3):
        m = 0
        for k in range(4):
            m |= 1 << ((c + k) * 7 + r)
        WIN_MASKS.append(m)
# Vertical
for c in range(COLS):
    for r in range(ROWS - 3):
        m = 0
        for k in range(4):
            m |= 1 << (c * 7 + (r + k))
        WIN_MASKS.append(m)
# Diagonal up-right
for c in range(COLS - 3):
    for r in range(ROWS - 3):
        m = 0
        for k in range(4):
            m |= 1 << ((c + k) * 7 + (r + k))
        WIN_MASKS.append(m)
# Diagonal down-right
for c in range(COLS - 3):
    for r in range(3, ROWS):
        m = 0
        for k in range(4):
            m |= 1 << ((c + k) * 7 + (r - k))
        WIN_MASKS.append(m)


def _popcount(x: int) -> int:
    return x.bit_count()


def _is_win(p: int) -> bool:
    # Check 4-in-a-row using bit shifts in 7-bit-per-column representation.
    for shift in (1, 7, 6, 8):
        m = p & (p >> shift)
        if (m & (m >> (2 * shift))) != 0:
            return True
    return False


def _can_play(mask: int, col: int) -> bool:
    # If top playable cell is empty in that column.
    return (mask & TOP_MASK[col]) == 0


def _move_bit(mask: int, col: int) -> int:
    # Compute the bit for the lowest empty cell in column.
    return (mask + BOTTOM_MASK[col]) & COLUMN_MASK[col]


def _legal_moves(mask: int) -> List[int]:
    return [c for c in MOVE_ORDER if _can_play(mask, c)]


def _immediate_winning_moves(position: int, mask: int) -> List[int]:
    wins = []
    for c in MOVE_ORDER:
        if not _can_play(mask, c):
            continue
        mv = _move_bit(mask, c)
        if _is_win(position | mv):
            wins.append(c)
    return wins


def _evaluate(position: int, mask: int) -> int:
    # Evaluate from the perspective of the player to move (whose stones are in 'position').
    opp = mask ^ position
    if _is_win(position):
        return WIN_SCORE
    if _is_win(opp):
        return -WIN_SCORE

    score = 0

    # Center column preference
    center_col = 3
    center_bits = COLUMN_MASK[center_col]
    score += 4 * (_popcount(position & center_bits) - _popcount(opp & center_bits))

    # Window scoring
    for wm in WIN_MASKS:
        pc = _popcount(position & wm)
        oc = _popcount(opp & wm)
        if oc and pc:
            continue
        if pc:
            score += WINDOW_WEIGHTS.get(pc, 0)
        elif oc:
            score -= WINDOW_WEIGHTS.get(oc, 0)

    return score


def _negamax(
    position: int,
    mask: int,
    depth: int,
    alpha: int,
    beta: int,
    ply: int,
    deadline: float,
    tt: Dict[Tuple[int, int], TTEntry],
) -> int:
    if time.perf_counter() >= deadline:
        raise _Timeout

    opp = mask ^ position
    if _is_win(opp):
        # Previous player (opponent) already connected 4: loss for side to move.
        return -WIN_SCORE + ply
    if depth == 0:
        return _evaluate(position, mask)

    key = (position, mask)
    entry = tt.get(key)
    if entry is not None and entry.depth >= depth:
        if entry.flag == 0:
            return entry.value
        elif entry.flag == 1:
            alpha = max(alpha, entry.value)
        else:  # upperbound
            beta = min(beta, entry.value)
        if alpha >= beta:
            return entry.value

    legal = _legal_moves(mask)
    if not legal:
        return 0  # draw

    # Strong move ordering:
    # 1) immediate wins
    # 2) blocks (opponent immediate wins)
    # 3) center-first default order
    win_moves = _immediate_winning_moves(position, mask)
    if win_moves:
        # Prefer faster wins: return direct terminal score.
        return WIN_SCORE - ply

    opp_win_moves = _immediate_winning_moves(opp, mask)
    ordered = []
    used = set()
    for c in opp_win_moves:
        if c in legal and c not in used:
            ordered.append(c)
            used.add(c)
    for c in legal:
        if c not in used:
            ordered.append(c)
            used.add(c)

    best = -INF
    a0 = alpha
    for c in ordered:
        mv = _move_bit(mask, c)
        # Play move: update mask, and switch side-to-move representation.
        new_mask = mask | mv
        new_position = position ^ mask  # opponent stones become "position" for next player to move
        val = -_negamax(new_position, new_mask, depth - 1, -beta, -alpha, ply + 1, deadline, tt)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    # Store TT bounds
    flag = 0
    if best <= a0:
        flag = 2  # upperbound
    elif best >= beta:
        flag = 1  # lowerbound
    else:
        flag = 0  # exact
    tt[key] = TTEntry(depth=depth, value=best, flag=flag)

    return best


def _board_to_bitboards(board: List[List[int]]) -> Tuple[int, int]:
    # Input board rows: 0 (top) ... 5 (bottom)
    position = 0  # current player's stones (encoded as 1 in board)
    mask = 0      # all stones
    for r_in in range(ROWS):
        for c in range(COLS):
            v = board[r_in][c]
            if v == 0:
                continue
            r = (ROWS - 1) - r_in  # convert to bitboard row (0 bottom)
            bit = 1 << (c * 7 + r)
            mask |= bit
            if v == 1:
                position |= bit
    return position, mask


def policy(board: List[List[int]]) -> int:
    # Convert to bitboards
    position, mask = _board_to_bitboards(board)

    legal = _legal_moves(mask)
    if not legal:
        return 0  # no legal moves; shouldn't happen in normal gameplay

    # Immediate tactical checks at root
    wins = _immediate_winning_moves(position, mask)
    if wins:
        return wins[0]

    opp = mask ^ position
    opp_wins = _immediate_winning_moves(opp, mask)
    if opp_wins:
        # If multiple threats exist, search will decide; but blocking is usually mandatory.
        # Still, picking one blocker immediately avoids blundering on shallow time.
        # Prefer center among blockers due to MOVE_ORDER.
        for c in MOVE_ORDER:
            if c in opp_wins and _can_play(mask, c):
                return c

    # Iterative deepening with alpha-beta
    start = time.perf_counter()
    # Keep a small safety margin under 1s.
    deadline = start + 0.94

    tt: Dict[Tuple[int, int], TTEntry] = {}

    best_move = legal[0]
    best_score = -INF

    # Depth schedule: typically reaches 7-9 within time in Python, depending on branching.
    max_depth = 10

    # Aspiration window around previous score
    window = 60

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() >= deadline:
                break

            # Root search with move ordering and aspiration
            alpha = -INF
            beta = INF
            if best_score > -INF // 2:
                alpha = best_score - window
                beta = best_score + window

            def root_search(a: int, b: int) -> Tuple[int, int]:
                nonlocal best_move, best_score
                local_best_move = best_move
                local_best_score = -INF

                # Root ordering: try previous best move first, then center-first.
                ordered = []
                if best_move in legal:
                    ordered.append(best_move)
                for c in MOVE_ORDER:
                    if c in legal and c not in ordered:
                        ordered.append(c)

                for c in ordered:
                    if time.perf_counter() >= deadline:
                        raise _Timeout
                    mv = _move_bit(mask, c)
                    new_mask = mask | mv
                    new_position = position ^ mask
                    val = -_negamax(new_position, new_mask, depth - 1, -b, -a, 1, deadline, tt)
                    if val > local_best_score:
                        local_best_score = val
                        local_best_move = c
                    if val > a:
                        a = val
                    # Classic root pruning
                    if a >= b:
                        break

                best_move = local_best_move
                best_score = local_best_score
                return local_best_move, local_best_score

            # Aspiration re-search if needed
            move, score = root_search(alpha, beta)
            if score <= alpha:
                move, score = root_search(-INF, beta)
            elif score >= beta:
                move, score = root_search(alpha, INF)

            best_move, best_score = move, score

            # If we found a forced win, stop early.
            if best_score >= WIN_SCORE - 10:
                break

            # Slowly widen aspiration window as depth increases
            window = min(400, window + 40)

    except _Timeout:
        pass

    # Ensure legality
    if _can_play(mask, best_move):
        return best_move

    # Fallback: first legal move in preferred order
    return legal[0]
