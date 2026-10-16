
import numpy as np
from functools import lru_cache
import math
import random

N = 4  # 4x4 boxes, 5x5 edge arrays


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    h = (horizontal != 0).astype(np.int8)
    v = (vertical != 0).astype(np.int8)

    moves = legal_moves(h, v)
    if not moves:
        return "0,0,H"  # should never happen in a valid non-terminal call

    # Endgame exact-ish alpha-beta.
    if len(moves) <= 14:
        best = None
        best_val = -10**9
        depth = min(18, len(moves) + 6)
        alpha = -10**9
        beta = 10**9
        for m in ordered_moves(h, v, moves):
            hh = h.copy()
            vv = v.copy()
            gained = apply_edge(hh, vv, m)
            if gained:
                val = gained + negamax(hh.tobytes(), vv.tobytes(), depth - 1, alpha, beta, 1)
            else:
                val = -negamax(hh.tobytes(), vv.tobytes(), depth - 1, -beta, -alpha, 1)
            if val > best_val:
                best_val = val
                best = m
            alpha = max(alpha, best_val)
        if best is not None:
            return move_to_str(best)

    # 1. Immediate captures.
    caps = []
    for m in moves:
        g = boxes_completed_by_move(h, v, m)
        if g > 0:
            caps.append(m)
    if caps:
        best = max(caps, key=lambda m: tactical_score_after_move(h, v, m))
        return move_to_str(best)

    # 2. Safe moves: do not create any 3-sided unclaimed box.
    safe = [m for m in moves if is_safe_move(h, v, m)]
    if safe:
        # Prefer moves that leave many future safe moves and avoid central overcommitment.
        best = max(safe, key=lambda m: safe_move_score(h, v, m))
        return move_to_str(best)

    # 3. No safe moves: sacrifice smallest chain/loop.
    best = min(moves, key=lambda m: sacrifice_cost(h, v, m))
    return move_to_str(best)


def legal_moves(h, v):
    res = []
    for r in range(5):
        for c in range(5):
            if h[r, c] == 0:
                res.append((r, c, 'H'))
            if v[r, c] == 0:
                res.append((r, c, 'V'))
    return res


def move_to_str(m):
    return f"{m[0]},{m[1]},{m[2]}"


def adjacent_boxes(m):
    r, c, d = m
    boxes = []
    if d == 'H':
        if 0 <= r - 1 < N and 0 <= c < N:
            boxes.append((r - 1, c))
        if 0 <= r < N and 0 <= c < N:
            boxes.append((r, c))
    else:
        if 0 <= r < N and 0 <= c - 1 < N:
            boxes.append((r, c - 1))
        if 0 <= r < N and 0 <= c < N:
            boxes.append((r, c))
    return boxes


def box_sides(h, v, r, c):
    return int(h[r, c]) + int(h[r + 1, c]) + int(v[r, c]) + int(v[r, c + 1])


def boxes_completed_by_move(h, v, m):
    cnt = 0
    for br, bc in adjacent_boxes(m):
        if box_sides(h, v, br, bc) == 3:
            cnt += 1
    return cnt


def apply_edge(h, v, m):
    r, c, d = m
    if d == 'H':
        h[r, c] = 1
    else:
        v[r, c] = 1
    gained = 0
    for br, bc in adjacent_boxes(m):
        if box_sides(h, v, br, bc) == 4:
            gained += 1
    return gained


def is_safe_move(h, v, m):
    if boxes_completed_by_move(h, v, m) > 0:
        return True
    hh = h.copy()
    vv = v.copy()
    apply_edge(hh, vv, m)
    for br, bc in adjacent_boxes(m):
        if box_sides(hh, vv, br, bc) == 3:
            return False
    return True


def safe_move_score(h, v, m):
    hh = h.copy()
    vv = v.copy()
    apply_edge(hh, vv, m)

    score = 0

    # Future safe mobility.
    lm = legal_moves(hh, vv)
    score += 8 * sum(1 for x in lm if is_safe_move(hh, vv, x))

    # Prefer edges touching boxes with fewer sides.
    for br, bc in adjacent_boxes(m):
        s = box_sides(h, v, br, bc)
        if s == 0:
            score += 4
        elif s == 1:
            score += 2
        elif s == 2:
            score -= 2

    # Mild preference for boundary moves early.
    r, c, d = m
    if d == 'H' and (r == 0 or r == 4):
        score += 2
    if d == 'V' and (c == 0 or c == 4):
        score += 2

    return score


def tactical_score_after_move(h, v, m):
    hh = h.copy()
    vv = v.copy()
    gained = apply_edge(hh, vv, m)
    score = 100 * gained

    # If we keep the turn, estimate capture continuation greedily.
    cont = greedy_capture_count(hh, vv)
    score += 30 * cont

    # Penalize leaving opponent captures if turn would pass, though captures keep turn.
    caps_left = sum(1 for x in legal_moves(hh, vv) if boxes_completed_by_move(hh, vv, x) > 0)
    score -= 5 * caps_left
    return score


def greedy_capture_count(h, v):
    hh = h.copy()
    vv = v.copy()
    total = 0
    while True:
        caps = [m for m in legal_moves(hh, vv) if boxes_completed_by_move(hh, vv, m) > 0]
        if not caps:
            break
        m = max(caps, key=lambda x: boxes_completed_by_move(hh, vv, x))
        total += apply_edge(hh, vv, m)
    return total


def sacrifice_cost(h, v, m):
    hh = h.copy()
    vv = v.copy()
    apply_edge(hh, vv, m)

    # Opponent can take capture chain. Estimate how many boxes become forced.
    return greedy_capture_count(hh, vv) * 100 - safe_move_score(h, v, m)


def ordered_moves(h, v, moves):
    return sorted(
        moves,
        key=lambda m: (
            boxes_completed_by_move(h, v, m),
            1 if is_safe_move(h, v, m) else 0,
            -sacrifice_cost(h, v, m)
        ),
        reverse=True
    )


@lru_cache(maxsize=200000)
def negamax(hb, vb, depth, alpha, beta, turnflag):
    h = np.frombuffer(hb, dtype=np.int8).reshape((5, 5)).copy()
    v = np.frombuffer(vb, dtype=np.int8).reshape((5, 5)).copy()
    moves = legal_moves(h, v)

    if not moves:
        return 0
    if depth <= 0:
        return heuristic_value(h, v)

    best = -10**9
    for m in ordered_moves(h, v, moves):
        hh = h.copy()
        vv = v.copy()
        gained = apply_edge(hh, vv, m)
        if gained:
            val = gained + negamax(hh.tobytes(), vv.tobytes(), depth - 1, alpha, beta, turnflag)
        else:
            val = -negamax(hh.tobytes(), vv.tobytes(), depth - 1, -beta, -alpha, 1 - turnflag)

        if val > best:
            best = val
        alpha = max(alpha, val)
        if alpha >= beta:
            break
    return best


def heuristic_value(h, v):
    # Positive means good for side to move.
    my_potential = 0
    opp_threats = 0

    for m in legal_moves(h, v):
        g = boxes_completed_by_move(h, v, m)
        if g:
            my_potential += 40 * g
        elif is_safe_move(h, v, m):
            my_potential += 2
        else:
            opp_threats += 5

    # In dots and boxes, having to open chains is bad.
    safe_count = sum(1 for m in legal_moves(h, v) if is_safe_move(h, v, m))
    if safe_count == 0:
        my_potential -= 15

    return my_potential - opp_threats
