
import numpy as np

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Selects a move in the game of Kalah.

    Args:
        you: A list of length 7 representing your side of the board.
        opponent: A list of length 7 representing the opponent's side of the board.

    Returns:
        An integer i (0 <= i <= 5) representing the chosen house to move from.
    """

    def simulate_move(you, opponent, move):
        """Simulates a move and returns the updated board states and whether an extra move is granted."""
        you = you[:]
        opponent = opponent[:]
        seeds = you[move]
        you[move] = 0
        current_index = move + 1
        is_your_side = True

        while seeds > 0:
            if is_your_side:
                if current_index == 6:
                    you[6] += 1
                    seeds -= 1
                    if seeds == 0:
                        return you, opponent, True  # Extra move
                    current_index = 0
                    is_your_side = False
                else:
                    you[current_index] += 1
                    seeds -= 1
                    current_index += 1
            else:
                if current_index == 6:
                    # Skip opponent's store
                    current_index = 0
                    is_your_side = True
                else:
                    opponent[current_index] += 1
                    seeds -= 1
                    current_index += 1
                    
            if current_index == 6 and not is_your_side:
               current_index = 0
               is_your_side = True
            elif current_index == 6 and is_your_side:
               pass
            elif current_index == 6:
               current_index = 0
               is_your_side = True

            if current_index > 5 and is_your_side:
                current_index = 0

            if current_index > 5 and not is_your_side:
                current_index = 0
        
        # Capture check (seeds == 0 at this point)
        if is_your_side and current_index-1 >= 0 and you[current_index-1] == 1 and opponent[5 - (current_index-1)] > 0 and (current_index-1<6):
            you[6] += 1 + opponent[5 - (current_index-1)]
            opponent[5 - (current_index-1)] = 0
            you[current_index-1] = 0

        return you, opponent, False

    # 1. Check for extra move
    for i in range(6):
        if you[i] > 0:
            temp_you, temp_opponent, extra_move = simulate_move(you, opponent, i)
            if extra_move:
                return i

    # 2. Check for capture
    for i in range(6):
        if you[i] > 0:
            temp_you, temp_opponent, extra_move = simulate_move(you, opponent, i)
            if temp_you[6] > you[6]:  # Capture occurred
                return i

    # 3. Avoid potentially bad moves (giving opponent capture)
    for i in range(6):
        if you[i] > 0:
            temp_you, temp_opponent, extra_move = simulate_move(you, opponent, i)
            last_index = -1
            seeds = you[i] + i
            
            houses = 6
            
            is_yours = True
            
            remainder = seeds
            
            
            
                
                
            
            last_index = seeds
            
           
    
            #print("I is ", i, " and last index is", last_index )
            
    # 4. Default: choose the first legal move
    for i in range(6):
        if you[i] > 0:
            return i

    # Should never reach here because policy is never called when no legal moves available
    return -1
