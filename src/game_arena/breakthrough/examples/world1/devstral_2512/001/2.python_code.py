
import random
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Determine direction based on color
    direction = 1 if color == 'w' else -1
    home_row = 7 if color == 'w' else 0
    opponent_home_row = 0 if color == 'w' else 7

    # Convert positions to sets for faster lookup
    my_positions = set(me)
    opp_positions = set(opp)

    # Check for immediate winning moves
    for (r, c) in me:
        # Check forward move to opponent's home row
        new_r = r + direction
        if new_r == opponent_home_row:
            if (new_r, c) not in my_positions and (new_r, c) not in opp_positions:
                return ((r, c), (new_r, c))

        # Check diagonal moves to opponent's home row
        for dc in [-1, 1]:
            new_c = c + dc
            if 0 <= new_c < 8:
                new_r = r + direction
                if new_r == opponent_home_row:
                    if (new_r, new_c) not in my_positions and (new_r, new_c) not in opp_positions:
                        return ((r, c), (new_r, new_c))

    # Generate all possible moves with scores
    moves = []

    for (r, c) in me:
        # Forward move
        new_r = r + direction
        if 0 <= new_r < 8:
            if (new_r, c) not in my_positions and (new_r, c) not in opp_positions:
                # Score based on how close we get to opponent's home row
                score = 10 * (7 - abs(new_r - opponent_home_row))
                # Bonus for center control
                score += 5 * (3 - abs(new_c - 3.5))
                moves.append((score, ((r, c), (new_r, c))))

        # Diagonal moves (both capture and non-capture)
        for dc in [-1, 1]:
            new_c = c + dc
            new_r = r + direction
            if 0 <= new_r < 8 and 0 <= new_c < 8:
                if (new_r, new_c) in opp_positions:
                    # Capture move - higher priority
                    score = 50  # Base score for capture
                    # Bonus for capturing advanced pieces
                    score += 10 * (abs(new_r - home_row))
                    # Bonus for center control
                    score += 5 * (3 - abs(new_c - 3.5))
                    moves.append((score, ((r, c), (new_r, new_c))))
                elif (new_r, new_c) not in my_positions:
                    # Regular diagonal move
                    score = 8 * (7 - abs(new_r - opponent_home_row))
                    score += 5 * (3 - abs(new_c - 3.5))
                    moves.append((score, ((r, c), (new_r, new_c))))

    # If no moves found (shouldn't happen in valid game), return a random legal move
    if not moves:
        # Find all possible moves (including captures)
        for (r, c) in me:
            # Forward move
            new_r = r + direction
            if 0 <= new_r < 8:
                if (new_r, c) not in my_positions and (new_r, c) not in opp_positions:
                    return ((r, c), (new_r, c))

            # Diagonal moves
            for dc in [-1, 1]:
                new_c = c + dc
                new_r = r + direction
                if 0 <= new_r < 8 and 0 <= new_c < 8:
                    if (new_r, new_c) in opp_positions or (new_r, new_c) not in my_positions:
                        return ((r, c), (new_r, new_c))

        # If still no moves, return first piece's forward move (shouldn't happen)
        r, c = me[0]
        new_r = r + direction
        return ((r, c), (new_r, c))

    # Sort moves by score and return the highest scoring one
    moves.sort(reverse=True, key=lambda x: x[0])
    return moves[0][1]
