
import numpy as np
from functools import lru_cache
import time

N = 4
TIME_LIMIT = 0.92

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    start_time = time.time()

    H0 = (horizontal != 0).astype(np.int8)
    V0 = (vertical != 0).astype(np.int8)
    C0 = capture.astype(np.int8)

    def legal_moves(H, V):
        moves = []
        for r in range(N + 1):
            for c in range(N):
                if H[r, c] == 0:
                    moves.append((r, c, 'H'))
        for r in range(N):
            for c in range(N + 1):
                if V[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves

    def box_sides(H, V, r, c):
        return int(H[r, c] != 0) + int(H[r + 1, c] != 0) + int(V[r, c] != 0) + int(V[r, c + 1] != 0)

    def completed_by_move(H, V, C, move):
        r, c, d = move
        made = 0
        if d == 'H':
            if r > 0 and C[r - 1, c] == 0 and box_sides(H, V, r - 1, c) == 3:
                made += 1
            if r < N and C[r, c] == 0 and box_sides(H, V, r, c) == 3:
                made += 1
        else:
            if c > 0 and C[r, c - 1] == 0 and box_sides(H, V, r, c - 1) == 3:
                made += 1
            if c < N and C[r, c] == 0 and box_sides(H, V, r, c) == 3:
                made += 1
        return made

    def apply_move(H, V, C, move, player):
        H2 = H.copy()
        V2 = V.copy()
        C2 = C.copy()
        r, c, d = move
        if d == 'H':
            H2[r, c] = player
        else:
            V2[r, c] = player

        gained = 0
        if d == 'H':
            if r > 0 and C2[r - 1, c] == 0 and box_sides(H2, V2, r - 1, c) == 4:
                C2[r - 1, c] = player
                gained += 1
            if r < N and C2[r, c] == 0 and box_sides(H2, V2, r, c) == 4:
                C2[r, c] = player
                gained += 1
        else:
            if c > 0 and C2[r, c - 1] == 0 and box_sides(H2, V2, r, c - 1) == 4:
                C2[r, c - 1] = player
                gained += 1
            if c < N and C2[r, c] == 0 and box_sides(H2, V2, r, c) == 4:
                C2[r, c] = player
                gained += 1
        return H2, V2, C2, gained

    def creates_threes(H, V, C, move):
        H2 = H.copy()
        V2 = V.copy()
        r, c, d = move
        if d == 'H':
            H2[r, c] = 1
        else:
            V2[r, c] = 1
        cnt = 0
        affected = []
        if d == 'H':
            if r > 0:
                affected.append((r - 1, c))
            if r < N:
                affected.append((r, c))
        else:
            if c > 0:
                affected.append((r, c - 1))
            if c < N:
                affected.append((r, c))
        for br, bc in affected:
            if C[br, bc] == 0 and box_sides(H2, V2, br, bc) == 3:
                cnt += 1
        return cnt

    def immediate_captures_available(H, V, C):
        return [m for m in legal_moves(H, V) if completed_by_move(H, V, C, m) > 0]

    def safe_score(H, V, C, move):
        r, c, d = move
        danger = creates_threes(H, V, C, move)

        # Positional preference: central edges are often more flexible early,
        # but border edges can be safer. Balance both.
        border = 0
        if d == 'H' and (r == 0 or r == N):
            border = 1
        if d == 'V' and (c == 0 or c == N):
            border = 1

        adj_boxes = 0
        if d == 'H':
            adj_boxes = (1 if r > 0 else 0) + (1 if r < N else 0)
        else:
            adj_boxes = (1 if c > 0 else 0) + (1 if c < N else 0)

        # Prefer moves adjacent to boxes with fewer sides.
        ssum = 0
        if d == 'H':
            if r > 0:
                ssum += box_sides(H, V, r - 1, c)
            if r < N:
                ssum += box_sides(H, V, r, c)
        else:
            if c > 0:
                ssum += box_sides(H, V, r, c - 1)
            if c < N:
                ssum += box_sides(H, V, r, c)

        return -100 * danger - 4 * ssum + 2 * border - adj_boxes

    def state_key(H, V, C, turn):
        return (H.tobytes(), V.tobytes(), C.tobytes(), turn)

    remaining = len(legal_moves(H0, V0))

    # Exact/near-exact search in the late game.
    if remaining <= 17:
        @lru_cache(None)
        def negamax(Hb, Vb, Cb, turn):
            if time.time() - start_time > TIME_LIMIT:
                return 0
            H = np.frombuffer(Hb, dtype=np.int8).reshape((N + 1, N + 1))
            V = np.frombuffer(Vb, dtype=np.int8).reshape((N + 1, N + 1))
            C = np.frombuffer(Cb, dtype=np.int8).reshape((N + 1, N + 1))
            moves = legal_moves(H, V)
            if not moves:
                return int(np.sum(C == 1) - np.sum(C == -1)) * turn

            caps = [m for m in moves if completed_by_move(H, V, C, m) > 0]
            ordered = caps + [m for m in moves if m not in caps]
            best = -999
            for m in ordered:
                H2, V2, C2, g = apply_move(H, V, C, m, turn)
                if g > 0:
                    val = negamax(H2.tobytes(), V2.tobytes(), C2.tobytes(), turn)
                else:
                    val = -negamax(H2.tobytes(), V2.tobytes(), C2.tobytes(), -turn)
                if val > best:
                    best = val
            return best

        best_m = None
        best_v = -999
        moves = legal_moves(H0, V0)
        caps = [m for m in moves if completed_by_move(H0, V0, C0, m) > 0]
        ordered = caps + sorted([m for m in moves if m not in caps], key=lambda x: safe_score(H0, V0, C0, x), reverse=True)
        for m in ordered:
            if time.time() - start_time > TIME_LIMIT:
                break
            H2, V2, C2, g = apply_move(H0, V0, C0, m, 1)
            if g > 0:
                v = negamax(H2.tobytes(), V2.tobytes(), C2.tobytes(), 1)
            else:
                v = -negamax(H2.tobytes(), V2.tobytes(), C2.tobytes(), -1)
            if v > best_v:
                best_v = v
                best_m = m
        if best_m is not None:
            return f"{best_m[0]},{best_m[1]},{best_m[2]}"

    # 1. Take boxes immediately.
    caps = immediate_captures_available(H0, V0, C0)
    if caps:
        # Prefer double-captures.
        caps.sort(key=lambda m: completed_by_move(H0, V0, C0, m), reverse=True)
        m = caps[0]
        return f"{m[0]},{m[1]},{m[2]}"

    moves = legal_moves(H0, V0)
    if not moves:
        return "0,0,H"  # Should never be reached in a nonterminal legal call.

    # 2. Prefer safe moves that do not create any three-sided box.
    safe = [m for m in moves if creates_threes(H0, V0, C0, m) == 0]
    if safe:
        safe.sort(key=lambda m: safe_score(H0, V0, C0, m), reverse=True)
        m = safe[0]
        return f"{m[0]},{m[1]},{m[2]}"

    # 3. Forced opening: minimize opponent's immediate captures after our move.
    best_m = None
    best_val = -10**9
    for m in moves:
        H2, V2, C2, g = apply_move(H0, V0, C0, m, 1)
        opp_caps = immediate_captures_available(H2, V2, C2)
        opp_gain = 0
        if opp_caps:
            opp_gain = max(completed_by_move(H2, V2, C2, om) for om in opp_caps)
        val = -1000 * opp_gain + safe_score(H0, V0, C0, m)
        if val > best_val:
            best_val = val
            best_m = m

    if best_m is not None:
        return f"{best_m[0]},{best_m[1]},{best_m[2]}"

    # Absolute legal fallback.
    m = moves[0]
    return f"{m[0]},{m[1]},{m[2]}"
