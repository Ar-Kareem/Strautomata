
import random
from functools import lru_cache

def policy(piles: list[int]) -> str:
    # Try to find a winning move using Nim-sum
    # For Misère Nim (last to move loses) with 4 piles, 
    # the strategy is similar to normal Nim but with special handling
    # when the game is in a "danger zone" (few objects left).
    
    # First, check if we are in a position where we can force a win
    # by leaving the opponent with exactly one stone in total
    total_stones = sum(piles)
    
    # If there are only 2 stones left total, we must leave exactly 1 for the opponent
    if total_stones == 2:
        # Find a pile with 2 stones and take 1
        for i, p in enumerate(piles):
            if p == 2:
                return f"{i},1"
    
    # If there's exactly 1 stone left total, we're forced to take it and lose
    # But this shouldn't happen if we play optimally
    if total_stones == 1:
        # Just take the last stone
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
    
    # Calculate Nim-sum
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # If nim_sum is 0, we're in a losing position (assuming perfect play from opponent)
    # In this case, we should make a random move
    if nim_sum == 0:
        # Find a non-empty pile and take a random number of stones
        non_empty_piles = [i for i, p in enumerate(piles) if p > 0]
        if non_empty_piles:
            pile = random.choice(non_empty_piles)
            take = random.randint(1, piles[pile])
            return f"{pile},{take}"
    
    # If nim_sum is not 0, we can make a winning move
    # Find a pile where we can reduce it to make the new nim_sum 0
    for i, p in enumerate(piles):
        if p ^ nim_sum < p:
            # This move will make the nim_sum 0
            return f"{i},{p - (p ^ nim_sum)}"
    
    # Fallback: just take 1 from the first non-empty pile
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
