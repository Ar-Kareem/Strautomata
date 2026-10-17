
from __future__ import annotations

import time

# 3x3x3 board bit indexing:
# idx = i*9 + j*3 + k
ALL_MASK = (1 << 27) - 1
CENTER_IDX = 13
WIN = 1_000_000
INF = 10_000_000

TT = {}
DEADLINE = 0.0
NODES = 0


class TimeoutSearch(Exception):
    pass


def _in_bounds(x: int, y: int, z: int) -> bool:
    return 0 <= x < 3 and 0 <= y < 3 and 0 <= z < 3


def _make_win_masks():
    directions = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dy == dz == 0:
                    continue
                # Canonicalize direction: first nonzero component is positive.
                for v in (dx, dy, dz):
                    if v != 0:
                        if v > 0:
                            directions.append((dx, dy, dz))
                        break

    masks = set()
    for dx, dy, dz in directions:
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    px, py, pz = x - dx, y - dy, z - dz
                    if _in_bounds(px, py, pz):
                        continue

                    cells = []
                    cx, cy, cz = x, y, z
                    while _in_bounds(cx, cy, cz):
                        idx = cx * 9 + cy * 3 + cz
                        cells.append(idx)
                        cx += dx
                        cy += dy
                        cz += dz

                    if len(cells) == 3:
                        m = 0
                        for idx in cells:
                            m |= 1 << idx
                        masks.add(m)

    return tuple(sorted(masks))


WIN_MASKS = _make_win_masks()

CELL_LINES = [[] for _ in range(27)]
for lm in WIN_MASKS:
    for idx in range(27):
        if lm & (1 << idx):
            CELL_LINES[idx].append(lm)

# Positional value: number of winning lines through the cell.
# Center is best in 3x3x3, then corners/edges according to line participation.
POS = [len(CELL_LINES[i]) for i in range(27)]


def _idx_to_move(idx: int) -> tuple[int, int, int]:
    return idx // 9, (idx % 9) // 3, idx % 3


def _bits(mask: int):
    while mask:
        b = mask & -mask
        yield b.bit_length() - 1
        mask ^= b


def _is_win(mask: int) -> bool:
    for lm in WIN_MASKS:
        if (mask & lm) == lm:
            return True
    return False


def _winning_moves(player: int, occupied: int) -> list[int]:
    """Return distinct empty cells where player wins immediately."""
    res = set()
    for lm in WIN_MASKS:
        if (player & lm).bit_count() == 2:
            empty = lm & ~occupied
            if empty and (empty & (empty - 1)) == 0:
                res.add(empty.bit_length() - 1)
    return list(res)


def _move_score(idx: int, cur: int, opp: int) -> int:
    """Fast move-ordering score from current player's perspective."""
    score = POS[idx] * 12
    for lm in CELL_LINES[idx]:
        c = (cur & lm).bit_count()
        o = (opp & lm).bit_count()

        if o == 0:
            if c == 2:
                score += 100000
            elif c == 1:
                score += 260
            else:
                score += 15

        if c == 0:
            if o == 2:
                score += 90000
            elif o == 1:
                score += 170

    if idx == CENTER_IDX:
        score += 100
    return score


def _ordered_moves(cur: int, opp: int, empty: int, preferred: int | None = None) -> list[int]:
    moves = list(_bits(empty))
    moves.sort(key=lambda x: _move_score(x, cur, opp), reverse=True)
    if preferred is not None and preferred in moves:
        moves.remove(preferred)
        moves.insert(0, preferred)
    return moves


def _static_eval(cur: int, opp: int) -> int:
    """Evaluation from side-to-move/current-player perspective."""
    score = 0

    for lm in WIN_MASKS:
        c = (cur & lm).bit_count()
        o = (opp & lm).bit_count()

        if c and o:
            continue
        if c:
            if c == 1:
                score += 5
            elif c == 2:
                score += 135
        elif o:
            if o == 1:
                score -= 6
            elif o == 2:
                score -= 165

    cm = cur
    while cm:
        b = cm & -cm
        score += POS[b.bit_length() - 1] * 3
        cm ^= b

    om = opp
    while om:
        b = om & -om
        score -= POS[b.bit_length() - 1] * 3
        om ^= b

    return score


def _check_time():
    global NODES
    NODES += 1
    if (NODES & 2047) == 0 and time.perf_counter() > DEADLINE:
        raise TimeoutSearch()


