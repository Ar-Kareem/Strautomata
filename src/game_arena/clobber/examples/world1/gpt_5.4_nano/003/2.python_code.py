
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    you = np.array(you, dtype=int).reshape(5, 6)
    opp = np.array(opponent, dtype=int).reshape(5, 6)

    R, C = 5, 6
    dirs = {
        'U': (-1, 0),
        'D': (1, 0),
        'L': (0, -1),
        'R': (0, 1),
    }

    def legal_moves(board_you, board_opp):
        moves = []
        ys, xs = np.where(board_you == 1)
        for r, c in zip(ys, xs):
            for dch, (dr, dc) in dirs.items():
                nr, nc = r + dr, c + dc
                if 0 <= nr < R and 0 <= nc < C and board_opp[nr, nc] == 1:
                    moves.append((r, c, dch))
        return moves

    def apply_move(board_you, board_opp, move):
        r, c, dch = move
        dr, dc = dirs[dch]
        nr, nc = r + dr, c + dc
        new_you = board_you.copy()
        new_opp = board_opp.copy()
        new_you[r, c] = 0
        new_you[nr, nc] = 1
        new_opp[nr, nc] = 0
        return new_you, new_opp

    def mobility(board_you, board_opp):
        return len(legal_moves(board_you, board_opp))

    # Generate legal moves for current state
    moves = legal_moves(you, opp)
    if not moves:
        # No legal move: return something syntactically valid (shouldn't happen in arena),
        # but we must return a legal move string; if no move exists, any will be illegal.
        # To avoid disqualification, attempt to find a move-like fallback (still illegal).
        # However, in correct games this branch should not occur.
        # We'll return a deterministic string from an existing piece (may be illegal if truly no moves).
        ys, xs = np.where(you == 1)
        if len(ys) == 0:
            return "0,0,U"
        return f"{int(ys[0])},{int(xs[0])},U"

    # Centrality weighting for captured squares (higher is better)
    center_r = (R - 1) / 2.0
    center_c = (C - 1) / 2.0
    def centrality(r, c):
        # higher score toward center
        return -((r - center_r) ** 2 + (c - center_c) ** 2)

    # Lightweight 1-ply lookahead with mobility considerations
    best_move = moves[0]
    best_score = -10**18

    my_mob_now = mobility(you, opp)

    for mv in moves:
        new_you, new_opp = apply_move(you, opp, mv)

        # Immediate win: if opponent has no legal moves after we play, choose it.
        opp_moves = legal_moves(new_you, new_opp)  # opponent to move uses their pieces=opp
        # Important: legal_moves expects "board_you" = player pieces; so swap roles:
        opp_can_move = len(legal_moves(new_opp, new_you)) > 0

        if not opp_can_move:
            return f"{mv[0]},{mv[1]},{mv[2]}"

        # Otherwise, evaluate:
        # - Prefer increasing (or not decreasing too much) our mobility
        my_mob_after = mobility(new_you, new_opp)

        # - Prefer reducing opponent mobility after our move (their turn)
        opp_mob_after = mobility(new_opp, new_you)

        # Captured square
        r, c, dch = mv
        dr, dc = dirs[dch]
        nr, nc = r + dr, c + dc

        # Additional tactical: count how many of opponent pieces are adjacent to the landing square
        adj_threat = 0
        for (dr2, dc2) in dirs.values():
            ar, ac = nr + dr2, nc + dc2
            if 0 <= ar < R and 0 <= ac < C and new_opp[ar, ac] == 1:
                adj_threat += 1

        # Score components
        score = 0.0
        score += 3.0 * centrality(nr, nc)
        score += 2.0 * adj_threat
        score += 2.5 * (my_mob_after - my_mob_now)
        score -= 3.0 * opp_mob_after

        # If my mobility drops drastically, penalize
        if my_mob_after <= 1:
            score -= 5.0

        # Tie-breaker: small preference for moves that land closer to center and create mobility
        score += 0.1 * my_mob_after

        if score > best_score:
            best_score = score
            best_move = mv

    r, c, dch = best_move
    return f"{r},{c},{dch}"
