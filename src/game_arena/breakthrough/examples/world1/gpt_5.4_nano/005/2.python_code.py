
from __future__ import annotations

from typing import List, Tuple
import math

BoardPos = Tuple[int, int]

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    my_positions = list(me)
    opp_positions = list(opp)

    my_set = set(my_positions)
    opp_set = set(opp_positions)

    # Board occupancy
    def occupied(r: int, c: int) -> bool:
        return (r, c) in my_set or (r, c) in opp_set

    # Directions
    # black moves down (to lower row); white moves up (to higher row)
    if color == 'b':
        dr = -1
        goal_row = 0
        start_row = 7
    else:
        dr = 1
        goal_row = 7
        start_row = 0

    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < 8 and 0 <= c < 8

    def opponent_color() -> str:
        return 'w' if color == 'b' else 'b'

    opp_dr = -dr  # opponent moves opposite direction

    # Generate legal moves for one side
    def legal_moves(for_me: List[BoardPos], for_opp_set: set[BoardPos], for_my_set: set[BoardPos]) -> List[Tuple[BoardPos, BoardPos]]:
        moves = []
        for r, c in for_me:
            for dc in (0, -1, 1):
                nr, nc = r + dr, c + dc
                if not in_bounds(nr, nc):
                    continue
                if dc == 0:
                    # forward move must be empty
                    if (nr, nc) not in for_opp_set and (nr, nc) not in for_my_set:
                        moves.append(((r, c), (nr, nc)))
                else:
                    # diagonal forward: can be empty move or capture by landing on opponent piece
                    # rules: diagonal forward allowed only if empty; capture only if opponent occupies
                    if (nr, nc) in for_opp_set:
                        moves.append(((r, c), (nr, nc)))
                    else:
                        if (nr, nc) not in for_my_set:
                            moves.append(((r, c), (nr, nc)))
        return moves

    # Check immediate win
    def is_win_after_move(move_from: BoardPos, move_to: BoardPos) -> bool:
        tr, tc = move_to
        return tr == goal_row

    # Threat evaluation: can opponent capture our piece at some square?
    # i.e., if we have a piece at (r,c), does opponent have a piece that could capture onto it next move?
    def squares_under_threat(sq: BoardPos, opp_set_now: set[BoardPos]) -> bool:
        r, c = sq
        # Opponent captures diagonally forward onto sq.
        # If opponent moves with opp_dr, then their from squares could be:
        # from_row = r - opp_dr ; from_col = c +/- 1
        fr = r - opp_dr
        for dc in (-1, 1):
            fc = c + dc
            if in_bounds(fr, fc) and (fr, fc) in opp_set_now:
                # ensure move is capture diagonal onto sq; that implies opponent can capture
                return True
        return False

    # Generate our legal moves
    moves = legal_moves(my_positions, opp_set, my_set)

    # Guaranteed legality fallback: if something went wrong, choose the first (should not happen)
    if not moves:
        # no legal moves shouldn't occur in this game usually, but to avoid disqualification:
        # return a dummy legal-ish move if possible (should be legal by construction; otherwise keep scanning)
        # We'll scan all squares for any forward/diagonal move.
        for r, c in my_positions:
            for dc in (0, -1, 1):
                nr, nc = r + dr, c + dc
                if not in_bounds(nr, nc):
                    continue
                if dc == 0:
                    if (nr, nc) not in my_set and (nr, nc) not in opp_set:
                        return ((r, c), (nr, nc))
                else:
                    if (nr, nc) in opp_set:
                        return ((r, c), (nr, nc))
                    if (nr, nc) not in my_set:
                        return ((r, c), (nr, nc))
        # If truly no move, pick any (illegal would disqualify, so better raise)
        raise RuntimeError("No legal moves found.")

    # Score moves with tactical lookahead
    # We prefer:
    # 1) Immediate win
    # 2) Captures (especially those that also create further threats)
    # 3) Advancing toward goal
    # 4) Blocking: avoid moving into immediate capture, and if possible capture a piece that prevents opponent advancement
    def evaluate_move(move_from: BoardPos, move_to: BoardPos) -> float:
        fr, fc = move_from
        tr, tc = move_to

        # immediate win
        if is_win_after_move(move_from, move_to):
            return 1e9

        # Determine if capture
        is_capture = (tr, tc) in opp_set

        # Simulate position after our move (single ply)
        new_my_set = set(my_set)
        new_opp_set = set(opp_set)

        new_my_set.remove((fr, fc))
        new_my_set.add((tr, tc))
        if is_capture:
            new_opp_set.remove((tr, tc))

        # If opponent has any immediate winning move, penalize
        # Generate opponent moves and check their immediate win
        opp_positions_now = list(new_opp_set)
        opp_my_set = set(new_my_set)

        opp_moves = []
        # opponent dr is opp_dr
        # We can use same move generator logic but inlined to avoid complexity
        for orr, oc in opp_positions_now:
            # forward
            nr = orr + opp_dr
            if in_bounds(nr, oc):
                if (nr, oc) not in opp_my_set and (nr, oc) not in new_opp_set:
                    opp_moves.append(((orr, oc), (nr, oc)))
            # diagonals
            for dc in (-1, 1):
                nc = oc + dc
                nr = orr + opp_dr
                if in_bounds(nr, nc):
                    if (nr, nc) in opp_my_set:
                        opp_moves.append(((orr, oc), (nr, nc)))
                    else:
                        if (nr, nc) not in new_opp_set:
                            opp_moves.append(((orr, oc), (nr, nc)))

        # Opponent win row is our start? For opponent, their goal is the opposite home row.
        opp_goal_row = 0 if color == 'w' else 7  # if we are 'b', opp is 'w' goal row is 0; if we are 'w', opp goal row is 7
        for _, to in opp_moves:
            if to[0] == opp_goal_row:
                # Strongly avoid allowing immediate loss
                return -1e8

        # Our piece safety: if the moved piece is immediately capturable by opponent, penalize
        moved_piece_under_threat = squares_under_threat((tr, tc), new_opp_set)
        threat_penalty = 0.0
        if moved_piece_under_threat:
            threat_penalty = 6000.0  # significant

        # Advancement: prefer getting closer to opponent home row
        # For black (goal_row=0), progress = (fr - tr); for white (goal_row=7), progress = (tr - fr)
        progress = (fr - tr) if color == 'b' else (tr - fr)
        # Also consider absolute distance from goal (smaller is better)
        dist_before = abs(fr - goal_row)
        dist_after = abs(tr - goal_row)
        dist_improvement = dist_before - dist_after

        # Centralization: prefer columns near middle (3.5)
        center = 3.5
        central_before = abs(fc - center)
        central_after = abs(tc - center)
        central_improvement = central_before - central_after

        score = 0.0

        # Capture value
        if is_capture:
            # base capture bonus
            score += 20000.0
            # discourage capturing if it makes us immediately capturable (handled by threat_penalty)
            # slight preference for captures that move further forward
            score += 800.0 * progress
            # also prefer capturing higher-advanced enemy pieces (proxy by their row)
            # (for black we want capture that targets large row (closer to our goal is smaller, but just use dist from our home))
            # We'll use how far the captured piece was from our goal: farther enemy piece captured is good.
            captured_r = tr
            enemy_progress = (captured_r - start_row) if color == 'w' else (start_row - captured_r)
            # normalize
            score += 50.0 * enemy_progress

        # Advancement heuristic
        score += 350.0 * dist_improvement
        score += 120.0 * progress
        score += 25.0 * central_improvement

        # Extra heuristic: create threats (if our move lands so that we can capture opponent next turn)
        # Check if from the new position we have a diagonal capture available.
        threat_next = 0
        for dc in (-1, 1):
            nr, nc = tr + dr, tc + dc
            if in_bounds(nr, nc) and (nr, nc) in new_opp_set:
                threat_next += 1
        score += 220.0 * threat_next

        # If we are not capturing, consider blocking: if opponent piece(s) are directly in front diagonals,
        # maybe diagonal empty moves still good to position.
        if not is_capture:
            # If we moved forward to a square that blocks opponent advances, small bonus
            # For each opponent piece, see if their direct forward square equals our new square.
            block_bonus = 0.0
            for orr, oc in new_opp_set:
                nr = orr + opp_dr
                if in_bounds(nr, oc) and (nr, oc) == (tr, tc):
                    block_bonus += 60.0
            score += block_bonus

        score -= threat_penalty

        return score

    # Choose best move
    best_move = None
    best_score = -math.inf
    for fr, to in [(m[0], m[1]) for m in moves]:
        # (This comprehension isn't necessary; we already have from/to)
        pass

    for move in moves:
        fr, to = move
        sc = evaluate_move(fr, to)
        if sc > best_score:
            best_score = sc
            best_move = move

    # Ensure best_move is legal by construction (from our legal generator)
    # Return as required format.
    return best_move
