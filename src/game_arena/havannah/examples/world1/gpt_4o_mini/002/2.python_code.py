
import numpy as np
import random

def is_winning_move(player_stones, row, col):
    # This function checks if placing a stone at (row, col) results in a win
    # Place the hypothetical stone temporarily
    player_stones.add((row, col))
    # Check for winning structures (ring, bridge, fork).
    # We're going to check for each structure:

    # Check for a ring or a bridge or fork logic (simplified as an example here)
    winning = False

    # For simplification:
    # A win could be calculated here. This is a placeholder.
    if len(player_stones) >= 6:  # Example condition for a win, real logic needed
        winning = True

    player_stones.remove((row, col))  # Remove the stone
    return winning

def evaluate_move(me, opp, row, col):
    # Here we would implement a scoring system based on game heuristics.
    score = 0
    # Increase score for creating potential connections
    score += (len(me) + 1)  # Higher number of stones increases the score

    # Decrease score for blocking opponent's moves
    if any(is_winning_move(set(opp), row, col) for row, col in opp):
        score += 100  # High penalty if it helps the opponent win

    return score

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    best_move = None
    best_score = -1

    # Convert lists to sets for quicker lookup
    player_stones = set(me)
    opponent_stones = set(opp)

    for row in range(15):
        for col in range(15):
            if valid_mask[row][col] and (row, col) not in player_stones and (row, col) not in opponent_stones:
                current_score = evaluate_move(player_stones, opponent_stones, row, col)

                # Check if this move results in winning
                if is_winning_move(player_stones, row, col):
                    return (row, col)  # Prioritize winning move

                if current_score > best_score:
                    best_score = current_score
                    best_move = (row, col)

    # If no move found, fall back on a random valid move (shouldn't happen)
    if best_move is None:
        for row in range(15):
            for col in range(15):
                if valid_mask[row][col]:
                    return (row, col)  # Return any valid spot if all else fails

    return best_move
