
import math
from typing import List

def terminal_state(you: List[int], opponent: List[int]) -> bool:
    # Check if either player has no seeds in their houses (0..5)
    return (all(h == 0 for h in you[0:6]) or all(h == 0 for h in opponent[0:6]))

def final_score(you: List[int], opponent: List[int]) -> int:
    # Computes the final score from our perspective in a terminal state.
    if all(h == 0 for h in you[0:6]) and all(h == 0 for h in opponent[0:6]):
        # Both players have no seeds in houses: return difference in stores
        return you[6] - opponent[6]
    elif all(h == 0 for h in opponent[0:6]):
        # Opponent has no seeds in houses: we collect our remaining houses
        return (you[6] + sum(you[0:6])) - opponent[6]
    else:  # You have no seeds in houses
        return you[6] - (opponent[6] + sum(opponent[0:6]))

def simulate_move(you: List[int], opponent: List[int], index: int) -> (List[int], List[int], bool):
    # Returns the new state after making the move and whether an extra move is granted.
    if you[index] == 0:
        # Should not happen, but return as if no move and no extra move.
        return you, opponent, False

    # Make copies to avoid mutating the original state.
    you_copy = you[:]
    opponent_copy = opponent[:]
    seeds = you_copy[index]
    you_copy[index] = 0  # Remove seeds from the chosen house

    # Save the state of our houses before the drop (for capture condition)
    you_houses_before = you[:6]  # The original state of our houses

    current = (index + 1) % 14  # 14 positions: 0-5 (our houses), 6 (our store), 7-12 (opponent houses), 13 (skip)
    positions = []
    while seeds > 0:
        if current == 13:  # Skip opponent's store
            current = 0
        else:
            positions.append(current)
            seeds -= 1
            current = (current + 1) % 14

    extra_move = False
    if positions:
        last_pos = positions[-1]
        # Update the state for each position in the list.
        for i, pos in enumerate(positions):
            if pos < 7:  # In our side (you_copy)
                if pos == 6:  # Our store
                    you_copy[6] += 1
                else:
                    # Update the house
                    you_copy[pos] += 1
                    # Check if this is the last seed and capture condition
                    if i == len(positions) - 1 and you_houses_before[pos] == 0:
                        # Capture condition: last seed in an empty house of ours, and opposite opponent house has seeds.
                        captured = opponent_copy[5 - pos]
                        if captured > 0:
                            # Capture: move to our store and clear both houses.
                            you_copy[6] += captured + 1  # +1 for the seed just dropped
                            you_copy[pos] = 0
                            opponent_copy[5 - pos] = 0
                        else:
                            # Only the last seed remains in the house
                            you_copy[pos] = 1
            else:  # In opponent's side (opponent_copy)
                idx = pos - 7
                opponent_copy[idx] += 1

        # Check for extra move: if the last seed landed in our store
        extra_move = (last_pos == 6)
    else:
        extra_move = False

    return you_copy, opponent_copy, extra_move

def minimax(you: List[int], opponent: List[int], depth: int, player: int, alpha: float, beta: float) -> int:
    # player: 1 for current player (us), -1 for opponent.
    if depth == 0:
        return (you[6] - opponent[6]) * player

    # Check for terminal state
    if terminal_state(you, opponent):
        return final_score(you, opponent) * player

    if player == 1:  # Our turn (maximizing)
        moves = [i for i in range(6) if you[i] > 0]
        best = -math.inf
        for i in moves:
            new_you, new_opponent, extra_move = simulate_move(you, opponent, i)
            if extra_move:
                value = minimax(new_you, new_opponent, depth - 1, player, alpha, beta)
            else:
                value = minimax(new_you, new_opponent, depth - 1, -player, alpha, beta)
            if value > best:
                best = value
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
        return best
    else:  # Opponent's turn (minimizing)
        moves = [i for i in range(6) if opponent[i] > 0]
        best = math.inf
        for i in moves:
            # Simulate opponent's move: they are the current player, so we pass (opponent, you)
            new_opponent, new_you, extra_move = simulate_move(opponent, you, i)
            if extra_move:
                value = minimax(new_you, new_opponent, depth - 1, player, alpha, beta)
            else:
                value = minimax(new_you, new_opponent, depth - 1, -player, alpha, beta)
            if value < best:
                best = value
                beta = min(beta, value)
                if beta <= alpha:
                    break
        return best

def policy(you: List[int], opponent: List[int]) -> int:
    depth = 4
    moves = [i for i in range(6) if you[i] > 0]
    best_move = None
    best_value = -math.inf
    for i in moves:
        new_you, new_opponent, extra_move = simulate_move(you, opponent, i)
        if extra_move:
            value = minimax(new_you, new_opponent, depth - 1, 1, -math.inf, math.inf)
        else:
            value = minimax(new_you, new_opponent, depth - 1, -1, -math.inf, math.inf)
        if value > best_value:
            best_value = value
            best_move = i
    return best_move
