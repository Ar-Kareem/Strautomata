
import numpy as np
from functools import lru_cache

# 4x4 boxes:
# Horizontal legal edges: row 0..4, col 0..3
# Vertical legal edges:   row 0..3, col 0..4

N = 4


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    h = np.array(horizontal, copy=True)
    v = np.array(vertical, copy=True)
    c = np.array(capture, copy=True)

    moves = legal_moves(h, v)
    if not moves:
        # Should never happen before game end, but return any empty array slot if present.
        fallback = any_empty_array_slot(horizontal, vertical)
        return fallback if fallback is not None else "0,0,H"

    # Exact search in late game.
    if len(moves) <= 13:
        try:
            best = choose_by_full_search(h, v, c, moves)
            if best is not None:
                return move_to_str(best)
        except Exception:
            pass

    # 1. Take captures immediately.
    captures = []
    for m in moves:
        gain = capture_count_after_move(h, v, c, m)
        if gain > 0:
            captures.append((gain, m))

    if captures:
        # Prefer moves that score more, then that leave fewer immediate replies.
        best_score = -10**9
        best_move = captures[0][1]
        for gain, m in captures:
            hh, vv, cc, _ = apply_move(h, v, c, m, 1)
            opp_caps = sum(1 for om in legal_moves(hh, vv) if capture_count_after_move(hh, vv, cc, om) > 0)
            score = 100 * gain - 7 * opp_caps + position_heuristic(hh, vv, cc)
            if score > best_score:
                best_score = score
                best_move = m
        return move_to_str(best_move)

    # 2. Prefer safe non-capturing moves that do not create a 3-sided box.
    safe = []
    for m in moves:
        if is_safe_move(h, v, c, m):
            safe.append(m)

    if safe:
        best_score = -10**9
        best_move = safe[0]
        for m in safe:
            hh, vv, cc, _ = apply_move(h, v, c, m, 1)

            # Prefer positions with many remaining safe moves and few future capture gifts.
            future_safe = sum(1 for x in legal_moves(hh, vv) if capture_count_after_move(hh, vv, cc, x) == 0 and is_safe_move(hh, vv, cc, x))
            future_caps = sum(1 for x in legal_moves(hh, vv) if capture_count_after_move(hh, vv, cc, x) > 0)

            # Prefer playing around boxes with fewer sides.
            local = -local_danger(h, v, c, m)

            score = 10 * future_safe - 20 * future_caps + 3 * local + position_heuristic(hh, vv, cc)
            if score > best_score:
                best_score = score
                best_move = m
        return move_to_str(best_move)

    # 3. No safe move exists: sacrifice as little as possible.
    best_score = -10**9
    best_move = moves[0]
    for m in moves:
        hh, vv, cc, _ = apply_move(h, v, c, m, 1)

        # Count boxes we create with exactly three sides, which opponent can likely take.
        created_threes = count_three_sided_boxes(hh, vv, cc)

        # Count opponent immediate captures.
        opp_capture_moves = 0
        opp_capture_amount = 0
        for om in legal_moves(hh, vv):
            g = capture_count_after_move(hh, vv, cc, om)
            if g > 0:
                opp_capture_moves += 1
                opp_capture_amount += g

        score = (
            -100 * opp_capture_amount
            -30 * opp_capture_moves
            -15 * created_threes
            + position_heuristic(hh, vv, cc)
        )

        if score > best_score:
            best_score = score
            best_move = m

    return move_to_str(best_move)


def legal_moves(h, v):
    out = []
    for r in range(N + 1):
        for col in range(N):
            if h[r, col] == 0:
                out.append((r, col, "H"))
    for r in range(N):
        for col in range(N + 1):
            if v[r, col] == 0:
                out.append((r, col, "V"))
    return out


def any_empty_array_slot(horizontal, vertical):
    for r in range(5):
        for col in range(5):
            if horizontal[r, col] == 0:
                return f"{r},{col},H"
    for r in range(5):
        for col in range(5):
            if vertical[r, col] == 0:
                return f"{r},{col},V"
    return None


def move_to_str(m):
    return f"{m[0]},{m[1]},{m[2]}"


def box_sides(h, v, r, col):
    return (
        int(h[r, col] != 0) +
        int(h[r + 1, col] != 0) +
        int(v[r, col] != 0) +
        int(v[r, col + 1] != 0)
    )


def adjacent_boxes(m):
    r, col, d = m
    boxes = []
    if d == "H":
        if r > 0 and 0 <= col < N:
            boxes.append((r - 1, col))
        if r < N and 0 <= col < N:
            boxes.append((r, col))
    else:
        if col > 0 and 0 <= r < N:
            boxes.append((r, col - 1))
        if col < N and 0 <= r < N:
            boxes.append((r, col))
    return boxes


def capture_count_after_move(h, v, c, m):
    r, col, d = m
    if d == "H":
        if h[r, col] != 0:
            return -1
    else:
        if v[r, col] != 0:
            return -1

    # Temporarily count as filled.
    gain = 0
    for br, bc in adjacent_boxes(m):
        if c[br, bc] == 0:
            sides = box_sides(h, v, br, bc)
            # The move is one of this box's missing edges, so sides increases by one.
            if sides + 1 >= 4:
                gain += 1
    return gain


