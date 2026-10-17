
import numpy as np
import time
import math
from functools import lru_cache

N = 4
TIME_LIMIT = 0.90


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    start = time.time()

    H = (horizontal != 0).astype(np.int8)
    V = (vertical != 0).astype(np.int8)
    C = np.array(capture, dtype=np.int8)

    moves = legal_moves(H, V)
    if not moves:
        return "0,0,H"  # Should never happen in valid non-terminal calls.

    # 1. Immediate captures are almost always mandatory/good.
    caps = []
    for m in moves:
        gain = capture_count(H, V, C, m)
        if gain > 0:
            caps.append((gain, m))

    if caps:
        # In forced capture phases, shallow minimax can choose between captures.
        if len(moves) <= 18:
            best = try_minimax(H, V, C, moves, start)
            if best is not None:
                return fmt(best)
        caps.sort(key=lambda x: (x[0], capture_tiebreak_score(H, V, C, x[1])), reverse=True)
        return fmt(caps[0][1])

    # 2. If possible, play a safe move that creates no 3-sided box.
    safe = [m for m in moves if not creates_third_side(H, V, C, m)]
    if safe:
        # Mid/late game minimax if feasible.
        if len(moves) <= 20:
            best = try_minimax(H, V, C, moves, start)
            if best is not None:
                return fmt(best)

        safe.sort(key=lambda m: safe_move_score(H, V, C, m), reverse=True)
        return fmt(safe[0])

    # 3. No safe moves: sacrifice. Use minimax if possible, otherwise heuristic.
    if len(moves) <= 24:
        best = try_minimax(H, V, C, moves, start)
        if best is not None:
            return fmt(best)

    moves.sort(key=lambda m: sacrifice_score(H, V, C, m), reverse=True)
    return fmt(moves[0])


def legal_moves(H, V):
    ms = []
    for r in range(5):
        for c in range(4):
            if H[r, c] == 0:
                ms.append((r, c, 'H'))
    for r in range(4):
        for c in range(5):
            if V[r, c] == 0:
                ms.append((r, c, 'V'))
    return ms


def fmt(m):
    return f"{m[0]},{m[1]},{m[2]}"


def box_sides(H, V, r, c):
    return int(H[r, c]) + int(H[r + 1, c]) + int(V[r, c]) + int(V[r, c + 1])


def adjacent_boxes(m):
    r, c, d = m
    bs = []
    if d == 'H':
        if r > 0 and c < 4:
            bs.append((r - 1, c))
        if r < 4 and c < 4:
            bs.append((r, c))
    else:
        if c > 0 and r < 4:
            bs.append((r, c - 1))
        if c < 4 and r < 4:
            bs.append((r, c))
    return [(br, bc) for br, bc in bs if 0 <= br < 4 and 0 <= bc < 4]


def capture_count(H, V, C, m):
    cnt = 0
    for r, c in adjacent_boxes(m):
        if C[r, c] == 0 and box_sides(H, V, r, c) == 3:
            cnt += 1
    return cnt


def apply_move(H, V, C, m, player):
    H2 = H.copy()
    V2 = V.copy()
    C2 = C.copy()
    r, c, d = m
    if d == 'H':
        H2[r, c] = 1
    else:
        V2[r, c] = 1
    gain = 0
    for br, bc in adjacent_boxes(m):
        if C2[br, bc] == 0 and box_sides(H2, V2, br, bc) == 4:
            C2[br, bc] = player
            gain += 1
    return H2, V2, C2, gain


def creates_third_side(H, V, C, m):
    H2 = H.copy()
    V2 = V.copy()
    r, c, d = m
    if d == 'H':
        H2[r, c] = 1
    else:
        V2[r, c] = 1
    for br, bc in adjacent_boxes(m):
        if C[br, bc] == 0 and box_sides(H2, V2, br, bc) == 3:
            return True
    return False


def count_threes_after(H, V, C, m):
    H2 = H.copy()
    V2 = V.copy()
    r, c, d = m
    if d == 'H':
        H2[r, c] = 1
    else:
        V2[r, c] = 1
    t = 0
    for br in range(4):
        for bc in range(4):
            if C[br, bc] == 0 and box_sides(H2, V2, br, bc) == 3:
                t += 1
    return t


def safe_move_score(H, V, C, m):
    # Higher is better.
    r, c, d = m
    score = 0.0

    # Prefer edges adjacent to boxes with fewer sides.
    for br, bc in adjacent_boxes(m):
        s = box_sides(H, V, br, bc)
        score += (2 - s) * 5

    # Prefer border moves: they affect only one box, often safer strategically.
    if len(adjacent_boxes(m)) == 1:
        score += 3.0

    # Slightly prefer corners/outer frame.
    if d == 'H':
        if r == 0 or r == 4:
            score += 2.0
        if c == 0 or c == 3:
            score += 0.5
    else:
        if c == 0 or c == 4:
            score += 2.0
        if r == 0 or r == 3:
            score += 0.5

    # Avoid making many 2-sided boxes if alternatives exist.
    H2, V2, C2, _ = apply_move(H, V, C, m, 1)
    twos = 0
    ones = 0
    for br in range(4):
        for bc in range(4):
            if C2[br, bc] == 0:
                s = box_sides(H2, V2, br, bc)
                if s == 2:
                    twos += 1
                elif s <= 1:
                    ones += 1
    score -= 0.8 * twos
    score += 0.15 * ones

    # Deterministic tiny tie breaker.
    score -= 0.001 * (r * 10 + c + (0 if d == 'H' else 50))
    return score


