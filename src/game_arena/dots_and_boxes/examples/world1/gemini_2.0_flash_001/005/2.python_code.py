
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    A Dots and Boxes policy for a 4x4 grid.
    """

    def is_legal_move(row: int, col: int, direction: str, horizontal: np.ndarray, vertical: np.ndarray) -> bool:
        """
        Checks if a move is legal.
        """
        if direction == 'H':
            return horizontal[row, col] == 0
        elif direction == 'V':
            return vertical[row, col] == 0
        return False

    def check_capture(row: int, col: int, horizontal: np.ndarray, vertical: np.ndarray) -> int:
        """
        Checks if a box is captured by playing a move.
        Returns 1 if captured, 0 otherwise.
        """
        if row < 0 or row >= 4 or col < 0 or col >= 4:
            return 0

        h_top = horizontal[row, col] != 0
        h_bottom = horizontal[row + 1, col] != 0
        v_left = vertical[row, col] != 0
        v_right = vertical[row, col + 1] != 0

        if h_top and h_bottom and v_left and v_right:
            return 1
        return 0

    def find_capturing_moves(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> list:
        """
        Finds moves that result in capturing one or more boxes.
        """
        capturing_moves = []
        for row in range(5):
            for col in range(5):
                if is_legal_move(row, col, 'H', horizontal, vertical):
                    temp_horizontal = horizontal.copy()
                    temp_horizontal[row, col] = 1
                    captured_boxes = check_capture(row-1, col-1, temp_horizontal, vertical) + check_capture(row, col-1, temp_horizontal, vertical)
                    if captured_boxes > 0:
                        capturing_moves.append((row, col, 'H'))
                if is_legal_move(row, col, 'V', horizontal, vertical):
                    temp_vertical = vertical.copy()
                    temp_vertical[row, col] = 1
                    captured_boxes = check_capture(row-1, col-1, horizontal, temp_vertical) + check_capture(row-1, col, horizontal, temp_vertical)
                    if captured_boxes > 0:
                        capturing_moves.append((row, col, 'V'))
        return capturing_moves

    def find_giving_moves(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> list:
        """
        Finds moves that would complete a box for the opponent.
        """
        giving_moves = []
        for row in range(5):
            for col in range(5):
                if is_legal_move(row, col, 'H', horizontal, vertical):
                    temp_horizontal = horizontal.copy()
                    temp_horizontal[row, col] = 1
                    if check_almost_capture(row-1, col-1, temp_horizontal, vertical) or check_almost_capture(row, col-1, temp_horizontal, vertical):
                        giving_moves.append((row, col, 'H'))
                if is_legal_move(row, col, 'V', horizontal, vertical):
                    temp_vertical = vertical.copy()
                    temp_vertical[row, col] = 1
                    if check_almost_capture(row-1, col-1, horizontal, temp_vertical) or check_almost_capture(row-1, col, horizontal, temp_vertical):
                        giving_moves.append((row, col, 'V'))
        return giving_moves

    def check_almost_capture(row: int, col: int, horizontal: np.ndarray, vertical: np.ndarray) -> bool:
        """
        Checks if a box has 3 sides already filled.
        """
        if row < 0 or row >= 4 or col < 0 or col >= 4:
            return False

        h_top = horizontal[row, col] != 0
        h_bottom = horizontal[row + 1, col] != 0
        v_left = vertical[row, col] != 0
        v_right = vertical[row, col + 1] != 0

        filled_sides = sum([h_top, h_bottom, v_left, v_right])
        return filled_sides == 3

    def find_adjacent_captures(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> list:
        """
        Finds moves adjacent to already captured boxes.
        """
        adjacent_moves = []
        captured_boxes = np.where(capture != 0)
        for row, col in zip(captured_boxes[0], captured_boxes[1]):
            for r, c, d in [(row, col, 'H'), (row+1, col, 'H'), (row, col, 'V'), (row, col+1, 'V')]:
                if 0 <= r < 5 and 0 <= c < 5:
                    if is_legal_move(r, c, d, horizontal, vertical):
                         adjacent_moves.append((r, c, d))
        return adjacent_moves

    # 1. Capture if possible
    capturing_moves = find_capturing_moves(horizontal, vertical, capture)
    if capturing_moves:
        row, col, direction = random.choice(capturing_moves)
        return f"{row},{col},{direction}"

    # 2. Avoid giving captures
    giving_moves = find_giving_moves(horizontal, vertical, capture)
    legal_moves = []
    for row in range(5):
        for col in range(5):
            if is_legal_move(row, col, 'H', horizontal, vertical):
                legal_moves.append((row, col, 'H'))
            if is_legal_move(row, col, 'V', horizontal, vertical):
                legal_moves.append((row, col, 'V'))

    safe_moves = [move for move in legal_moves if move not in giving_moves]
    if safe_moves:
        row, col, direction = random.choice(safe_moves)
        return f"{row},{col},{direction}"
    
    #3. priorize moves adjecent to existing captures
    adjacent_capture_moves = find_adjacent_captures(horizontal, vertical, capture)
    if adjacent_capture_moves:
        row, col, direction = random.choice(adjacent_capture_moves)
        return f"{row},{col},{direction}"

    # 4. Random Legal Move
    if legal_moves:
        row, col, direction = random.choice(legal_moves)
        return f"{row},{col},{direction}"

    # Should never happen, but return a default legal move if all else fails
    return "0,0,H"
