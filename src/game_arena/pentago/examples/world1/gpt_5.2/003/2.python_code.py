
import time
from typing import List, Tuple, Dict, Any

# Pentago policy: bitboard + alpha-beta negamax with time cutoff

FULL_MASK = (1 << 36) - 1
INF = 10**9

# Precompute all 5-in-a-row segment masks on 6x6
WIN_MASKS: List[int] = []
# Horizontal
for r in range(6):
    for c in range(2):
        m = 0
        for i in range(5):
            m |= 1 << (r * 6 + (c + i))
        WIN_MASKS.append(m)
# Vertical
for c in range(6):
    for r in range(2):
        m = 0
        for i in range(5):
            m |= 1 << ((r + i) * 6 + c)
        WIN_MASKS.append(m)
# Diagonal down-right
for r in range(2):
    for c in range(2):
        m = 0
        for i in range(5):
            m |= 1 << ((r + i) * 6 + (c + i))
        WIN_MASKS.append(m)
# Diagonal up-right
for r in range(4, 6):
    for c in range(2):
        m = 0
        for i in range(5):
            m |= 1 << ((r - i) * 6 + (c + i))
        WIN_MASKS.append(m)

# Positional weights (prefer center-ish squares slightly)
_POS_W = [
    1, 1, 2, 2, 1, 1,
    1, 2, 3, 3, 2, 1,
    2, 3, 4, 4, 3, 2,
    2, 3, 4, 4, 3, 2,
    1, 2, 3, 3, 2, 1,
    1, 1, 2, 2, 1, 1,
]

# Segment weights by count in an unblocked 5-segment
LINE_W = [0, 2, 10, 60, 350, 500000]  # 5 should be essentially terminal anyway

# Precompute quadrant rotation maps for 3x3 blocks.
# Quadrants:
# 0: rows 0..2, cols 0..2
# 1: rows 0..2, cols 3..5
# 2: rows 3..5, cols 0..2
# 3: rows 3..5, cols 3..5
_QUAD_BASE = {
    0: (0, 0),
    1: (0, 3),
    2: (3, 0),
    3: (3, 3),
}

ROT_MAPS: Dict[Tuple[int, str], Tuple[List[int], List[int], int]] = {}
# key -> (old_indices, new_indices, quad_mask)
for q in range(4):
    br, bc = _QUAD_BASE[q]
    quad_cells = []
    for sr in range(3):
        for sc in range(3):
            idx = (br + sr) * 6 + (bc + sc)
            quad_cells.append((sr, sc, idx))
    quad_mask = 0
    for _, _, idx in quad_cells:
        quad_mask |= 1 << idx

    # Clockwise: old(sr,sc) -> new(sc, 2-sr)
    old_cw, new_cw = [], []
    for sr, sc, old_idx in quad_cells:
        nsr, nsc = sc, 2 - sr
        new_idx = (br + nsr) * 6 + (bc + nsc)
        old_cw.append(old_idx)
        new_cw.append(new_idx)

    # Counter-clockwise: old(sr,sc) -> new(2-sc, sr)
    old_ccw, new_ccw = [], []
    for sr, sc, old_idx in quad_cells:
        nsr, nsc = 2 - sc, sr
        new_idx = (br + nsr) * 6 + (bc + nsc)
        old_ccw.append(old_idx)
        new_ccw.append(new_idx)

    ROT_MAPS[(q, "R")] = (old_cw, new_cw, quad_mask)
    ROT_MAPS[(q, "L")] = (old_ccw, new_ccw, quad_mask)


def _rotate_bits(bits: int, quad: int, direction: str) -> int:
    old_idx, new_idx, qmask = ROT_MAPS[(quad, direction)]
    res = bits & ~qmask
    # Only 9 bits to remap
    for oi, ni in zip(old_idx, new_idx):
        if (bits >> oi) & 1:
            res |= 1 << ni
    return res


def _is_win(bits: int) -> bool:
    for m in WIN_MASKS:
        if (bits & m) == m:
            return True
    return False


def _positional_sum(bits: int) -> int:
    s = 0
    b = bits
    while b:
        lsb = b & -b
        idx = (lsb.bit_length() - 1)
        s += _POS_W[idx]
        b ^= lsb
    return s


def _heuristic(you_bits: int, opp_bits: int) -> int:
    # If already terminal, return strong score
    yw = _is_win(you_bits)
    ow = _is_win(opp_bits)
    if yw and not ow:
        return INF // 2
    if ow and not yw:
        return -INF // 2
    if yw and ow:
        return 0

    score = 3 * (_positional_sum(you_bits) - _positional_sum(opp_bits))

    # Line-based evaluation on 5-length segments
    for m in WIN_MASKS:
        yb = you_bits & m
        ob = opp_bits & m
        if yb and ob:
            continue
        ny = yb.bit_count()
        no = ob.bit_count()
        if no == 0 and ny > 0:
            score += LINE_W[ny]
        elif ny == 0 and no > 0:
            score -= LINE_W[no]

    return score


def _apply_move(you_bits: int, opp_bits: int, pos: int, quad: int, direction: str) -> Tuple[int, int]:
    # Place
    you_bits2 = you_bits | (1 << pos)
    opp_bits2 = opp_bits
    # Rotate quadrant for both
    you_bits2 = _rotate_bits(you_bits2, quad, direction)
    opp_bits2 = _rotate_bits(opp_bits2, quad, direction)
    return you_bits2, opp_bits2


