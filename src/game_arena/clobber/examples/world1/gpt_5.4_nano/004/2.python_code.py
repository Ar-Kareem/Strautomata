
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    """
    Returns a legal move string 'row,col,dir' for Clobber on a 5x6 grid.
    you and opponent are 5x6 flattened lists or arrays of 0/1.
    """
    you = np.array(you, dtype=np.int8).reshape(5, 6)
    opp = np.array(opponent, dtype=np.int8).reshape(5, 6)

    H, W = 5, 6
    dirs = {
        'U': (-1, 0),
        'R': (0, 1),
        'D': (1, 0),
        'L': (0, -1),
    }

    def legal_moves(you_board, opp_board):
        moves = []
        # You capture adjacent opponent: move orthogonally onto opponent piece.
        for r in range(H):
            for c in range(W):
                if you_board[r, c] != 1:
                    continue
                for dch, (dr, dc) in dirs.items():
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < H and 0 <= nc < W and opp_board[nr, nc] == 1:
                        moves.append((r, c, dch))
        return moves

    def apply_move(you_board, opp_board, move):
        r, c, dch = move
        dr, dc = dirs[dch]
        nr, nc = r + dr, c + dc
        new_you = you_board.copy()
        new_opp = opp_board.copy()
        # capture
        new_you[r, c] = 0
        new_you[nr, nc] = 1
        new_opp[nr, nc] = 0
        return new_you, new_opp

    # Fallback: if somehow no legal moves, return a dummy (shouldn't happen)
    possible = legal_moves(you, opp)
    if not possible:
        return "0,0,U"

    # Heuristic scoring with 1-ply lookahead
    # We want: maximize our mobility after the move, minimize opponent mobility.
    # Also prefer removing opponent pieces that reduce their options (capturing tends to do so),
    # and avoid moves that keep us with few moves.
    best_move = None
    best_score = -10**9

    # Precompute center bonus / corner penalty for tiebreaks
    # (centralization tends to keep flexibility on a small grid)
    center = np.array([[abs(2 - r) + abs(2 - c) for c in range(W)] for r in range(H)], dtype=np.int8)

    for mv in possible:
        y2, o2 = apply_move(you, opp, mv)
        # our subsequent moves
        my_next = legal_moves(y2, o2)
        # opponent subsequent moves (swap roles)
        opp_next = legal_moves(o2, y2)

        my_mob = len(my_next)
        opp_mob = len(opp_next)

        r, c, dch = mv
        dr, dc = dirs[dch]
        nr, nc = r + dr, c + dc

        # Immediate progress: moving to cell that is surrounded by more opponent targets for us later
        # (counts adjacent opponent pieces from the landing square in current position after our move)
        adj_opp = 0
        for _, (adr, adc) in dirs.items():
            rr, cc = nr + _,  # dummy to avoid confusion (never used)
        # We'll just do explicitly:
        for (dr2, dc2) in [(-1,0),(0,1),(1,0),(0,-1)]:
            rr, cc = nr + dr2, nc + dc2
            if 0 <= rr < H and 0 <= cc < W and o2[rr, cc] == 1:
                adj_opp += 1

        # Risk: count opponent captures on their next turn by mobility already computed (opp_mob).
        # Additional small risk: if our landing square is adjacent to many opponent pieces, opponent
        # might immediately recapture.
        land_adj_ourpieces_for_opponent = 0
        for (dr2, dc2) in [(-1,0),(0,1),(1,0),(0,-1)]:
            rr, cc = nr + dr2, nc + dc2
            if 0 <= rr < H and 0 <= cc < W and y2[rr, cc] == 1:
                land_adj_ourpieces_for_opponent += 1

        # Score components:
        # - Strongly prefer lower opponent mobility
        # - Prefer higher our mobility
        # - Prefer landing with higher adjacent opponent targets (adj_opp)
        # - Prefer central landing (lower center distance)
        # - Small preference to reduce our fragmentation (fewer adjacent own pieces is generally safer)
        score = 0
        score += (8 * my_mob)              # our mobility
        score -= (10 * opp_mob)           # opponent mobility is very important
        score += (3 * adj_opp)            # potential follow-up captures
        score += (1.0 / (1 + center[nr, nc])) * 2  # center preference
        score -= (0.5 * land_adj_ourpieces_for_opponent)

        # Win/lose detection isn't guaranteed at 1-ply, but if we can move leaving opponent with 0 moves, that's great
        if opp_mob == 0:
            score += 10_000

        # Break ties deterministically to avoid randomness
        if score > best_score:
            best_score = score
            best_move = mv
        elif score == best_score and best_move is not None:
            # Tie-break: prefer lexicographically smaller (r,c,dir) for determinism,
            # but also a slight preference to moves with higher my_mob.
            bm_r, bm_c, bm_d = best_move
            if (my_mob, adj_opp, -center[nr, nc]) > (0, 0, 0):
                # Use a stable comparison including immediate landing value
                if (r, c, dch) < (bm_r, bm_c, bm_d):
                    best_move = mv

    r, c, dch = best_move
    return f"{r},{c},{dch}"
