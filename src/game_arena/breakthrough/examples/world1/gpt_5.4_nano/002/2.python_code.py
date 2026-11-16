
import random
from typing import List, Tuple, Optional

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Breakthrough move generator + tactical policy for 8x8.
    color: 'b' moves forward by -1 row (towards smaller row values),
           'w' moves forward by +1 row (towards larger row values),
    based on prompt: black moves downwards (to lower row values) and white upwards (to higher row values).
    """
    # Determine direction and target home row
    # From prompt: black moves downwards -> to lower row values => dr = -1, home row for black = 0? (opponent's home row is furthest from you)
    # From prompt: white moves upwards -> to higher row values => dr = +1
    if color == 'b':
        dr = -1
        opp_home_row = 7  # opponent is white whose home row is 7
    else:
        dr = 1
        opp_home_row = 0  # opponent is black whose home row is 0

    my_set = set(me)
    opp_set = set(opp)

    def in_bounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def is_empty(r, c):
        return (r, c) not in my_set and (r, c) not in opp_set

    def would_be_captured_by_opp(pos_after, opp_pieces):
        """Check if opponent can capture pos_after immediately on their next move."""
        tr, tc = pos_after
        # If opponent piece at (r0, c0) can capture diagonally forward onto (tr, tc)
        # For opponent color, their forward direction is -dr
        opp_dr = -dr
        # If opponent captures onto (tr, tc), then opponent piece must be one step behind:
        # opponent piece at (tr - opp_dr, tc-1) captures to (tr, tc) or (tr - opp_dr, tc+1)
        r0 = tr - opp_dr
        for dc in (-1, 1):
            c0 = tc - dc
            if in_bounds(r0, c0) and (r0, c0) in opp_set:
                return True
        return False

    def generate_moves(my_positions, opp_positions, color_char):
        my_s = set(my_positions)
        opp_s = set(opp_positions)
        forward = dr if color_char == color else (dr)  # dr already for current color
        moves = []
        for r, c in my_s:
            fr = r + forward
            if in_bounds(fr, c):
                # straight move
                if (fr, c) not in my_s and (fr, c) not in opp_s:
                    moves.append(((r, c), (fr, c)))
                # diagonal captures only if opponent piece present and diagonal empty not required (must be occupied)
                for dc in (-1, 1):
                    fc = c + dc
                    if in_bounds(fr, fc) and (fr, fc) in opp_s:
                        moves.append(((r, c), (fr, fc)))
                    # diagonal non-capture move if empty
                    if in_bounds(fr, fc) and (fr, fc) not in my_s and (fr, fc) not in opp_s:
                        moves.append(((r, c), (fr, fc)))
        return moves

    def move_is_legal(move, my_positions, opp_positions, color_char):
        ((r0, c0), (r1, c1)) = move
        if (r0, c0) not in my_positions:
            return False
        if not in_bounds(r1, c1):
            return False
        if color_char == 'b':
            nd = -1
        else:
            nd = 1
        if r1 - r0 != nd:
            return False
        if abs(c1 - c0) > 1:
            return False
        my_s = set(my_positions)
        opp_s = set(opp_positions)
        # straight
        if c1 == c0:
            # must be empty
            return (r1, c1) not in my_s and (r1, c1) not in opp_s
        else:
            # diagonal: either empty move or capture onto opponent
            if (r1, c1) in opp_s:
                return True
            return (r1, c1) not in my_s and (r1, c1) not in opp_s

    # If something inconsistent happens, ensure we always return a legal move.
    legal_moves = generate_moves(me, opp, color)
    legal_moves = [m for m in legal_moves if move_is_legal(m, me, opp, color)]
    if not legal_moves:
        # Should not happen in normal games, but return a dummy legal if possible
        # (pick any move from generated)
        return ((me[0][0], me[0][1]), (me[0][0] + dr, me[0][1]))

    # Immediate win check: move onto opponent's home row
    for m in legal_moves:
        (_, _), (tr, _) = m
        if tr == opp_home_row:
            return m

    # Evaluation
    def evaluate(my_positions, opp_positions):
        # higher is better
        my_s = set(my_positions)
        opp_s = set(opp_positions)

        # Material: fewer opponent pieces is better
        score = 1000 * (len(opp_positions) == 0)  # huge if win
        score += (len(me) - len(opp_positions)) * 50

        # Advancement: reward pieces closer to opponent home row
        # For black (dr=-1), opponent home row=7; distance = opp_home_row - r
        # For white (dr=+1), opponent home row=0; distance = r - opp_home_row
        for r, c in my_positions:
            # progress toward opponent home row
            progress = (opp_home_row - r) if color == 'b' else (r - opp_home_row)
            # progress range 0..7
            score += progress * 12

        # Centrality: encourage files 3,4
        for r, c in my_positions:
            score -= abs(c - 3.5) * 2

        # Penalty if a move has left a piece capturable is handled during lookahead.
        # Small penalty if we're losing mobility (not used heavily).
        score -= len(my_positions) * 2  # slight penalty for having fewer pieces

        # Encourage being able to capture (positional)
        # reward opponent threatened squares
        opp_dr = -dr
        for r, c in opp_s:
            # if our piece could capture onto/around this piece next move, add a small reward
            pass

        return score

    def apply_move(my_positions, opp_positions, move):
        my_s = set(my_positions)
        opp_s = set(opp_positions)
        ((r0, c0), (r1, c1)) = move
        my_s.remove((r0, c0))
        captured = (r1, c1) in opp_s
        if captured:
            opp_s.remove((r1, c1))
        my_s.add((r1, c1))
        return list(my_s), list(opp_s), captured

    # Shallow lookahead: for each move, consider opponent best response and choose move maximizing (our eval - their eval after response).
    # Additionally, strong immediate capture-back avoidance.
    best_moves = []
    best_score = None

    # Shuffle for tie-breaking
    random.shuffle(legal_moves)

    for m in legal_moves:
        my_after, opp_after, captured = apply_move(me, opp, m)

        # If we just captured, avoid blunders: if any of our pieces is immediately capturable, penalize.
        # Specifically, check the moved piece (and optionally others) for vulnerability next turn.
        moved_to = m[1]
        vulnerability = 0
        # moved piece vulnerability
        if would_be_captured_by_opp(moved_to, opp):
            vulnerability += 1
        # also check any other piece that can be captured (light)
        for p in my_after:
            if p != moved_to and would_be_captured_by_opp(p, opp):
                vulnerability += 0.5

        # Opponent response
        opp_moves = []
        # Generate opponent moves based on their color (opposite)
        opp_color = 'w' if color == 'b' else 'b'
        # For move generation, we can reuse generate_moves with global dr fixed for current color,
        # so implement a local generation using opp_color's direction.
        # We'll just compute with a small helper.
        opp_dr = -dr

        def generate_moves_generic(positions, opp_positions, move_dr):
            moves = []
            pos_s = set(positions)
            opp_s = set(opp_positions)
            for r, c in pos_s:
                fr = r + move_dr
                if in_bounds(fr, c):
                    if (fr, c) not in pos_s and (fr, c) not in opp_s:
                        moves.append(((r, c), (fr, c)))
                    for dc in (-1, 1):
                        fc = c + dc
                        if in_bounds(fr, fc):
                            if (fr, fc) in opp_s:
                                moves.append(((r, c), (fr, fc)))
                            else:
                                if (fr, fc) not in pos_s:
                                    moves.append(((r, c), (fr, fc)))
            # Filter legality roughly (should be legal by construction)
            return moves

        opp_moves = generate_moves_generic(opp_after, my_after, opp_dr)

        # If opponent has no moves (rare), treat as good
        if not opp_moves:
            opp_best_reply_score = -10**9
        else:
            opp_best_reply_score = None
            # For each reply, compute our evaluation after that reply
            for om in opp_moves:
                # Check immediate win for opponent (they would land on our home row)
                ((or0, oc0), (or1, oc1)) = om
                # opponent's target home row (which is our home row) is 0 if they are 'b', 7 if they are 'w'
                # Using their direction sign:
                opp_home = 0 if opp_color == 'b' else 7
                if or1 == opp_home:
                    # they can win immediately, so punish heavily
                    score_after = -10**7
                else:
                    my_reply_after, opp_reply_after, _ = apply_move(my_after, opp_after, ((or0, oc0), (or1, oc1)) )
                    # Wait: apply_move assumes current player moves pieces from my_positions.
                    # So for opponent move, swap roles: treat opponent as "my" in apply_move.
                    # We'll implement properly here:
                    # Recompute with correct semantics:
                    my_s = set(my_after)
                    opp_s = set(opp_after)
                    # opponent moves from (or0,oc0) to (or1,oc1)
                    opp_s.remove((or0, oc0))
                    captured_onto = (or1, oc1) in my_s
                    if captured_onto:
                        my_s.remove((or1, oc1))
                    opp_s.add((or1, oc1))
                    my_reply_after = list(my_s)
                    opp_reply_after = list(opp_s)

                    score_after = evaluate(my_reply_after, opp_reply_after)
                # opponent will choose the move that minimizes our score
                if opp_best_reply_score is None or score_after < opp_best_reply_score:
                    opp_best_reply_score = score_after

        # Our score: prefer higher evaluation after opponent reply, penalize vulnerability
        base = evaluate(my_after, opp_after)
        # But we already computed opp_best_reply_score as "our score after best opponent reply".
        # Use that directly as the decision criterion.
        decision = opp_best_reply_score

        # Capturing is good, but capturing into vulnerability is bad.
        if captured:
            decision += 80
        decision -= vulnerability * 220

        # Slight tie-break: prefer more advanced move
        (r1, c1) = m[1]
        progress = (opp_home_row - r1) if color == 'b' else (r1 - opp_home_row)
        decision += progress * 2

        if best_score is None or decision > best_score:
            best_score = decision
            best_moves = [m]
        elif decision == best_score:
            best_moves.append(m)

    # Return one of best moves (stable)
    return best_moves[0]
