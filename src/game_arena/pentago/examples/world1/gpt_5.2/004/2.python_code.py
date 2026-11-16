
# pentago_policy.py
# Implements: policy(you, opponent) -> "row,col,quad,dir"

from __future__ import annotations
import time
from typing import Iterable, List, Tuple, Optional

ALL_MASK = (1 << 36) - 1

WIN_SCORE = 1_000_000
# Escalating weights for uncontested 5-cell windows (index = count in window)
LINE_W = [0, 2, 10, 60, 800, 20000]

DIRS = ("L", "R")


def _rc_to_idx(r: int, c: int) -> int:
    return r * 6 + c


def _idx_to_move_str(idx: int, quad: int, d: str) -> str:
    r = idx // 6 + 1
    c = idx % 6 + 1
    return f"{r},{c},{quad},{d}"


def _build_win_masks() -> List[int]:
    masks = []
    # horizontal windows length 5 on 6x6
    for r in range(6):
        for c0 in range(2):
            m = 0
            for k in range(5):
                m |= 1 << _rc_to_idx(r, c0 + k)
            masks.append(m)
    # vertical
    for c in range(6):
        for r0 in range(2):
            m = 0
            for k in range(5):
                m |= 1 << _rc_to_idx(r0 + k, c)
            masks.append(m)
    # diag down-right
    for r0 in range(2):
        for c0 in range(2):
            m = 0
            for k in range(5):
                m |= 1 << _rc_to_idx(r0 + k, c0 + k)
            masks.append(m)
    # diag down-left
    for r0 in range(2):
        for c0 in range(4, 6):
            m = 0
            for k in range(5):
                m |= 1 << _rc_to_idx(r0 + k, c0 - k)
            masks.append(m)
    return masks


WIN_MASKS = _build_win_masks()


def _wins(bits: int) -> bool:
    for m in WIN_MASKS:
        if (bits & m) == m:
            return True
    return False


def _build_rotation_maps():
    # For each quad and dir, build:
    # - qmask: mask for quadrant squares
    # - moves: list[(srcbit, dstbit)] mapping old -> new
    rot = [[None, None] for _ in range(4)]  # [quad][0=L,1=R] = (qmask, moves)
    origins = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for q, (r0, c0) in enumerate(origins):
        positions = []
        qmask = 0
        for dr in range(3):
            for dc in range(3):
                idx = _rc_to_idx(r0 + dr, c0 + dc)
                positions.append((dr, dc, idx))
                qmask |= 1 << idx

        # mapping old(dr,dc)->new(dr',dc')
        for di, d in enumerate(DIRS):
            moves = []
            for dr, dc, idx_old in positions:
                if d == "R":
                    nr, nc = dc, 2 - dr
                else:  # "L"
                    nr, nc = 2 - dc, dr
                idx_new = _rc_to_idx(r0 + nr, c0 + nc)
                moves.append((1 << idx_old, 1 << idx_new))
            rot[q][di] = (qmask, moves)
    return rot


ROT = _build_rotation_maps()

# Small positional bias: prefer central area (helps many lines).
CENTER = 0
CENTER2 = 0
# 4 central-most cells
for (r, c) in [(2, 2), (2, 3), (3, 2), (3, 3)]:
    CENTER |= 1 << _rc_to_idx(r, c)
# ring around center (a bit wider)
for r in range(1, 5):
    for c in range(1, 5):
        if (r, c) not in [(2, 2), (2, 3), (3, 2), (3, 3)]:
            CENTER2 |= 1 << _rc_to_idx(r, c)

# Precompute move strings for speed
MOVE_STR = [[[None for _ in range(2)] for _ in range(4)] for _ in range(36)]
for idx in range(36):
    for q in range(4):
        for di, d in enumerate(DIRS):
            MOVE_STR[idx][q][di] = _idx_to_move_str(idx, q, d)


def _rotate_bits(bits: int, quad: int, di: int) -> int:
    qmask, moves = ROT[quad][di]
    qb = bits & qmask
    if qb == 0:
        return bits
    bits ^= qb
    # apply mapping old->new using qb snapshot
    for src, dst in moves:
        if qb & src:
            bits |= dst
    return bits


def _apply_move(you_b: int, opp_b: int, pos_idx: int, quad: int, di: int, us_to_move: bool) -> Tuple[int, int]:
    bit = 1 << pos_idx
    if us_to_move:
        you_b |= bit
    else:
        opp_b |= bit
    # rotate affects both players
    you_b = _rotate_bits(you_b, quad, di)
    opp_b = _rotate_bits(opp_b, quad, di)
    return you_b, opp_b


def _terminal_value(you_b: int, opp_b: int) -> Optional[int]:
    yw = _wins(you_b)
    ow = _wins(opp_b)
    if yw and ow:
        return 0  # draw
    if yw:
        return WIN_SCORE
    if ow:
        return -WIN_SCORE
    if (you_b | opp_b) == ALL_MASK:
        return 0
    return None


def _eval(you_b: int, opp_b: int) -> int:
    t = _terminal_value(you_b, opp_b)
    if t is not None:
        return t

    score = 0
    # line windows
    for m in WIN_MASKS:
        y = (you_b & m).bit_count()
        o = (opp_b & m).bit_count()
        if y and o:
            continue
        if y:
            score += LINE_W[y]
        elif o:
            score -= LINE_W[o]

    # positional bias
    score += 6 * ((you_b & CENTER).bit_count() - (opp_b & CENTER).bit_count())
    score += 2 * ((you_b & CENTER2).bit_count() - (opp_b & CENTER2).bit_count())
    return score


