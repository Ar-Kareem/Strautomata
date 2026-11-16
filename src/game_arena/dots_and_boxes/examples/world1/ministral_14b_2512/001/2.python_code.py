
import numpy as np
from typing import List, Tuple

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Directions: 'H' for horizontal, 'V' for vertical
    # Possible moves: all (row, col, dir) where the edge is 0
    possible_moves = []

    # Generate all possible legal moves
    for row in range(5):
        for col in range(5):
            # Check horizontal edges (row, col) where col < 4 (since edges are between dots)
            if col < 4 and horizontal[row, col] == 0:
                possible_moves.append((row, col, 'H'))
            # Check vertical edges (row, col) where row < 4
            if row < 4 and vertical[row, col] == 0:
                possible_moves.append((row, col, 'V'))

    if not possible_moves:
        raise ValueError("No legal moves available (game should be over)")

    # Evaluate each move
    def evaluate_move(move: Tuple[int, int, str]) -> int:
        row, col, dir = move
        # Simulate the move
        if dir == 'H':
            new_horizontal = horizontal.copy()
            new_horizontal[row, col] = 1
            new_capture = capture.copy()
        else:  # 'V'
            new_vertical = vertical.copy()
            new_vertical[row, col] = 1
            new_capture = capture.copy()

        # Check if the move completes any boxes
        boxes_captured = 0
        if dir == 'H':
            # Check the box to the right (row, col+1)
            if col + 1 < 4:
                box_row, box_col = row, col
                if (new_horizontal[box_row, box_col] == 1 and
                    new_vertical[box_row, box_col] == 1 and
                    new_vertical[box_row, box_col + 1] == 1):
                    new_capture[box_row, box_col] = 1
                    boxes_captured += 1
            # Check the box to the left (row, col-1) if col > 0
            if col > 0:
                box_row, box_col = row, col - 1
                if (new_horizontal[box_row, box_col] == 1 and
                    new_vertical[box_row, box_col] == 1 and
                    new_vertical[box_row, box_col + 1] == 1):
                    new_capture[box_row, box_col] = 1
                    boxes_captured += 1
        else:  # 'V'
            # Check the box below (row+1, col)
            if row + 1 < 4:
                box_row, box_col = row + 1, col
                if (new_vertical[box_row - 1, box_col] == 1 and
                    new_horizontal[box_row, box_col] == 1 and
                    new_horizontal[box_row, box_col - 1] == 1):
                    new_capture[box_row, box_col] = 1
                    boxes_captured += 1
            # Check the box above (row-1, col) if row > 0
            if row > 0:
                box_row, box_col = row, col
                if (new_vertical[box_row - 1, box_col] == 1 and
                    new_horizontal[box_row, box_col] == 1 and
                    new_horizontal[box_row, box_col - 1] == 1):
                    new_capture[box_row, box_col] = 1
                    boxes_captured += 1

        # If no boxes are captured, check for threats (opponent can capture)
        if boxes_captured == 0:
            # Check if the move creates a threat (3 edges of a box)
            threats_created = 0
            if dir == 'H':
                # Check right box
                if col + 1 < 4:
                    box_row, box_col = row, col
                    edges = [
                        new_horizontal[box_row, box_col],
                        new_vertical[box_row, box_col],
                        new_vertical[box_row, box_col + 1]
                    ]
                    if sum(edges) == 3:
                        threats_created += 1
                # Check left box
                if col > 0:
                    box_row, box_col = row, col - 1
                    edges = [
                        new_horizontal[box_row, box_col],
                        new_vertical[box_row, box_col],
                        new_vertical[box_row, box_col + 1]
                    ]
                    if sum(edges) == 3:
                        threats_created += 1
            else:  # 'V'
                # Check bottom box
                if row + 1 < 4:
                    box_row, box_col = row + 1, col
                    edges = [
                        new_vertical[box_row - 1, box_col],
                        new_horizontal[box_row, box_col],
                        new_horizontal[box_row, box_col - 1]
                    ]
                    if sum(edges) == 3:
                        threats_created += 1
                # Check top box
                if row > 0:
                    box_row, box_col = row, col
                    edges = [
                        new_vertical[box_row - 1, box_col],
                        new_horizontal[box_row, box_col],
                        new_horizontal[box_row, box_col - 1]
                    ]
                    if sum(edges) == 3:
                        threats_created += 1
            # Score is negative if threats are created (opponent can capture)
            return -threats_created
        else:
            return boxes_captured

    # Evaluate all moves and pick the best one
    best_score = -float('inf')
    best_move = None

    for move in possible_moves:
        score = evaluate_move(move)
        if score > best_score:
            best_score = score
            best_move = move
        elif score == best_score:
            # Prefer moves that don't create threats for the opponent
            threats = evaluate_move(move)
            if threats < 0:
                best_move = move

    # If no move captures boxes or creates threats, pick a random move
    if best_move is None:
        best_move = np.random.choice(possible_moves)

    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
