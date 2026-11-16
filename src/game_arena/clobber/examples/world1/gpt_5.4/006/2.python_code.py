
import time
from typing import List, Tuple

ROWS = 5
COLS = 6
DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
CENTER_R = 2.0
CENTER_C = 2.5


def _to_masks(you, opp):
    my_mask = 0
    op_mask = 0
    idx = 0
    for r in range(ROWS):
        yr = you[r]
        orow = opp[r]
        for c in range(COLS):
            if yr[c]:
                my_mask |= (1 << idx)
            elif orow[c]:
                op_mask |= (1 << idx)
            idx += 1
    return my_mask, op_mask


def _bit(rc):
    r, c = rc
    return 1 << (r * COLS + c)


def _iter_bits(mask):
    while mask:
        lsb = mask & -mask
        yield lsb
        mask ^= lsb


def _bit_index(lsb):
    return lsb.bit_length() - 1


def _rc_from_idx(idx):
    return idx // COLS, idx % COLS


def _legal_moves(my_mask: int, op_mask: int):
    moves = []
    for b in _iter_bits(my_mask):
        idx = _bit_index(b)
        r, c = _rc_from_idx(idx)
        for dr, dc, ch in DIRS:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                nidx = nr * COLS + nc
                nb = 1 << nidx
                if op_mask & nb:
                    moves.append((idx, nidx, ch))
    return moves


def _apply_move(my_mask: int, op_mask: int, move):
    src, dst, _ = move
    srcb = 1 << src
    dstb = 1 << dst
    new_my = (my_mask ^ srcb) | dstb
    new_op = op_mask ^ dstb
    return new_op, new_my  # swap side to move


def _adj_enemy_count(pos_idx: int, enemy_mask: int):
    r, c = _rc_from_idx(pos_idx)
    cnt = 0
    if r > 0 and (enemy_mask & (1 << ((r - 1) * COLS + c))):
        cnt += 1
    if c + 1 < COLS and (enemy_mask & (1 << (r * COLS + c + 1))):
        cnt += 1
    if r + 1 < ROWS and (enemy_mask & (1 << ((r + 1) * COLS + c))):
        cnt += 1
    if c > 0 and (enemy_mask & (1 << (r * COLS + c - 1))):
        cnt += 1
    return cnt


def _adj_friend_count(pos_idx: int, my_mask: int):
    r, c = _rc_from_idx(pos_idx)
    cnt = 0
    if r > 0 and (my_mask & (1 << ((r - 1) * COLS + c))):
        cnt += 1
    if c + 1 < COLS and (my_mask & (1 << (r * COLS + c + 1))):
        cnt += 1
    if r + 1 < ROWS and (my_mask & (1 << ((r + 1) * COLS + c))):
        cnt += 1
    if c > 0 and (my_mask & (1 << (r * COLS + c - 1))):
        cnt += 1
    return cnt


def _evaluate(my_mask: int, op_mask: int):
    my_moves = _legal_moves(my_mask, op_mask)
    if not my_moves:
        return -100000
    op_moves = _legal_moves(op_mask, my_mask)
    if not op_moves:
        return 100000

    score = 0

    score += 120 * (len(my_moves) - len(op_moves))
    score += 18 * (my_mask.bit_count() - op_mask.bit_count())

    my_attack = 0
    my_risk = 0
    my_shape = 0
    my_center = 0.0
    for b in _iter_bits(my_mask):
        idx = _bit_index(b)
        r, c = _rc_from_idx(idx)
        my_attack += _adj_enemy_count(idx, op_mask)
        my_risk += _adj_enemy_count(idx, op_mask)
        my_shape += _adj_friend_count(idx, my_mask)
        my_center -= abs(r - CENTER_R) + abs(c - CENTER_C)

    op_attack = 0
    op_risk = 0
    op_shape = 0
    op_center = 0.0
    for b in _iter_bits(op_mask):
        idx = _bit_index(b)
        r, c = _rc_from_idx(idx)
        op_attack += _adj_enemy_count(idx, my_mask)
        op_risk += _adj_enemy_count(idx, my_mask)
        op_shape += _adj_friend_count(idx, op_mask)
        op_center -= abs(r - CENTER_R) + abs(c - CENTER_C)

    score += 20 * (my_attack - op_attack)
    score += 6 * (my_shape - op_shape)
    score += int(3 * (my_center - op_center))
    score -= 14 * my_risk
    score += 14 * op_risk

    return score


