
import itertools

def policy(state: dict) -> str:
    """
    A Backgammon AI policy.

    Args:
        state: A dictionary representing the current game state.

    Returns:
        A move string in the format: '<ORDER>:<FROM1>,<FROM2>'.
    """

    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    def find_possible_moves(dice_order):
        moves = []

        def is_legal_move(start, die):
            if my_bar > 0 and start != 'B':
                return False
            if start == 'P':
                return True
            if start == 'B':
                dest = start_pt + die if start_pt + die < 24 else 24 # Use start_pt as 0 for bar
                if dest == 24:  # Bearing off
                    if not can_bear_off():
                        return False
                elif opp_pts[dest] >= 2:
                    return False
            else:
                start_pt = int(start[1:])
                if my_pts[start_pt] == 0:
                    return False
                dest = start_pt + die
                if dest < 0 or dest > 23:   # out of bounds
                    return False

                if dest >= 24: # Bearing off
                    if not can_bear_off():
                        return False
                elif opp_pts[dest] >= 2:
                    return False
            return True

        def can_bear_off():
            for i in range(0, 18): # Modified Range
                if my_pts[i] > 0:
                    return False
            if my_bar > 0:
                return False
            return True

        def generate_moves(current_move, remaining_dice, points_used):
            if not remaining_dice:
                moves.append(current_move)
                return

            die = remaining_dice[0]
            possible_starts = []

            if my_bar > 0:
                possible_starts = ['B']
                start_pt = 0
            else:
                possible_starts = [f'A{i}' for i in range(24) if my_pts[i] > 0]
                start_pt = -1 # Unused, but kept for consistency

            possible_starts = ['P'] + possible_starts # Always allow a pass

            for start in possible_starts:
                if start != 'P':
                    start_pt = 0 if start == 'B' else int(start[1:])
                    if start in points_used and points_used[start] == my_pts[start_pt]: continue # Don't move more pieces than you have

                if is_legal_move(start, die):
                    new_points_used = points_used.copy() # Create a copy so we don't ruin previous states
                    if start != 'P':
                       if start in new_points_used:
                           new_points_used[start]+=1
                       else:
                           start_pt = 0 if start == 'B' else int(start[1:])

                           new_points_used[start] = 1
                    generate_moves(current_move + [start], remaining_dice[1:], new_points_used)

        if len(dice) == 2:

            d1, d2 = dice_order

            generate_moves([], [d1, d2],{})

        elif len(dice) == 1:
            die = dice[0]
            generate_moves([], [die],{})
        return moves
    
    def evaluate_move(move):
        """A simple heuristic to evaluate a move."""
        score = 0

        # Bearing off is good
        for m in move:
            if m != "P":
                start_pt = 0 if m == 'B' else int(m[1:])
                die = dice[1] if dice[0] >dice[1] else dice[0]
                dest = start_pt + die if start_pt + die < 24 else 24
                if dest>=24:   #Bear off
                    score += 10
                else:
                    if opp_pts[dest] == 1:
                        score += 5
        return score


    possible_moves_high = find_possible_moves(sorted(dice, reverse=True))
    possible_moves_low = find_possible_moves(sorted(dice, reverse=False))

    if not possible_moves_high and not possible_moves_low:
        return 'H:P,P'


    best_move = None
    best_score = -10000

    order = 'H'
    
    for move in possible_moves_high:
            score = evaluate_move(move)
            if score > best_score:
                best_score = score
                best_move = move
                order = 'H'
                
    for move in possible_moves_low:
            score = evaluate_move(move)
            if score > best_score:
                best_score = score
                best_move = move
                order = 'L'

    if best_move:
        move_str = order + ":" + ",".join(best_move)
        if len(best_move) == 1 and dice:
             move_str = order + ":" + best_move[0] + ",P"
        return move_str
    else:
        return 'H:P,P'
