
import numpy as np

def policy(state: dict) -> str:
    """
    A Backgammon policy that prioritizes bar moves, hitting blots, making points,
    avoiding blots, and bearing off checkers when possible.
    """

    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'], reverse=True) # Sort dice high to low

    def find_moves(dice_order):
        moves = []

        def check_move(from_pt, die):
            if my_bar > 0 and from_pt != 'B':
                return False
            if my_bar == 0 and from_pt == 'B':
                return False

            if from_pt == 'B':
                dest_pt = 24 - die  # Bar to board (my perspective)
            else:
                dest_pt = from_pt - die

            if dest_pt < 0: # off board
                can_bear_off = all(my_pts[i] == 0 for i in range(6, 24))

                if not can_bear_off:
                    return False

            elif opp_pts[dest_pt] >= 2:
                return False

            return True
        
        def evaluate_move(from_pt, die): 
            # Simple evaluation function
            score = 0

            if from_pt == 'B':
                dest_pt = 24 - die
            else:
                dest_pt = from_pt - die

            # Avoid hitting yourself on the bar
            if dest_pt >= 0 and my_pts[dest_pt] > 0:
                score -= 1

            if dest_pt >= 0 and opp_pts[dest_pt] == 1:
                score += 5 # Hitting a blot is good
                
            if dest_pt >= 0 and my_pts[dest_pt] == 1:
                score -= 2 # avoid blots

            return score



        # First die
        possible_first_moves = []

        if my_bar > 0:
            if check_move('B', dice[0]):
                possible_first_moves.append(('B', evaluate_move('B', dice[0])))
        else:
            for i in range(24):
                if my_pts[i] > 0 and check_move(i, dice[0]):
                    possible_first_moves.append((i, evaluate_move(i, dice[0])))

        # Sort candidate first moves based on evaluation function
        possible_first_moves = sorted(possible_first_moves, key = lambda x: x[1], reverse=True)

        if not possible_first_moves:
            first_move = 'P'
        else:
            first_move = possible_first_moves[0][0] if isinstance(possible_first_moves[0][0], str) else f'A{possible_first_moves[0][0]}'

        # Second die
        possible_second_moves = []
        if first_move == 'P':  # No first move, check all points
            if my_bar > 0:
                if check_move('B', dice[1]):
                    possible_second_moves.append(('B', evaluate_move('B', dice[1])))

            else:
                for i in range(24):
                    if my_pts[i] > 0 and check_move(i, dice[1]):
                        possible_second_moves.append((i, evaluate_move(i, dice[1])))

            possible_second_moves = sorted(possible_second_moves, key = lambda x: x[1], reverse=True)

            if not possible_second_moves:
                second_move = 'P'
            else:
                 second_move = possible_second_moves[0][0] if isinstance(possible_second_moves[0][0], str) else f'A{possible_second_moves[0][0]}'

        else: # A first move was made, adjust the board state and find the second move

            temp_my_pts = my_pts[:]
            temp_my_bar = my_bar

            if first_move == 'B':
                dest_pt = 24 - dice[0]
                temp_my_bar -= 1

                if dest_pt >= 0: # not bearing off
                    if opp_pts[dest_pt] == 1:  # Hit opponent
                        pass  # Logic handled by the engine
                    temp_my_pts[dest_pt] += 1
                
            else:
                from_pt = int(first_move[1:])
                dest_pt = from_pt - dice[0]
                temp_my_pts[from_pt] -= 1
            
                if dest_pt >= 0:
                    if opp_pts[dest_pt] == 1:
                        pass
                    temp_my_pts[dest_pt] += 1
            
            if my_bar > 0: #Bar first
                if check_move('B', dice[1]):
                    possible_second_moves.append(('B', evaluate_move('B', dice[1])))
            else:
                for i in range(24):

                    if temp_my_pts[i] > 0 and check_move(i, dice[1]):
                         possible_second_moves.append((i, evaluate_move(i, dice[1])))
            
            possible_second_moves = sorted(possible_second_moves, key = lambda x: x[1], reverse=True)

            if not possible_second_moves:
                second_move = 'P'
            else:
                second_move = possible_second_moves[0][0] if isinstance(possible_second_moves[0][0], str) else f'A{possible_second_moves[0][0]}'


        moves.append((first_move, second_move))
        return moves

    # Try higher die first, then lower
    moves_high_first = find_moves("high")

    move_str = f'H:{moves_high_first[0][0]},{moves_high_first[0][1]}'

    return move_str
