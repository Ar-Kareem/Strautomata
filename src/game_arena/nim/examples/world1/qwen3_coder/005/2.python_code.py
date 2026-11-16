
def policy(piles: list[int]) -> str:
    # Calculate nim-sum
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    
    # Count piles greater than 1
    large_piles = sum(1 for p in piles if p > 1)
    
    # If there's more than one large pile, play normally
    if large_piles > 1:
        # Find a move that makes nim-sum 0
        for i in range(4):
            if piles[i] > 0:
                target = piles[i] ^ nim_sum
                if target < piles[i]:
                    take = piles[i] - target
                    if take > 0:
                        return f"{i},{take}"
        
        # Fallback: take 1 from first non-empty pile
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
    
    else:
        # Endgame strategy
        
        # Count total non-empty piles
        non_empty = sum(1 for p in piles if p > 0)
        
        # If all piles are size <= 1
        if large_piles == 0:
            # Take 1 from any pile of size 1 
            # Only if it leaves an even number of non-empty piles for opponent
            for i in range(4):
                if piles[i] == 1:
                    return f"{i},1"
            
            # If no pile of size 1, take 1 from any non-empty pile
            for i in range(4):
                if piles[i] > 0:
                    return f"{i},1"
        
        else:
            # Exactly one large pile
            # Count single items (piles of size 1)
            ones = sum(1 for p in piles if p == 1)
            
            # Find the large pile
            large_pile_idx = -1
            for i in range(4):
                if piles[i] > 1:
                    large_pile_idx = i
                    break
            
            # We want to leave an odd number of non-empty piles for the opponent
            # because in misere play, if all remaining piles are of size 1,
            # the player seeing an odd number of them will lose
            
            # This means we should leave an even number of 1-piles
            # plus considering the large pile
            
            if ones % 2 == 0:
                # Leave the large pile at 1 (if possible) otherwise 0
                if piles[large_pile_idx] > 1:
                    return f"{large_pile_idx},{piles[large_pile_idx] - 1}"
                else:
                    return f"{large_pile_idx},1"
            else:
                # Leave the large pile at 0 (take it completely)
                return f"{large_pile_idx},{piles[large_pile_idx]}"
                
    # Should never reach here but just in case
    for i in range(4):
        if piles[i] > 0:
            return f"{i},1"
