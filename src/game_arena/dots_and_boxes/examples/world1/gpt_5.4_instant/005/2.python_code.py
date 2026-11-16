
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    N = 4  # 4x4 boxes, 5x5 edge arrays used by environment

    def box_sides(h, v, r, c):
        # box (r,c) for 0<=r,c<4
        return (1 if h[r, c] != 0 else 0) + \
               (1 if h[r + 1, c] != 0 else 0) + \
               (1 if v[r, c] != 0 else 0) + \
               (1 if v[r, c + 1] != 0 else 0)

    def adjacent_boxes(move):
        r, c, d = move
        boxes = []
        if d == 'H':
            if r > 0 and c < N:
                boxes.append((r - 1, c))
            if r < N and c < N:
                boxes.append((r, c))
        else:  # 'V'
            if c > 0 and r < N:
                boxes.append((r, c - 1))
            if c < N and r < N:
                boxes.append((r, c))
        return boxes

    def legal_moves(h, v):
        moves = []
        for r in range(5):
            for c in range(5):
                if h[r, c] == 0:
                    moves.append((r, c, 'H'))
                if v[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves

    def simulate_move(h, v, cap, move, player=1):
        h2 = h.copy()
        v2 = v.copy()
        cap2 = cap.copy()
        r, c, d = move
        if d == 'H':
            h2[r, c] = player
        else:
            v2[r, c] = player

        captured = 0
        for br, bc in adjacent_boxes(move):
            if 0 <= br < N and 0 <= bc < N and cap2[br, bc] == 0:
                if box_sides(h2, v2, br, bc) == 4:
                    cap2[br, bc] = player
                    captured += 1
        return h2, v2, cap2, captured

    def move_captures(h, v, cap, move):
        _, _, _, got = simulate_move(h, v, cap, move, 1)
        return got

    def creates_third_side_count(h, v, cap, move):
        # How many adjacent unclaimed boxes become exactly 3-sided after this move?
        r, c, d = move
        count = 0
        for br, bc in adjacent_boxes(move):
            if 0 <= br < N and 0 <= bc < N and cap[br, bc] == 0:
                before = box_sides(h, v, br, bc)
                after = before + 1
                if before < 4 and after == 3:
                    count += 1
        return count

    def center_score(move):
        # Prefer edges nearer the center as a mild tie-breaker
        r, c, d = move
        return -((r - 2) ** 2 + (c - 2) ** 2)

    def opponent_forced_gain_after(h, v, cap, move):
        # Estimate how many boxes the opponent can force immediately via capture chain
        h2, v2, cap2, got = simulate_move(h, v, cap, move, 1)
        if got > 0:
            return 0  # we move again; not a giveaway move

        total = 0
        # Greedy capture-chain estimate for opponent
        while True:
            caps = []
            for m in legal_moves(h2, v2):
                g = move_captures(h2, v2, cap2, m)
                if g > 0:
                    # Prefer bigger immediate capture
                    caps.append((g, m))
            if not caps:
                break
            caps.sort(reverse=True, key=lambda x: x[0])
            g, best = caps[0]
            h2, v2, cap2, got2 = simulate_move(h2, v2, cap2, best, -1)
            total += got2
            # opponent continues while capturing; loop handles that
        return total

    moves = legal_moves(horizontal, vertical)

    # Safety fallback: should never happen in a normal ongoing game
    if not moves:
        return "0,0,H"

    # 1. Take captures immediately, maximizing boxes taken now.
    capturing = []
    for m in moves:
        g = move_captures(horizontal, vertical, capture, m)
        if g > 0:
            capturing.append((g, center_score(m), m))
    if capturing:
        capturing.sort(reverse=True)
        r, c, d = capturing[0][2]
        return f"{r},{c},{d}"

    # 2. Prefer safe moves: moves that create no 3-sided box.
    safe = []
    risky = []
    for m in moves:
        t = creates_third_side_count(horizontal, vertical, capture, m)
        item = (t, center_score(m), m)
        if t == 0:
            safe.append(item)
        else:
            risky.append(item)

    if safe:
        safe.sort(key=lambda x: (x[1]), reverse=True)
        r, c, d = safe[0][2]
        return f"{r},{c},{d}"

    # 3. No safe moves: minimize immediate danger, then estimated opponent chain.
    scored = []
    for t, cs, m in risky:
        opp_gain = opponent_forced_gain_after(horizontal, vertical, capture, m)
        scored.append((t, opp_gain, -cs, m))

    scored.sort(key=lambda x: (x[0], x[1], x[2]))
    r, c, d = scored[0][3]
    return f"{r},{c},{d}"
