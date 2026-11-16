
import time
from typing import List, Tuple

SIZE = 3
N_CELLS = 27
FULL_MASK = (1 << N_CELLS) - 1
WIN_SCORE = 1_000_000
INF = 10**18

# Globals reset each policy call
TT_EXACT = {}
TT_BEST = {}
WIN_CACHE = {}
WMOVES_CACHE = {}
DEADLINE = 0.0
NODE_COUNTER = 0


class _Timeout(Exception):
    pass


def _idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k


INDEX_TO_COORD = [(i, j, k) for i in range(3) for j in range(3) for k in range(3)]
CENTER_IDX = _idx(1, 1, 1)
CENTER_BIT = 1 << CENTER_IDX

CORNER_MASK = 0
for i in (0, 2):
    for j in (0, 2):
        for k in (0, 2):
            CORNER_MASK |= 1 << _idx(i, j, k)


def _in_bounds(x: int, y: int, z: int) -> bool:
    return 0 <= x < 3 and 0 <= y < 3 and 0 <= z < 3


def _generate_line_masks():
    directions = [
        (1, 0, 0), (0, 1, 0), (0, 0, 1),
        (1, 1, 0), (1, -1, 0),
        (1, 0, 1), (1, 0, -1),
        (0, 1, 1), (0, 1, -1),
        (1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1),
    ]
    lines = set()
    for dx, dy, dz in directions:
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    px, py, pz = x - dx, y - dy, z - dz
                    x2, y2, z2 = x + 2 * dx, y + 2 * dy, z + 2 * dz
                    if _in_bounds(px, py, pz):
                        continue
                    if not _in_bounds(x2, y2, z2):
                        continue
                    mask = 0
                    for t in range(3):
                        xx, yy, zz = x + t * dx, y + t * dy, z + t * dz
                        mask |= 1 << _idx(xx, yy, zz)
                    lines.add(mask)
    line_masks = tuple(sorted(lines))

    cell_lines = [[] for _ in range(N_CELLS)]
    for lm in line_masks:
        m = lm
        while m:
            lsb = m & -m
            idx = lsb.bit_length() - 1
            cell_lines[idx].append(lm)
            m ^= lsb

    cell_line_counts = [len(v) for v in cell_lines]
    return line_masks, tuple(tuple(v) for v in cell_lines), tuple(cell_line_counts)


LINE_MASKS, CELL_LINE_MASKS, CELL_WEIGHTS = _generate_line_masks()

# Open-line heuristic weights: 1 stone / 2 stones in an otherwise open line
LINE_WEIGHTS = (0, 4, 50, 0)


def _bits(mask: int):
    while mask:
        lsb = mask & -mask
        yield lsb.bit_length() - 1
        mask ^= lsb


def _has_win(mask: int) -> bool:
    cached = WIN_CACHE.get(mask)
    if cached is not None:
        return cached
    for lm in LINE_MASKS:
        if (mask & lm) == lm:
            WIN_CACHE[mask] = True
            return True
    WIN_CACHE[mask] = False
    return False


def _winning_moves_mask(player: int, opp: int) -> int:
    key = (player, opp)
    cached = WMOVES_CACHE.get(key)
    if cached is not None:
        return cached

    empty = FULL_MASK ^ (player | opp)
    wins = 0
    for lm in LINE_MASKS:
        if lm & opp:
            continue
        pcount = (lm & player).bit_count()
        if pcount == 2:
            wins |= lm & empty

    WMOVES_CACHE[key] = wins
    return wins


def _positional_score(mask: int) -> int:
    score = 0
    m = mask
    while m:
        lsb = m & -m
        idx = lsb.bit_length() - 1
        score += CELL_WEIGHTS[idx]
        m ^= lsb
    return score


