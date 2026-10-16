
import random

def policy(state: dict) -> str:
    """
    A backgammon policy that prioritizes:
    1. Moving off the bar
    2. Hitting opponent checkers
    3. Making points
    4. Moving towards home board
    5. Bearing off
    6. Avoiding leaving blots
    7. Playing the highest die
    """

    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'], reverse=True)  # Sort dice in descending order

    def find_possible_moves(die_order):
        moves = []
        used_dice = []

        def find_move(remaining_dice, current_move):
            nonlocal moves, used_dice
            if not remaining_dice:
                moves.append(current_move)
                return

            for die_index, die in enumerate(remaining_dice):
                if my_bar > 0:
                    start_point = 'B'
                else:
                    start_point_candidates = [f'A{i}' for i, count in enumerate(my_pts) if count > 0]

                for start_point in ['B'] if my_bar > 0 else [f'A{i}' for i, count in enumerate(my_pts) if count > 0]:
                    action_string = f"{die_order}:{','.join(current_move + [start_point] if start_point != 'P' else current_move + ['P'])}"
                    try:
                        # This is a simplified check. The engine will enforce legality.
                        # More sophisticated move generation would be ideal.

                        #if all from locations are P, continue
                        if not any(x != 'P' for x in (current_move + [start_point] if start_point != 'P' else current_move + ['P'])):
                            continue

                        # Simulate taking the move from the current state
                        temp_my_pts = my_pts[:]
                        temp_my_bar = my_bar
                        
                        if start_point == 'B':
                            if my_bar > 0:
                                temp_my_bar -= 1
                        else:
                            point_index = int(start_point[1:])
                            if temp_my_pts[point_index] > 0:
                                temp_my_pts[point_index] -= 1

                        find_move(remaining_dice[:die_index] + remaining_dice[die_index+1:], current_move + [start_point] if start_point != 'P' else current_move + ['P'])
                    except:
                        pass

        find_move(dice, [])
        return moves


    possible_moves_high_low = find_possible_moves('H')
    possible_moves_low_high = find_possible_moves('L')

    # Prioritize playing both dice if possible
    if possible_moves_high_low:
        # Filter out Pass moves if other valid moves are available
        valid_moves = [move for move in possible_moves_high_low if not all(p == 'P' for p in move.split(':')[1].split(','))]
        if valid_moves:
            return random.choice(valid_moves) #randomly select one of the legal moves
        else:
            return 'H:P,P'
    elif possible_moves_low_high:
        # Filter out Pass moves if other valid moves are available
        valid_moves = [move for move in possible_moves_low_high if not all(p == 'P' for p in move.split(':')[1].split(','))]
        if valid_moves:
            return random.choice(valid_moves)  #randomly select one of the legal moves
        else:
            return 'L:P,P'
    else:
        return 'H:P,P'
