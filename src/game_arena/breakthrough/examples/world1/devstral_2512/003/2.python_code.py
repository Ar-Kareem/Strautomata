
import random
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Determine direction based on color
    direction = 1 if color == 'w' else -1
    home_row = 7 if color == 'w' else 0

    # Convert positions to sets for faster lookup
    my_positions = set(me)
    opp_positions = set(opp)

    # Generate all possible moves
    moves = []
    captures = []

    for (r, c) in me:
        # Check forward move
        new_r = r + direction
        if 0 <= new_r < 8:
            # Straight forward
            if (new_r, c) not in my_positions and (new_r, c) not in opp_positions:
                moves.append(((r, c), (new_r, c)))

            # Diagonal left
            new_c = c - 1
            if 0 <= new_c < 8:
                if (new_r, new_c) in opp_positions:
                    captures.append(((r, c), (new_r, new_c)))
                elif (new_r, new_c) not in my_positions:
                    moves.append(((r, c), (new_r, new_c)))

            # Diagonal right
            new_c = c + 1
            if 0 <= new_c < 8:
                if (new_r, new_c) in opp_positions:
                    captures.append(((r, c), (new_r, new_c)))
                elif (new_r, new_c) not in my_positions:
                    moves.append(((r, c), (new_r, new_c)))

    # Check for immediate win moves (reaching opponent's home row)
    win_moves = [move for move in moves + captures if move[1][0] == home_row]
    if win_moves:
        return random.choice(win_moves)

    # Prefer captures over regular moves
    if captures:
        # Evaluate captures based on piece safety and position
        def evaluate_capture(move):
            from_pos, to_pos = move
            # Check if the capturing piece is safe (not easily captured next turn)
            safe = True
            for dr, dc in [(-direction, -1), (-direction, 1)]:
                check_r, check_c = to_pos[0] + dr, to_pos[1] + dc
                if 0 <= check_r < 8 and 0 <= check_c < 8:
                    if (check_r, check_c) in opp_positions:
                        safe = False
                        break
            # Prefer captures that are safe and move toward center
            center_distance = abs(to_pos[1] - 3.5)
            return (safe, -center_distance, random.random())

        captures.sort(key=evaluate_capture, reverse=True)
        return captures[0]

    # Evaluate regular moves
    if moves:
        def evaluate_move(move):
            from_pos, to_pos = move
            # Prefer moves that advance toward opponent's home row
            progress = abs(to_pos[0] - home_row)
            # Prefer moves toward center
            center_distance = abs(to_pos[1] - 3.5)
            # Check if the piece is safe after moving
            safe = True
            for dr, dc in [(-direction, -1), (-direction, 1)]:
                check_r, check_c = to_pos[0] + dr, to_pos[1] + dc
                if 0 <= check_r < 8 and 0 <= check_c < 8:
                    if (check_r, check_c) in opp_positions:
                        safe = False
                        break
            return (-progress, -center_distance, safe, random.random())

        moves.sort(key=evaluate_move)
        return moves[0]

    # If no moves available (shouldn't happen in valid game state)
    # Return a random legal move from the original position
    return random.choice(me), random.choice(me)
