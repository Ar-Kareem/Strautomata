
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    N = 4  # 4x4 boxes, arrays are 5x5

    def legal_moves(h, v):
        moves = []
        for r in range(5):
            for c in range(5):
                if h[r, c] == 0:
                    moves.append((r, c, 'H'))
                if v[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves

    def box_sides(h, v, r, c):
        # box at (r,c), 0<=r,c<4
        return (
            (1 if h[r, c] != 0 else 0) +
            (1 if h[r + 1, c] != 0 else 0) +
            (1 if v[r, c] != 0 else 0) +
            (1 if v[r, c + 1] != 0 else 0)
        )

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

    def apply_move(h, v, cap, move, player=1):
        r, c, d = move
        h2 = h.copy()
        v2 = v.copy()
        cap2 = cap.copy()
        if d == 'H':
            h2[r, c] = player
        else:
            v2[r, c] = player

        gained = 0
        for br, bc in adjacent_boxes(move):
            if cap2[br, bc] == 0 and box_sides(h2, v2, br, bc) == 4:
                cap2[br, bc] = player
                gained += 1
        return h2, v2, cap2, gained

    def creates_three_side_box(h, v, move):
        # True if after move, any adjacent uncaptured box has exactly 3 sides
        h2, v2, cap2, gained = apply_move(h, v, capture, move, player=1)
        if gained > 0:
            return False
        for br, bc in adjacent_boxes(move):
            if 0 <= br < N and 0 <= bc < N and cap2[br, bc] == 0:
                if box_sides(h2, v2, br, bc) == 3:
                    return True
        return False

    def immediate_gain(h, v, cap, move):
        _, _, _, gained = apply_move(h, v, cap, move, player=1)
        return gained

    def forced_capture_count_for_current_player(h, v, cap):
        # Greedily count how many boxes the current player can take by
        # repeatedly taking any available capturing move.
        total = 0
        h2 = h.copy()
        v2 = v.copy()
        cap2 = cap.copy()

        while True:
            found = None
            best_gain = 0
            for mv in legal_moves(h2, v2):
                _, _, _, g = apply_move(h2, v2, cap2, mv, player=1)
                if g > best_gain:
                    best_gain = g
                    found = mv
                    if g == 2:
                        break
            if found is None or best_gain == 0:
                break
            h2, v2, cap2, g = apply_move(h2, v2, cap2, found, player=1)
            total += g
        return total

    def opponent_chain_value_after_move(h, v, cap, move):
        # If we play a non-capturing move, estimate how many boxes opponent
        # can collect immediately/forced afterward.
        h2, v2, cap2, gained = apply_move(h, v, cap, move, player=1)
        if gained > 0:
            return 0
        return forced_capture_count_for_current_player(h2, v2, cap2)

    def centrality_score(move):
        r, c, d = move
        # prefer center-ish edges as tie-break
        if d == 'H':
            x, y = r, c + 0.5
        else:
            x, y = r + 0.5, c
        return -((x - 2.0) ** 2 + (y - 2.0) ** 2)

    moves = legal_moves(horizontal, vertical)
    if not moves:
        return "0,0,H"  # fallback; should never happen in a valid nonterminal state

    # 1. Take captures immediately, preferring larger gain, then centrality
    capturing = []
    for mv in moves:
        g = immediate_gain(horizontal, vertical, capture, mv)
        if g > 0:
            capturing.append((g, centrality_score(mv), mv))
    if capturing:
        capturing.sort(key=lambda x: (x[0], x[1]), reverse=True)
        r, c, d = capturing[0][2]
        return f"{r},{c},{d}"

    # 2. Prefer safe moves that do not create a 3-sided box
    safe_moves = []
    risky_moves = []
    for mv in moves:
        if creates_three_side_box(horizontal, vertical, mv):
            risky_moves.append(mv)
        else:
            safe_moves.append(mv)

    if safe_moves:
        # Among safe moves, prefer those that keep opponent immediate captures low
        scored = []
        for mv in safe_moves:
            opp = opponent_chain_value_after_move(horizontal, vertical, capture, mv)
            scored.append((-opp, centrality_score(mv), mv))
        scored.sort(reverse=True)
        r, c, d = scored[0][2]
        return f"{r},{c},{d}"

    # 3. If forced to open something, minimize opponent's chain
    scored = []
    for mv in risky_moves:
        opp = opponent_chain_value_after_move(horizontal, vertical, capture, mv)
        # also prefer creating fewer adjacent 3-side boxes
        h2, v2, cap2, _ = apply_move(horizontal, vertical, capture, mv, player=1)
        threes = 0
        for br, bc in adjacent_boxes(mv):
            if 0 <= br < N and 0 <= bc < N and cap2[br, bc] == 0:
                if box_sides(h2, v2, br, bc) == 3:
                    threes += 1
        scored.append((-opp, -threes, centrality_score(mv), mv))

    scored.sort(reverse=True)
    r, c, d = scored[0][3]
    return f"{r},{c},{d}"
