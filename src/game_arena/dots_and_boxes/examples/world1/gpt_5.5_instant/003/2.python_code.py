
import numpy as np
from functools import lru_cache

N = 4

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    H = (horizontal != 0).astype(np.int8)
    V = (vertical != 0).astype(np.int8)

    def legal_moves(h, v):
        moves = []
        for r in range(N + 1):
            for c in range(N):
                if h[r, c] == 0:
                    moves.append((r, c, 'H'))
        for r in range(N):
            for c in range(N + 1):
                if v[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves

    def box_sides(h, v, r, c):
        return int(h[r, c] != 0) + int(h[r + 1, c] != 0) + int(v[r, c] != 0) + int(v[r, c + 1] != 0)

    def adjacent_boxes(move):
        r, c, d = move
        out = []
        if d == 'H':
            if r > 0:
                out.append((r - 1, c))
            if r < N:
                out.append((r, c))
        else:
            if c > 0:
                out.append((r, c - 1))
            if c < N:
                out.append((r, c))
        return out

    def apply_move(h, v, move):
        h2 = h.copy()
        v2 = v.copy()
        r, c, d = move
        gained = 0

        if d == 'H':
            h2[r, c] = 1
        else:
            v2[r, c] = 1

        for br, bc in adjacent_boxes(move):
            if box_sides(h2, v2, br, bc) == 4:
                gained += 1

        return h2, v2, gained

    def move_to_str(m):
        return f"{m[0]},{m[1]},{m[2]}"

    moves = legal_moves(H, V)
    if not moves:
        return "0,0,H"

    # 1. Take immediate captures, preferring double captures.
    capture_moves = []
    for m in moves:
        h2, v2, gain = apply_move(H, V, m)
        if gain > 0:
            # Prefer captures that leave fewer immediate captures for opponent if turn continues later.
            danger = 0
            for om in legal_moves(h2, v2):
                _, _, og = apply_move(h2, v2, om)
                if og > 0:
                    danger += og
            capture_moves.append((gain, -danger, m))

    if capture_moves:
        capture_moves.sort(reverse=True, key=lambda x: (x[0], x[1]))
        return move_to_str(capture_moves[0][2])

    # Helper: count newly created 3-sided boxes after a non-capturing move.
    def created_threes(h, v, move):
        h2, v2, gain = apply_move(h, v, move)
        if gain > 0:
            return 99
        cnt = 0
        for br, bc in adjacent_boxes(move):
            if box_sides(h2, v2, br, bc) == 3:
                cnt += 1
        return cnt

    # 2. Prefer completely safe moves.
    safe = []
    for m in moves:
        h2, v2, gain = apply_move(H, V, m)
        if gain == 0:
            bad = 0
            for br, bc in adjacent_boxes(m):
                if box_sides(h2, v2, br, bc) == 3:
                    bad += 1
            if bad == 0:
                # Positional heuristic: prefer boundary/corner-ish edges and low total side pressure.
                pressure = 0
                twos = 0
                ones = 0
                for br, bc in adjacent_boxes(m):
                    s = box_sides(h2, v2, br, bc)
                    pressure += s
                    if s == 2:
                        twos += 1
                    if s == 1:
                        ones += 1

                # Count opponent capture opportunities after this move.
                opp_caps = 0
                for om in legal_moves(h2, v2):
                    _, _, og = apply_move(h2, v2, om)
                    if og > 0:
                        opp_caps += og

                # Slight preference for edges touching fewer boxes, i.e. boundary edges.
                boundary_bonus = 2 - len(adjacent_boxes(m))
                safe.append((opp_caps, twos, pressure, -boundary_bonus, -ones, m))

    if safe:
        safe.sort(key=lambda x: (x[0], x[1], x[2], x[3], x[4]))
        return move_to_str(safe[0][5])

    # 3. If all moves give away boxes, use a small negamax search.
    # Score is boxes gained by side-to-move minus opponent boxes from this point.
    def pack(h, v):
        return (tuple(h[:, :N].reshape(-1).tolist()), tuple(v[:N, :].reshape(-1).tolist()))

    @lru_cache(None)
    def negamax(hkey, vkey, depth):
        h = np.array(hkey, dtype=np.int8).reshape((N + 1, N))
        v = np.array(vkey, dtype=np.int8).reshape((N, N + 1))
        lm = legal_moves(h, v)

        if not lm:
            return 0

        if depth <= 0:
            # Static evaluation: penalize available captures for side to move,
            # reward forced opportunities already present.
            val = 0
            for m in lm:
                _, _, g = apply_move(h, v, m)
                if g > 0:
                    val += 2 * g
                else:
                    ct = created_threes(h, v, m)
                    val -= ct
            return val

        best = -10**9
        # Search promising moves first.
        ordered = []
        for m in lm:
            h2, v2, g = apply_move(h, v, m)
            ct = created_threes(h, v, m) if g == 0 else -g
            ordered.append((ct, -g, m, h2, v2, g))
        ordered.sort(key=lambda x: (x[0], x[1]))

        for _, _, m, h2, v2, g in ordered:
            hk, vk = pack(h2, v2)
            if g > 0:
                # Extra turn: same player continues.
                val = g + negamax(hk, vk, depth - 1)
            else:
                # Turn passes.
                val = -negamax(hk, vk, depth - 1)
            if val > best:
                best = val
        return best

    remaining = len(moves)
    depth = 8 if remaining <= 14 else 6

    best_move = moves[0]
    best_val = -10**9

    ordered_root = []
    for m in moves:
        h2, v2, g = apply_move(H, V, m)
        ct = created_threes(H, V, m) if g == 0 else -g
        ordered_root.append((ct, -g, m, h2, v2, g))
    ordered_root.sort(key=lambda x: (x[0], x[1]))

    for _, _, m, h2, v2, g in ordered_root:
        hk, vk = pack(h2, v2)
        if g > 0:
            val = g + negamax(hk, vk, depth - 1)
        else:
            val = -negamax(hk, vk, depth - 1)

        # Tie-break: give away fewer immediate boxes.
        giveaway = 0
        for om in legal_moves(h2, v2):
            _, _, og = apply_move(h2, v2, om)
            giveaway = max(giveaway, og)

        val2 = val - 0.05 * giveaway
        if val2 > best_val:
            best_val = val2
            best_move = m

    return move_to_str(best_move)