def _iter_empty_positions(occupied: int):
    empties = (~occupied) & FULL_MASK
    while empties:
        lsb = empties & -empties
        pos = lsb.bit_length() - 1
        yield pos
        empties ^= lsb


def _terminal_value_after_move(y2: int, o2: int, ply: int) -> int:
    yw = _is_win(y2)
    ow = _is_win(o2)
    if yw and not ow:
        return INF - ply
    if ow and not yw:
        return -INF + ply
    if yw and ow:
        return 0
    if ((y2 | o2) & FULL_MASK) == FULL_MASK:
        return 0
    return None  # not terminal


class _Search:
    __slots__ = ("deadline", "tt")

    def __init__(self, deadline: float):
        self.deadline = deadline
        self.tt: Dict[Tuple[int, int, int], int] = {}

    def negamax(self, you_bits: int, opp_bits: int, depth: int, alpha: int, beta: int, ply: int) -> int:
        if time.perf_counter() >= self.deadline:
            return _heuristic(you_bits, opp_bits)

        key = (you_bits, opp_bits, depth)
        v = self.tt.get(key)
        if v is not None:
            return v

        # Terminal check at node (rare but safe)
        yw = _is_win(you_bits)
        ow = _is_win(opp_bits)
        if yw and not ow:
            return INF - ply
        if ow and not yw:
            return -INF + ply
        if yw and ow:
            return 0

        if depth <= 0:
            return _heuristic(you_bits, opp_bits)

        occupied = you_bits | opp_bits
        if occupied == FULL_MASK:
            return 0

        # Generate moves with light ordering: prefer higher immediate heuristic
        moves = []
        for pos in _iter_empty_positions(occupied):
            for quad in range(4):
                # try both directions
                for direction in ("L", "R"):
                    y2, o2 = _apply_move(you_bits, opp_bits, pos, quad, direction)
                    tv = _terminal_value_after_move(y2, o2, ply)
                    if tv is not None:
                        est = tv
                    else:
                        est = _heuristic(y2, o2)
                    moves.append((est, pos, quad, direction, y2, o2))
        moves.sort(key=lambda x: x[0], reverse=True)

        best = -INF
        a = alpha
        for _, pos, quad, direction, y2, o2 in moves:
            if time.perf_counter() >= self.deadline:
                break

            tv = _terminal_value_after_move(y2, o2, ply)
            if tv is not None:
                val = tv
            else:
                val = -self.negamax(o2, y2, depth - 1, -beta, -a, ply + 1)

            if val > best:
                best = val
            if best > a:
                a = best
            if a >= beta:
                break

        # Store exact value (good enough for this constrained domain)
        self.tt[key] = best
        return best


def policy(you, opponent) -> str:
    # Convert input arrays to bitboards
    you_bits = 0
    opp_bits = 0
    for r in range(6):
        rowy = you[r]
        rowo = opponent[r]
        for c in range(6):
            idx = r * 6 + c
            if int(rowy[c]) == 1:
                you_bits |= 1 << idx
            elif int(rowo[c]) == 1:
                opp_bits |= 1 << idx

    occupied = you_bits | opp_bits
    # Fallback legal move (guaranteed if at least one empty exists)
    first_empty = next(_iter_empty_positions(occupied))
    fallback = f"{first_empty // 6 + 1},{first_empty % 6 + 1},0,L"

    # Choose search depth by remaining empties
    empties_count = (FULL_MASK ^ occupied).bit_count()
    if empties_count > 18:
        max_depth = 2
    elif empties_count > 10:
        max_depth = 3
    elif empties_count > 6:
        max_depth = 4
    else:
        max_depth = 5

    start = time.perf_counter()
    deadline = start + 0.95  # keep margin
    search = _Search(deadline)

    best_move = None
    best_val = -INF

    # Root move ordering
    root_moves = []
    for pos in _iter_empty_positions(occupied):
        for quad in range(4):
            for direction in ("L", "R"):
                y2, o2 = _apply_move(you_bits, opp_bits, pos, quad, direction)
                tv = _terminal_value_after_move(y2, o2, 0)
                if tv is not None:
                    est = tv
                else:
                    est = _heuristic(y2, o2)
                root_moves.append((est, pos, quad, direction, y2, o2))
    root_moves.sort(key=lambda x: x[0], reverse=True)

    # Iterative deepening
    for depth in range(1, max_depth + 1):
        if time.perf_counter() >= deadline:
            break
        cur_best_move = best_move
        cur_best_val = -INF
        alpha = -INF
        beta = INF

        for _, pos, quad, direction, y2, o2 in root_moves:
            if time.perf_counter() >= deadline:
                break

            tv = _terminal_value_after_move(y2, o2, 0)
            if tv is not None:
                val = tv
            else:
                # After our move, opponent to play
                val = -search.negamax(o2, y2, depth - 1, -beta, -alpha, 1)

            if val > cur_best_val:
                cur_best_val = val
                cur_best_move = (pos, quad, direction)
            if val > alpha:
                alpha = val

            # If we found a forced win at this depth, keep it
            if cur_best_val >= INF - 5:
                break

        if cur_best_move is not None:
            best_move = cur_best_move
            best_val = cur_best_val

        if best_val >= INF - 5:
            break

    if best_move is None:
        return fallback

    pos, quad, direction = best_move
    r = pos // 6 + 1
    c = pos % 6 + 1
    return f"{r},{c},{quad},{direction}"
