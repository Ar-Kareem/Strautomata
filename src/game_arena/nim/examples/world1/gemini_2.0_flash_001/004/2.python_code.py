
import random

def policy(piles: list[int]) -> str:
    """
    Chooses a move for Nim (4 piles) to play against other policies in an arena.

    The strategy is to compute the nim-sum of the piles.
    If the nim-sum is zero, then make a random legal move.
    If the nim-sum is non-zero, then find a pile such that taking objects from that
    pile will make the nim-sum zero. Take the appropriate number of objects from
    that pile.

    Args:
        piles: list[int] of length 4. Each entry is the number of objects remaining
            in that pile.

    Returns:
        A move as a string in the format 'pile,take' (both are integers,
        comma-separated, no extra text).
        pile is the 0-based pile index (0-3).
        take is how many objects to remove from that pile (must be >= 1).
    """

    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]

    if nim_sum == 0:
        # Make a random legal move
        while True:
            pile = random.randint(0, 3)
            if piles[pile] > 0:
                take = random.randint(1, piles[pile])
                return f'{pile},{take}'
    else:
        # Find a pile to take from to make the nim-sum zero
        for pile in range(4):
            target_size = piles[pile] ^ nim_sum
            if target_size >= 0 and target_size < piles[pile]:
                take = piles[pile] - target_size
                return f'{pile},{take}'
            elif target_size == 0 and piles[pile] > 0:
                take = 1
                return f'{pile},{take}'
            elif target_size < 0 and piles[pile] > 0:
                take = 1
                return f'{pile},{take}'
        
        # If no improving move found (should be impossible except due to rounding errors), make random legal move
        while True:
            pile = random.randint(0, 3)
            if piles[pile] > 0:
                take = random.randint(1, piles[pile])
                return f'{pile},{take}'
