
import numpy as np
from typing import List, Tuple, Optional

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Directions: (row, col, dir) where dir is 'H' or 'V'
    # Possible moves: all (row, col, dir) where horizontal[row, col] == 0 or vertical[row, col] == 0
    legal_moves = []
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                legal_moves.append((row, col, 'H'))
            if vertical[row, col] == 0:
                legal_moves.append((row, col, 'V'))

    # Check for forced moves (completing a box)
    forced_moves = []
    for row in range(4):
        for col in range(4):
            # Check all 4 edges of the box (row, col)
            edges = [
                ('H', row, col),    # bottom edge
                ('H', row + 1, col), # top edge
                ('V', row, col),    # left edge
                ('V', row, col + 1) # right edge
            ]
            drawn_edges = 0
            for dir_, r, c in edges:
                if dir_ == 'H' and horizontal[r, c] != 0:
                    drawn_edges += 1
                elif dir_ == 'V' and vertical[r, c] != 0:
                    drawn_edges += 1
            if drawn_edges == 3:
                # Find which edge is missing
                for dir_, r, c in edges:
                    if dir_ == 'H' and horizontal[r, c] == 0:
                        forced_moves.append((r, c, 'H'))
                    elif dir_ == 'V' and vertical[r, c] == 0:
                        forced_moves.append((r, c, 'V'))

    # If forced moves exist, pick one (prioritize box completion)
    if forced_moves:
        return f"{forced_moves[0][0]},{forced_moves[0][1]},{forced_moves[0][2]}"

    # Block opponent forced moves (prevent them from completing boxes)
    opponent_forced_moves = []
    for row in range(4):
        for col in range(4):
            edges = [
                ('H', row, col),
                ('H', row + 1, col),
                ('V', row, col),
                ('V', row, col + 1)
            ]
            drawn_edges = 0
            for dir_, r, c in edges:
                if dir_ == 'H' and horizontal[r, c] == -1:
                    drawn_edges += 1
                elif dir_ == 'V' and vertical[r, c] == -1:
                    drawn_edges += 1
            if drawn_edges == 3:
                for dir_, r, c in edges:
                    if dir_ == 'H' and horizontal[r, c] == 0:
                        opponent_forced_moves.append((r, c, 'H'))
                    elif dir_ == 'V' and vertical[r, c] == 0:
                        opponent_forced_moves.append((r, c, 'V'))

    if opponent_forced_moves:
        return f"{opponent_forced_moves[0][0]},{opponent_forced_moves[0][1]},{opponent_forced_moves[0][2]}"

    # If no forced moves, use a heuristic to pick the best move
    # Heuristic: prefer edges that are part of multiple potential boxes
    # and avoid creating opponent forced moves
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        row, col, dir_ = move
        # Simulate the move
        if dir_ == 'H':
            new_horizontal = horizontal.copy()
            new_horizontal[row, col] = 1
            new_capture = capture.copy()
            # Check if this move completes any boxes
            boxes_completed = check_box_completion(new_horizontal, vertical, new_capture)
            score = len(boxes_completed)
        else:  # dir_ == 'V'
            new_vertical = vertical.copy()
            new_vertical[row, col] = 1
            new_capture = capture.copy()
            boxes_completed = check_box_completion(horizontal, new_vertical, new_capture)
            score = len(boxes_completed)

        # Penalize moves that create opponent forced moves
        if dir_ == 'H':
            opponent_forced = check_opponent_forced_moves(new_horizontal, vertical, new_capture)
        else:
            opponent_forced = check_opponent_forced_moves(horizontal, new_vertical, new_capture)
        score -= len(opponent_forced) * 2  # Strong penalty for creating opponent forced moves

        # Prefer edges in the center (higher score for central edges)
        center_score = (2 - abs(row - 2)) + (2 - abs(col - 2))
        score += center_score * 0.5

        if score > best_score:
            best_score = score
            best_move = move

    if best_move:
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # Fallback: random legal move
    return f"{legal_moves[0][0]},{legal_moves[0][1]},{legal_moves[0][2]}"

def check_box_completion(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> List[Tuple[int, int]]:
    completed_boxes = []
    for row in range(4):
        for col in range(4):
            # Check all 4 edges of the box (row, col)
            edges = [
                ('H', row, col),    # bottom edge
                ('H', row + 1, col), # top edge
                ('V', row, col),    # left edge
                ('V', row, col + 1) # right edge
            ]
            drawn_edges = 0
            for dir_, r, c in edges:
                if dir_ == 'H' and horizontal[r, c] != 0:
                    drawn_edges += 1
                elif dir_ == 'V' and vertical[r, c] != 0:
                    drawn_edges += 1
            if drawn_edges == 4 and capture[row, col] == 0:
                completed_boxes.append((row, col))
    return completed_boxes

def check_opponent_forced_moves(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> List[Tuple[int, int, str]]:
    forced_moves = []
    for row in range(4):
        for col in range(4):
            edges = [
                ('H', row, col),
                ('H', row + 1, col),
                ('V', row, col),
                ('V', row, col + 1)
            ]
            opponent_edges = 0
            for dir_, r, c in edges:
                if dir_ == 'H' and horizontal[r, c] == -1:
                    opponent_edges += 1
                elif dir_ == 'V' and vertical[r, c] == -1:
                    opponent_edges += 1
            if opponent_edges == 3:
                for dir_, r, c in edges:
                    if dir_ == 'H' and horizontal[r, c] == 0:
                        forced_moves.append((r, c, 'H'))
                    elif dir_ == 'V' and vertical[r, c] == 0:
                        forced_moves.append((r, c, 'V'))
    return forced_moves
