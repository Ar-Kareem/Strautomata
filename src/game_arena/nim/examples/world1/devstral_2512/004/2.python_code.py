
import random

def policy(piles: list[int]) -> str:
    # Calculate the Nim-sum (bitwise XOR of all pile sizes)
    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]

    # If Nim-sum is zero, we're in a losing position - make a random legal move
    if nim_sum == 0:
        # Find all possible moves
        possible_moves = []
        for i in range(4):
            for take in range(1, piles[i] + 1):
                possible_moves.append((i, take))

        # Choose a random move
        if possible_moves:
            pile, take = random.choice(possible_moves)
            return f"{pile},{take}"
        else:
            # This should never happen as the game would be over
            return "0,1"

    # If Nim-sum is non-zero, find a move that makes it zero
    for i in range(4):
        # Calculate what the pile should be to make Nim-sum zero
        target = piles[i] ^ nim_sum

        # If this is smaller than current pile, we can take from it
        if target < piles[i]:
            take = piles[i] - target
            return f"{i},{take}"

    # Fallback (should never reach here if input is valid)
    return "0,1"
