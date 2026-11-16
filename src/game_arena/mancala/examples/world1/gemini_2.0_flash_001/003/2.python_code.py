
import random

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Selects a move for the Kalah game.

    Args:
        you: Your houses and store.
        opponent: Opponent's houses and store.

    Returns:
        The index of the house to move from (0-5).
    """

    def simulate_move(move: int, current_you: list[int], current_opponent: list[int]) -> tuple[list[int], list[int]]:
        you_copy = current_you[:]
        opponent_copy = current_opponent[:]
        seeds = you_copy[move]
        you_copy[move] = 0
        index = move + 1
        while seeds > 0:
            if index == 6:
                you_copy[index] += 1
                seeds -= 1
                if seeds == 0:
                    return you_copy, opponent_copy, True, None # extra turn
            elif index > 6 + 5:
                index = 0
            elif index > 5:
                index = 0

                
            else:
                you_copy[index] += 1
                seeds -= 1

            index += 1

        index -=1

        if index < 6 and seeds == 0 and you_copy[index] == 1:
          index2 = 5-index
          if opponent_copy[index2] > 0:
            you_copy[6] += 1 + opponent_copy[index2]
            you_copy[index] = 0
            opponent_copy[index2] = 0
            return you_copy, opponent_copy, False, True # capture
        return you_copy, opponent_copy, False, False # default

        
    # Check for immediate captures
    for move in range(6):
        if you[move] > 0:
            you_copy, opponent_copy, extra_turn, capture = simulate_move(move, you, opponent)
            if capture:
                return move

    # If no captures available, try to get an extra turn
    for move in range(6):
        if you[move] > 0:
            you_copy, opponent_copy, extra_turn, capture = simulate_move(move, you, opponent)
            if extra_turn:
                return move

    # Choose a random legal move
    legal_moves = [i for i in range(6) if you[i] > 0]
    return random.choice(legal_moves)
