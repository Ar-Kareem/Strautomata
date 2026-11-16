
import random

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Selects a legal move in Kalah based on a simple strategy.

    Args:
        you: Your board state (list of 7 integers).
        opponent: Opponent's board state (list of 7 integers).

    Returns:
        The index of the house to move (integer between 0 and 5).
    """
    
    # 1. Check for moves that lead to another turn (landing in your store)
    for i in range(6):
        if you[i] > 0:
            seeds = you[i]
            position = i + seeds
            
            # Calculate the final landing position index.
            final_position = position % 12

            # Check if the calculated position is within your store (6)
            if final_position == 6 - i:  #Landing position within your side 
                 
                return i    
  
    # 2. Check for capture moves
    for i in range(6):
        if you[i] > 0:
            seeds = you[i]
            position = i + seeds
          
            final_position = position % 12

            # Determine which index the stone lands on. The landing position MUST be on your side with 0 stones within it. AND opposite pit must contain stones.
            if final_position < 6 - i and you[final_position] == 0 and opponent[5 - final_position] > 0 and final_position >= 0 and final_position <6:
                return i            
  
    # 3. Choose a random legal move if no captures or extra turns are available.
    legal_moves = [i for i in range(6) if you[i] > 0]
    return random.choice(legal_moves)
