
import numpy as np


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Smart Dots and Boxes policy for a 4x4 box grid.

    Board convention:
    - Valid horizontal edges: horizontal[r, c] for r in 0..4, c in 0..3
    - Valid vertical edges:   vertical[r, c]   for r in 0..3, c in 0..4
    - Boxes: capture[r, c] for r in 0..3, c in 0..3
    """

    N = 4

    def valid_moves(h, v):
        moves = []
        for r in range(N + 1):
            for c in range(N):
                if h[r, c] == 0:
                    moves.append((r, c, "H"))
        for r in range(N):
            for c in range(N + 1):
                if v[r, c] == 0:
                    moves.append((r, c, "V"))
        return moves

    def adjacent_boxes(move):
        r, c, d = move
        boxes = []
        if d == "H":
            if r > 0:
                boxes.append((r - 1, c))
            if r < N:
                boxes.append((r, c))
        else:
            if c > 0:
                boxes.append((r, c - 1))
            if c < N:
                boxes.append((r, c))
        return boxes

    def box_sides(h, v, br, bc):
        return (
            int(h[br, bc] != 0) +
            int(h[br + 1, bc] != 0) +
            int(v[br, bc] != 0) +
            int(v[br, bc + 1] != 0)
        )

    def captures_made_by_move(h, v, cap, move):
        made = 0
        for br, bc in adjacent_boxes(move):
            if 0 <= br < N and 0 <= bc < N and cap[br, bc] == 0:
                if box_sides(h, v, br, bc) == 3:
                    made += 1
        return made

    def apply_move(h, v, cap, move, player):
        h2 = h.copy()
        v2 = v.copy()
        cap2 = cap.copy()

        r, c, d = move
        if d == "H":
            h2[r, c] = player
        else:
            v2[r, c] = player

        gained = 0
        for br, bc in adjacent_boxes(move):
            if 0 <= br < N and 0 <= bc < N and cap2[br, bc] == 0:
                if box_sides(h2, v2, br, bc) == 4:
                    cap2[br, bc] = player
                    gained += 1

        return h2, v2, cap2, gained

    def creates_three_box(h, v, cap, move):
        h2 = h.copy()
        v2 = v.copy()
        r, c, d = move
        if d == "H":
            h2[r, c] = 1
        else:
            v2[r, c] = 1

        for br, bc in adjacent_boxes(move):
            if 0 <= br < N and 0 <= bc < N and cap[br, bc] == 0:
                if box_sides(h2, v2, br, bc) == 3:
                    return True
        return False

    def safe_move_score(h, v, cap, move):
        """
        Heuristic for non-capturing safe moves.
        Prefer moves that:
        - Are safe.
        - Touch boxes with more existing sides, as long as they do not create a 3-side box.
        - Avoid center openings slightly less than boundary moves.
        """
        score = 0
        r, c, d = move

        for br, bc in adjacent_boxes(move):
            if 0 <= br < N and 0 <= bc < N and cap[br, bc] == 0:
                s = box_sides(h, v, br, bc)
                score += s * 10

        # Slight preference for boundary edges, as they usually have fewer consequences.
        if d == "H" and (r == 0 or r == N):
            score += 3
        if d == "V" and (c == 0 or c == N):
            score += 3

        # Mild centrality penalty.
        score -= abs(r - 2) + abs(c - 2)

        return score

    def greedy_capture_run(h, v, cap, player):
        """
        Estimate how many boxes 'player' can take by repeatedly taking available captures.
        This is not exact game search, but it is fast and good at detecting chain giveaways.
        """
        total = 0
        hcur = h.copy()
        vcur = v.copy()
        capcur = cap.copy()

        while True:
            moves = valid_moves(hcur, vcur)
            capture_moves = []
            for mv in moves:
                gain = captures_made_by_move(hcur, vcur, capcur, mv)
                if gain > 0:
                    capture_moves.append((gain, mv))

            if not capture_moves:
                break

            capture_moves.sort(reverse=True, key=lambda x: x[0])
            _, best = capture_moves[0]
            hcur, vcur, capcur, gained = apply_move(hcur, vcur, capcur, best, player)
            total += gained

        return total

    def danger_after_move(h, v, cap, move):
        """
        Estimate how dangerous a non-scoring move is by simulating it,
        then allowing the opponent to greedily collect captures.
        """
        h2, v2, cap2, gained = apply_move(h, v, cap, move, 1)

        # If we somehow score, this is not dangerous in the same way.
        if gained > 0:
            return -100 - gained

        opponent_gain = greedy_capture_run(h2, v2, cap2, -1)

        # Also count how many immediate captures opponent has.
        immediate = 0
        for mv in valid_moves(h2, v2):
            immediate = max(immediate, captures_made_by_move(h2, v2, cap2, mv))

        return opponent_gain * 10 + immediate

    moves = valid_moves(horizontal, vertical)

    # Absolute fallback in case the environment has unusual indexing.
    if not moves:
        for r in range(5):
            for c in range(5):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
        for r in range(5):
            for c in range(5):
                if vertical[r, c] == 0:
                    return f"{r},{c},V"
        return "0,0,H"

    # 1. Take captures immediately.
    capture_moves = []
    for mv in moves:
        gain = captures_made_by_move(horizontal, vertical, capture, mv)
        if gain > 0:
            h2, v2, c2, _ = apply_move(horizontal, vertical, capture, mv, 1)
            future_opp = greedy_capture_run(h2, v2, c2, -1)
            capture_moves.append((gain, -future_opp, mv))

    if capture_moves:
        capture_moves.sort(reverse=True, key=lambda x: (x[0], x[1]))
        r, c, d = capture_moves[0][2]
        return f"{r},{c},{d}"

    # 2. Prefer safe non-capturing moves.
    safe_moves = []
    for mv in moves:
        if not creates_three_box(horizontal, vertical, capture, mv):
            safe_moves.append((safe_move_score(horizontal, vertical, capture, mv), mv))

    if safe_moves:
        safe_moves.sort(reverse=True, key=lambda x: x[0])
        r, c, d = safe_moves[0][1]
        return f"{r},{c},{d}"

    # 3. If forced to open a chain, give away as little as possible.
    risky = []
    for mv in moves:
        danger = danger_after_move(horizontal, vertical, capture, mv)
        # Tie-breaker: prefer boundary moves.
        boundary_bonus = 0
        r, c, d = mv
        if d == "H" and (r == 0 or r == N):
            boundary_bonus = -1
        if d == "V" and (c == 0 or c == N):
            boundary_bonus = -1
        risky.append((danger + boundary_bonus, mv))

    risky.sort(key=lambda x: x[0])
    r, c, d = risky[0][1]
    return f"{r},{c},{d}"
