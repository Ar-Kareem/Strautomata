
import random

def policy(piles: list[int]) -> str:
    # Calculate the Nim-sum (bitwise XOR of all pile sizes)
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile

    # If Nim-sum is zero, make a random legal move
    if nim_sum == 0:
        # Find all possible moves
        possible_moves = []
        for i in range(4):
            for take in range(1, piles[i] + 1):
                possible_moves.append((i, take))
        # Choose a random move
        pile, take = random.choice(possible_moves)
        return f"{pile},{take}"

    # If Nim-sum is non-zero, find the optimal move
    for i in range(4):
        # Calculate the target size for this pile to make Nim-sum zero
        target = piles[i] ^ nim_sum
        if target < piles[i]:
            take = piles[i] - target
            return f"{i},{take}"

    # Fallback: if no optimal move found (should not happen), make a random move
    possible_moves = []
    for i in range(4):
        for take in range(1, piles[i] + 1):
            possible_moves.append((i, take))
    pile, take = random.choice(possible_moves)
    return f"{pile},{take}"
