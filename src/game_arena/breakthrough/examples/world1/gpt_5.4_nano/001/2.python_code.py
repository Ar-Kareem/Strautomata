
from __future__ import annotations

from typing import List, Tuple
import math

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Board helpers
    me_set = set(me)
    opp_set = set(opp)

    # Directions: black moves down (towards smaller row values), white moves up (towards larger row values)
    # In this problem statement: black -> lower row values, white -> higher row values.
    if color == 'b':
        dir_row = -1
        opp_home_row = 7
    else:
        dir_row = 1
        opp_home_row = 0

    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < 8 and 0 <= c < 8

    def generate_moves(for_me: List[Tuple[int, int]], my_set: set, o_set: set, my_color: str):
        # returns list of ((fr,fc),(tr,tc))
        moves = []
        dr = -1 if my_color == 'b' else 1
        for (r, c) in for_me:
            # forward straight
            r1, c1 = r + dr, c
            if in_bounds(r1, c1) and (r1, c1) not in my_set and (r1, c1) not in o_set:
                moves.append(((r, c), (r1, c1)))
            # diagonal left/right
            for dc in (-1, 1):
                r2, c2 = r + dr, c + dc
                if in_bounds(r2, c2):
                    # capture diagonal onto opponent piece
                    if (r2, c2) in o_set:
                        moves.append(((r, c), (r2, c2)))
                    else:
                        # non-capture diagonal move requires target empty
                        if (r2, c2) not in my_set:
                            moves.append(((r, c), (r2, c2)))
        return moves

    def apply_move(move, my_set, o_set, my_color):
        (fr, fc), (tr, tc) = move
        new_my = set(my_set)
        new_opp = set(o_set)
        # remove from start
        new_my.remove((fr, fc))
        # capture if landing on opponent
        if (tr, tc) in new_opp:
            new_opp.remove((tr, tc))
        new_my.add((tr, tc))
        return new_my, new_opp

    def can_capture_onto(mover_set: set, opp_set_local: set, my_color: str, from_pos: Tuple[int,int], target_pos: Tuple[int,int]) -> bool:
        # not used directly; kept for possible extensions
        return False

    def opponent_can_capture_immediately(after_my_set: set, after_opp_set: set) -> bool:
        # After our move, opponent moves next. If opponent has any capture available, we consider it risky.
        # Opponent color is the other one.
        opp_color = 'w' if color == 'b' else 'b'
        opp_dr = -1 if opp_color == 'b' else 1
        for (r, c) in after_opp_set:
            # diagonal captures only
            for dc in (-1, 1):
                tr, tc = r + opp_dr, c + dc
                if not in_bounds(tr, tc):
                    continue
                if (tr, tc) in after_my_set:
                    # opponent can capture a piece
                    return True
        return False

    def evaluate_board(my_set: set, o_set: set) -> float:
        # Higher is better for us.
        # Progress: measure average advancement toward opponent's home row.
        # For black (dir=-1), advancement is (opp_home_row - row)?? Let's unify by using "distance to goal".
        # Goal is opp_home_row. Since black goes downward (row decreasing), black goal is row=0? Wait:
        # win if piece reaches opponent's home row (furthest row from you).
        # If color='b', opponent is 'w' whose home row is 0 => furthest from black is 0.
        # But we set opp_home_row above as the row we need to reach to win.
        # Fix: opponent's home row is:
        # - if we are black, opponent (white) home row is 0
        # - if we are white, opponent (black) home row is 7
        # So update:
        nonlocal opp_home_row
        # Correct opp_home_row based on color:
        goal_row = 0 if color == 'b' else 7

        # If a piece already reached goal, winning state.
        if any(r == goal_row for (r, c) in my_set):
            return 1e9

        if not o_set:
            return 1e8

        # Progress: closer to goal is better. Use negative distance.
        prog = 0.0
        for (r, c) in my_set:
            dist = abs(goal_row - r)
            # closer => larger
            prog += (7 - dist)

        # Material advantage
        mat = 2.5 * (len(my_set) - len(o_set))

        # Center preference
        center = sum(3.5 - abs(c - 3.5) for (r, c) in my_set) * 0.05

        return prog + mat + center

    # Generate legal moves
    legal_moves = []
    # Use our local move generator
    # But our movement rules: non-capture diagonal move requires empty target.
    # We'll use generate_moves as defined.
    # For occupancy we can just pass current sets.
    legal_moves = generate_moves(me, me_set, opp_set, color)

    # Ensure legality and non-empty target constraints already handled.
    if not legal_moves:
        # Should not happen in Breakthrough, but return any legal-looking move fallback
        # (pick a piece forward if possible)
        return ((me[0][0], me[0][1]), (me[0][0], me[0][1]))

    goal_row = 0 if color == 'b' else 7

    # 1) Immediate win
    for mv in legal_moves:
        (_, _), (tr, _) = mv
        if tr == goal_row:
            return mv

    # 2) Otherwise score moves with one-ply risk + heuristic
    opp_can_any_capture = False
    best_move = None
    best_score = -math.inf

    for mv in legal_moves:
        my_after, opp_after = apply_move(mv, me_set, opp_set, color)

        # If move captures, reward it
        captured = len(opp_set) - len(opp_after)

        # Risk: if opponent can capture immediately, penalize heavily, especially if we moved into diagonals
        risky = opponent_can_capture_immediately(my_after, opp_after)

        # Evaluate resulting position
        score = evaluate_board(my_after, opp_after)

        # Add advancement bonus
        (fr, fc), (tr, tc) = mv
        advance_bonus = (abs(goal_row - fr) - abs(goal_row - tr)) * 0.8
        score += advance_bonus

        # Captures are good
        score += 5.0 * captured

        # Strongly discourage immediate recapture opportunities
        if risky:
            score -= 50.0

        # Slightly prefer moves that keep more pieces
        score += len(my_after) * 0.5

        if score > best_score:
            best_score = score
            best_move = mv

    # Fallback (should never be None)
    if best_move is None:
        best_move = legal_moves[0]

    return best_move
