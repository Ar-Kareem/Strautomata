
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    A Dots and Boxes policy.
    """

    def check_capture(row, col, dir, horizontal, vertical):
        """
        Checks if a move captures a box.
        """
        if dir == 'H':
            # Check box above
            if row > 0 and horizontal[row-1, col] != 0 and vertical[row-1, col] != 0 and vertical[row-1, col+1] != 0:
                return True
            # Check box below
            if row < 4 and horizontal[row+1, col] != 0 and vertical[row, col] != 0 and vertical[row, col+1] != 0:
                return True
        else:  # dir == 'V'
            # Check box to the left
            if col > 0 and vertical[row, col-1] != 0 and horizontal[row, col-1] != 0 and horizontal[row+1, col-1] != 0:
                return True
            # Check box to the right
            if col < 4 and vertical[row, col+1] != 0 and horizontal[row, col] != 0 and horizontal[row+1, col] != 0:
                return True
        return False

    def find_capture_move(horizontal, vertical):
        """
        Finds a move that captures a box.
        """
        for row in range(5):
            for col in range(5):
                if horizontal[row, col] == 0 and check_capture(row, col, 'H', horizontal, vertical):
                    return f'{row},{col},H'
                if vertical[row, col] == 0 and check_capture(row, col, 'V', horizontal, vertical):
                    return f'{row},{col},V'
        return None

    def check_opponent_capture(row, col, dir, horizontal, vertical):
        """
        Checks if a move would allow the opponent to capture a box immediately.
        """
        horizontal_copy = horizontal.copy()
        vertical_copy = vertical.copy()

        if dir == 'H':
            horizontal_copy[row, col] = -1
        else:
            vertical_copy[row, col] = -1

        if dir == 'H':
            # Check box above
            if row > 0 and horizontal_copy[row-1, col] != 0 and vertical_copy[row-1, col] != 0 and vertical_copy[row-1, col+1] != 0:
                return True
            # Check box below
            if row < 4 and horizontal_copy[row+1, col] != 0 and vertical_copy[row, col] != 0 and vertical_copy[row, col+1] != 0:
                return True
        else:  # dir == 'V'
            # Check box to the left
            if col > 0 and vertical_copy[row, col-1] != 0 and horizontal_copy[row, col-1] != 0 and horizontal_copy[row+1, col-1] != 0:
                return True
            # Check box to the right
            if col < 4 and vertical_copy[row, col+1] != 0 and horizontal_copy[row, col] != 0 and horizontal_copy[row+1, col] != 0:
                return True
        return False

    def find_safe_move(horizontal, vertical):
        """
        Finds a move that doesn't give the opponent a free box.
        """
        safe_moves = []
        for row in range(5):
            for col in range(5):
                if horizontal[row, col] == 0 and not check_opponent_capture(row, col, 'H', horizontal, vertical):
                    safe_moves.append(f'{row},{col},H')
                if vertical[row, col] == 0 and not check_opponent_capture(row, col, 'V', horizontal, vertical):
                    safe_moves.append(f'{row},{col},V')
        if safe_moves:
            return random.choice(safe_moves)
        return None

    def find_chain_move(horizontal, vertical):
        """
        Finds a move that captures one box and sets up another.
        """
        for row in range(5):
            for col in range(5):
                if horizontal[row, col] == 0 and check_capture(row, col, 'H', horizontal, vertical):
                   
                    # check if completing box abover sets up another box
                    if row > 0:
                      count = 0
                      if horizontal[row-1, col] != 0: count+=1
                      if vertical[row-1, col] != 0: count+=1
                      if vertical[row-1, col+1] != 0: count+=1
                      if count == 2: return f'{row},{col},H'
                    
                    # check if completing box below sets up another box
                    if row < 4:
                      count = 0
                      if horizontal[row+1, col] != 0: count+=1
                      if vertical[row, col] != 0: count+=1
                      if vertical[row, col+1] != 0: count+=1
                      if count == 2: return f'{row},{col},H'
                
                if vertical[row, col] == 0 and check_capture(row, col, 'V', horizontal, vertical):

                    # check if completing box to the left sets up another box
                    if col > 0:
                      count = 0
                      if vertical[row, col-1] != 0: count+=1
                      if horizontal[row, col-1] != 0: count+=1
                      if horizontal[row+1, col-1] != 0: count+=1
                      if count == 2: return f'{row},{col},V'

                    # check if completing box to the right sets up another box
                    if col < 4:
                      count = 0
                      if vertical[row, col+1] != 0: count+=1
                      if horizontal[row, col] != 0: count+=1
                      if horizontal[row+1, col] != 0: count+=1
                      if count == 2: return f'{row},{col},V'
                    
        return None
        

    # 1. Try to capture a box
    capture_move = find_capture_move(horizontal, vertical)
    if capture_move:
        return capture_move

    # 2. Try to set up chain reaction
    chain_move = find_chain_move(horizontal,vertical)
    if chain_move:
      return chain_move
    
    # 3. Play safe - avoid giving opponent a free capture
    safe_move = find_safe_move(horizontal, vertical)
    if safe_move:
        return safe_move

    # 4. If all else fails, make a random legal move
    possible_moves = []
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                possible_moves.append(f'{row},{col},H')
            if vertical[row, col] == 0:
                possible_moves.append(f'{row},{col},V')

    if possible_moves:
        return random.choice(possible_moves)
    else:
      # Should never happen, but include for robustness
      return '0,0,H'
