
import numpy as np

# Othello/Reversi policy for 8x8.
# Returns a legal move like "d3" or "pass" if no legal moves exist.

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

ALG_COLS = "abcdefgh"

def on_board(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def compute_legal_moves(you, opp):
    """Return dict: move_index (r,c) -> flips_list (list of (rr,cc))."""
    moves = {}
    empty = (you == 0) & (opp == 0)
    # For each empty cell, test all directions for bracket pattern.
    for r in range(8):
        for c in range(8):
            if not empty[r, c]:
                continue
            total_flips = []
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if not on_board(rr, cc) or opp[rr, cc] == 0:
                    continue
                # Collect contiguous opponent discs
                line = []
                while on_board(rr, cc) and opp[rr, cc] == 1:
                    line.append((rr, cc))
                    rr += dr
                    cc += dc
                if on_board(rr, cc) and you[rr, cc] == 1 and line:
                    total_flips.extend(line)
            if total_flips:
                moves[(r, c)] = total_flips
    return moves

def apply_move(you, opp, move_rc, flips):
    """Return new (you, opp) after current player places at move_rc."""
    r, c = move_rc
    new_you = you.copy()
    new_opp = opp.copy()
    new_you[r, c] = 1
    for rr, cc in flips:
        new_you[rr, cc] = 1
        new_opp[rr, cc] = 0
    return new_opp, new_you  # swap perspective: opponent becomes 'you'

# Positional weights (classic-ish): corners huge, near-corners negative.
CORNER_WEIGHT = 300
EDGE_WEIGHT = 15
CENTER_WEIGHT = 3

# Corners
CORNERS = {(0,0), (0,7), (7,0), (7,7)}
# Adjacent to corners (can be dangerous if corner is empty)
ADJ_TO_CORNER = {(0,1), (1,0), (0,6), (1,7), (6,0), (7,1), (6,7), (7,6)}
# Diagonally adjacent to corners
DIAG_TO_CORNER = {(1,1), (1,6), (6,1), (6,6)}

def evaluate(you, opp):
    """Heuristic evaluation from current player's perspective."""
    # Material
    you_count = int(you.sum())
    opp_count = int(opp.sum())
    disc_diff = you_count - opp_count

    # Mobility
    legal = compute_legal_moves(you, opp)
    opp_legal = compute_legal_moves(opp, you)
    mobility = (len(legal) - len(opp_legal))

    # Corners
    corner_score = 0
    for (r, c) in CORNERS:
        if you[r, c] == 1:
            corner_score += CORNER_WEIGHT
        elif opp[r, c] == 1:
            corner_score -= CORNER_WEIGHT

    # Edge control (light)
    edge_score = 0
    for i in range(8):
        for (r, c) in [(0, i), (7, i), (i, 0), (i, 7)]:
            if (r, c) in CORNERS:
                continue
            if you[r, c] == 1:
                edge_score += EDGE_WEIGHT
            elif opp[r, c] == 1:
                edge_score -= EDGE_WEIGHT

    # Center preference (small)
    center_score = 0
    for r in range(2, 6):
        for c in range(2, 6):
            if you[r, c] == 1:
                center_score += CENTER_WEIGHT
            elif opp[r, c] == 1:
                center_score -= CENTER_WEIGHT

    # Corner adjacency risk
    adj_score = 0
    for (r, c) in ADJ_TO_CORNER:
        # Determine corresponding corner
        # Map adjacency squares to their corner(s)
        # (0,1)->(0,0), (1,0)->(0,0), (0,6)->(0,7), (1,7)->(0,7), etc.
        if (r, c) in {(0,1), (1,0)}:
            corner = (0,0)
        elif (r, c) in {(0,6), (1,7)}:
            corner = (0,7)
        elif (r, c) in {(6,0), (7,1)}:
            corner = (7,0)
        else:
            corner = (7,7)
        if you[corner] == 0 and opp[corner] == 0:
            if you[r, c] == 1:
                adj_score -= 80
            elif opp[r, c] == 1:
                adj_score += 80

    # Diagonal corner adjacency: also risky if corner is empty
    diag_score = 0
    for (r, c) in DIAG_TO_CORNER:
        if (r, c) in {(1,1)}:
            corner = (0,0)
        elif (r, c) in {(1,6)}:
            corner = (0,7)
        elif (r, c) in {(6,1)}:
            corner = (7,0)
        else:
            corner = (7,7)
        if you[corner] == 0 and opp[corner] == 0:
            if you[r, c] == 1:
                diag_score -= 40
            elif opp[r, c] == 1:
                diag_score += 40

    # Combine: weights tuned for shallow search
    score = (10 * disc_diff) + (6 * mobility) + corner_score + edge_score + center_score + adj_score + diag_score
    return score

def move_order_key(move_rc, flips):
    """Prefer more flips, corners, and safer squares."""
    r, c = move_rc
    # Base by flip count
    k = len(flips) * 10
    # Corner preference
    if (r, c) in CORNERS:
        k += 10000
    # Avoid dangerous near-corner when the corner is empty (handled in evaluation too, but quick boost/penalty)
    if (r, c) in ADJ_TO_CORNER:
        k -= 300
    if (r, c) in DIAG_TO_CORNER:
        k -= 120
    # Slight preference for edges
    if r in (0,7) or c in (0,7):
        k += 30
    return k

def alphabeta(you, opp, depth, alpha, beta):
    """
    Alpha-beta from current player's perspective.
    Returns best value.
    """
    legal = compute_legal_moves(you, opp)
    if depth == 0 or not legal:
        if not legal:
            # If current player has no moves, game may end or opponent plays again.
            # According to rules, we can pass. Model as swapping turns with same board.
            opp_legal = compute_legal_moves(opp, you)
            if not opp_legal:
                return evaluate(you, opp)
            # Pass: opponent becomes current player; but since evaluation expects "you",
            # we just swap and keep depth-1 to encourage endgame.
            return alphabeta(opp, you, depth-1, -beta, -alpha)
        return evaluate(you, opp)

    # Max node
    # Order moves
    items = list(legal.items())
    # compute ordering based on flips length and position
    items.sort(key=lambda kv: move_order_key(kv[0], kv[1]), reverse=True)

    best = -10**18
    for (r, c), flips in items:
        n_opp, n_you = apply_move(you, opp, (r, c), flips)  # swap perspective already
        val = -alphabeta(n_you, n_opp, depth-1, -beta, -alpha)  # negamax style
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def choose_best_move(you, opp):
    legal = compute_legal_moves(you, opp)
    if not legal:
        return "pass"

    # Shallow search depth based on game phase (more pieces -> deeper)
    total_discs = int(you.sum() + opp.sum())
    if total_discs < 20:
        depth = 3
    elif total_discs < 40:
        depth = 3
    else:
        depth = 4  # endgame a bit deeper, still usually fine

    # If move count is huge, do only greedy+ordering; else search.
    if len(legal) > 10 and depth >= 3:
        # Greedy with evaluation tie-break
        best_mv = None
        best_score = -10**18
        items = list(legal.items())
        items.sort(key=lambda kv: move_order_key(kv[0], kv[1]), reverse=True)
        for (r, c), flips in items[:6]:
            n_opp, n_you = apply_move(you, opp, (r, c), flips)
            score = evaluate(n_you, n_opp)  # evaluation from next player's perspective? swap back:
            score = -score
            # incorporate immediate flip advantage
            score += len(flips) * 2
            if score > best_score:
                best_score = score
                best_mv = (r, c)
        r, c = best_mv
        return f"{ALG_COLS[c]}{r+1}"

    # Full-ish search over ordered moves
    items = list(legal.items())
    items.sort(key=lambda kv: move_order_key(kv[0], kv[1]), reverse=True)

    best_val = -10**18
    best_move = items[0][0]
    # Narrow aspiration window by using first move
    for (r, c), flips in items[:min(len(items), 14)]:
        n_opp, n_you = apply_move(you, opp, (r, c), flips)
        val = -alphabeta(n_you, n_opp, depth-1, -10**18, 10**18)
        # small tie-breakers
        val += len(flips) * 0.5
        if val > best_val:
            best_val = val
            best_move = (r, c)

    r, c = best_move
    return f"{ALG_COLS[c]}{r+1}"

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    return choose_best_move(you.astype(np.int8), opponent.astype(np.int8))
