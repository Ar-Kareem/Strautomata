
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Selects the next move for Dots and Boxes on a 4x4 grid.

    Args:
        horizontal: 5x5 numpy array indicating horizontal edges.
        vertical: 5x5 numpy array indicating vertical edges.
        capture: 4x4 numpy array indicating box ownership.

    Returns:
        A string representing the next move in the format 'row,col,dir'.
    """

    def check_capture(row, col, direction):
        """Checks if a move captures a box."""
        if direction == 'H':
            if row > 0 and horizontal[row-1, col] == 0 and vertical[row-1, col] != 0 and vertical[row-1, col+1] != 0:
                if horizontal[row - 1, col] == 0 and vertical[row,col] != 0 and vertical[row, col+1] != 0:
                    return True
            if row < 4 and horizontal[row+1, col] == 0 and vertical[row, col] != 0 and vertical[row, col+1] != 0:
                if horizontal[row + 1, col] == 0 and vertical[row,col] != 0 and vertical[row, col+1] != 0:
                    return True

        elif direction == 'V':
            if col > 0 and vertical[row, col-1] == 0 and horizontal[row, col-1] != 0 and horizontal[row+1, col-1] != 0:
                if vertical[row,col-1] == 0 and horizontal[row, col] != 0 and horizontal[row+1, col] != 0:
                    return True

            if col < 4 and vertical[row, col+1] == 0 and horizontal[row, col] != 0 and horizontal[row+1, col] != 0:
                if vertical[row,col+1] == 0 and horizontal[row, col] != 0 and horizontal[row+1, col] != 0:
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

    def avoid_three_sides():
        """Avoid moves that create a box with three sides filled."""
        for row in range(5):
            for col in range(5):
                if horizontal[row, col] == 0:
                    # Check if placing horizontal edge at (row, col) creates 3-sided box
                    count = 0
                    if row > 0 and horizontal[row - 1, col] != 0:
                        count += 1
                    if row > 0 and vertical[row-1, col] != 0:
                        count += 1
                    if row > 0 and vertical[row-1, col+1] != 0:
                        count += 1

                    if count == 2:
                        continue
                    
                    count = 0
                    if row < 4 and horizontal[row + 1, col] != 0:
                        count +=1
                    if row < 4 and vertical[row, col] != 0:
                       count += 1
                    if row < 4 and vertical[row, col+1] != 0:
                        count += 1
                    if count == 2:
                        continue
                    
                    return f"{row},{col},H"

                if vertical[row, col] == 0:
                    # Check if placing vertical edge at (row, col) creates 3-sided box
                    count = 0
                    if col > 0 and vertical[row, col - 1] != 0:
                        count += 1
                    if col > 0 and horizontal[row, col-1] != 0:
                        count += 1
                    if col > 0 and horizontal[row+1, col-1] != 0:
                        count += 1

                    if count == 2:
                        continue

                    count = 0
                    if col < 4 and vertical[row, col + 1] != 0:
                        count += 1
                    if col < 4 and horizontal[row, col] != 0:
                        count += 1
                    if col < 4 and horizontal[row+1, col] != 0:
                        count += 1

                    if count == 2:
                        continue
                    return f"{row},{col},V"
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
        return None

    # 1. Try to capture a box
    capture_move = find_capture_move()
    if capture_move:
        return capture_move

    # 2. Avoid giving the opponent a free capture
    avoid_move = avoid_three_sides()
    if avoid_move:
        return avoid_move

    # 3. Play a random legal move
    random_move = find_random_legal_move()
    if random_move:
        return random_move

    #If we reach here, all edges are taken, which should not happen
    return "0,0,H" #Should never happen, but return a legal format string
