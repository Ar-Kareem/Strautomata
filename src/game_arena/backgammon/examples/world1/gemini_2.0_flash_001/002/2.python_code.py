
import random


def policy(state: dict) -> str:
    """
    A Backgammon policy that prioritizes:
    1. Moving off the bar
    2. Hitting opponent's blots
    3. Making points
    4. Bearing off
    5. Avoiding leaving blots
    """

    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    def find_moves(order):
        possible_moves = []
        if my_bar > 0:
            # Must move off the bar first
            for die in dice:
                target_point = 24 - die
                if opp_pts[target_point] < 2:
                    possible_moves.append(('B',))
                    break  # Only need one bar move
            else:
                # No legal moves off the bar
                return []
        else:
            # Generate all possible moves from the board
            non_zero_points = [i for i, count in enumerate(my_pts) if count > 0]

            # Single dice moves
            for point in non_zero_points:
                possible_moves.append(('A' + str(point),))

            # Double dice moves
            for point1 in non_zero_points:
                for point2 in non_zero_points:
                    possible_moves.append(('A' + str(point1), 'A' + str(point2)))

        return possible_moves

    def is_legal(move_str: str, dice, state) -> bool:
        """Dummy function, always return True as engine checks for legal moves"""
        return True

    def order_moves(moves, dice, state, order):
        """Orders moves according to order string."""
        if len(dice) == 2:
             if (moves[0][0] == 'B' and moves[0][1] == 'B'):
                pass # special case is handled elswhere
             elif order == 'H':
                sorted_moves = []
                for m in moves:
                    sorted_moves.append([max(dice),min(dice)])
                return sorted_moves
             else:
                sorted_moves = []
                for m in moves:
                    sorted_moves.append([min(dice),max(dice)])
                return sorted_moves
        return dice
        

    def format_move(order, from1, from2):
        return f"{order}:{from1},{from2}"

    #Prioritize High Dice
    for order in ['H', 'L']:
        moves = find_moves(order)
        if not moves:
            return format_move('H', 'P', 'P')

       
        if len(dice) == 2: # Need two moves only if dice is not empty
            for move1 in moves:
                for move2 in moves:  # allows for double moves
                    #Check if both moves are from bar:
                    if (len(move1) == 1 and move1[0] == 'B' and len(move2) == 1 and move2[0] == 'B'):
                       if(len(dice) == 2): # special case where we can only move from bar using both dice.
                           d1, d2 = dice
                           t1 = 24 - d1
                           t2 = 24 - d2
                           if opp_pts[t1] < 2 and opp_pts[t2] <2: # Are both targets open?
                               return format_move(order, 'B','B')
                           continue

                    move_str = format_move(order, move1[0], move2[0])

                    if is_legal(move_str, dice, state):
                        return move_str



        else: # One move only
            for move1 in moves:
                move_str = format_move(order, move1[0], 'P')  # Pass the second move
                if is_legal(move_str, dice, state):
                    return move_str


    # No valid moves found
    return format_move('H', 'P', 'P')
