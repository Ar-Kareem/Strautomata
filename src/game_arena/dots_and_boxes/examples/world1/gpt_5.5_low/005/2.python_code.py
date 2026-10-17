
import numpy as np


N = 4


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Smart Dots and Boxes policy for a 4x4 box grid.

    Returns:
        Move string in the format 'row,col,H' or 'row,col,V'.
    """

    h = np.array(horizontal, copy=True)
    v = np.array(vertical, copy=True)
    cap = np.array(capture, copy=True)

    def move_to_str(m):
        r, c, d = m
        return f"{r},{c},{d}"

    def legal_moves(hh, vv):
        moves = []
        for r in range(N + 1):
            for c in range(N):
                if hh[r, c] == 0:
                    moves.append((r, c, "H"))
        for r in range(N):
            for c in range(N + 1):
                if vv[r, c] == 0:
                    moves.append((r, c, "V"))
        return moves

    def adjacent_boxes(m):
        r, c, d = m
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

    def box_sides(hh, vv, br, bc):
        return (
            int(hh[br, bc] != 0)
            + int(hh[br + 1, bc] != 0)
            + int(vv[br, bc] != 0)
            + int(vv[br, bc + 1] != 0)
        )

    def apply_move(hh, vv, cc, m, player):
        """
        Apply move to copied arrays in-place.
        Returns number of boxes captured.
        """
        r, c, d = m
        if d == "H":
            hh[r, c] = player
        else:
            vv[r, c] = player

        gained = 0
        for br, bc in adjacent_boxes(m):
            if 0 <= br < N and 0 <= bc < N and cc[br, bc] == 0:
                if box_sides(hh, vv, br, bc) == 4:
                    cc[br, bc] = player
                    gained += 1
        return gained

    def completes_box(hh, vv, cc, m):
        for br, bc in adjacent_boxes(m):
            if 0 <= br < N and 0 <= bc < N and cc[br, bc] == 0:
                if box_sides(hh, vv, br, bc) == 3:
                    return True
        return False

    def creates_three_box(hh, vv, cc, m):
        hh2 = hh.copy()
        vv2 = vv.copy()
        cc2 = cc.copy()
        apply_move(hh2, vv2, cc2, m, 1)

        for br in range(N):
            for bc in range(N):
                if cc2[br, bc] == 0 and box_sides(hh2, vv2, br, bc) == 3:
                    return True
        return False

    def board_features(hh, vv, cc):
        ones = 0
        twos = 0
        threes = 0
        for br in range(N):
            for bc in range(N):
                if cc[br, bc] == 0:
                    s = box_sides(hh, vv, br, bc)
                    if s == 1:
                        ones += 1
                    elif s == 2:
                        twos += 1
                    elif s == 3:
                        threes += 1
        return ones, twos, threes

    def greedy_capture_sequence(hh, vv, cc, player):
        """
        Greedily play all available captures for player.
        Returns number of boxes captured.
        """
        total = 0
        guard = 0

        while guard < 50:
            guard += 1
            moves = legal_moves(hh, vv)
            caps = [m for m in moves if completes_box(hh, vv, cc, m)]
            if not caps:
                break

            best_m = None
            best_score = -10**9

            for m in caps:
                h2 = hh.copy()
                v2 = vv.copy()
                c2 = cc.copy()
                gain = apply_move(h2, v2, c2, m, player)
                ones, twos, threes = board_features(h2, v2, c2)

                # Prefer more immediate captures, fewer future 3-boxes for opponent.
                score = 100 * gain - 5 * threes - twos
                if score > best_score:
                    best_score = score
                    best_m = m

            total += apply_move(hh, vv, cc, best_m, player)

        return total

    moves = legal_moves(h, v)

    # Absolute fallback: should never be needed during a normal game.
    if not moves:
        for r in range(5):
            for c in range(5):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
                if vertical[r, c] == 0:
                    return f"{r},{c},V"
        return "0,0,H"

    capture_moves = [m for m in moves if completes_box(h, v, cap, m)]

    # If we can score, score. Choose the capture with the best short rollout.
    if capture_moves:
        best_move = capture_moves[0]
        best_score = -10**9

        for m in capture_moves:
            h2 = h.copy()
            v2 = v.copy()
            c2 = cap.copy()

            my_gain = apply_move(h2, v2, c2, m, 1)
            my_gain += greedy_capture_sequence(h2, v2, c2, 1)

            # Once our capture run ends, estimate opponent's immediate reply.
            opp_gain = greedy_capture_sequence(h2, v2, c2, -1)

            ones, twos, threes = board_features(h2, v2, c2)
            score = 100 * (my_gain - opp_gain) - 3 * threes - twos + ones

            if score > best_score:
                best_score = score
                best_move = m

        return move_to_str(best_move)

    # Otherwise, look for safe moves that do not create a 3-sided box.
    safe_moves = [m for m in moves if not creates_three_box(h, v, cap, m)]

    if safe_moves:
        best_move = safe_moves[0]
        best_score = -10**9

        for m in safe_moves:
            h2 = h.copy()
            v2 = v.copy()
            c2 = cap.copy()
            apply_move(h2, v2, c2, m, 1)

            ones, twos, threes = board_features(h2, v2, c2)

            # Safe move heuristic:
            # - avoid creating many 2-sided boxes
            # - mildly prefer edges away from excessive chain formation
            # - prefer keeping the board flexible
            r, c, d = m
            border_bonus = 0
            if d == "H" and (r == 0 or r == N):
                border_bonus = 1
            if d == "V" and (c == 0 or c == N):
                border_bonus = 1

            score = 4 * ones - 6 * twos - 20 * threes + border_bonus

            if score > best_score:
                best_score = score
                best_move = m

        return move_to_str(best_move)

    # No safe moves: we must open something. Minimize opponent's capture run.
    best_move = moves[0]
    best_score = -10**9

    for m in moves:
        h2 = h.copy()
        v2 = v.copy()
        c2 = cap.copy()

        my_gain = apply_move(h2, v2, c2, m, 1)

        # If somehow this move captures, include it, though capture_moves was empty.
        if my_gain > 0:
            my_gain += greedy_capture_sequence(h2, v2, c2, 1)

        opp_gain = greedy_capture_sequence(h2, v2, c2, -1)

        ones, twos, threes = board_features(h2, v2, c2)

        # In forced positions, the main goal is to give away as little as possible.
        score = 100 * (my_gain - opp_gain) - 4 * threes - twos + ones

        if score > best_score:
            best_score = score
            best_move = m

    return move_to_str(best_move)
