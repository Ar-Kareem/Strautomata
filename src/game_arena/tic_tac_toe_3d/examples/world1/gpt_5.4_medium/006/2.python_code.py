
import time
from typing import List, Tuple

# ------------- Precomputation -------------

def _idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k

def _coord(p: int) -> Tuple[int, int, int]:
    return (p // 9, (p // 3) % 3, p % 3)

def _build_win_masks():
    raw_lines = []

    # Axis-aligned lines
    for j in range(3):
        for k in range(3):
            raw_lines.append([_idx(i, j, k) for i in range(3)])
    for i in range(3):
        for k in range(3):
            raw_lines.append([_idx(i, j, k) for j in range(3)])
    for i in range(3):
        for j in range(3):
            raw_lines.append([_idx(i, j, k) for k in range(3)])

    # Plane diagonals
    for i in range(3):  # yz planes
        raw_lines.append([_idx(i, t, t) for t in range(3)])
        raw_lines.append([_idx(i, t, 2 - t) for t in range(3)])
    for j in range(3):  # xz planes
        raw_lines.append([_idx(t, j, t) for t in range(3)])
        raw_lines.append([_idx(t, j, 2 - t) for t in range(3)])
    for k in range(3):  # xy planes
        raw_lines.append([_idx(t, t, k) for t in range(3)])
        raw_lines.append([_idx(t, 2 - t, k) for t in range(3)])

    # Space diagonals
    raw_lines.append([_idx(t, t, t) for t in range(3)])
    raw_lines.append([_idx(t, t, 2 - t) for t in range(3)])
    raw_lines.append([_idx(t, 2 - t, t) for t in range(3)])
    raw_lines.append([_idx(2 - t, t, t) for t in range(3)])

    seen = set()
    masks = []
    for line in raw_lines:
        m = 0
        for p in line:
            m |= 1 << p
        if m not in seen:
            seen.add(m)
            masks.append(m)

    return tuple(masks)

WIN_MASKS = _build_win_masks()
ALL_MASK = (1 << 27) - 1

CELL_LINES = [[] for _ in range(27)]
for mask in WIN_MASKS:
    x = mask
    while x:
        b = x & -x
        p = b.bit_length() - 1
        CELL_LINES[p].append(mask)
        x ^= b

# Higher is better: center > corners/face-centers > edges
CELL_CONNECTIVITY = tuple(len(CELL_LINES[p]) for p in range(27))
ORDER_BASE = tuple(CELL_CONNECTIVITY[p] * 20 + (15 if p == 13 else 0) for p in range(27))
POS_BASE = tuple(CELL_CONNECTIVITY[p] * 2 + (4 if p == 13 else 0) for p in range(27))

WIN_SCORE = 1_000_000
INF = 10_000_000


# ------------- Bitboard helpers -------------

def _iter_bits(mask: int):
    while mask:
        b = mask & -mask
        yield b.bit_length() - 1, b
        mask ^= b

def _has_win(bits: int) -> bool:
    for m in WIN_MASKS:
        if (bits & m) == m:
            return True
    return False

def _sum_pos(bits: int) -> int:
    s = 0
    while bits:
        b = bits & -bits
        s += POS_BASE[b.bit_length() - 1]
        bits ^= b
    return s

def _immediate_win_moves(me: int, opp: int, empties_mask: int) -> List[int]:
    wins = []
    for p, b in _iter_bits(empties_mask):
        for line in CELL_LINES[p]:
            if (line & opp) == 0 and ((line & me).bit_count() == 2):
                wins.append(p)
                break
    return wins

def _ordered_moves(me: int, opp: int, empties_mask: int, block_cells=(), limit=None) -> List[int]:
    block_set = set(block_cells) if block_cells else ()
    scored = []

    for p, b in _iter_bits(empties_mask):
        score = ORDER_BASE[p]

        if block_set and p in block_set:
            score += 300_000

        for line in CELL_LINES[p]:
            myc = (line & me).bit_count()
            opc = (line & opp).bit_count()
            if myc and opc:
                continue

            if opc == 0:
                if myc == 2:
                    score += 1_000_000
                elif myc == 1:
                    score += 90
                else:
                    score += 8
            elif myc == 0:
                if opc == 2:
                    score += 700_000
                elif opc == 1:
                    score += 70

        scored.append((score, p))

    scored.sort(reverse=True)
    moves = [p for _, p in scored]
    if limit is not None and len(moves) > limit:
        moves = moves[:limit]
    return moves

def _move_limit(empties_count: int, depth: int):
    # Full width in tactical / late positions; trimmed width early for speed.
    if depth <= 1:
        return None
    if empties_count >= 22:
        return 10
    if empties_count >= 18:
        return 12
    if empties_count >= 14:
        return 16
    return None

def _evaluate(me: int, opp: int, empties_mask: int, opp_wins_cached=None) -> int:
    score = 0

    # Positional value
    score += _sum_pos(me)
    score -= _sum_pos(opp)

    # Open-line value
    for line in WIN_MASKS:
        myc = (line & me).bit_count()
        opc = (line & opp).bit_count()
        if myc and opc:
            continue
        if myc == 1:
            score += 4
        elif myc == 2:
            score += 50
        elif opc == 1:
            score -= 5
        elif opc == 2:
            score -= 55

    # Threats / forks
    my_wins = _immediate_win_moves(me, opp, empties_mask)
    opp_wins = opp_wins_cached if opp_wins_cached is not None else _immediate_win_moves(opp, me, empties_mask)

    score += 180 * len(my_wins)
    score -= 220 * len(opp_wins)

    if len(my_wins) >= 2:
        score += 180
    if len(opp_wins) >= 2:
        score -= 350

    return score


# ------------- Main policy -------------

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    me = 0
    opp = 0
    first_empty = None

    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                p = _idx(i, j, k)
                if v == 1:
                    me |= 1 << p
                elif v == -1:
                    opp |= 1 << p
                else:
                    if first_empty is None:
                        first_empty = (i, j, k)

    # Hard fallback if the board is somehow full.
    if first_empty is None:
        return (0, 0, 0)

    occupied = me | opp
    empties_mask = ALL_MASK ^ occupied
    empties_count = empties_mask.bit_count()

    # Trivial opening book
    if occupied == 0 and ((empties_mask >> 13) & 1):
        return (1, 1, 1)

    # If called on a terminal board, just return any legal move.
    if _has_win(me) or _has_win(opp):
        return first_empty

    # Tactical checks first
    my_wins = _immediate_win_moves(me, opp, empties_mask)
    if my_wins:
        best = max(my_wins, key=lambda p: ORDER_BASE[p])
        return _coord(best)

    opp_wins = _immediate_win_moves(opp, me, empties_mask)
    if len(opp_wins) == 1:
        return _coord(opp_wins[0])
    if len(opp_wins) > 1:
        # Unavoidable loss if no immediate win for us; still return a legal move.
        best = max(opp_wins, key=lambda p: ORDER_BASE[p])
        return _coord(best)

    deadline = time.perf_counter() + 0.92
    tt = {}

    def negamax(cur: int, other: int, depth: int, alpha: int, beta: int) -> int:
        if time.perf_counter() >= deadline:
            raise TimeoutError

        occupied_local = cur | other
        empties_local = ALL_MASK ^ occupied_local

        if empties_local == 0:
            return 0

        key = (cur, other, depth)
        if key in tt:
            return tt[key]

        cur_wins = _immediate_win_moves(cur, other, empties_local)
        if cur_wins:
            val = WIN_SCORE + depth
            tt[key] = val
            return val

        other_wins = _immediate_win_moves(other, cur, empties_local)
        if len(other_wins) > 1:
            val = -WIN_SCORE - depth
            tt[key] = val
            return val

        if depth == 0:
            val = _evaluate(cur, other, empties_local, other_wins)
            tt[key] = val
            return val

        forced_block = other_wins[0] if len(other_wins) == 1 else None
        if forced_block is not None:
            moves = [forced_block]
        else:
            limit = _move_limit(empties_local.bit_count(), depth)
            moves = _ordered_moves(cur, other, empties_local, other_wins, limit)

        if not moves:
            return 0

        best = -INF
        cutoff = False

        for mv in moves:
            score = -negamax(other, cur | (1 << mv), depth - 1, -beta, -alpha)

            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                cutoff = True
                break

        if not cutoff:
            tt[key] = best
        return best

    root_moves = _ordered_moves(me, opp, empties_mask, (), None)
    if not root_moves:
        return first_empty

    best_move = root_moves[0]

    # Adaptive max depth; iterative deepening will stop on timeout anyway.
    if empties_count <= 8:
        max_depth = empties_count
    elif empties_count <= 12:
        max_depth = 8
    elif empties_count <= 16:
        max_depth = 7
    elif empties_count <= 20:
        max_depth = 6
    else:
        max_depth = 5

    for depth in range(1, max_depth + 1):
        try:
            alpha = -INF
            beta = INF
            current_best_move = best_move
            current_best_score = -INF

            root_limit = _move_limit(empties_count, depth)
            moves = _ordered_moves(me, opp, empties_mask, (), root_limit)

            for mv in moves:
                if time.perf_counter() >= deadline:
                    raise TimeoutError

                score = -negamax(opp, me | (1 << mv), depth - 1, -beta, -alpha)

                if score > current_best_score:
                    current_best_score = score
                    current_best_move = mv
                if score > alpha:
                    alpha = score

            best_move = current_best_move

        except TimeoutError:
            break

    return _coord(best_move)
