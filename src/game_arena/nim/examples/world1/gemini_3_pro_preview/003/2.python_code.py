
def policy(piles: list[int]) -> str:
    # Calculate the Nim-sum (XOR sum) of all piles
    nim_sum = 0
    for p in piles:
        nim_sum ^= p

    # Identify indices of piles with more than 1 item
    large_piles = [i for i, p in enumerate(piles) if p > 1]
    
    # Identify indices of all non-empty piles
    active_piles = [i for i, p in enumerate(piles) if p > 0]

    # --- CASE 1: Endgame Scenario ---
    # If all piles are size 0 or 1, we are in the endgame.
    # In Misere play, we want to leave an ODD number of 1s.
    if not large_piles:
        # Since we must move, we take 1 from any available pile (turning a 1 into a 0).
        # We cannot choose parity here; it's forced by the previous move.
        # We simply execute the only valid move.
        if active_piles:
            return f"{active_piles[0]},1"
        return "0,0" # Should effectively never happen for player moving

    # --- CASE 2: Mid-game Strategy ---
    # If there is at least one pile > 1, we generally play Normal Nim (Target S=0).
    # However, we must watch out for the transition to the Endgame.
    
    if nim_sum != 0:
        for i in active_piles:
            p = piles[i]
            target = p ^ nim_sum
            
            # The move is valid if we reduce the pile size
            if target < p:
                # Check if this move forces the game into the Endgame (all piles <= 1)
                
                # Check remaining 'large' piles excluding current one
                # If 'p' was the only large pile, and 'target' <= 1, then we are entering endgame.
                is_endgame_transition = False
                
                # Logic: If this pile is in large_piles, are there others?
                if p > 1:
                    if len(large_piles) == 1 and target <= 1:
                        is_endgame_transition = True
                # Note: if p=1, it's not a large pile, and reducing it to 0 won't eliminate other large piles.
                # Since we are in Case 2, we know len(large_piles) >= 1.
                
                if is_endgame_transition:
                    # We need to ensure the count of 1s left is ODD.
                    
                    # Count 1s in OTHER piles
                    ones_count = sum(1 for j, x in enumerate(piles) if j != i and x == 1)
                    
                    # Add result of current pile
                    if target == 1:
                        ones_count += 1
                        
                    # If total ones is Even, we must flip our target (0 vs 1) to make it Odd.
                    if ones_count % 2 == 0:
                        target = 1 if target == 0 else 0
                
                # Calculate amount to take
                take = p - target
                return f"{i},{take}"

    # --- CASE 3: Losing Position ---
    # If nim_sum is 0, we can't force a win. Play defensively.
    # Taking 1 from a large pile is a standard heuristic to complicate play.
    if large_piles:
        return f"{large_piles[0]},1"
    
    # Fallback (should be covered by Case 1, but for safety)
    return f"{active_piles[0]},1"
