
def policy(piles: list[int]) -> str:
    """
    This policy implements a losing strategy for Nim.

    Args:
        piles: A list of 4 integers representing the number of objects in each pile.

    Returns:
        A string in the format 'pile,take' representing the move to make.
    """

    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]

    if all(p == 0 for p in piles):
      #if game is over then return the string we want from random policy
      return "0,1"

    if nim_sum == 0:
        # If nim_sum is already 0, make a random legal move
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
        # Should never happen, but just in case
        return "0,1" 

    else:
        # Try to make the nim_sum 0
        for i in range(4):
            target = piles[i] ^ nim_sum
            if target < piles[i]:
                take = piles[i] - target
                return f"{i},{take}"

        
        # Find a pile available for taking
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
        
        return "0,1" # should not happen
