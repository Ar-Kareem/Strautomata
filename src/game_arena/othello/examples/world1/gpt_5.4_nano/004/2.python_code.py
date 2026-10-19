
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Othello (Reversi) move policy for 8x8 boards.
    Returns a legal move string like 'd3' or 'pass' if no legal move exists.
    """
    # ---- Helpers ----
    DIRS = [(-1, -1), (-1, 0), (-1, 1),
            (0, -1),          (0, 1),
            (1, -1),  (1, 0),  (1, 1)]
    COLS = "abcdefgh"

    you = (you.astype(np.int8)).copy()
    opponent = (opponent.astype(np.int8)).copy()
    empty = 1 - (you | opponent)

    def on_board(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def legal_moves(player, opp):
        """Return list of (r,c) legal moves for player with discs=1."""
        moves = []
        for r in range(8):
            for c in range(8):
                if player[r, c] == 1 or opp[r, c] == 1:
                    continue
                if empty[r, c] == 0:  # occupied
                    continue
                # Check capture in any direction
                ok = False
                for dr, dc in DIRS:
                    rr, cc = r + dr, c + dc
                    found_opp = False
                    while on_board(rr, cc) and opp[rr, cc] == 1:
                        found_opp = True
                        rr += dr
                        cc += dc
                    if found_opp and on_board(rr, cc) and player[rr, cc] == 1:
                        ok = True
                        break
                if ok:
                    moves.append((r, c))
        return moves

    def apply_move(player, opp, move):
        """Return new (player', opp') after current player plays move (r,c)."""
        r, c = move
        new_player = player.copy()
        new_opp = opp.copy()
        new_player[r, c] = 1
        # Flip along all directions
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            captured = []
            while on_board(rr, cc) and new_opp[rr, cc] == 1:
                captured.append((rr, cc))
                rr += dr
                cc += dc
            if captured and on_board(rr, cc) and new_player[rr, cc] == 1:
                # bracketed
                for fr, fc in captured:
                    new_opp[fr, fc] = 0
                    new_player[fr, fc] = 1
        return new_player, new_opp

    def move_to_str(move):
        r, c = move
        return f"{COLS[c]}{r+1}"

    # Positional weights (classic-ish)
    # High for corners, negative for X-squares / C-squares to avoid early traps
    POS_W = np.array([
        [120, -20,  20,   5,   5,  20, -20, 120],
        [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
        [ 20,  -5,  15,   3,   3,  15,  -5,  20],
        [  5,  -5,   3,   3,   3,   3,  -5,   5],
        [  5,  -5,   3,   3,   3,   3,  -5,   5],
        [ 20,  -5,  15,   3,   3,  15,  -5,  20],
        [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
        [120, -20,  20,   5,   5,  20, -20, 120],
    ], dtype=np.float32)

    CORNERS = [(0,0),(0,7),(7,0),(7,7)]
    # Squares adjacent to corners (to encourage corner taking / discourage giving away)
    ADJ = {
        (0,0): [(0,1),(1,0),(1,1)],
        (0,7): [(0,6),(1,7),(1,6)],
        (7,0): [(6,0),(7,1),(6,1)],
        (7,7): [(6,7),(7,6),(6,6)],
    }

    def count_stableish(player, opp):
        """Quick proxy: corners + edges occupied by player/opp."""
        # True stability is complex; we approximate with corners and full edge ownership.
        corners_player = sum(player[r,c] for r,c in CORNERS)
        corners_opp = sum(opp[r,c] for r,c in CORNERS)

        # Edge occupancy (not empty) - rough
        edges = []
        # top/bottom rows
        for c in range(8):
            edges.append((0,c)); edges.append((7,c))
        # left/right cols excluding corners already
        for r in range(1,7):
            edges.append((r,0)); edges.append((r,7))

        ep = sum(player[r,c] for r,c in edges)
        eo = sum(opp[r,c] for r,c in edges)
        return corners_player, corners_opp, ep, eo

    def evaluate(player, opp, ply_remaining):
        """Heuristic evaluation from perspective of current 'player'."""
        # Disc diff (scaled down early)
        disc_diff = (player.sum() - opp.sum())

        # Corner control
        cp, co, ep, eo = count_stableish(player, opp)
        corner_diff = 25.0 * (cp - co)

        # Near-corner penalty/bonus
        # If you own a corner, adjacent squares less important; otherwise having adjacent squares
        # is risky unless corner secured.
        near_score = 0.0
        for corner in CORNERS:
            cr, cc = corner
            if player[cr,cc] == 1:
                for (ar,ac) in ADJ[corner]:
                    if player[ar,ac] == 1:
                        near_score += 2.5
                    elif opp[ar,ac] == 1:
                        near_score -= 2.5
            elif opp[cr,cc] == 1:
                for (ar,ac) in ADJ[corner]:
                    if opp[ar,ac] == 1:
                        near_score += 2.5
                    elif player[ar,ac] == 1:
                        near_score -= 2.5
            else:
                # neither corner taken: discourage playing adjacent
                for (ar,ac) in ADJ[corner]:
                    if player[ar,ac] == 1:
                        near_score -= 3.0
                    elif opp[ar,ac] == 1:
                        near_score += 3.0

        # Positional weight
        pos_score = float((player - opp).astype(np.float32) @ POS_W)

        # Mobility
        # compute legal moves count
        # (mobility is strong; do not overcompute too deep; but used in evaluation)
        moves_p = legal_moves(player, opp)
        moves_o = legal_moves(opp, player)
        mobility = len(moves_p) - len(moves_o)

        # Game phase adjustment
        filled = int(player.sum() + opp.sum())
        # Early ~0-20, mid ~20-48, late ~48+
        if filled < 20:
            disc_weight = 1.0
            mobility_weight = 6.0
            pos_weight = 1.0
        elif filled < 44:
            disc_weight = 1.3
            mobility_weight = 7.5
            pos_weight = 1.1
        else:
            disc_weight = 2.0
            mobility_weight = 3.0
            pos_weight = 1.0

        # Endgame: emphasize disc difference
        if ply_remaining <= 6 or filled >= 56:
            disc_weight *= 2.2
            mobility_weight *= 0.7

        score = (
            disc_weight * disc_diff
            + mobility_weight * mobility
            + corner_diff
            + 0.8 * near_score
            + pos_weight * pos_score
        )
        return score

    def ordered_moves(player, opp):
        """Generate legal moves with heuristic ordering for alpha-beta."""
        moves = legal_moves(player, opp)
        if not moves:
            return []
        # quick scoring: corners first, then positional weights, then mobility after move
        scored = []
        for m in moves:
            r, c = m
            corner_bonus = 0.0
            if (r, c) in CORNERS:
                corner_bonus = 500.0
            elif (r, c) in [(0,1),(1,0),(1,1),(0,6),(1,6),(1,7),(6,0),(6,1),(7,1),(6,6),(6,7),(7,6),
                             (1,1),(1,6),(6,1),(6,6)]:
                corner_bonus = -120.0  # adjacent-ish penalty
            # positional weight
            pw = float(POS_W[r, c])
            # mobility after
            np1, no1 = apply_move(player, opp, m)
            mob = len(legal_moves(np1, no1)) - len(legal_moves(no1, np1))
            scored.append((corner_bonus + 0.35*pw + 0.8*mob, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]

    def minimax(player, opp, depth, alpha, beta, ply_remaining):
        moves = legal_moves(player, opp)
        if depth == 0 or not moves:
            # If no moves, current player passes: game continues with opponent to move.
            if not moves:
                opp_moves = legal_moves(opp, player)
                if not opp_moves:
                    # terminal
                    return evaluate(player, opp, ply_remaining), None
                # pass turn
                score, _ = minimax(opp, player, depth-1, -beta, -alpha, ply_remaining-1)
                return -score, None
            return evaluate(player, opp, ply_remaining), None

        best_move = None
        # Order moves
        for m in ordered_moves(player, opp):
            np1, no1 = apply_move(player, opp, m)
            score, _ = minimax(no1, np1, depth-1, -beta, -alpha, ply_remaining-1)
            score = -score
            if score > alpha:
                alpha = score
                best_move = m
            if alpha >= beta:
                break
        return alpha, best_move

    # ---- Main move selection ----
    initial_moves = legal_moves(you, opponent)
    if not initial_moves:
        return "pass"

    # Determine depth by stage: faster early/mid, deeper late.
    filled = int(you.sum() + opponent.sum())
    if filled < 18:
        depth = 3
    elif filled < 44:
        depth = 4
    else:
        depth = 5

    # Slight time safety: keep within 1s by limiting branching through ordering + pruning.
    # Also cap by remaining empties.
    empty_count = 64 - filled
    depth = min(depth, 2 + empty_count // 10)

    ply_remaining = empty_count

    alpha = -1e18
    beta = 1e18
    best_score, best_move = minimax(you, opponent, depth, alpha, beta, ply_remaining)

    if best_move is None:
        # Fallback: pick best immediate heuristic
        moves = ordered_moves(you, opponent)
        best_move = moves[0]

    return move_to_str(best_move)
