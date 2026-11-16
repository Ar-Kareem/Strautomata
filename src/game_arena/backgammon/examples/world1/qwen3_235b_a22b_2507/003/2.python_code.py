
import numpy as np
from itertools import permutations

def policy(state: dict) -> str:
    my_pts = np.array(state['my_pts'], dtype=int)
    opp_pts = np.array(state['opp_pts'], dtype=int)
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'], reverse=True)
    die1, die2 = dice[0], dice[1] if len(dice) > 1 else 0

    # Convert index to action string
    def idx_to_str(idx):
        if idx == 'B': return 'B'
        if idx == 'P': return 'P'
        return f"A{idx}"

    # Check if a point is safe (0 or 1 opponent checker)
    def is_safe(pt_idx):
        return opp_pts[pt_idx] <= 1

    # Check if we can bear off (all checkers in home board: A0-A5)
    def can_bear_off():
        return np.sum(my_pts[6:]) == 0

    # Generate all legal moves from bar
    def moves_from_bar():
        moves = []
        for die in dice:
            pt_idx = die - 1  # From bar, move to A[dist-1]
            if pt_idx < 0 or pt_idx >= 24:
                continue
            if opp_pts[pt_idx] <= 1:  # Can move to that point
                moves.append(('B', die))
        return moves

    # Generate all legal moves from board
    def moves_from_board():
        moves = []
        for pt in range(24):
            if my_pts[pt] == 0:
                continue
            for die in dice:
                dest = pt - die
                if dest < 0:
                    if can_bear_off():
                        moves.append((pt, die))
                elif dest >= 0 and is_safe(dest):
                    moves.append((pt, die))
        return moves

    # Check if a move hits an opponent (dest occupied by exactly one opp checker)
    def would_hit(pt, die):
        dest = pt - die
        if dest < 0:
            return False
        return opp_pts[dest] == 1

    # Evaluate board safety (number of blots, made points, etc.)
    def evaluate():
        score = 0
        blots = 0
        made_points = 0
        for i in range(24):
            if my_pts[i] == 1:
                blots += 1
            elif my_pts[i] >= 2:
                made_points += 1
        # Bonus for reducing blots
        score -= 20 * blots
        # Bonus for made points
        score += 5 * made_points

        # Prime bonus: 6 consecutive points with >=2 checkers
        prime_bonus = 0
        for i in range(18):
            if all(my_pts[i+j] >= 2 for j in range(6)):
                prime_bonus += 100
        score += prime_bonus

        # Forward progress: sum of point indices (want to minimize)
        if np.sum(my_pts) > 0:
            weighted_pos = np.sum(np.arange(24) * my_pts)
            score -= 1 * weighted_pos  # Prefer moving checkers forward

        # Bonus for bearing off
        score += 15 * my_off

        # Penalty for being on bar
        score -= 50 * my_bar

        return score

    # Get destination after move
    def get_dest(src, die):
        return src - die

    # Apply a move and return new state
    def apply_move(src, die, temp_my_pts, temp_my_off):
        new_my_pts = temp_my_pts.copy()
        new_my_off = temp_my_off
        if src == 'B':
            pt_idx = die - 1
            if pt_idx >= 0:
                new_my_pts[pt_idx] += 1
            else:
                pass  # invalid, shouldn't happen
        else:
            new_my_pts[src] -= 1
            dest = get_dest(src, die)
            if dest < 0:
                new_my_off += 1
            else:
                new_my_pts[dest] += 1
        return new_my_pts, new_my_off

    # Generate all possible two-move sequences
    def generate_moves():
        legal_moves = []

        # Case 1: Checkers on bar
        if my_bar > 0:
            bar_moves = moves_from_bar()
            if not bar_moves:
                return [('H', 'P', 'P')]  # No move from bar
            # Try one or two moves from bar
            for src_die1, die1_val in bar_moves:
                rem_dice = [die2] if die2 != 0 else []
                if die2 == 0:
                    legal_moves.append(('H', 'B', 'P'))  # Only one die
                else:
                    # After first move, check second move
                    temp_my_pts, temp_my_off = apply_move(src_die1, die1_val, my_pts, my_off)
                    temp_my_bar = my_bar - 1
                    second_moves = []
                    for die in rem_dice:
                        for pt in range(24):
                            if temp_my_pts[pt] == 0:
                                continue
                            dest = pt - die
                            if dest >= 0:
                                if opp_pts[dest] <= 1:  # can move
                                    second_moves.append((pt, die))
                            else:
                                if all(temp_my_pts[i] == 0 for i in range(6, 24)):
                                    second_moves.append((pt, die))
                    if second_moves:
                        for src2, die2_val in second_moves:
                            if die1_val >= die2_val:
                                order = 'H'
                                from1, from2 = 'B', src2
                            else:
                                order = 'L'
                                from1, from2 = src2, 'B'
                            legal_moves.append((order, from1, from2))
                    else:
                        # Only one move possible
                        if die1_val == 6 or die1_val == die2:
                            legal_moves.append(('H', 'B', 'P'))
                        else:
                            legal_moves.append(('L', 'B', 'P'))
            return legal_moves

        # Case 2: No checkers on bar
        board_moves = moves_from_board()
        if not board_moves:
            return [('H', 'P', 'P')]

        # Must use higher die if only one move possible
        can_use_die1 = any(die == die1 for _, die in board_moves)
        can_use_die2 = die2 > 0 and any(die == die2 for _, die in board_moves)

        if not can_use_die1 and not can_use_die2:
            return [('H', 'P', 'P')]

        if not can_use_die1:
            # Must use die2 (higher die not possible)
            for src, die in board_moves:
                if die == die2:
                    legal_moves.append(('L', src, 'P'))
            return legal_moves

        if die2 == 0 or not can_use_die2:
            # Only one die to play
            for src, die in board_moves:
                if die == die1:
                    legal_moves.append(('H', src, 'P'))
            return legal_moves

        # Both dice can be played: must use both
        # Try all sequences
        for src1, die1_val in board_moves:
            for src2, die2_val in board_moves:
                if src1 == src2 and die1_val != die2_val:
                    continue  # Can't move same checker twice unless doubles
                if src1 == src2 and die1_val == die2_val and my_pts[src1] < 2:
                    continue  # Need at least two checkers
                if die1_val == die1 and die2_val == die2:
                    if die1_val >= die2_val:
                        legal_moves.append(('H', src1, src2))
                    else:
                        legal_moves.append(('L', src1, src2))
                if die1_val == die2 and die2_val == die1:
                    if die2_val >= die1_val:
                        legal_moves.append(('H', src2, src1))
                    else:
                        legal_moves.append(('L', src2, src1))

        # Remove duplicates and invalid
        seen = set()
        unique_moves = []
        for order, f1, f2 in legal_moves:
            key = (order, f1, f2)
            if key not in seen:
                seen.add(key)
                unique_moves.append((order, f1, f2))
        return unique_moves if unique_moves else [('H', 'P', 'P')]

    # Score a move by simulating it
    def score_move(order, from1, from2):
        temp_my_pts = my_pts.copy()
        temp_my_off = my_off
        temp_my_bar = my_bar

        # Apply first move
        if from1 != 'P':
            if from1 == 'B':
                pt_idx = (die1 if order == 'H' else die2) - 1
                if pt_idx < 0 or pt_idx >= 24:
                    return -1000
                if opp_pts[pt_idx] > 1:
                    return -1000
                temp_my_pts[pt_idx] += 1
                temp_my_bar -= 1
            else:
                die_used = die1 if order == 'H' else die2
                if temp_my_pts[from1] == 0:
                    return -1000
                temp_my_pts[from1] -= 1
                dest = from1 - die_used
                if dest < 0:
                    if not can_bear_off():
                        return -1000
                    temp_my_off += 1
                else:
                    if opp_pts[dest] > 1:
                        return -1000
                    temp_my_pts[dest] += 1

        # Apply second move
        if from2 != 'P':
            die_used = die2 if order == 'H' else die1
            if from2 == 'B':
                pt_idx = die_used - 1
                if pt_idx < 0 or pt_idx >= 24:
                    return -1000
                if opp_pts[pt_idx] > 1:
                    return -1000
                temp_my_pts[pt_idx] += 1
                temp_my_bar -= 1
            else:
                if temp_my_pts[from2] == 0:
                    return -1000
                temp_my_pts[from2] -= 1
                dest = from2 - die_used
                if dest < 0:
                    if not can_bear_off():
                        return -1000
                    temp_my_off += 1
                else:
                    if opp_pts[dest] > 1:
                        return -1000
                    temp_my_pts[dest] += 1

        # Evaluate the resulting board
        return evaluate()

    # Get all legal moves
    legal_moves = generate_moves()

    # Score all moves
    scored_moves = []
    for order, from1, from2 in legal_moves:
        score = score_move(order, from1, from2)
        scored_moves.append((score, order, from1, from2))

    # Choose the best move
    best_move = max(scored_moves, key=lambda x: x[0])
    _, order, from1, from2 = best_move

    # Format move string
    from1_str = idx_to_str(from1)
    from2_str = idx_to_str(from2)
    move_str = f"{order}:{from1_str},{from2_str}"
    return move_str
