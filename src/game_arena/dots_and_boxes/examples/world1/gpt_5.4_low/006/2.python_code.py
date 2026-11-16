
import numpy as np


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # ---------- Helpers ----------
    def valid_h(r, c):
        return 0 <= r < 5 and 0 <= c < 4

    def valid_v(r, c):
        return 0 <= r < 4 and 0 <= c < 5

    def legal_moves(h, v):
        moves = []
        for r in range(5):
            for c in range(4):
                if h[r, c] == 0:
                    moves.append((r, c, 'H'))
        for r in range(4):
            for c in range(5):
                if v[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves

    def box_side_count(h, v, r, c):
        # valid boxes are 0..3, 0..3
        cnt = 0
        if h[r, c] != 0:
            cnt += 1
        if h[r + 1, c] != 0:
            cnt += 1
        if v[r, c] != 0:
            cnt += 1
        if v[r, c + 1] != 0:
            cnt += 1
        return cnt

    def adjacent_boxes(move):
        r, c, d = move
        boxes = []
        if d == 'H':
            # box above
            if r > 0 and c < 4:
                boxes.append((r - 1, c))
            # box below
            if r < 4 and c < 4:
                boxes.append((r, c))
        else:  # 'V'
            # box left
            if c > 0 and r < 4:
                boxes.append((r, c - 1))
            # box right
            if c < 4 and r < 4:
                boxes.append((r, c))
        return boxes

    def apply_move(h, v, cap, move, player=1):
        h2 = h.copy()
        v2 = v.copy()
        cap2 = cap.copy()
        r, c, d = move
        if d == 'H':
            h2[r, c] = player
        else:
            v2[r, c] = player

        gained = 0
        for br, bc in adjacent_boxes(move):
            if 0 <= br < 4 and 0 <= bc < 4 and cap2[br, bc] == 0:
                if box_side_count(h2, v2, br, bc) == 4:
                    cap2[br, bc] = player
                    gained += 1
        return h2, v2, cap2, gained

    def move_features(h, v, cap, move):
        # Returns:
        # gained_boxes, creates_three_sided_unclaimed, heuristic_risk_score
        r, c, d = move
        h2 = h.copy()
        v2 = v.copy()
        if d == 'H':
            h2[r, c] = 1
        else:
            v2[r, c] = 1

        gained = 0
        creates_three = False
        risk = 0

        for br, bc in adjacent_boxes(move):
            if not (0 <= br < 4 and 0 <= bc < 4):
                continue
            if cap[br, bc] != 0:
                continue
            cnt = box_side_count(h2, v2, br, bc)
            if cnt == 4:
                gained += 1
            elif cnt == 3:
                creates_three = True
                risk += 100
            else:
                # Lower counts are safer; prefer leaving boxes at 1 side rather than 2.
                risk += cnt * cnt

        # Slight preference for boundary moves when otherwise similar.
        boundary_bonus = 0
        if d == 'H':
            if r == 0 or r == 4:
                boundary_bonus = -1
        else:
            if c == 0 or c == 4:
                boundary_bonus = -1

        return gained, creates_three, risk + boundary_bonus

    def greedy_capture_count(h, v, cap, player=-1):
        # Estimate boxes current player can collect in one turn
        # assuming they greedily keep taking captures until no capture remains.
        total = 0
        h2 = h.copy()
        v2 = v.copy()
        cap2 = cap.copy()

        while True:
            best_move = None
            best_gain = 0

            for mv in legal_moves(h2, v2):
                _, _, _, gain = apply_move(h2, v2, cap2, mv, player=player)
                if gain > best_gain:
                    best_gain = gain
                    best_move = mv

            if best_move is None or best_gain == 0:
                break

            h2, v2, cap2, gain = apply_move(h2, v2, cap2, best_move, player=player)
            total += gain

        return total

    # ---------- Main decision ----------
    moves = legal_moves(horizontal, vertical)
    if not moves:
        # Should not normally happen, but return a syntactically valid fallback.
        return "0,0,H"

    # 1) Immediate captures first
    capture_moves = []
    for mv in moves:
        gained, creates_three, risk = move_features(horizontal, vertical, capture, mv)
        if gained > 0:
            # Prefer more captures, then lower resulting risk
            capture_moves.append((gained, -risk, mv))
    if capture_moves:
        capture_moves.sort(reverse=True)
        r, c, d = capture_moves[0][2]
        return f"{r},{c},{d}"

    # 2) Safe moves: no capture and no created 3-sided box
    safe_moves = []
    for mv in moves:
        gained, creates_three, risk = move_features(horizontal, vertical, capture, mv)
        if gained == 0 and not creates_three:
            safe_moves.append((risk, mv))

    if safe_moves:
        safe_moves.sort(key=lambda x: x[0])
        r, c, d = safe_moves[0][1]
        return f"{r},{c},{d}"

    # 3) No safe move exists: choose move minimizing opponent greedy capture run
    best_mv = None
    best_score = None

    for mv in moves:
        h2, v2, cap2, gained = apply_move(horizontal, vertical, capture, mv, player=1)
        opp_gain = greedy_capture_count(h2, v2, cap2, player=-1)

        # Secondary tie-breaks:
        # - prefer moves with lower local risk
        # - prefer boundary edges slightly
        _, _, risk = move_features(horizontal, vertical, capture, mv)

        score = (opp_gain, risk)
        if best_score is None or score < best_score:
            best_score = score
            best_mv = mv

    if best_mv is not None:
        r, c, d = best_mv
        return f"{r},{c},{d}"

    # Final fallback: guaranteed legal if any move exists
    r, c, d = moves[0]
    return f"{r},{c},{d}"
