
import numpy as np

# Directions: 8 neighbors
DIRS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
]

def _on_board(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def _find_flips(you, opponent, r, c):
    """Return list of positions to flip if placing at (r,c) for 'you'. Empty assumed."""
    flips = []
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        line = []
        while _on_board(rr, cc) and opponent[rr, cc] == 1:
            line.append((rr, cc))
            rr += dr
            cc += dc
        if line and _on_board(rr, cc) and you[rr, cc] == 1:
            flips.extend(line)
    return flips

def _legal_moves(you, opponent):
    moves = []
    empties = np.argwhere((you == 0) & (opponent == 0))
    for r, c in empties:
        if _find_flips(you, opponent, int(r), int(c)):
            moves.append((int(r), int(c)))
    return moves

def _apply_move(you, opponent, r, c):
    """Return new (you2, opponent2) arrays after current player places at (r,c)."""
    flips = _find_flips(you, opponent, r, c)
    you2 = you.copy()
    opp2 = opponent.copy()
    you2[r, c] = 1
    for rr, cc in flips:
        opp2[rr, cc] = 0
        you2[rr, cc] = 1
    return you2, opp2

def _count_discs(a):
    return int(a.sum())

def _opponent_legal_count(you_next, opp_next):
    # opponent to move after we apply move: opponent = opp_next, you = you_next
    return len(_legal_moves(opp_next, you_next))

def _corner_bonus(r, c):
    # corners: (0,0)=a1, (0,7)=h1, (7,0)=a8, (7,7)=h8 in array coords
    if (r, c) in [(0,0), (0,7), (7,0), (7,7)]:
        return 1000.0
    return 0.0

def _bad_x_square_penalty(r, c, you, opponent):
    """
    Penalize moves adjacent to corners if the corner isn't ours yet.
    Common Othello heuristic: X-squares (diagonally adjacent) are risky when corner empty.
    Also penalize edge-adjacent squares (A-squares) when corner empty.
    """
    # Corner positions
    corners = {
        (0,0): (1,1), (0,7): (1,6), (7,0): (6,1), (7,7): (6,6)  # X-squares
    }
    x_squares = {(1,1), (1,6), (6,1), (6,6)}
    a_squares = {(0,1), (1,0), (0,6), (1,7), (7,1), (6,0), (7,6), (6,7)}  # edge-adjacent to corners

    # If corner is not occupied by us, then X/A squares are typically bad
    penalty = 0.0
    # Determine which corner corresponds roughly
    # For X-squares:
    if (r, c) in x_squares:
        # map to nearest corner diagonal
        if r <= 1 and c <= 1:
            corner = (0,0)
        elif r <= 1 and c >= 6:
            corner = (0,7)
        elif r >= 6 and c <= 1:
            corner = (7,0)
        else:
            corner = (7,7)
        if you[corner] == 0:
            penalty -= 120.0
    if (r, c) in a_squares:
        # map to corresponding corner on same corner region
        if r == 0 and c == 1:
            corner = (0,0)
        elif r == 1 and c == 0:
            corner = (0,0)
        elif r == 0 and c == 6:
            corner = (0,7)
        elif r == 1 and c == 7:
            corner = (0,7)
        elif r == 7 and c == 1:
            corner = (7,0)
        elif r == 6 and c == 0:
            corner = (7,0)
        elif r == 7 and c == 6:
            corner = (7,7)
        elif r == 6 and c == 7:
            corner = (7,7)
        else:
            corner = None
        if corner is not None and you[corner] == 0:
            penalty -= 60.0
    return penalty

def _edge_corner_mobility_heuristic(you, opponent, r, c):
    # Prefer corners and edges slightly; avoid interior overemphasis.
    score = 0.0
    if r in (0, 7) or c in (0, 7):
        score += 6.0
    # Disc count proxy: owning more after move can help
    # (handled more strongly with lookahead)
    # X/A squares penalties:
    score += _bad_x_square_penalty(r, c, you, opponent)
    return score

def _move_to_str(r, c):
    return chr(ord('a') + c) + str(r + 1)

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    you = np.array(you, dtype=np.int8)
    opponent = np.array(opponent, dtype=np.int8)

    legal = _legal_moves(you, opponent)
    if not legal:
        return "pass"

    # Precompute game phase
    discs = _count_discs(you) + _count_discs(opponent)
    empties = 64 - discs

    # Corners are critical late; reduce randomness and increase lookahead when late
    depth2 = empties <= 20  # small depth-2 near end
    depth2 = depth2 or (discs >= 44)  # also for late-mid

    best_move = None
    best_score = -1e18

    for (r, c) in legal:
        flips = _find_flips(you, opponent, r, c)
        n_flips = len(flips)

        # Immediate heuristic
        score = 0.0

        # Corner
        score += _corner_bonus(r, c)

        # Avoid risky squares
        score += _edge_corner_mobility_heuristic(you, opponent, r, c)

        # Prefer taking more discs early/mid; less important late when stable corners dominate
        if empties > 30:
            score += 2.5 * n_flips
        else:
            score += 1.2 * n_flips

        # Mobility: after move, try to limit opponent options
        you2, opp2 = _apply_move(you, opponent, r, c)
        opp_moves = _legal_moves(opp2, you2)
        opp_mob = len(opp_moves)
        score += (18.0 - opp_mob) * 1.8  # lower opponent mobility -> higher score

        # Disc differential slight preference
        score += 3.0 * (_count_discs(you2) - _count_discs(opp2))

        # Depth-2 lookahead to reduce tactical mistakes
        if depth2:
            # Opponent chooses best for itself => worst for us.
            worst_reply_score = 1e18
            opp_legal = opp_moves
            if not opp_legal:
                # opponent has no move: good, we likely win tempo
                # add strong bonus
                score += 200.0
            else:
                for (rr, cc) in opp_legal:
                    # opponent places at (rr,cc); then we are 'opponent' player relative
                    opp2_after, you2_after = _apply_move(opp2, you2, rr, cc)  # now opp2_after = opponent discs
                    # Evaluate our result after opponent reply
                    # Our discs are you2_after
                    # Simple evaluation
                    discs_diff = _count_discs(you2_after) - _count_discs(opp2_after)
                    # mobility for us after that
                    my_legal_next = _legal_moves(you2_after, opp2_after)
                    my_mob = len(my_legal_next)
                    # corner capture if any
                    corner_gain = 0.0
                    for (cr, cc2) in [(0,0),(0,7),(7,0),(7,7)]:
                        if you2_after[cr, cc2] == 1 and you[cr, cc2] == 0:
                            corner_gain += 250.0

                    reply_score = (
                        discs_diff * 12.0 +
                        my_mob * 1.5 +
                        corner_gain
                    )
                    # We maximize our outcome, so opponent will minimize this score.
                    worst_reply_score = min(worst_reply_score, reply_score)

                # Incorporate into score
                score += worst_reply_score

        # Tie-break: prefer corners, then prefer fewer opponent moves, then prefer more flips
        if score > best_score + 1e-9:
            best_score = score
            best_move = (r, c)
        elif abs(score - best_score) <= 1e-9 and best_move is not None:
            br, bc = best_move
            # corner preference
            if _corner_bonus(r, c) > _corner_bonus(br, bc):
                best_move = (r, c)
            else:
                # fewer opponent moves
                _, _ = you, opponent
                you2, opp2 = _apply_move(you, opponent, r, c)
                br2, bc2 = best_move
                youb2, oppb2 = _apply_move(you, opponent, br2, bc2)
                opp_m = len(_legal_moves(opp2, you2))
                opp_mb = len(_legal_moves(oppb2, youb2))
                if opp_m < opp_mb:
                    best_move = (r, c)
                else:
                    # more flips
                    if n_flips > len(_find_flips(you, opponent, br2, bc2)):
                        best_move = (r, c)

    r, c = best_move
    # Ensure legality (should be, but keep robust)
    if not _find_flips(you, opponent, r, c):
        # fallback: any legal move
        r, c = legal[0]
    return _move_to_str(r, c)
