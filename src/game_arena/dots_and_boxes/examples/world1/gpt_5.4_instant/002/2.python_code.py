
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    N = 4  # 4x4 boxes, arrays are 5x5

    def edge_drawn(h, v, r, c, d):
        return h[r, c] != 0 if d == 'H' else v[r, c] != 0

    def list_moves(h, v):
        moves = []
        for r in range(5):
            for c in range(5):
                if h[r, c] == 0:
                    moves.append((r, c, 'H'))
        for r in range(5):
            for c in range(5):
                if v[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves

    def adjacent_boxes_of_edge(r, c, d):
        boxes = []
        if d == 'H':
            if r > 0 and c < N:
                boxes.append((r - 1, c))
            if r < N and c < N:
                boxes.append((r, c))
        else:  # V
            if c > 0 and r < N:
                boxes.append((r, c - 1))
            if c < N and r < N:
                boxes.append((r, c))
        return boxes

    def box_sides_count(h, v, br, bc):
        cnt = 0
        if h[br, bc] != 0:
            cnt += 1
        if h[br + 1, bc] != 0:
            cnt += 1
        if v[br, bc] != 0:
            cnt += 1
        if v[br, bc + 1] != 0:
            cnt += 1
        return cnt

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
        for br, bc in adjacent_boxes_of_edge(r, c, d):
            if cap2[br, bc] == 0 and box_sides_count(h2, v2, br, bc) == 4:
                cap2[br, bc] = player
                gained += 1
        return h2, v2, cap2, gained

    def boxes_completed_by_move(h, v, cap, move):
        h2, v2, cap2, gained = apply_move(h, v, cap, move, player=1)
        return gained

    def creates_three_sided_box(h, v, cap, move):
        r, c, d = move
        for br, bc in adjacent_boxes_of_edge(r, c, d):
            if cap[br, bc] == 0:
                s = box_sides_count(h, v, br, bc)
                if s == 2:
                    return True
        return False

    def move_risk_score(h, v, cap, move):
        # Lower is better.
        # Penalize creating 3-sided boxes; slightly prefer central-ish, low-impact moves.
        r, c, d = move
        score = 0

        touched = adjacent_boxes_of_edge(r, c, d)
        for br, bc in touched:
            if cap[br, bc] != 0:
                continue
            s = box_sides_count(h, v, br, bc)
            if s == 2:
                score += 100  # very bad: gives opponent a box
            elif s == 1:
                score += 3
            elif s == 0:
                score += 1

        # Prefer edges touching fewer boxes (boundary) a little in early/safe play
        score += 2 - len(touched)

        # Tiny centrality preference to avoid awkward outer-chain constructions
        center_dist = abs(r - 2) + abs(c - 2)
        score += 0.1 * center_dist
        return score

    def forced_capture_count(h, v, cap):
        # Simulate a player to move who greedily/necessarily keeps taking boxes
        # until no immediate capture exists. Returns number of boxes captured.
        total = 0
        h2 = h.copy()
        v2 = v.copy()
        cap2 = cap.copy()

        while True:
            capture_moves = []
            for mv in list_moves(h2, v2):
                g = boxes_completed_by_move(h2, v2, cap2, mv)
                if g > 0:
                    capture_moves.append((g, mv))

            if not capture_moves:
                break

            # Prefer larger immediate gain, then continue.
            capture_moves.sort(key=lambda x: (-x[0], x[1][2], x[1][0], x[1][1]))
            g, mv = capture_moves[0]
            h2, v2, cap2, gained = apply_move(h2, v2, cap2, mv, player=1)
            total += gained

        return total

    def opponent_forced_gain_after_move(h, v, cap, move):
        # We make a non-capturing move, then opponent moves.
        # Estimate opponent gain by assuming they take all forced captures available.
        h2, v2, cap2, gained = apply_move(h, v, cap, move, player=1)
        if gained > 0:
            return -gained  # capturing now is great; but normally handled earlier
        return forced_capture_count(h2, v2, cap2)

    moves = list_moves(horizontal, vertical)
    if not moves:
        return "0,0,H"  # should not happen in valid games

    # 1. Always take available captures, maximizing immediate gain, then future forced gain.
    capture_moves = []
    for mv in moves:
        g = boxes_completed_by_move(horizontal, vertical, capture, mv)
        if g > 0:
            h2, v2, c2, gained = apply_move(horizontal, vertical, capture, mv, player=1)
            future = forced_capture_count(h2, v2, c2)
            capture_moves.append((gained + future, gained, mv))
    if capture_moves:
        capture_moves.sort(key=lambda x: (-x[0], -x[1], x[2][2], x[2][0], x[2][1]))
        r, c, d = capture_moves[0][2]
        return f"{r},{c},{d}"

    # 2. Prefer safe moves that do not create a 3-sided box.
    safe_moves = [mv for mv in moves if not creates_three_sided_box(horizontal, vertical, capture, mv)]
    if safe_moves:
        safe_moves.sort(key=lambda mv: (move_risk_score(horizontal, vertical, capture, mv),
                                        mv[2], mv[0], mv[1]))
        r, c, d = safe_moves[0]
        return f"{r},{c},{d}"

    # 3. If all moves are unsafe, choose the one minimizing opponent's forced gain.
    best_mv = None
    best_score = None
    for mv in moves:
        opp_gain = opponent_forced_gain_after_move(horizontal, vertical, capture, mv)
        # Secondary tie-break: lower local risk
        score = (opp_gain, move_risk_score(horizontal, vertical, capture, mv))
        if best_score is None or score < best_score:
            best_score = score
            best_mv = mv

    if best_mv is not None:
        r, c, d = best_mv
        return f"{r},{c},{d}"

    # 4. Absolute fallback: first legal move.
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
    for r in range(5):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    return "0,0,H"
