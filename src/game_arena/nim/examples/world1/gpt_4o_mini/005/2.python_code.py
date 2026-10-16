
def policy(piles: list[int]) -> str:
    nim_sum = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
    
    # Try to find a move that makes the new nim_sum zero
    for i in range(4):
        if piles[i] > 0:  # Only consider non-empty piles
            new_pile_count = piles[i] ^ nim_sum
            if new_pile_count < piles[i]:  # Valid move found
                return f'{i},{piles[i] - new_pile_count}'
    
    # If no move makes the nim sum zero, take from any pile legally
    for i in range(4):
        if piles[i] > 0:  
            return f'{i},1'  # Take 1 item from the first non-empty pile
