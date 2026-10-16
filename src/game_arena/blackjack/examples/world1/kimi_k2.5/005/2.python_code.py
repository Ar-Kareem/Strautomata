
from functools import lru_cache

def policy(hand: list[str], target: int) -> str:
    """
    Optimal stopping policy for the simplified Blackjack game.
    Maximizes expected final hand value using dynamic programming.
    """
    # Define the 13 distinct cards in order
    ALL_CARDS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    CARD_TO_IDX = {card: i for i, card in enumerate(ALL_CARDS)}
    FULL_MASK = (1 << 13) - 1
    
    # Convert hand list to bitmask
    current_mask = 0
    for card in hand:
        current_mask |= 1 << CARD_TO_IDX[card]
    
    def calculate_value(mask: int) -> int:
        """Calculate hand value with Aces as 11 or 1 optimally."""
        total = 0
        aces = 0
        for i in range(13):
            if mask & (1 << i):
                card = ALL_CARDS[i]
                if card == "A":
                    total += 11
                    aces += 1
                elif card in ("J", "Q", "K"):
                    total += 10
                else:
                    total += int(card)
        # Reduce Aces from 11 to 1 as needed to avoid busting
        while total > target and aces > 0:
            total -= 10
            aces -= 1
        return total
    
    current_val = calculate_value(current_mask)
    
    # If already bust, must stay
    if current_val > target:
        return "STAY"
    
    # If deck is empty, must stay
    if current_mask == FULL_MASK:
        return "STAY"
    
    @lru_cache(maxsize=None)
    def dp(mask: int) -> float:
        """
        Returns the expected final score from this state assuming optimal play.
        If bust, returns 0.
        """
        val = calculate_value(mask)
        if val > target:
            return 0.0
        
        # Determine remaining cards
        remaining = []
        for i in range(13):
            if not (mask & (1 << i)):
                remaining.append(i)
        
        if not remaining:
            return float(val)
        
        # Expected value if we hit now
        exp_hit = 0.0
        for i in remaining:
            exp_hit += dp(mask | (1 << i))
        exp_hit /= len(remaining)
        
        # Optimal choice: stay (get val) or hit (get exp_hit)
        return max(float(val), exp_hit)
    
    # Calculate expected value of hitting from current state
    remaining_indices = [i for i in range(13) if not (current_mask & (1 << i))]
    exp_hit_now = sum(dp(current_mask | (1 << i)) for i in remaining_indices) / len(remaining_indices)
    
    if exp_hit_now > current_val:
        return "HIT"
    else:
        return "STAY"