def _move_order_score(my_mask: int, op_mask: int, move):
    src, dst, _ = move
    new_my, new_op = _apply_move_no_swap(my_mask, op_mask, move)

    opp_moves = _legal_moves(new_op, new_my)
    if not opp_moves:
        return 10**9

    my_next_moves = _legal_moves(new_my, new_op)

    dst_attack = _adj_enemy_count(dst, new_op)
    dst_risk = _adj_enemy_count(dst, new_op)
    src_r, src_c = _rc_from_idx(src)
    dst_r, dst_c = _rc_from_idx(dst)
    center_gain = (abs(src_r - CENTER_R) + abs(src_c - CENTER_C)) - (abs(dst_r - CENTER_R) + abs(dst_c - CENTER_C))

    return (
        5000 * (len(my_next_moves) - len(opp_moves))
        + 200 * dst_attack
        - 180 * dst_risk
        + int(20 * center_gain)
    )


def _apply_move_no_swap(my_mask: int, op_mask: int, move):
    src, dst, _ = move
    srcb = 1 << src
    dstb = 1 << dst
    new_my = (my_mask ^ srcb) | dstb
    new_op = op_mask ^ dstb
    return new_my, new_op


def _alphabeta(my_mask: int, op_mask: int, depth: int, alpha: int, beta: int, end_time: float):
    if time.time() >= end_time:
        raise TimeoutError

    moves = _legal_moves(my_mask, op_mask)
    if not moves:
        return -100000 - depth, None
    if depth == 0:
        return _evaluate(my_mask, op_mask), None

    ordered = sorted(moves, key=lambda m: _move_order_score(my_mask, op_mask, m), reverse=True)

    best_move = ordered[0]
    best_val = -10**18

    for mv in ordered:
        nmy, nop = _apply_move(my_mask, op_mask, mv)
        child_val, _ = _alphabeta(nmy, nop, depth - 1, -beta, -alpha, end_time)
        val = -child_val

        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    return best_val, best_move


def _move_to_str(move):
    src, _, ch = move
    r, c = _rc_from_idx(src)
    return f"{r},{c},{ch}"


def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    my_mask, op_mask = _to_masks(you, opponent)
    legal = _legal_moves(my_mask, op_mask)

    if not legal:
        # Should not happen in valid arena states, but return a syntactically valid string.
        return "0,0,R"

    # Immediate tactical checks
    winning = []
    safeish = []
    for mv in legal:
        nmy, nop = _apply_move_no_swap(my_mask, op_mask, mv)
        opp_moves = _legal_moves(nop, nmy)
        if not opp_moves:
            winning.append(mv)
        else:
            risk = _adj_enemy_count(mv[1], nop)
            if risk == 0:
                safeish.append(mv)

    if winning:
        best = max(winning, key=lambda m: _move_order_score(my_mask, op_mask, m))
        return _move_to_str(best)

    # Search with iterative deepening
    end_time = time.time() + 0.92
    best_move = max(legal, key=lambda m: _move_order_score(my_mask, op_mask, m))

    try:
        depth = 1
        while depth <= 12:
            val, mv = _alphabeta(my_mask, op_mask, depth, -10**18, 10**18, end_time)
            if mv is not None:
                best_move = mv
            depth += 1
    except TimeoutError:
        pass
    except Exception:
        # Safety fallback
        if safeish:
            best_move = max(safeish, key=lambda m: _move_order_score(my_mask, op_mask, m))
        else:
            best_move = max(legal, key=lambda m: _move_order_score(my_mask, op_mask, m))

    # Final legality safeguard
    move_str = _move_to_str(best_move)

    src, dst, ch = best_move
    srcb = 1 << src
    dstb = 1 << dst
    if (my_mask & srcb) and (op_mask & dstb):
        return move_str

    # Guaranteed legal fallback
    fallback = legal[0]
    return _move_to_str(fallback)