def _negamax(cur: int, opp: int, depth: int, alpha: int, beta: int) -> int:
    _check_time()

    occupied = cur | opp
    empty = ALL_MASK & ~occupied

    # The opponent is the player who just moved.
    if _is_win(opp):
        return -WIN - depth

    if empty == 0:
        return 0

    # Tactical quiescence: if current player can win now, take it.
    cur_wins = _winning_moves(cur, occupied)
    if cur_wins:
        return WIN + depth

    # If opponent has multiple distinct immediate wins and we cannot win now,
    # this is a forced loss.
    opp_wins = _winning_moves(opp, occupied)
    if len(opp_wins) > 1:
        return -WIN - depth

    if depth <= 0:
        return _static_eval(cur, opp)

    key = (cur, opp, depth)
    alpha_orig = alpha
    entry = TT.get(key)
    if entry is not None:
        val, flag = entry
        if flag == 0:      # exact
            return val
        elif flag == 1:    # lower bound
            if val > alpha:
                alpha = val
        else:              # upper bound
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    # If opponent has exactly one immediate winning move, blocking is forced.
    if len(opp_wins) == 1:
        moves = opp_wins
    else:
        moves = _ordered_moves(cur, opp, empty)

    best = -INF
    for idx in moves:
        bit = 1 << idx
        val = -_negamax(opp, cur | bit, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= alpha_orig:
        flag = 2       # upper bound
    elif best >= beta:
        flag = 1       # lower bound
    else:
        flag = 0       # exact
    TT[key] = (best, flag)

    return best


def _root_search(my: int, opp: int, depth: int, preferred: int | None) -> tuple[int, int]:
    occupied = my | opp
    empty = ALL_MASK & ~occupied

    moves = _ordered_moves(my, opp, empty, preferred)
    best_val = -INF
    best_idx = moves[0]
    alpha = -INF

    for idx in moves:
        bit = 1 << idx
        val = -_negamax(opp, my | bit, depth - 1, -INF, -alpha)

        if val > best_val:
            best_val = val
            best_idx = idx

        if val > alpha:
            alpha = val

    return best_val, best_idx


def _fallback_move(my: int, opp: int) -> int:
    """Always produce a legal move using tactical/positional heuristics."""
    occupied = my | opp
    empty = ALL_MASK & ~occupied
    legal = list(_bits(empty))

    if not legal:
        return 0

    best_idx = legal[0]
    best_score = -10**18

    for idx in legal:
        bit = 1 << idx
        nmy = my | bit
        nocc = occupied | bit

        score = _move_score(idx, my, opp)
        score += _static_eval(nmy, opp)

        my_threats = len(_winning_moves(nmy, nocc))
        opp_threats = len(_winning_moves(opp, nocc))

        if my_threats >= 2:
            score += 25000 + 2000 * my_threats
        else:
            score += 500 * my_threats

        score -= 800 * opp_threats

        # Penalize allowing opponent fork moves.
        opp_forks = 0
        opp_empty = ALL_MASK & ~nocc
        for oidx in _bits(opp_empty):
            obit = 1 << oidx
            if len(_winning_moves(opp | obit, nocc | obit)) >= 2:
                opp_forks += 1
        score -= 5500 * opp_forks

        if score > best_score:
            best_score = score
            best_idx = idx

    return best_idx


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    global TT, DEADLINE, NODES

    my = 0
    opp = 0

    for i in range(3):
        for j in range(3):
            for k in range(3):
                idx = i * 9 + j * 3 + k
                v = board[i][j][k]
                if v == 1:
                    my |= 1 << idx
                elif v == -1:
                    opp |= 1 << idx

    occupied = my | opp
    empty = ALL_MASK & ~occupied

    # No legal move exists. This should not occur in normal play.
    if empty == 0:
        return (0, 0, 0)

    # 1. Win immediately if possible.
    wins = _winning_moves(my, occupied)
    if wins:
        wins.sort(key=lambda x: _move_score(x, my, opp), reverse=True)
        return _idx_to_move(wins[0])

    # 2. Block opponent's immediate win.
    blocks = _winning_moves(opp, occupied)
    if blocks:
        blocks.sort(key=lambda x: _move_score(x, my, opp), reverse=True)
        return _idx_to_move(blocks[0])

    # 3. Strong opening: center dominates the most lines.
    move_count = occupied.bit_count()
    if move_count <= 1 and (empty & (1 << CENTER_IDX)):
        return _idx_to_move(CENTER_IDX)

    # 4. Create an immediate fork if available.
    fork_candidates = []
    for idx in _bits(empty):
        bit = 1 << idx
        if len(_winning_moves(my | bit, occupied | bit)) >= 2:
            fork_candidates.append(idx)
    if fork_candidates:
        fork_candidates.sort(key=lambda x: _move_score(x, my, opp), reverse=True)
        return _idx_to_move(fork_candidates[0])

    # Heuristic fallback is computed first so timeout still returns legal move.
    fallback = _fallback_move(my, opp)
    best_idx = fallback

    # Iterative deepening alpha-beta search with a conservative time guard.
    TT = {}
    NODES = 0
    DEADLINE = time.perf_counter() + 0.85

    empties = empty.bit_count()
    if empties <= 9:
        max_depth = empties
    elif empties <= 12:
        max_depth = 9
    elif empties <= 16:
        max_depth = 7
    elif empties <= 21:
        max_depth = 6
    else:
        max_depth = 5

    preferred = best_idx

    try:
        for depth in range(1, max_depth + 1):
            val, idx = _root_search(my, opp, depth, preferred)
            best_idx = idx
            preferred = idx

            # Proven win/loss found; no need to search deeper.
            if abs(val) >= WIN:
                break

            if time.perf_counter() > DEADLINE:
                break
    except TimeoutSearch:
        pass

    # Final legality guard.
    if not (empty & (1 << best_idx)):
        best_idx = next(_bits(empty))

    return _idx_to_move(best_idx)
