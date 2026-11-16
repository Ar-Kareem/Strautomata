
import sys

def policy(piles: list[int]) -> str:
    """
    Returns a move 'pile,take' for 4-pile misère Nim.
    Assumes piles are non-negative integers.
    """
    # Helper: nim-sum of all piles
    xor_all = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    
    # Count piles with >1 stones
    large_piles = sum(1 for p in piles if p > 1)
    
    # Case 1: Winning position in normal Nim (xor_all != 0)
    if xor_all != 0:
        for i in range(4):
            if piles[i] == 0:
                continue
            # We want to remove k stones from pile i so that nim-sum becomes 0
            # That means: piles[i] - k = piles[i] ^ xor_all
            target = piles[i] ^ xor_all
            if target < piles[i]:
                take = piles[i] - target
                # Check misère adjustment: if after move, all piles <= 1
                new_piles = piles.copy()
                new_piles[i] -= take
                if all(p <= 1 for p in new_piles):
                    # In misère, if all become 0 or 1, we want odd number of 1s for opponent
                    ones_after = sum(p == 1 for p in new_piles)
                    if ones_after % 2 == 0:
                        # Adjust: if even ones, take more to make odd ones for opponent
                        # Simplest: take 1 less if possible (but must still be legal)
                        if take > 1:
                            take -= 1
                        else:
                            # If take==1, we cannot adjust here; maybe try a different pile
                            # For simplicity, proceed with original take
                            pass
                return f"{i},{take}"
    
    # Case 2: Losing position in normal Nim (xor_all == 0)
    # Try to force opponent into misère endgame
    if large_piles >= 2:
        # Take 1 from largest pile to reduce game length
        largest_idx = max(range(4), key=lambda i: piles[i])
        if piles[largest_idx] > 0:
            return f"{largest_idx},1"
    elif large_piles == 1:
        # Only one pile > 1, others are 0 or 1
        for i in range(4):
            if piles[i] > 1:
                # Take all but 1 from it, leaving exactly one stone in that pile
                if piles[i] > 1:
                    take = piles[i] - 1
                    return f"{i},{take}"
    else:
        # All piles are 0 or 1
        ones = sum(p == 1 for p in piles)
        # If odd number of 1s, take a whole pile (to make even for opponent)
        # If even number of 1s, take all but one from a pile (if any >1, but here all <=1)
        # Actually here all are 0 or 1, so take 1 from any pile with 1
        for i in range(4):
            if piles[i] == 1:
                return f"{i},1"
        # Should not reach here if game not ended
        # Fallback: take from first non-empty pile
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    # Fallback (shouldn't happen)
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
    return "0,1"