def _evaluate(cur: int, opp: int) -> int:
    if _has_win(cur):
        return WIN_SCORE
    if _has_win(opp):
        return -WIN_SCORE

    score = 0

    for lm in LINE_MASKS:
        c = (lm & cur).bit_count()
        o = (lm & opp).bit_count()
        if c and o:
            continue
        if c:
            score += LINE_WEIGHTS[c]
        elif o:
            score -= LINE_WEIGHTS[o]

    my_wins = _winning_moves_mask(cur, opp).bit_count()
    opp_wins = _winning_moves_mask(opp, cur).bit_count()

    score += 130 * my_wins
    score -= 160 * opp_wins

    if my_wins >= 2:
        score += 260
    if opp_wins >= 2:
        score -= 320

    score += _positional_score(cur)
    score -= _positional_score(opp)

    return score


def _pick_best_from_mask(mask: int, cur: int, opp: int) -> int:
    best_idx = None
    best_score = -INF

    for idx in _bits(mask):
        b = 1 << idx
        score = CELL_WEIGHTS[idx] * 20

        # Local line potential
        for lm in CELL_LINE_MASKS[idx]:
            c = (lm & cur).bit_count()
            o = (lm & opp).bit_count()
            if o == 0:
                if c == 0:
                    score += 3
                elif c == 1:
                    score += 12
                elif c == 2:
                    score += 120
            elif c == 0:
                if o == 1:
                    score -= 4
                elif o == 2:
                    score -= 40

        future_my_wins = _winning_moves_mask(cur | b, opp).bit_count()
        future_opp_wins = _winning_moves_mask(opp, cur | b).bit_count()
        score += 150 * future_my_wins
        score -= 80 * future_opp_wins

        if idx == CENTER_IDX:
            score += 25
        if (1 << idx) & CORNER_MASK:
            score += 10

        if score > best_score:
            best_score = score
            best_idx = idx

    return best_idx


def _ordered_moves(cur: int, opp: int, empties: int, my_wins: int, opp_wins: int, tt_move):
    if my_wins:
        cand = my_wins
    elif opp_wins:
        cand = opp_wins
    else:
        cand = empties

    moves = []
    for idx in _bits(cand):
        b = 1 << idx
        score = CELL_WEIGHTS[idx] * 20

        if tt_move is not None and idx == tt_move:
            score += 2_000_000
        if my_wins & b:
            score += 1_000_000
        if opp_wins & b:
            score += 400_000
        if idx == CENTER_IDX:
            score += 40
        if b & CORNER_MASK:
            score += 15

        # Cheap local ordering bonus
        for lm in CELL_LINE_MASKS[idx]:
            c = (lm & cur).bit_count()
            o = (lm & opp).bit_count()
            if o == 0:
                if c == 0:
                    score += 2
                elif c == 1:
                    score += 10
                elif c == 2:
                    score += 80
            elif c == 0:
                if o == 2:
                    score -= 20

        moves.append((score, idx))

    moves.sort(reverse=True)
    return [idx for _, idx in moves]


