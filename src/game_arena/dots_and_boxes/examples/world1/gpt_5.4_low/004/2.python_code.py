
import numpy as np

# 4x4 boxes => physical edges are:
# Horizontal: rows 0..4, cols 0..3
# Vertical:   rows 0..3, cols 0..4

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    H = np.array(horizontal, copy=True)
    V = np.array(vertical, copy=True)
    C = np.array(capture, copy=True)

    def valid_h_moves(H_):
        for r in range(5):
            for c in range(4):
                if H_[r, c] == 0:
                    yield (r, c, 'H')

    def valid_v_moves(V_):
        for r in range(4):
            for c in range(5):
                if V_[r, c] == 0:
                    yield (r, c, 'V')

    def all_moves(H_, V_):
        return list(valid_h_moves(H_)) + list(valid_v_moves(V_))

    def box_sides(H_, V_, r, c):
        # box (r,c), r,c in 0..3
        s = 0
        if H_[r, c] != 0:
            s += 1
        if H_[r + 1, c] != 0:
            s += 1
        if V_[r, c] != 0:
            s += 1
        if V_[r, c + 1] != 0:
            s += 1
        return s

    def adjacent_boxes(move):
        r, c, d = move
        boxes = []
        if d == 'H':
            if r > 0 and c < 4:
                boxes.append((r - 1, c))
            if r < 4 and c < 4:
                boxes.append((r, c))
        else:  # 'V'
            if c > 0 and r < 4:
                boxes.append((r, c - 1))
            if c < 4 and r < 4:
                boxes.append((r, c))
        return boxes

    def apply_move(H_, V_, C_, move, player=1):
        r, c, d = move
        H2 = H_.copy()
        V2 = V_.copy()
        C2 = C_.copy()

        if d == 'H':
            H2[r, c] = player
        else:
            V2[r, c] = player

        gained = 0
        for br, bc in adjacent_boxes(move):
            if 0 <= br < 4 and 0 <= bc < 4 and C2[br, bc] == 0:
                if box_sides(H2, V2, br, bc) == 4:
                    C2[br, bc] = player
                    gained += 1
        return H2, V2, C2, gained

    def capturing_moves(H_, V_, C_):
        caps = []
        for m in all_moves(H_, V_):
            _, _, _, g = apply_move(H_, V_, C_, m, 1)
            if g > 0:
                caps.append((m, g))
        return caps

    def created_three_sided_boxes(H_, V_, C_, move):
        # For a non-capturing move, count adjacent unclaimed boxes that become 3-sided.
        H2, V2, C2, gained = apply_move(H_, V_, C_, move, 1)
        if gained > 0:
            return 0
        count = 0
        for br, bc in adjacent_boxes(move):
            if 0 <= br < 4 and 0 <= bc < 4 and C2[br, bc] == 0:
                if box_sides(H2, V2, br, bc) == 3:
                    count += 1
        return count

    def local_side_sum_after(H_, V_, C_, move):
        # Smaller is generally safer/less committal.
        H2, V2, C2, _ = apply_move(H_, V_, C_, move, 1)
        total = 0
        for br, bc in adjacent_boxes(move):
            if 0 <= br < 4 and 0 <= bc < 4 and C2[br, bc] == 0:
                total += box_sides(H2, V2, br, bc)
        return total

    def greedy_capture_sequence(H_, V_, C_, player=1):
        # Approximate continued extra-turn play:
        # repeatedly take a move that captures the most boxes immediately.
        total = 0
        Hc, Vc, Cc = H_.copy(), V_.copy(), C_.copy()
        while True:
            best_move = None
            best_gain = 0
            for m in all_moves(Hc, Vc):
                Hn, Vn, Cn, g = apply_move(Hc, Vc, Cc, m, player)
                if g > best_gain:
                    best_gain = g
                    best_move = (m, Hn, Vn, Cn, g)
            if best_move is None or best_gain == 0:
                break
            _, Hc, Vc, Cc, g = best_move
            total += g
        return total

    def opponent_greedy_damage_after(H_, V_, C_, move):
        # After we make a non-capturing move, estimate how many boxes
        # opponent can collect immediately via greedy chain-taking.
        H2, V2, C2, gained = apply_move(H_, V_, C_, move, 1)
        if gained > 0:
            return 0
        return greedy_capture_sequence(H2, V2, C2, player=-1)

    moves = all_moves(H, V)
    if not moves:
        # Should not happen in a valid nonterminal call, but keep a safe fallback.
        return "0,0,H"

    # 1) Immediate captures: strongly prefer them.
    capture_candidates = []
    for m in moves:
        H2, V2, C2, gained = apply_move(H, V, C, m, 1)
        if gained > 0:
            future_gain = greedy_capture_sequence(H2, V2, C2, player=1)
            # Score: immediate gain first, then likely continuation.
            capture_candidates.append((gained, future_gain, m))

    if capture_candidates:
        capture_candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        r, c, d = capture_candidates[0][2]
        return f"{r},{c},{d}"

    # 2) Safe moves: avoid creating 3-sided boxes.
    safe_moves = []
    risky_moves = []
    for m in moves:
        threes = created_three_sided_boxes(H, V, C, m)
        local_sum = local_side_sum_after(H, V, C, m)
        item = (threes, local_sum, m)
        if threes == 0:
            safe_moves.append(item)
        else:
            risky_moves.append(item)

    if safe_moves:
        # Prefer lower local side count; slight bias toward border/corner edges is not necessary.
        safe_moves.sort(key=lambda x: (x[1], x[2][0], x[2][1], x[2][2]))
        r, c, d = safe_moves[0][2]
        return f"{r},{c},{d}"

    # 3) No safe moves: minimize estimated opponent capture spree.
    best = None
    for threes, local_sum, m in risky_moves:
        damage = opponent_greedy_damage_after(H, V, C, m)
        score = (damage, threes, local_sum)
        if best is None or score < best[0]:
            best = (score, m)

    if best is not None:
        r, c, d = best[1]
        return f"{r},{c},{d}"

    # 4) Final legality fallback.
    for r in range(5):
        for c in range(4):
            if H[r, c] == 0:
                return f"{r},{c},H"
    for r in range(4):
        for c in range(5):
            if V[r, c] == 0:
                return f"{r},{c},V"

    # Extra defensive fallback in case of unexpected board formatting.
    for r in range(5):
        for c in range(5):
            if H[r, c] == 0:
                return f"{r},{c},H"
    for r in range(5):
        for c in range(5):
            if V[r, c] == 0:
                return f"{r},{c},V"

    return "0,0,H"