def apply_move(h, v, c, m, player):
    hh = h.copy()
    vv = v.copy()
    cc = c.copy()
    r, col, d = m

    if d == "H":
        hh[r, col] = player
    else:
        vv[r, col] = player

    gain = 0
    for br, bc in adjacent_boxes(m):
        if cc[br, bc] == 0 and box_sides(hh, vv, br, bc) >= 4:
            cc[br, bc] = player
            gain += 1

    return hh, vv, cc, gain


def is_safe_move(h, v, c, m):
    # A safe move is non-scoring and does not create any unclaimed 3-sided box.
    if capture_count_after_move(h, v, c, m) > 0:
        return True

    hh, vv, cc, _ = apply_move(h, v, c, m, 1)

    for br, bc in adjacent_boxes(m):
        if cc[br, bc] == 0 and box_sides(hh, vv, br, bc) == 3:
            return False
    return True


def count_three_sided_boxes(h, v, c):
    total = 0
    for r in range(N):
        for col in range(N):
            if c[r, col] == 0 and box_sides(h, v, r, col) == 3:
                total += 1
    return total


def local_danger(h, v, c, m):
    # Higher means more dangerous local area before the move.
    danger = 0
    for br, bc in adjacent_boxes(m):
        if c[br, bc] == 0:
            s = box_sides(h, v, br, bc)
            danger += s * s
    return danger


def position_heuristic(h, v, c):
    # Positive is good for us.
    score = int(np.sum(c))

    # Penalize unclaimed boxes with three sides, reward stable low-side boxes.
    threes = 0
    twos = 0
    ones = 0
    for r in range(N):
        for col in range(N):
            if c[r, col] == 0:
                s = box_sides(h, v, r, col)
                if s == 3:
                    threes += 1
                elif s == 2:
                    twos += 1
                elif s <= 1:
                    ones += 1

    return 20 * score - 5 * threes + 1 * ones - 1 * twos


def choose_by_full_search(h, v, c, moves):
    # Alpha-beta exact search from current player = us.
    key0 = make_key(h, v, c, 1)

    @lru_cache(maxsize=200000)
    def search(key):
        hh, vv, cc, player = unpack_key(key)
        ms = legal_moves(hh, vv)
        if not ms:
            return int(np.sum(cc))

        if player == 1:
            best = -10**9
            alpha = -10**9
            beta = 10**9
            ordered = order_moves(hh, vv, cc, ms)
            for m in ordered:
                nh, nv, nc, gain = apply_move(hh, vv, cc, m, player)
                np_player = player if gain > 0 else -player
                val = search(make_key(nh, nv, nc, np_player))
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best
        else:
            best = 10**9
            alpha = -10**9
            beta = 10**9
            ordered = order_moves(hh, vv, cc, ms)
            for m in ordered:
                nh, nv, nc, gain = apply_move(hh, vv, cc, m, player)
                np_player = player if gain > 0 else -player
                val = search(make_key(nh, nv, nc, np_player))
                if val < best:
                    best = val
                if best < beta:
                    beta = best
                if alpha >= beta:
                    break
            return best

    best_val = -10**9
    best_move = None

    for m in order_moves(h, v, c, moves):
        nh, nv, nc, gain = apply_move(h, v, c, m, 1)
        np_player = 1 if gain > 0 else -1
        val = search(make_key(nh, nv, nc, np_player))
        if val > best_val:
            best_val = val
            best_move = m

    return best_move


def order_moves(h, v, c, moves):
    def score(m):
        g = capture_count_after_move(h, v, c, m)
        safe = is_safe_move(h, v, c, m)
        return 100 * g + (10 if safe else 0) - local_danger(h, v, c, m)

    return sorted(moves, key=score, reverse=True)


def make_key(h, v, c, player):
    # Only standard geometry matters.
    hb = tuple(int(x) for x in h[:N + 1, :N].reshape(-1))
    vb = tuple(int(x) for x in v[:N, :N + 1].reshape(-1))
    cb = tuple(int(x) for x in c[:N, :N].reshape(-1))
    return hb + vb + cb + (int(player),)


def unpack_key(key):
    idx = 0

    hh = np.zeros((5, 5), dtype=int)
    vv = np.zeros((5, 5), dtype=int)
    cc = np.zeros((5, 5), dtype=int)

    hvals = key[idx:idx + (N + 1) * N]
    idx += (N + 1) * N
    hh[:N + 1, :N] = np.array(hvals, dtype=int).reshape((N + 1, N))

    vvals = key[idx:idx + N * (N + 1)]
    idx += N * (N + 1)
    vv[:N, :N + 1] = np.array(vvals, dtype=int).reshape((N, N + 1))

    cvals = key[idx:idx + N * N]
    idx += N * N
    cc[:N, :N] = np.array(cvals, dtype=int).reshape((N, N))

    player = int(key[-1])
    return hh, vv, cc, player
