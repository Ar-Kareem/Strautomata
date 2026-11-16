
import sys

def policy(piles: list[int]) -> str:
    """
    Calculates the optimal move for Misère Nim (last player to move loses).
    """
    # Calculate the Nim-sum (XOR of all pile sizes)
    nim_sum = 0
    for p in piles:
        nim_sum ^= p
    
    # Check if we are in the endgame (no piles > 1)
    max_pile = max(piles)
    
    if max_pile <= 1:
        # Endgame phase: logic is based on parity of piles with size 1.
        # In Misère Nim endgame, winning means leaving an ODD number of size-1 piles.
        # (Because with 1 pile left, opponent takes last and loses.
        # With 2 piles left, I take one, opponent takes last and loses -> wait, 2 piles means I take 1, leaving 1. Opponent takes last and loses. So I win.
        # Correct logic:
        # 1 pile: P1 takes 1, leaves 0. P1 loses. (Bad for P1)
        # 2 piles: P1 takes 1, leaves 1. P2 takes last, P2 loses. (Good for P1)
        # 3 piles: P1 takes 1, leaves 2. P2 wins. (Bad for P1)
        # Conclusion: Leaving an ODD number of size-1 piles is winning for the player to move.
        # Therefore, we want to leave an EVEN number of size-1 piles for the opponent.
        
        count_ones = sum(1 for p in piles if p == 1)
        
        # If count_ones is odd, it's a winning position for us. We take 1 to make it even.
        # If count_ones is even, it's a losing position. We take 1 (forced).
        for i, p in enumerate(piles):
            if p == 1:
                return f"{i},1"
        
        # Fallback if something is wrong (e.g. all 0s)
        return "0,0"

    else:
        # Normal phase (at least one pile > 1)
        
        if nim_sum != 0:
            # Winning position. Try to find a move that makes Nim-sum 0.
            for i, p in enumerate(piles):
                target_size = p ^ nim_sum
                if target_size < p:
                    # This is the standard winning move.
                    take = p - target_size
                    
                    # Check for Misère condition:
                    # If this move results in a state where ALL piles are <= 1,
                    # we must ensure we leave an ODD number of size-1 piles.
                    
                    # Check if this move empties the last large pile
                    other_large_exists = False
                    for j, q in enumerate(piles):
                        if i != j and q > 1:
                            other_large_exists = True
                            break
                    
                    if not other_large_exists and target_size <= 1:
                        # We are transitioning to endgame.
                        # Calculate number of size-1 piles in the resulting state.
                        ones_count = 0
                        for j, q in enumerate(piles):
                            if i == j:
                                if target_size == 1:
                                    ones_count += 1
                            else:
                                if q == 1:
                                    ones_count += 1
                        
                        # We want to leave the opponent in a losing endgame position.
                        # Losing endgame position = Even number of size-1 piles.
                        # (Derived: Odd size-1 piles is win for player to move).
                        # So we want to leave Even number of size-1 piles.
                        # Wait, earlier I concluded leaving ODD is winning for player to move.
                        # So if I leave ODD for opponent, opponent wins. I lose.
                        # I want to leave EVEN for opponent.
                        
                        if ones_count % 2 != 0:
                            # Odd count -> Good for opponent. We need to adjust.
                            # We can change target_size from 0 to 1 or 1 to 0.
                            # This flips the count parity.
                            # We know p > 1, so we can always reduce to 0 or 1.
                            target_size = target_size ^ 1
                            take = p - target_size
                            return f"{i},{take}"
                    
                    # Standard move is safe
                    return f"{i},{take}"
        else:
            # Losing position (Nim-sum is 0).
            # Play a delay move. Take 1 from the first pile > 1.
            for i, p in enumerate(piles):
                if p > 1:
                    return f"{i},1"
    
    # Fallback (should not be reached with valid inputs)
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
    return "0,0"
