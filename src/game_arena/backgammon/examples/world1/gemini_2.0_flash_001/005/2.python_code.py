
import random

def policy(state: dict) -> str:
    """
    Calculates the next move for a Backgammon game based on the game state.

    Args:
        state (dict): A dictionary representing the current game state.

    Returns:
        str: A string representing the chosen move in the required format.
    """

    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    def get_possible_moves(dice, my_pts, opp_pts, my_bar):
        """Generates all possible legal moves for the given dice roll."""
        moves = []

        def find_moves(current_move, remaining_dice, current_points, current_bar):
            if not remaining_dice:
                moves.append(current_move)
                return

            die_options = list(remaining_dice)

            for die in die_options:
                for start_point in range(24):
                    if current_bar > 0:
                        start_point = -1  # Represent bar as -1
                        
                    if start_point == -1:  # Moving from the bar
                        if current_bar == 0:
                            continue
                        end_point = 24 - die
                        if end_point >= 0 and current_points[end_point] < 2:
                            new_points = list(current_points)
                            new_bar = current_bar - 1
                            new_points[end_point] += 1
                            new_move = current_move + ['B']
                            find_moves(new_move, remaining_dice[:remaining_dice.index(die)] + remaining_dice[remaining_dice.index(die)+1:], new_points, new_bar)

                    elif current_points[start_point] > 0:

                        end_point = start_point - die

                        if end_point >= 0 and current_points[end_point] < 2:
                            new_points = list(current_points)
                            new_points[start_point] -= 1
                            new_points[end_point] += 1
                            new_move = current_move + [f'A{start_point}']
                            find_moves(new_move, remaining_dice[:remaining_dice.index(die)] + remaining_dice[remaining_dice.index(die)+1:], new_points, current_bar)
                        elif end_point < 0: # Bear off
                            can_bear_off = True
                            for i in range(6,24):
                                if current_points[i] > 0:
                                    can_bear_off = False
                                    break 
                            if can_bear_off:
                                new_points = list(current_points)
                                new_points[start_point] -= 1
                                new_move = current_move + [f'A{start_point}']
                                find_moves(new_move, remaining_dice[:remaining_dice.index(die)] + remaining_dice[remaining_dice.index(die)+1:], new_points, current_bar)

        initial_points = list(my_pts)
        find_moves([], dice, initial_points, my_bar)

        #Filter moves by length. Shorter moves are impossible because we must play all dice if possible.
        max_length = 0
        for move in moves:
            max_length = max(max_length, len(move))

        filtered_moves = []
        for move in moves:
            if len(move) == max_length:
                filtered_moves.append(move)
        
        return filtered_moves

    possible_moves = get_possible_moves(dice, my_pts, opp_pts, my_bar)

    # If no moves are possible, return a pass.
    if not possible_moves:
        return "H:P,P"
    
    # Choose a random move from the possible moves for simplicity.
    chosen_move = random.choice(possible_moves)

    # Format the chosen move into the required string format.
    if len(chosen_move) == 1:
        move_str = f"H:{chosen_move[0]},P"
    elif len(chosen_move) == 2:
        move_str = f"H:{chosen_move[0]},{chosen_move[1]}"
    else: 
        return "H:P,P"

    return move_str
