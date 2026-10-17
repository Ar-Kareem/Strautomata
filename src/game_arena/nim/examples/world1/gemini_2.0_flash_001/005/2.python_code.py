
import random

def policy(piles: list[int]) -> str:
    """
    Chooses a move in the Nim game (4 piles) to play optimally.

    Args:
        piles: list[int] of length 4. Each entry is the number of objects
               remaining in that pile.

    Returns:
        A move as a string in the format 'pile,take', where pile is the
        0-based pile index and take is how many objects to remove from that
        pile.
    """

    xor_sum = 0
    for pile_size in piles:
        xor_sum ^= pile_size

    if xor_sum == 0:
        # Losing position: Make a random legal move
        possible_moves = []
        for i in range(4):
            if piles[i] > 0:
                possible_moves.append(i)

        if not possible_moves:
            return "0,1" #All piles are zero, return illegal move to ensure that at least the code returns. Will lose this game
                
        pile_index = random.choice(possible_moves)
        take = 1
        
        return f"{pile_index},{take}"
    else:
        # Winning position: Find a move to make the XOR sum zero
        for i in range(4):
            if piles[i] ^ xor_sum < piles[i]:
                take = piles[i] - (piles[i] ^ xor_sum)
                return f"{i},{take}"

        # Should not happen, but if it does, make a random move
        possible_moves = []
        for i in range(4):
            if piles[i] > 0:
                possible_moves.append(i)

        if not possible_moves:
            return "0,1"  #All piles are zero, return illegal move to ensure that at least the code returns. Will lose this game

        pile_index = random.choice(possible_moves)
        take = 1
        return f"{pile_index},{take}"
