
from __future__ import annotations

import time


WIN_SCORE = 1_000_000
INF = 1_000_000_000
TIME_BUDGET = 0.88

FULL_MASK = (1 << 27) - 1
CENTER_IDX = 13
CENTER_BIT = 1 << CENTER_IDX

_TT = {}
_DEADLINE = 0.0
_NODES = 0


def _idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k


def _decode(idx: int) -> tuple[int, int, int]:
    return (idx // 9, (idx // 3) % 3, idx % 3)


def _generate_lines() -> tuple[int, ...]:
    directions = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dy == dz == 0:
                    continue
                # Keep only one orientation for each line direction.
                first = dx if dx != 0 else (dy if dy != 0 else dz)
                if first > 0:
                    directions.append((dx, dy, dz))

    masks = set()
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for dx, dy, dz in directions:
                    i2, j2, k2 = i + 2 * dx, j + 2 * dy, k + 2 * dz
                    if 0 <= i2 < 3 and 0 <= j2 < 3 and 0 <= k2 < 3:
                        mask = 0
                        for t in range(3):
                            mask |= 1 << _idx(i + t * dx, j + t * dy, k + t * dz)
                        masks.add(mask)
    return tuple(sorted(masks))


WIN_MASKS = _generate_lines()

_cell_lines = [[] for _ in range(27)]
for _lm in WIN_MASKS:
    _m = _lm
    while _m:
        _b = _m & -_m
        _p = _b.bit_length() - 1
        _cell_lines[_p].append(_lm)
        _m ^= _b
CELL_LINES = tuple(tuple(x) for x in _cell_lines)

CORNER_MASK = 0
for _i in (0, 2):
    for _j in (0, 2):
        for _k in (0, 2):
            CORNER_MASK |= 1 << _idx(_i, _j, _k)

# Positional weight: number of winning lines through the cell, with small bonuses.
_pos = []
for p in range(27):
    bonus = 0
    if p == CENTER_IDX:
        bonus += 16
    elif (1 << p) & CORNER_MASK:
        bonus += 8
    _pos.append(10 * len(CELL_LINES[p]) + bonus)
POS_WEIGHT = tuple(_pos)

LINE_VALUE_X = (0, 10, 260, WIN_SCORE)
LINE_VALUE_O = (0, 11, 285, WIN_SCORE)


def _bit_iter(mask: int):
    while mask:
        b = mask & -mask
        yield b.bit_length() - 1
        mask ^= b


def _first_bit(mask: int) -> int:
    b = mask & -mask
    return b.bit_length() - 1


def _masks_from_board(board: list[list[list[int]]]) -> tuple[int, int]:
    xmask = 0
    omask = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                bit = 1 << _idx(i, j, k)
                v = board[i][j][k]
                if v == 1:
                    xmask |= bit
                elif v == -1:
                    omask |= bit
    return xmask, omask


def _is_winning_move(mask: int, idx: int) -> bool:
    new_mask = mask | (1 << idx)
    for lm in CELL_LINES[idx]:
        if (new_mask & lm) == lm:
            return True
    return False


def _has_win(mask: int) -> bool:
    for lm in WIN_MASKS:
        if (mask & lm) == lm:
            return True
    return False


def _winning_moves(player_mask: int, opp_mask: int) -> int:
    """All empty cells where player would win immediately."""
    occupied = player_mask | opp_mask
    wins = 0
    for lm in WIN_MASKS:
        if lm & opp_mask:
            continue
        if (lm & player_mask).bit_count() == 2:
            wins |= lm & ~occupied
    return wins


def _created_threat_mask(own: int, opp: int, idx: int) -> int:
    """After own plays idx, return all cells that become immediate wins."""
    bit = 1 << idx
    new_own = own | bit
    occupied = new_own | opp
    threats = 0
    for lm in CELL_LINES[idx]:
        if lm & opp:
            continue
        if (lm & new_own).bit_count() == 2:
            threats |= lm & ~occupied
    return threats


def _find_fork_moves(own: int, opp: int) -> int:
    legal = FULL_MASK & ~(own | opp)
    forks = 0
    for idx in _bit_iter(legal):
        if _created_threat_mask(own, opp, idx).bit_count() >= 2:
            forks |= 1 << idx
    return forks


def _count_fork_moves(own: int, opp: int, limit: int = 99) -> tuple[int, int]:
    legal = FULL_MASK & ~(own | opp)
    count = 0
    mask = 0
    for idx in _bit_iter(legal):
        if _is_winning_move(own, idx):
            continue
        if _created_threat_mask(own, opp, idx).bit_count() >= 2:
            count += 1
            mask |= 1 << idx
            if count >= limit:
                return count, mask
    return count, mask


def _evaluate(xmask: int, omask: int) -> int:
    if _has_win(xmask):
        return WIN_SCORE
    if _has_win(omask):
        return -WIN_SCORE

    score = 0

    # Occupied-cell positional score.
    m = xmask
    while m:
        b = m & -m
        score += POS_WEIGHT[b.bit_length() - 1]
        m ^= b

    m = omask
    while m:
        b = m & -m
        score -= POS_WEIGHT[b.bit_length() - 1]
        m ^= b

    # Open-line score.
    for lm in WIN_MASKS:
        xc = (xmask & lm).bit_count()
        oc = (omask & lm).bit_count()
        if xc and oc:
            continue
        if oc == 0:
            score += LINE_VALUE_X[xc]
        elif xc == 0:
            score -= LINE_VALUE_O[oc]

    # Potential fork/intersection score for empty cells.
    empty = FULL_MASK & ~(xmask | omask)
    for idx in _bit_iter(empty):
        xopen = 0
        oopen = 0
        for lm in CELL_LINES[idx]:
            if not (lm & omask):
                c = (lm & xmask).bit_count()
                if c == 1:
                    xopen += 1
                elif c == 2:
                    xopen += 3
            if not (lm & xmask):
                c = (lm & omask).bit_count()
                if c == 1:
                    oopen += 1
                elif c == 2:
                    oopen += 3

        if xopen:
            score += 3 * xopen + 8 * xopen * xopen
        if oopen:
            score -= 4 * oopen + 9 * oopen * oopen

    return score


def _move_order_score(idx: int, xmask: int, omask: int, player: int) -> int:
    if player == 1:
        own, opp = xmask, omask
    else:
        own, opp = omask, xmask

    bit = 1 << idx
    new_own = own | bit

    if _is_winning_move(own, idx):
        return 10_000_000 + POS_WEIGHT[idx]

    score = POS_WEIGHT[idx] * 4

    for lm in CELL_LINES[idx]:
        own_c = (own & lm).bit_count()
        opp_c = (opp & lm).bit_count()

        if opp_c == 0:
            after = own_c + 1
            if after == 2:
                score += 140
            elif after == 1:
                score += 14
            elif after == 3:
                score += 100_000

        if own_c == 0:
            if opp_c == 2:
                score += 2400
            elif opp_c == 1:
                score += 45

    threats = _created_threat_mask(own, opp, idx).bit_count()
    if threats >= 2:
        score += 7000 + 1000 * threats
    elif threats == 1:
        score += 450

    # Prefer moves that keep many useful lines alive.
    for lm in CELL_LINES[idx]:
        if not (lm & opp):
            score += 5 * (new_own & lm).bit_count()

    return score


def _ordered_moves(mask: int, xmask: int, omask: int, player: int) -> list[int]:
    scored = []
    for idx in _bit_iter(mask):
        scored.append((_move_order_score(idx, xmask, omask, player), idx))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [idx for _, idx in scored]


def _root_move_score(idx: int, xmask: int, omask: int) -> int:
    bit = 1 << idx
    if _is_winning_move(xmask, idx):
        return WIN_SCORE + POS_WEIGHT[idx]

    nx = xmask | bit
    score = _evaluate(nx, omask) + POS_WEIGHT[idx]

    threats = _created_threat_mask(xmask, omask, idx).bit_count()
    if threats >= 2:
        score += 250_000 + 3000 * threats
    elif threats == 1:
        score += 2200

    own_forks, _ = _count_fork_moves(nx, omask, limit=4)
    opp_forks, _ = _count_fork_moves(omask, nx, limit=4)
    score += 2600 * own_forks
    score -= 5600 * opp_forks

    return score


def _ordered_root_moves(mask: int, xmask: int, omask: int) -> list[int]:
    scored = []
    for idx in _bit_iter(mask):
        scored.append((_root_move_score(idx, xmask, omask), idx))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [idx for _, idx in scored]


def _best_mask_move(mask: int, xmask: int, omask: int) -> int:
    legal = FULL_MASK & ~(xmask | omask)
    mask &= legal
    if not mask:
        return _first_bit(legal)

    best = None
    best_score = -INF
    for idx in _bit_iter(mask):
        s = _root_move_score(idx, xmask, omask)
        if s > best_score:
            best_score = s
            best = idx
    return best if best is not None else _first_bit(legal)


def _check_time() -> None:
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise TimeoutError


def _alphabeta(
    xmask: int,
    omask: int,
    player: int,
    depth: int,
    alpha: int,
    beta: int,
    ply: int,
) -> int:
    _check_time()

    legal = FULL_MASK & ~(xmask | omask)
    if not legal:
        return 0

    dkey = depth if depth > 0 else 0
    key = (xmask, omask, player)
    entry = _TT.get(key)
    if entry is not None and entry[0] >= dkey:
        _, val, flag = entry
        if flag == 0:
            return val
        if flag == 1:
            if val > alpha:
                alpha = val
        else:
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    orig_alpha, orig_beta = alpha, beta

    if player == 1:
        own, opp = xmask, omask
        own_wins = _winning_moves(own, opp) & legal
        if own_wins:
            return WIN_SCORE - (ply + 1)

        opp_wins = _winning_moves(opp, own) & legal
        if opp_wins:
            if opp_wins & (opp_wins - 1):
                return -WIN_SCORE + (ply + 2)
            moves_mask = opp_wins
        else:
            if depth <= 0:
                val = _evaluate(xmask, omask)
                if len(_TT) < 300_000:
                    _TT[key] = (dkey, val, 0)
                return val
            moves_mask = legal

        best = -INF
        next_depth = depth - 1
        for idx in _ordered_moves(moves_mask, xmask, omask, player):
            val = _alphabeta(xmask | (1 << idx), omask, -1, next_depth, alpha, beta, ply + 1)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

    else:
        own, opp = omask, xmask
        own_wins = _winning_moves(own, opp) & legal
        if own_wins:
            return -WIN_SCORE + (ply + 1)

        opp_wins = _winning_moves(opp, own) & legal
        if opp_wins:
            if opp_wins & (opp_wins - 1):
                return WIN_SCORE - (ply + 2)
            moves_mask = opp_wins
        else:
            if depth <= 0:
                val = _evaluate(xmask, omask)
                if len(_TT) < 300_000:
                    _TT[key] = (dkey, val, 0)
                return val
            moves_mask = legal

        best = INF
        next_depth = depth - 1
        for idx in _ordered_moves(moves_mask, xmask, omask, player):
            val = _alphabeta(xmask, omask | (1 << idx), 1, next_depth, alpha, beta, ply + 1)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break

    if best <= orig_alpha:
        flag = -1  # upper bound
    elif best >= orig_beta:
        flag = 1   # lower bound
    else:
        flag = 0   # exact

    if len(_TT) < 300_000:
        _TT[key] = (dkey, best, flag)

    return best


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    global _TT, _DEADLINE, _NODES

    _DEADLINE = time.perf_counter() + TIME_BUDGET
    _NODES = 0
    _TT = {}

    xmask, omask = _masks_from_board(board)
    legal = FULL_MASK & ~(xmask | omask)

    # No legal move exists; this should not happen in a normal arena call.
    if not legal:
        return (0, 0, 0)

    # If somehow called after a terminal board, still return a legal move.
    if _has_win(xmask) or _has_win(omask):
        return _decode(_best_mask_move(legal, xmask, omask))

    # 1. Win immediately.
    our_wins = _winning_moves(xmask, omask) & legal
    if our_wins:
        return _decode(_best_mask_move(our_wins, xmask, omask))

    # 2. Block immediate opponent win.
    opp_wins = _winning_moves(omask, xmask) & legal
    if opp_wins:
        return _decode(_best_mask_move(opp_wins, xmask, omask))

    # 3. Opening rules.
    if xmask.bit_count() == 0:
        if legal & CENTER_BIT:
            return (1, 1, 1)
        corners = legal & CORNER_MASK
        if corners:
            return _decode(_best_mask_move(corners, xmask, omask))

    if (legal & CENTER_BIT) and (xmask | omask).bit_count() <= 2:
        return (1, 1, 1)

    # 4. A double threat is normally a forced win.
    fork_moves = _find_fork_moves(xmask, omask) & legal
    if fork_moves:
        return _decode(_best_mask_move(fork_moves, xmask, omask))

    # 5. Heuristic fallback before search, guaranteeing legality.
    root_moves = _ordered_root_moves(legal, xmask, omask)
    best_move = root_moves[0] if root_moves else _first_bit(legal)

    # 6. Iterative-deepening alpha-beta search.
    empties = legal.bit_count()
    try:
        for depth in range(1, empties + 1):
            if time.perf_counter() > _DEADLINE:
                break

            alpha = -INF
            beta = INF
            best_at_depth = best_move
            best_val = -INF
            scored = []

            for idx in root_moves:
                if time.perf_counter() > _DEADLINE:
                    raise TimeoutError

                val = _alphabeta(xmask | (1 << idx), omask, -1, depth - 1, alpha, beta, 1)
                scored.append((val, idx))

                if val > best_val:
                    best_val = val
                    best_at_depth = idx
                if val > alpha:
                    alpha = val

            best_move = best_at_depth
            scored.sort(key=lambda t: t[0], reverse=True)
            root_moves = [idx for _, idx in scored]

            # A found forced win is enough.
            if best_val >= WIN_SCORE - 1000:
                break

    except TimeoutError:
        pass

    if not (legal & (1 << best_move)):
        best_move = _first_bit(legal)

    return _decode(best_move)
