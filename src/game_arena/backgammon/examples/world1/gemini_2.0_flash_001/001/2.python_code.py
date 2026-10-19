
import random

def find_moves(state, die, start_points):
    """Finds possible moves given the current state and a die.

    Args:
        state: The game state dictionary.
        die: The die value.
        start_points: Possible starting points (e.g., 'B' + points 0-23).

    Returns:
        A list of valid moves (start_point strings).
    """
    valid_moves = []
    for start_point in start_points:
        if start_point == 'B':
            dest = 24 - die
            if state['my_bar'] > 0 and state['opp_pts'][dest] < 2:
                valid_moves.append(start_point)
                continue  # Only bar can be moved if possible
        else:
            start_index = int(start_point[1:])
            dest = start_index - die

            # Bearing off
            if dest < 0:
                # Must check bearing off conditions
                can_bear_off = True
                for i in range(6, 24):
                    if state['my_pts'][i] > 0:
                        can_bear_off = False
                        break
                if can_bear_off:
                    valid_moves.append(start_point)
                    continue

            # Normal move
            elif dest >= 0 and state['my_pts'][start_index] > 0 and state['opp_pts'][dest] < 2:
                valid_moves.append(start_point)
    return valid_moves


def policy(state: dict) -> str:
    """
    Determines the next move for a Backgammon game.
    """
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    possible_points = ['A' + str(i) for i in range(24)]
    if state['my_bar'] > 0:
        possible_points = ['B']

    if not dice:
        return "H:P,P"

    die1, die2 = (dice[0], dice[1]) if len(dice) == 2 else (dice[0], dice[0])


    # Try using both dice
    if len(dice) == 2 and die1 != die2:
        # Prioritize using higher die first
        moves_die1 = find_moves(state, die1, ['B'] + ['A' + str(i) for i in range(24)])
        if moves_die1:
            for move1 in moves_die1:
                temp_state = {k:list(v) if isinstance(v,list) else v for k,v in state.items()}
                if move1 == 'B':
                    temp_state['my_bar'] -= 1
                    dest1 = 24 - die1
                    temp_state['my_pts'][dest1] +=1
                    if temp_state['opp_pts'][dest1] == 1:
                         temp_state['opp_pts'][dest1] = 0
                         temp_state['opp_bar'] += 1
                else:
                    start_index1 = int(move1[1:])
                    dest1 = start_index1 - die1
                    temp_state['my_pts'][start_index1] -= 1

                    if dest1 < 0: # bearing off
                        temp_state['my_off'] += 1
                    else:
                        temp_state['my_pts'][dest1] += 1

                        if temp_state['opp_pts'][dest1] == 1:
                             temp_state['opp_pts'][dest1] = 0
                             temp_state['opp_bar'] += 1

                moves_die2 = find_moves(temp_state, die2, ['B'] + ['A' + str(i) for i in range(24)])
                if moves_die2:
                    move2 = moves_die2[0]
                    return "H:" + move1 + "," + move2

        moves_die2 = find_moves(state, die2, ['B'] + ['A' + str(i) for i in range(24)])
        if moves_die2:
            for move2 in moves_die2:
                temp_state = {k:list(v) if isinstance(v,list) else v for k,v in state.items()}

                if move2 == 'B':
                    temp_state['my_bar'] -= 1
                    dest2 = 24 - die2
                    temp_state['my_pts'][dest2] +=1
                    if temp_state['opp_pts'][dest2] == 1:
                         temp_state['opp_pts'][dest2] = 0
                         temp_state['opp_bar'] += 1
                else:
                    start_index2 = int(move2[1:])
                    dest2 = start_index2 - die2
                    temp_state['my_pts'][start_index2] -= 1

                    if dest2 < 0: # bearing off
                        temp_state['my_off'] += 1
                    else:
                        temp_state['my_pts'][dest2] += 1
                        if temp_state['opp_pts'][dest2] == 1:
                             temp_state['opp_pts'][dest2] = 0
                             temp_state['opp_bar'] += 1


                moves_die1 = find_moves(temp_state, die1, ['B'] + ['A' + str(i) for i in range(24)])
                if moves_die1:
                    move1 = moves_die1[0]
                    return "L:" + move2 + "," + move1



    # If only one die can be played (or it is a double), prioritize higher
    moves_die1 = find_moves(state, die1, ['B'] + ['A' + str(i) for i in range(24)]) if len(dice)==1 or die1>=die2 else find_moves(state, max(die1,die2), ['B'] + ['A' + str(i) for i in range(24)])
    if moves_die1:
        return "H:" + moves_die1[0] + ",P"

    # Play second die if first one is not playable
    moves_die2 = find_moves(state, die2, ['B'] + ['A' + str(i) for i in range(24)]) if len(dice)==1 or die1>=die2 else find_moves(state, min(die1,die2), ['B'] + ['A' + str(i) for i in range(24)])

    if moves_die2:
        return "L:" + moves_die2[0] + ",P"


    # If can't play anything, pass
    return "H:P,P"
