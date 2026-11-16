
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    A Dots and Boxes policy that prioritizes captures and avoids giving the opponent free captures.
    """

    def is_legal_move(row: int, col: int, direction: str) -> bool:
        """Checks if a move is legal."""
        if direction == 'H':
            return horizontal[row, col] == 0
        elif direction == 'V':
            return vertical[row, col] == 0
        return False

    def get_capture_count(row: int, col: int, direction: str) -> int:
        """Determines how many boxes are captured by making a given move."""
        count = 0
        if direction == 'H':
            if row > 0 and horizontal[row - 1, col] != 0 and vertical[row - 1, col] != 0 and vertical[row - 1, col + 1] != 0 and capture[row-1, col] == 0:
                count += 1
            if row < 4 and horizontal[row + 1, col] != 0 and vertical[row, col] != 0 and vertical[row, col + 1] != 0 and capture[row, col] == 0:
                count += 1
        elif direction == 'V':
            if col > 0 and vertical[row, col - 1] != 0 and horizontal[row, col - 1] != 0 and horizontal[row + 1, col - 1] != 0 and capture[row, col-1] == 0:
                count += 1
            if col < 4 and vertical[row, col + 1] != 0 and horizontal[row, col] != 0 and horizontal[row + 1, col] != 0 and capture[row, col] == 0:
                count += 1
        return count

    def find_capturing_moves():
        """Finds all moves that result in immediate captures."""
        capturing_moves = []
        for row in range(5):
            for col in range(5):
                if is_legal_move(row, col, 'H') and get_capture_count(row, col, 'H') > 0:
                    capturing_moves.append((row, col, 'H'))
                if is_legal_move(row, col, 'V') and get_capture_count(row, col, 'V') > 0:
                    capturing_moves.append((row, col, 'V'))
        return capturing_moves

    def find_safe_moves():
        """Finds moves that do not create a 3-sided box for the opponent."""
        safe_moves = []
        for row in range(5):
            for col in range(5):
                if is_legal_move(row, col, 'H'):
                    # Check if this move would create a 3-sided box
                    temp_h = horizontal.copy()
                    temp_h[row, col] = 1
                    opponent_capture = 0
                    if row > 0 and temp_h[row - 1, col] != 0 and vertical[row - 1, col] != 0 and vertical[row - 1, col + 1] != 0 and capture[row-1, col] == 0:
                        opponent_capture += 1
                    if row < 4 and temp_h[row + 1, col] != 0 and vertical[row, col] != 0 and vertical[row, col + 1] != 0 and capture[row, col] == 0:
                        opponent_capture += 1
                    if opponent_capture == 0:
                        safe_moves.append((row, col, 'H'))

                if is_legal_move(row, col, 'V'):
                    # Check if this move would create a 3-sided box
                    temp_v = vertical.copy()
                    temp_v[row, col] = 1
                    opponent_capture = 0
                    if col > 0 and temp_v[row, col - 1] != 0 and horizontal[row, col - 1] != 0 and horizontal[row + 1, col - 1] != 0 and capture[row, col-1] == 0:
                        opponent_capture += 1
                    if col < 4 and temp_v[row, col + 1] != 0 and horizontal[row, col] != 0 and horizontal[row + 1, col] != 0 and capture[row, col] == 0:
                        opponent_capture += 1
                    if opponent_capture == 0:
                        safe_moves.append((row, col, 'V'))
        return safe_moves

    # 1. Try to make a capture
    capturing_moves = find_capturing_moves()
    if capturing_moves:
        return f'{capturing_moves[0][0]},{capturing_moves[0][1]},{capturing_moves[0][2]}'

    # 2. Try to avoid giving the opponent a free capture
    safe_moves = find_safe_moves()
    if safe_moves:
        return f'{safe_moves[0][0]},{safe_moves[0][1]},{safe_moves[0][2]}'

    # 3. If no safe moves, just make any legal move
    for row in range(5):
        for col in range(5):
            if is_legal_move(row, col, 'H'):
                return f'{row},{col},H'
            if is_legal_move(row, col, 'V'):
                return f'{row},{col},V'

    # Should not reach here if the board is not full
    return '0,0,H' # Return a default move if no other move is found. This should never happen during normal game play

