
import numpy as np
from typing import List, Tuple

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Directions: 'H' for horizontal, 'V' for vertical
    # Possible moves: all (row, col, dir) where the edge is empty (0)
    possible_moves = []

    # Generate all possible legal moves
    for row in range(5):
        for col in range(5):
            # Check horizontal edges (row, col) where col < 4 (since horizontal edges are between columns)
            if col < 4 and horizontal[row, col] == 0:
                possible_moves.append((row, col, 'H'))
            # Check vertical edges (row, col) where row < 4 (since vertical edges are between rows)
            if row < 4 and vertical[row, col] == 0:
                possible_moves.append((row, col, 'V'))

    # If no moves left (shouldn't happen in a valid game)
    if not possible_moves:
        return "0,0,H"  # fallback, though game should end before this

    # Evaluate each move
    def evaluate_move(move: Tuple[int, int, str]) -> int:
        row, col, dir = move
        # Simulate the move
        if dir == 'H':
            new_horizontal = horizontal.copy()
            new_horizontal[row, col] = 1
            new_capture = capture.copy()
            # Check if this move completes any boxes
            boxes_completed = check_box_completion(new_horizontal, vertical, new_capture)
            return boxes_completed
        else:  # 'V'
            new_vertical = vertical.copy()
            new_vertical[row, col] = 1
            new_capture = capture.copy()
            # Check if this move completes any boxes
            boxes_completed = check_box_completion(horizontal, new_vertical, new_capture)
            return boxes_completed

    def check_box_completion(horiz: np.ndarray, vert: np.ndarray, cap: np.ndarray) -> int:
        # Check all boxes (rows 0-3, cols 0-3)
        boxes_completed = 0
        for box_row in range(4):
            for box_col in range(4):
                # Check if the box is already captured
                if cap[box_row, box_col] != 0:
                    continue
                # Check if all four edges are drawn
                # Top edge: horizontal[box_row, box_col]
                # Right edge: vertical[box_row, box_col + 1]
                # Bottom edge: horizontal[box_row + 1, box_col]
                # Left edge: vertical[box_row + 1, box_col]
                top = horiz[box_row, box_col] != 0
                right = vert[box_row, box_col + 1] != 0
                bottom = horiz[box_row + 1, box_col] != 0
                left = vert[box_row + 1, box_col] != 0
                if top and right and bottom and left:
                    cap[box_row, box_col] = 1  # You capture the box
                    boxes_completed += 1
        return boxes_completed

    # Check for opponent's forced moves (they have 3 edges)
    def opponent_has_forced_move() -> List[Tuple[int, int, str]]:
        forced_moves = []
        for row in range(4):
            for col in range(4):
                # Check if opponent has 3 edges of this box
                top = horizontal[row, col] == -1
                right = vertical[row, col + 1] == -1
                bottom = horizontal[row + 1, col] == -1
                left = vertical[row + 1, col] == -1
                edges = [top, right, bottom, left]
                if edges.count(True) == 3:
                    # Find the missing edge
                    if not top and horizontal[row, col] == 0:
                        forced_moves.append((row, col, 'H'))
                    if not right and vertical[row, col + 1] == 0:
                        forced_moves.append((row, col + 1, 'V'))
                    if not bottom and horizontal[row + 1, col] == 0:
                        forced_moves.append((row + 1, col, 'H'))
                    if not left and vertical[row + 1, col] == 0:
                        forced_moves.append((row + 1, col, 'V'))
        return forced_moves

    # Check for your forced moves (you have 3 edges)
    def you_have_forced_move() -> List[Tuple[int, int, str]]:
        forced_moves = []
        for row in range(4):
            for col in range(4):
                # Check if you have 3 edges of this box
                top = horizontal[row, col] == 1
                right = vertical[row, col + 1] == 1
                bottom = horizontal[row + 1, col] == 1
                left = vertical[row + 1, col] == 1
                edges = [top, right, bottom, left]
                if edges.count(True) == 3:
                    # Find the missing edge
                    if not top and horizontal[row, col] == 0:
                        forced_moves.append((row, col, 'H'))
                    if not right and vertical[row, col + 1] == 0:
                        forced_moves.append((row, col + 1, 'V'))
                    if not bottom and horizontal[row + 1, col] == 0:
                        forced_moves.append((row + 1, col, 'H'))
                    if not left and vertical[row + 1, col] == 0:
                        forced_moves.append((row + 1, col, 'V'))
        return forced_moves

    # Check for opponent's potential to complete a box (they have 2 edges)
    def opponent_potential() -> List[Tuple[int, int, str]]:
        potential_moves = []
        for row in range(4):
            for col in range(4):
                # Check if opponent has 2 edges of this box
                top = horizontal[row, col] == -1
                right = vertical[row, col + 1] == -1
                bottom = horizontal[row + 1, col] == -1
                left = vertical[row + 1, col] == -1
                edges = [top, right, bottom, left]
                if edges.count(True) == 2:
                    # Find the missing edges
                    if not top and horizontal[row, col] == 0:
                        potential_moves.append((row, col, 'H'))
                    if not right and vertical[row, col + 1] == 0:
                        potential_moves.append((row, col + 1, 'V'))
                    if not bottom and horizontal[row + 1, col] == 0:
                        potential_moves.append((row + 1, col, 'H'))
                    if not left and vertical[row + 1, col] == 0:
                        potential_moves.append((row + 1, col, 'V'))
        return potential_moves

    # Check for your potential to complete a box (you have 2 edges)
    def you_potential() -> List[Tuple[int, int, str]]:
        potential_moves = []
        for row in range(4):
            for col in range(4):
                # Check if you have 2 edges of this box
                top = horizontal[row, col] == 1
                right = vertical[row, col + 1] == 1
                bottom = horizontal[row + 1, col] == 1
                left = vertical[row + 1, col] == 1
                edges = [top, right, bottom, left]
                if edges.count(True) == 2:
                    # Find the missing edges
                    if not top and horizontal[row, col] == 0:
                        potential_moves.append((row, col, 'H'))
                    if not right and vertical[row, col + 1] == 0:
                        potential_moves.append((row, col + 1, 'V'))
                    if not bottom and horizontal[row + 1, col] == 0:
                        potential_moves.append((row + 1, col, 'H'))
                    if not left and vertical[row + 1, col] == 0:
                        potential_moves.append((row + 1, col, 'V'))
        return potential_moves

    # Priority 1: Block opponent's forced moves
    opponent_forced = opponent_has_forced_move()
    if opponent_forced:
        # Choose the first forced move (arbitrary, but must block)
        return f"{opponent_forced[0][0]},{opponent_forced[0][1]},{opponent_forced[0][2]}"

    # Priority 2: Complete your forced moves
    your_forced = you_have_forced_move()
    if your_forced:
        # Choose the first forced move (arbitrary, but must complete)
        return f"{your_forced[0][0]},{your_forced[0][1]},{your_forced[0][2]}"

    # Priority 3: Block opponent's potential (they have 2 edges)
    opponent_pot = opponent_potential()
    if opponent_pot:
        # Choose the first potential move to block
        return f"{opponent_pot[0][0]},{opponent_pot[0][1]},{opponent_pot[0][2]}"

    # Priority 4: Complete your potential (you have 2 edges)
    your_pot = you_potential()
    if your_pot:
        # Evaluate which move completes the most boxes
        best_move = None
        best_score = -1
        for move in your_pot:
            score = evaluate_move(move)
            if score > best_score:
                best_score = score
                best_move = move
        if best_move:
            return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # Priority 5: Choose a move that doesn't create a forced move for opponent
    # Evaluate all moves and choose the one that doesn't leave opponent with 3 edges
    best_move = None
    best_score = -1
    for move in possible_moves:
        row, col, dir = move
        # Simulate the move
        if dir == 'H':
            new_horizontal = horizontal.copy()
            new_horizontal[row, col] = 1
            # Check if this move creates a forced move for opponent
            forced_after = opponent_has_forced_move()
            if not forced_after:
                score = 1  # Prefer moves that don't force opponent
            else:
                score = 0
        else:  # 'V'
            new_vertical = vertical.copy()
            new_vertical[row, col] = 1
            # Check if this move creates a forced move for opponent
            forced_after = opponent_has_forced_move()
            if not forced_after:
                score = 1
            else:
                score = 0
        if score > best_score:
            best_score = score
            best_move = move
    if best_move:
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # Fallback: Choose a random move (shouldn't reach here if game is valid)
    return f"{possible_moves[0][0]},{possible_moves[0][1]},{possible_moves[0][2]}"
