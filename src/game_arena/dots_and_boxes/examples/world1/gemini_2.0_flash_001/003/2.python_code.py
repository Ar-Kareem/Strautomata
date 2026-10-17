
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    A Dots and Boxes policy for a 4x4 grid.
    """

    def check_capture(row, col, direction):
        """Checks if a move captures a box."""
        if direction == 'H':
            # Check box above
            if row > 0 and horizontal[row - 1, col] != 0 and vertical[row - 1, col] != 0 and \
                    vertical[row - 1, col + 1] != 0 and capture[row - 1, col] == 0:
                return True
            # Check box below
            if row < 4 and horizontal[row + 1, col] != 0 and vertical[row, col] != 0 and \
                    vertical[row, col + 1] != 0 and capture[row, col] == 0:
                return True
        else:  # direction == 'V'
            # Check box to the left
            if col > 0 and vertical[row, col - 1] != 0 and horizontal[row, col - 1] != 0 and \
                    horizontal[row + 1, col - 1] != 0 and capture[row, col - 1] == 0:
                return True
            # Check box to the right
            if col < 4 and vertical[row, col + 1] != 0 and horizontal[row, col] != 0 and \
                    horizontal[row + 1, col] != 0 and capture[row, col] == 0:
                return True
        return False

    def find_capture_move():
        """Finds a move that captures a box."""
        for row in range(5):
            for col in range(5):
                if horizontal[row, col] == 0 and check_capture(row, col, 'H'):
                    return f"{row},{col},H"
                if vertical[row, col] == 0 and check_capture(row, col, 'V'):
                    return f"{row},{col},V"
        return None

    def check_giveaway(row, col, direction):
        """Checks if a move gives away a box."""
        if direction == 'H':
            # Check box above
            if row > 0 and capture[row-1, col] == 0:
                sides = 0
                if horizontal[row - 1, col] != 0: sides += 1
                if vertical[row - 1, col] != 0: sides += 1
                if vertical[row - 1, col + 1] != 0: sides += 1
                if sides == 2: return True

            # Check box below
            if row < 4 and capture[row, col] == 0:
                sides = 0
                if horizontal[row + 1, col] != 0: sides += 1
                if vertical[row, col] != 0: sides += 1
                if vertical[row, col + 1] != 0: sides += 1
                if sides == 2: return True
        else:  # direction == 'V'
            # Check box to the left
            if col > 0 and capture[row, col-1] == 0:
                sides = 0
                if vertical[row, col - 1] != 0: sides += 1
                if horizontal[row, col - 1] != 0: sides += 1
                if horizontal[row + 1, col - 1] != 0: sides += 1
                if sides == 2: return True
            # Check box to the right
            if col < 4 and capture[row, col] == 0:
                sides = 0
                if vertical[row, col + 1] != 0: sides += 1
                if horizontal[row, col] != 0: sides += 1
                if horizontal[row + 1, col] != 0: sides += 1
                if sides == 2: return True
        return False

    def find_avoid_giveaway_move():
         """Finds a move that avoids giving away a box."""
         legal_moves = []
         for row in range(5):
             for col in range(5):
                 if horizontal[row, col] == 0 and not check_giveaway(row, col, 'H'):
                     legal_moves.append(f"{row},{col},H")
                 if vertical[row, col] == 0 and not check_giveaway(row, col, 'V'):
                     legal_moves.append(f"{row},{col},V")
         if legal_moves:
             return random.choice(legal_moves)
         return None

    def find_random_legal_move():
        """Finds a random legal move."""
        possible_moves = []
        for row in range(5):
            for col in range(5):
                if horizontal[row, col] == 0:
                    possible_moves.append(f"{row},{col},H")
                if vertical[row, col] == 0:
                    possible_moves.append(f"{row},{col},V")

        if possible_moves:
            return random.choice(possible_moves)
        else:
            return "0,0,H"  # Should not happen, but return a default legal move

    # 1. Capture
    capture_move = find_capture_move()
    if capture_move:
        return capture_move

    # 2. Avoid Giving Captures
    avoid_giveaway_move = find_avoid_giveaway_move()
    if avoid_giveaway_move:
        return avoid_giveaway_move

    # 3. Random Legal Move
    return find_random_legal_move()
