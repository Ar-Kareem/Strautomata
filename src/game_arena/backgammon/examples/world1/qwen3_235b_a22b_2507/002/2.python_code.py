
import numpy as np
from itertools import permutations

def policy(state: dict) -> str:
    my_pts = np.array(state['my_pts'])
    opp_pts = np.array(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'], reverse=True)
    high_die, low_die = dice if len(dice) == 2 else (dice[0] if dice else 0, 0)
    have_two_dice = len(dice) == 2

    # Check if all my checkers are in home board (points 0 to 5)
    in_home_board = np.all(my_pts[6:] == 0)
    opp_in_home_board = np.all(opp_pts[:18] == 0)

    # Generate list of legal starting points for a move using a die value
    def can_move_from(start, die):
        if start == 'B':
            if my_bar == 0:
                return False
            dest = die - 1  # entering from bar: die 1 goes to point 0
            return opp_pts[dest] <= 1
        # Regular move
        if my_pts[start] == 0:
            return False
        dest = start - die
        if dest < 0:
            # Bear off only if all checkers are in home board
            if in_home_board:
                # Check if this is a valid bear off (exact or deepest)
                max_checkers_point = np.where(my_pts > 0)[0].max() if np.any(my_pts) else -1
                if max_checkers_point < 6 and die >= 6 - max_checkers_point:
                    return True  # Can bear off
                if dest == -1 and start == 0:
                    return True  # Exact bear off
                return False
            return False
        # Can only move to a point with at most one opponent
        return opp_pts[dest] <= 1

    # Generate all legal moves
    def get_legal_moves():
        moves = []
        if my_bar > 0:
            # Must move from bar
            for die in dice:
                dest = die - 1
                if dest >= 0 and opp_pts[dest] <= 1:
                    moves.append(('B', die))
        else:
            for start in range(24):
                if my_pts[start] == 0:
                    continue
                for die in dice:
                    dest = start - die
                    if dest < 0:
                        if in_home_board:
                            max_point = np.where(my_pts > 0)[0].max() if np.any(my_pts) else -1
                            if max_point < 6 and die >= 6 - max_point:
                                moves.append((start, die))
                            elif dest == -1 and start == 0:
                                moves.append((start, die))
                        continue
                    if opp_pts[dest] <= 1:
                        moves.append((start, die))
        return moves

    legal_moves = get_legal_moves()

    # If no legal moves, pass
    if not legal_moves:
        return "H:P,P"

    # Group moves by die used
    high_moves = [m for m in legal_moves if m[1] == high_die]
    low_moves = [m for m in legal_moves if m[1] == low_die]

    # If two dice, try to find a sequence that uses both
    best_score = -1e9
    best_action = "H:P,P"

    # If on bar, only consider moves from bar
    if my_bar > 0:
        # Must move from bar — only bar moves allowed
        high_bar = any(m[0] == 'B' for m in high_moves)
        low_bar = any(m[0] == 'B' for m in low_moves)

        if high_bar and low_bar and have_two_dice:
            # Can use both dice from bar
            return "H:B,B"
        elif high_bar:
            return "H:B,P"
        elif low_bar:
            return "L:B,P"
        else:
            return "H:P,P"

    # Not on bar — consider all combinations
    for order in ['H', 'L']:
        d1, d2 = (high_die, low_die) if order == 'H' else (low_die, high_die)
        m1_list = high_moves if d1 == high_die else low_moves
        m2_list = low_moves if d2 == low_die and high_die != low_die else high_moves

        for m1 in m1_list:
            start1 = m1[0]
            # Simulate first move
            new_my_pts = my_pts.copy()
            new_opp_pts = opp_pts.copy()
            new_my_pts[start1] -= 1
            dest1 = start1 - d1
            if dest1 >= 0:
                if new_opp_pts[dest1] == 1:
                    new_opp_pts[dest1] = 0
                    new_my_pts[23 - dest1] += 1  # opponent checker goes to bar (but not used)
                new_my_pts[dest1] += 1
            # Else: bear off

            # Second move
            for m2 in m2_list:
                start2 = m2[0]
                if start2 == start1 and d1 == d2 and my_pts[start1] == 1:
                    continue  # not enough checkers
                if new_my_pts[start2] == 0:
                    continue
                dest2 = start2 - d2
                if dest2 >= 0 and new_opp_pts[dest2] >= 2:
                    continue

                # Both moves are valid
                action = f"{order}:{'B' if start1 == 'B' else f'A{start1}'}" \
                         f",{f'B' if start2 == 'B' else f'A{start2}'}"
                score = evaluate_move(start1, d1, start2, d2, my_pts, opp_pts, in_home_board, my_off, my_bar)
                if score > best_score:
                    best_score = score
                    best_action = action

        # Single move
        for m1 in m1_list:
            start1 = m1[0]
            # Check if second die can be played — if yes, we must play both
            can_play_second = False
            test_d2 = low_die if d1 == high_die else high_die
            for s in range(24):
                if my_pts[s] == 0:
                    continue
                d = s - test_d2
                if d >= 0 and opp_pts[d] <= 1:
                    can_play_second = True
                    break
                if d < 0 and in_home_board:
                    max_p = np.where(my_pts > 0)[0].max()
                    if max_p < 6 and test_d2 >= 6 - max_p:
                        can_play_second = True
                    elif d == -1 and s == 0:
                        can_play_second = True
            if can_play_second:
                continue  # Must play both if possible

            action = f"{order}:{'B' if start1 == 'B' else f'A{start1}'},P"
            score = evaluate_move(start1, d1, None, None, my_pts, opp_pts, in_home_board, my_off, my_bar)
            if score > best_score:
                best_score = score
                best_action = action

    return best_action

def evaluate_move(start1, die1, start2, die2, my_pts, opp_pts, in_home_board, my_off, my_bar):
    score = 0.0
    # Progress: moving checkers forward (lower index)
    if start1 is not None:
        dest1 = start1 - die1
        if dest1 >= 0:
            # Reward for moving backward checkers
            score += (23 - start1) * 0.1
            # Bonus for making points (if we add to a point with one checker)
            new_my_count = my_pts[dest1] + 1
            if new_my_count == 2:
                score += 0.5  # Great: made a point
            elif new_my_count == 1:
                # Risk: leaving a blot
                if opp_pts[dest1] == 1:  # can be hit
                    score -= 0.8
            # Penalty for leaving a blot
            if my_pts[start1] == 1:
                score -= 0.8  # was a blot, now gone
            else:
                score -= 0.3  # safe, but moving from safety
            # If hitting an opponent blot
            if dest1 < 24 and opp_pts[dest1] == 1:
                score += 1.2  # Big bonus for hitting
        else:
            # Bearing off
            if in_home_board:
                score += 1.5  # Good: getting checkers off
                if start1 == 0 and die1 == 1:
                    score += 0.5  # Exact bear off
                elif die1 >= 6:
                    score += 0.3  # High die bear off

    if start2 is not None:
        dest2 = start2 - die2
        if dest2 >= 0:
            score += (23 - start2) * 0.1
            new_my_count = my_pts[dest2] + (1 if dest2 != start1 - die1 else 2)  # adjust for both moves
            if new_my_count == 2:
                score += 0.5
            elif new_my_count == 1:
                if opp_pts[dest2] == 1:
                    score -= 0.8
            if my_pts[start2] == 1:
                score -= 0.8
            else:
                score -= 0.3
            if dest2 < 24 and opp_pts[dest2] == 1:
                score += 1.2
        else:
            score += 1.5
            if start2 == 0 and die2 == 1:
                score += 0.5
            elif die2 >= 6:
                score += 0.3

    # Bonus for reducing checkers on high points
    late_weight = np.array([1.0, 0.9, 0.8, 0.7, 0.6, 0.5] + [0] * 18)
    score += np.sum(my_pts * late_weight)

    # Incentive to close out opponent
    if np.sum(opp_pts[:6]) == 0 and np.sum(opp_pts[6:12]) == 0:
        score += 1.0  # Opponent is far behind

    return score
