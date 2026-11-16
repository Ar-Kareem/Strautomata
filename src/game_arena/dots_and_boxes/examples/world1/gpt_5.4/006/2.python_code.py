
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    N = 4  # 4x4 boxes, 5x5 arrays provided

    def legal_moves(h, v):
        moves = []
        for r in range(5):
            for c in range(5):
                if h[r, c] == 0:
                    moves.append((r, c, 'H'))
                if v[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves

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

    def box_edge_count(h, v, br, bc):
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
        h2 = h.copy()
        v2 = v.copy()
        c2 = cap.copy()
        r, c, d = move
        if d == 'H':
            h2[r, c] = player
        else:
            v2[r, c] = player

        gained = 0
        for br, bc in adjacent_boxes(move):
            if c2[br, bc] == 0 and box_edge_count(h2, v2, br, bc) == 4:
                c2[br, bc] = player
                gained += 1
        return h2, v2, c2, gained

    def immediate_gain(h, v, cap, move):
        _, _, _, g = apply_move(h, v, cap, move, player=1)
        return g

    def creates_third_side_count(h, v, move):
        # Count adjacent boxes that go from 2 sides to 3 sides after this move.
        count = 0
        for br, bc in adjacent_boxes(move):
            before = box_edge_count(h, v, br, bc)
            if before == 2:
                count += 1
        return count

    def creates_two_side_count(h, v, move):
        # Count adjacent boxes that go from 1 side to 2 sides after this move.
        count = 0
        for br, bc in adjacent_boxes(move):
            before = box_edge_count(h, v, br, bc)
            if before == 1:
                count += 1
        return count

    def centrality_score(move):
        r, c, d = move
        if d == 'H':
            x, y = r, c + 0.5
        else:
            x, y = r + 0.5, c
        return abs(x - 2.0) + abs(y - 2.0)

    def forced_capture_count(h, v, cap):
        # Estimate how many boxes the player to move can force immediately by
        # repeatedly taking available captures until none remain.
        h2 = h.copy()
        v2 = v.copy()
        c2 = cap.copy()
        total = 0

        while True:
            found = False
            for br in range(N):
                for bc in range(N):
                    if c2[br, bc] != 0:
                        continue
                    if box_edge_count(h2, v2, br, bc) == 3:
                        # Fill the missing edge for this box.
                        if h2[br, bc] == 0:
                            move = (br, bc, 'H')
                        elif h2[br + 1, bc] == 0:
                            move = (br + 1, bc, 'H')
                        elif v2[br, bc] == 0:
                            move = (br, bc, 'V')
                        else:
                            move = (br, bc + 1, 'V')
                        h2, v2, c2, gained = apply_move(h2, v2, c2, move, player=1)
                        total += gained
                        found = True
                        break
                if found:
                    break
            if not found:
                break
        return total

    moves = legal_moves(horizontal, vertical)
    if not moves:
        return "0,0,H"  # Should never happen in a nonterminal state, but keep safe.

    # 1. Take captures immediately; among them, prefer larger gain and continuation quality.
    capture_moves = []
    for m in moves:
        g = immediate_gain(horizontal, vertical, capture, m)
        if g > 0:
            h2, v2, c2, _ = apply_move(horizontal, vertical, capture, m, player=1)
            cont = forced_capture_count(h2, v2, c2)
            capture_moves.append((m, g, cont))
    if capture_moves:
        # Maximize immediate gain, then follow-up forced captures.
        capture_moves.sort(key=lambda x: (-x[1], -x[2], centrality_score(x[0])))
        r, c, d = capture_moves[0][0]
        return f"{r},{c},{d}"

    # 2. Safe moves: avoid creating any 3-sided box.
    safe_moves = []
    for m in moves:
        third = creates_third_side_count(horizontal, vertical, m)
        if third == 0:
            two = creates_two_side_count(horizontal, vertical, m)
            safe_moves.append((m, two, centrality_score(m)))

    if safe_moves:
        # Prefer fewer newly-created 2-sided boxes, then more central.
        safe_moves.sort(key=lambda x: (x[1], x[2]))
        r, c, d = safe_moves[0][0]
        return f"{r},{c},{d}"

    # 3. All moves are risky. Choose the one minimizing opponent's likely forced captures.
    risky = []
    for m in moves:
        h2, v2, c2, _ = apply_move(horizontal, vertical, capture, m, player=1)
        opp_gain = forced_capture_count(h2, v2, c2)
        third = creates_third_side_count(horizontal, vertical, m)
        two = creates_two_side_count(horizontal, vertical, m)
        risky.append((m, opp_gain, third, two, centrality_score(m)))

    risky.sort(key=lambda x: (x[1], x[2], x[3], x[4]))
    r, c, d = risky[0][0]
    return f"{r},{c},{d}"