def _iter_empty_positions(empty_mask: int) -> Iterable[int]:
    # iterate set bits
    while empty_mask:
        lsb = empty_mask & -empty_mask
        idx = (lsb.bit_length() - 1)
        yield idx
        empty_mask ^= lsb


def _generate_moves(you_b: int, opp_b: int) -> List[Tuple[int, int, int]]:
    # returns list of (pos_idx, quad, di)
    occ = you_b | opp_b
    empty = (~occ) & ALL_MASK
    moves = []
    for idx in _iter_empty_positions(empty):
        # 8 rotation choices
        for q in range(4):
            moves.append((idx, q, 0))
            moves.append((idx, q, 1))
    return moves


def policy(you, opponent) -> str:
    """
    you, opponent: 6x6 array-like containing 0/1
    Return: "row,col,quad,dir"
    """
    # Convert to bitboards
    you_b = 0
    opp_b = 0
    for r in range(6):
        rowy = you[r]
        rowo = opponent[r]
        for c in range(6):
            idx = r * 6 + c
            if int(rowy[c]) == 1:
                you_b |= 1 << idx
            elif int(rowo[c]) == 1:
                opp_b |= 1 << idx

    start = time.perf_counter()
    time_limit = 0.96  # safety margin

    # Generate all legal moves
    all_moves = _generate_moves(you_b, opp_b)
    if not all_moves:
        # Should not happen per problem statement, but must return something legal-looking.
        return "1,1,0,L"

    # 1) Immediate win search (prefer pure win over draw)
    best_draw_move = None
    for (idx, q, di) in all_moves:
        # ensure empty
        if ((you_b | opp_b) >> idx) & 1:
            continue
        ny, no = _apply_move(you_b, opp_b, idx, q, di, True)
        t = _terminal_value(ny, no)
        if t == WIN_SCORE:
            return MOVE_STR[idx][q][di]
        if t == 0 and best_draw_move is None:
            # draw by double-win or full board; keep as fallback if needed
            best_draw_move = MOVE_STR[idx][q][di]

    # 2) Depth-2 minimax with move ordering and pruning
    # Order root candidates by static eval after our move
    scored = []
    for (idx, q, di) in all_moves:
        if ((you_b | opp_b) >> idx) & 1:
            continue
        ny, no = _apply_move(you_b, opp_b, idx, q, di, True)
        t = _terminal_value(ny, no)
        if t is None:
            v = _eval(ny, no)
        else:
            v = t
        scored.append((v, idx, q, di))

    # If somehow no scored moves, return any legal move string
    if not scored:
        idx, q, di = all_moves[0]
        return MOVE_STR[idx][q][di]

    scored.sort(reverse=True, key=lambda x: x[0])

    # Limit breadth for speed; keep more if board is sparse
    empties = 36 - (you_b | opp_b).bit_count()
    root_k = 70 if empties >= 18 else 50
    opp_k = 50 if empties >= 18 else 35
    root_candidates = scored[: min(root_k, len(scored))]

    best_val = -10**18
    best_move = (root_candidates[0][1], root_candidates[0][2], root_candidates[0][3])

    for _, idx, q, di in root_candidates:
        if time.perf_counter() - start > time_limit:
            break

        ny, no = _apply_move(you_b, opp_b, idx, q, di, True)
        t = _terminal_value(ny, no)
        if t is not None:
            # WIN already handled; if draw, consider but keep searching for better
            val_after = t
            if val_after > best_val:
                best_val = val_after
                best_move = (idx, q, di)
            continue

        # Opponent replies: choose move minimizing our eval
        opp_moves = _generate_moves(ny, no)

        # Order opponent replies by (our eval after their move) ascending
        opp_scored = []
        for (oidx, oq, odi) in opp_moves:
            if ((ny | no) >> oidx) & 1:
                continue
            y2, o2 = _apply_move(ny, no, oidx, oq, odi, False)
            tt = _terminal_value(y2, o2)
            if tt is None:
                vv = _eval(y2, o2)
            else:
                vv = tt
            opp_scored.append((vv, oidx, oq, odi))

        if not opp_scored:
            # No opponent move means board full; treat as draw
            val = 0
        else:
            opp_scored.sort(key=lambda x: x[0])  # opponent wants smallest for us
            opp_considered = opp_scored[: min(opp_k, len(opp_scored))]

            worst_for_us = 10**18
            # alpha-beta style prune: if opponent can already force <= best_val, stop
            for vv, oidx, oq, odi in opp_considered:
                if time.perf_counter() - start > time_limit:
                    break
                if vv < worst_for_us:
                    worst_for_us = vv
                if worst_for_us <= best_val:
                    break
            val = worst_for_us

        if val > best_val:
            best_val = val
            best_move = (idx, q, di)

    # If we found only a draw fallback and best is very bad, still return best_move (legal).
    # Ensure legality and return.
    idx, q, di = best_move
    if ((you_b | opp_b) >> idx) & 1:
        # Safety fallback to first legal move in all_moves
        for (i2, q2, di2) in all_moves:
            if ((you_b | opp_b) >> i2) & 1:
                continue
            return MOVE_STR[i2][q2][di2]
        return "1,1,0,L"

    # Prefer draw move if everything looks losing extremely and we have a guaranteed draw now.
    if best_draw_move is not None and best_val < -WIN_SCORE // 5:
        return best_draw_move

    return MOVE_STR[idx][q][di]