def capture_tiebreak_score(H, V, C, m):
    H2, V2, C2, gain = apply_move(H, V, C, m, 1)
    # After capturing, prefer positions with more further captures for us.
    further = sum(capture_count(H2, V2, C2, x) for x in legal_moves(H2, V2))
    return 10 * gain + further - 0.5 * count_threes_global(H2, V2, C2)


def sacrifice_score(H, V, C, m):
    # Higher is better: give opponent fewer immediate boxes/chains.
    H2, V2, C2, _ = apply_move(H, V, C, m, 1)
    opp_caps = [capture_count(H2, V2, C2, x) for x in legal_moves(H2, V2)]
    maxcap = max(opp_caps) if opp_caps else 0
    totalcap = sum(opp_caps)
    threes = count_threes_global(H2, V2, C2)

    # Prefer opening the smallest apparent chain.
    opened = 0
    for br, bc in adjacent_boxes(m):
        if C2[br, bc] == 0 and box_sides(H2, V2, br, bc) == 3:
            opened += estimate_chain_len(H2, V2, C2, br, bc)

    border = 1 if len(adjacent_boxes(m)) == 1 else 0
    return -100 * maxcap - 10 * totalcap - 3 * threes - opened + border


def count_threes_global(H, V, C):
    t = 0
    for r in range(4):
        for c in range(4):
            if C[r, c] == 0 and box_sides(H, V, r, c) == 3:
                t += 1
    return t


def estimate_chain_len(H, V, C, sr, sc):
    # Rough BFS through boxes connected by undrawn shared edges.
    seen = set()
    stack = [(sr, sc)]
    while stack:
        r, c = stack.pop()
        if (r, c) in seen or not (0 <= r < 4 and 0 <= c < 4) or C[r, c] != 0:
            continue
        if box_sides(H, V, r, c) < 2:
            continue
        seen.add((r, c))
        # up shared H[r,c]
        if r > 0 and H[r, c] == 0:
            stack.append((r - 1, c))
        if r < 3 and H[r + 1, c] == 0:
            stack.append((r + 1, c))
        if c > 0 and V[r, c] == 0:
            stack.append((r, c - 1))
        if c < 3 and V[r, c + 1] == 0:
            stack.append((r, c + 1))
    return len(seen)


def serialize(H, V, C, turn):
    return (H.tobytes(), V.tobytes(), C.tobytes(), turn)


def eval_pos(H, V, C):
    # Evaluation from current policy player's perspective.
    my = int(np.sum(C == 1))
    op = int(np.sum(C == -1))
    val = 100.0 * (my - op)

    # Mobility/safety heuristic.
    ms = legal_moves(H, V)
    caps = sum(capture_count(H, V, C, m) for m in ms)
    safe = sum(1 for m in ms if capture_count(H, V, C, m) == 0 and not creates_third_side(H, V, C, m))
    threes = count_threes_global(H, V, C)

    val += 8.0 * caps
    val += 1.2 * safe
    val -= 4.0 * threes
    return val


def ordered_moves(H, V, C, moves, turn):
    def key(m):
        gain = capture_count(H, V, C, m)
        safe = not creates_third_side(H, V, C, m) if gain == 0 else True
        if turn == 1:
            return (gain * 1000 + (100 if safe else 0) + safe_move_score(H, V, C, m))
        else:
            return (gain * 1000 + (100 if safe else 0) + safe_move_score(H, V, C, m))
    return sorted(moves, key=key, reverse=True)


def try_minimax(H, V, C, root_moves, start):
    remaining = len(root_moves)
    if remaining <= 10:
        depth = 20
    elif remaining <= 14:
        depth = 12
    elif remaining <= 18:
        depth = 8
    else:
        depth = 6

    best_move = None
    best_val = -1e18
    alpha = -1e18
    beta = 1e18
    cache = {}

    for m in ordered_moves(H, V, C, root_moves, 1):
        if time.time() - start > TIME_LIMIT:
            break
        H2, V2, C2, gain = apply_move(H, V, C, m, 1)
        next_turn = 1 if gain > 0 else -1
        val = minimax(H2, V2, C2, next_turn, depth - 1, alpha, beta, start, cache)
        if val > best_val:
            best_val = val
            best_move = m
        alpha = max(alpha, best_val)

    return best_move


def minimax(H, V, C, turn, depth, alpha, beta, start, cache):
    if time.time() - start > TIME_LIMIT:
        return eval_pos(H, V, C)

    ms = legal_moves(H, V)
    if not ms:
        return 1000.0 * (int(np.sum(C == 1)) - int(np.sum(C == -1)))

    if depth <= 0:
        return eval_pos(H, V, C)

    key = None
    if len(ms) <= 18:
        key = serialize(H, V, C, turn)
        if key in cache and cache[key][0] >= depth:
            return cache[key][1]

    if turn == 1:
        val = -1e18
        for m in ordered_moves(H, V, C, ms, turn):
            H2, V2, C2, gain = apply_move(H, V, C, m, 1)
            nt = 1 if gain > 0 else -1
            val = max(val, minimax(H2, V2, C2, nt, depth - 1, alpha, beta, start, cache))
            alpha = max(alpha, val)
            if beta <= alpha:
                break
    else:
        val = 1e18
        for m in ordered_moves(H, V, C, ms, turn):
            H2, V2, C2, gain = apply_move(H, V, C, m, -1)
            nt = -1 if gain > 0 else 1
            val = min(val, minimax(H2, V2, C2, nt, depth - 1, alpha, beta, start, cache))
            beta = min(beta, val)
            if beta <= alpha:
                break

    if key is not None:
        cache[key] = (depth, val)
    return val