def _negamax(cur: int, opp: int, depth: int, alpha: int, beta: int):
    global NODE_COUNTER

    NODE_COUNTER += 1
    if (NODE_COUNTER & 2047) == 0 and time.perf_counter() > DEADLINE:
        raise _Timeout

    key = (cur, opp, depth)
    cached = TT_EXACT.get(key)
    if cached is not None:
        return cached

    if _has_win(cur):
        return WIN_SCORE + depth, None
    if _has_win(opp):
        return -WIN_SCORE - depth, None

    empties = FULL_MASK ^ (cur | opp)
    if empties == 0:
        return 0, None

    my_wins = _winning_moves_mask(cur, opp)
    if my_wins:
        mv = _pick_best_from_mask(my_wins, cur, opp)
        return WIN_SCORE + depth, mv

    if depth == 0:
        return _evaluate(cur, opp), None

    opp_wins = _winning_moves_mask(opp, cur)
    tt_move = TT_BEST.get((cur, opp))
    moves = _ordered_moves(cur, opp, empties, my_wins, opp_wins, tt_move)

    best_score = -INF
    best_move = moves[0]
    cutoff = False

    for mv in moves:
        b = 1 << mv
        child_score, _ = _negamax(opp, cur | b, depth - 1, -beta, -alpha)
        score = -child_score

        if score > best_score:
            best_score = score
            best_move = mv

        if score > alpha:
            alpha = score

        if alpha >= beta:
            cutoff = True
            break

    TT_BEST[(cur, opp)] = best_move
    if not cutoff:
        TT_EXACT[key] = (best_score, best_move)

    return best_score, best_move


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    global TT_EXACT, TT_BEST, WIN_CACHE, WMOVES_CACHE, DEADLINE, NODE_COUNTER

    cur = 0
    opp = 0
    first_empty = None

    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                idx = _idx(i, j, k)
                if v == 1:
                    cur |= 1 << idx
                elif v == -1:
                    opp |= 1 << idx
                else:
                    if first_empty is None:
                        first_empty = idx

    empties = FULL_MASK ^ (cur | opp)
    if empties == 0:
        # No legal move exists; return a fixed coordinate as a last resort.
        return (0, 0, 0)

    # Guaranteed legal fallback
    fallback = first_empty if first_empty is not None else next(_bits(empties))

    occupied_count = (cur | opp).bit_count()

    # Strong opening preference
    if occupied_count <= 1 and not ((cur | opp) & CENTER_BIT):
        return INDEX_TO_COORD[CENTER_IDX]

    my_wins = _winning_moves_mask(cur, opp)
    if my_wins:
        mv = _pick_best_from_mask(my_wins, cur, opp)
        return INDEX_TO_COORD[mv]

    opp_wins = _winning_moves_mask(opp, cur)
    if opp_wins and opp_wins.bit_count() == 1:
        mv = next(_bits(opp_wins))
        return INDEX_TO_COORD[mv]

    # Early fork creation if safe
    if not opp_wins and occupied_count <= 6:
        best_fork = None
        best_fork_score = -INF
        for mv in _bits(empties):
            b = 1 << mv
            my_next_wins = _winning_moves_mask(cur | b, opp).bit_count()
            opp_next_wins = _winning_moves_mask(opp, cur | b).bit_count()
            if my_next_wins >= 2 and opp_next_wins == 0:
                score = 1000 * my_next_wins + 20 * CELL_WEIGHTS[mv]
                if mv == CENTER_IDX:
                    score += 30
                if (1 << mv) & CORNER_MASK:
                    score += 10
                if score > best_fork_score:
                    best_fork_score = score
                    best_fork = mv
        if best_fork is not None:
            return INDEX_TO_COORD[best_fork]

    # Initialize per-call caches
    TT_EXACT = {}
    TT_BEST = {}
    WIN_CACHE = {}
    WMOVES_CACHE = {}
    NODE_COUNTER = 0
    DEADLINE = time.perf_counter() + 0.93

    # Recompute quick tactics after cache reset
    my_wins = _winning_moves_mask(cur, opp)
    opp_wins = _winning_moves_mask(opp, cur)

    if my_wins:
        mv = _pick_best_from_mask(my_wins, cur, opp)
        return INDEX_TO_COORD[mv]

    default_mask = opp_wins if opp_wins else empties
    best_move = _pick_best_from_mask(default_mask, cur, opp)
    if best_move is None:
        best_move = fallback

    empty_count = empties.bit_count()
    if empty_count >= 20:
        max_depth = 4
    elif empty_count >= 15:
        max_depth = 5
    elif empty_count >= 10:
        max_depth = 6
    else:
        max_depth = empty_count

    for depth in range(1, max_depth + 1):
        try:
            score, mv = _negamax(cur, opp, depth, -INF, INF)
            if mv is not None:
                best_move = mv
            if score >= WIN_SCORE // 2:
                break
        except _Timeout:
            break

    # Final legality guard
    bi, bj, bk = INDEX_TO_COORD[best_move]
    if board[bi][bj][bk] == 0:
        return (bi, bj, bk)

    for idx in _bits(empties):
        i, j, k = INDEX_TO_COORD[idx]
        if board[i][j][k] == 0:
            return (i, j, k)

    return INDEX_TO_COORD[fallback]
