
import numpy as np

def policy(you, opponent) -> str:
    you = np.array(you, dtype=np.int8)
    opp = np.array(opponent, dtype=np.int8)

    N = 6
    SIZE = 3

    def has_five(board):
        # board is 6x6 with 0/1 for a player
        b = board
        # horizontal/vertical
        for r in range(N):
            for c in range(N - 4):
                if b[r, c:c+5].sum() >= 5:
                    return True
        for c in range(N):
            for r in range(N - 4):
                if b[r:r+5, c].sum() >= 5:
                    return True
        # diagonals: down-right
        for r in range(N - 4):
            for c in range(N - 4):
                if np.diag(b[r:r+5, c:c+5]).sum() >= 5:
                    return True
        # diagonals: down-left
        for r in range(N - 4):
            for c in range(4, N):
                diag = [b[r+i, c-i] for i in range(5)]
                if np.sum(diag) >= 5:
                    return True
        return False

    def rotate_quadrant(board_you, board_opp, q, dirc):
        # Rotate 3x3 quadrant q in place affecting both boards
        # Return new copies
        y = board_you.copy()
        o = board_opp.copy()

        r0 = 0 if q in (0, 1) else 3
        c0 = 0 if q in (0, 2) else 3
        sub_y = y[r0:r0+3, c0:c0+3]
        sub_o = o[r0:r0+3, c0:c0+3]

        if dirc == 'L':  # 90 deg anticlockwise: use rot90(k=1) with -1? numpy rot90 rotates counterclockwise for k=1
            new_sub_y = np.rot90(sub_y, k=1)
            new_sub_o = np.rot90(sub_o, k=1)
        else:  # 'R' clockwise
            new_sub_y = np.rot90(sub_y, k=-1)
            new_sub_o = np.rot90(sub_o, k=-1)

        y[r0:r0+3, c0:c0+3] = new_sub_y
        o[r0:r0+3, c0:c0+3] = new_sub_o
        return y, o

    def apply_move(you_board, opp_board, r, c, q, dirc):
        y = you_board.copy()
        o = opp_board.copy()
        y[r, c] = 1
        y, o = rotate_quadrant(y, o, q, dirc)
        return y, o

    # Precompute all line segments (length 5) for evaluation
    segments = []
    # horizontal
    for r in range(N):
        for c in range(N - 4):
            segments.append([(r, c+i) for i in range(5)])
    # vertical
    for c in range(N):
        for r in range(N - 4):
            segments.append([(r+i, c) for i in range(5)])
    # diag down-right
    for r in range(N - 4):
        for c in range(N - 4):
            segments.append([(r+i, c+i) for i in range(5)])
    # diag down-left
    for r in range(N - 4):
        for c in range(4, N):
            segments.append([(r+i, c-i) for i in range(5)])

    def line_score(y_board, o_board):
        # Heuristic: score you's near-completions, heavily reward 5.
        # Also penalize opponent near-completions.
        y = y_board
        o = o_board
        score = 0
        for seg in segments:
            ys = sum(y[r, c] for r, c in seg)
            os = sum(o[r, c] for r, c in seg)
            if ys > 0 and os > 0:
                continue  # blocked segment
            if ys >= 5:
                score += 10_000
            elif ys > 0:
                # reward based on how many you have
                score += 50 * (ys * ys)
            if os >= 5:
                score -= 10_000
            elif os > 0:
                score -= 55 * (os * os)
        return score

    empty = np.where((you == 0) & (opp == 0))
    empties = list(zip(empty[0].tolist(), empty[1].tolist()))
    if not empties:
        # Shouldn't happen per prompt, but keep safe: return any legal-ish default
        return "1,1,0,R"

    best_move = None
    best_score = -10**18

    # Generate legal moves
    # For each empty placement, all 4 quadrant rotations and both directions
    dirs = ['L', 'R']
    quads = [0, 1, 2, 3]

    # 1) Immediate win for you, if exists. Pick best among them (all win).
    immediate_wins = []
    for r, c in empties:
        for q in quads:
            for d in dirs:
                y2, o2 = apply_move(you, opp, r, c, q, d)
                if has_five(y2):
                    # Check draw condition: opponent also has five
                    if not has_five(o2):
                        return f"{r+1},{c+1},{q},{d}"
                    else:
                        immediate_wins.append((r, c, q, d))
    # If only draw moves found as "immediate win" (both have five), choose one as best among them
    if immediate_wins:
        r, c, q, d = immediate_wins[0]
        return f"{r+1},{c+1},{q},{d}"

    # 2) Block opponent immediate wins: if opponent would win after our move, avoid if possible.
    # We'll still consider them if all lead to loss, but prefer non-losing.
    candidate_moves = []
    for r, c in empties:
        for q in quads:
            for d in dirs:
                y2, o2 = apply_move(you, opp, r, c, q, d)
                opp_wins = has_five(o2)
                if not opp_wins:
                    candidate_moves.append((r, c, q, d))
    if not candidate_moves:
        # Everyone allows opponent to win; pick the best score among all moves.
        candidate_moves = []
        for r, c in empties:
            for q in quads:
                for d in dirs:
                    candidate_moves.append((r, c, q, d))

    # 3) Heuristic evaluation
    # Prefer: winning lines quickly (score), also avoid giving opponent strong threats (score includes that).
    for r, c, q, d in candidate_moves:
        y2, o2 = apply_move(you, opp, r, c, q, d)

        # Additional safety: if opponent already has five (shouldn't in non-opp-wins list), penalize.
        if has_five(o2):
            score = -10_000_000
        else:
            score = line_score(y2, o2)

            # Micro-bias: prefer moves that increase your occupancy in the rotated quadrant
            r0 = 0 if q in (0, 1) else 3
            c0 = 0 if q in (0, 2) else 3
            your_quadrant = y2[r0:r0+3, c0:c0+3].sum()
            opp_quadrant = o2[r0:r0+3, c0:c0+3].sum()
            score += 3 * (your_quadrant * your_quadrant) - 2 * (opp_quadrant * opp_quadrant)

        if score > best_score:
            best_score = score
            best_move = (r, c, q, d)

    r, c, q, d = best_move
    return f"{r+1},{c+1},{q},{d}"
