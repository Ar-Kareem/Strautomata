
def policy(hand: list[str], target: int) -> str:
    # Full deck of 13 cards
    full_deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    # Determine which cards are left in the deck
    remaining_cards = full_deck.copy()
    for card in hand:
        if card in remaining_cards:
            remaining_cards.remove(card)
    
    # Function to compute hand value with optimal Ace handling
    def compute_hand_value(cards):
        # First, compute sum without Aces
        value = 0
        aces = 0
        for card in cards:
            if card == "A":
                aces += 1
            elif card in ["J", "Q", "K"]:
                value += 10
            else:
                value += int(card)
        
        # Now, for each Ace, decide whether to add 1 or 11
        # Add as many 11s as possible without busting
        for _ in range(aces):
            if value + 11 <= target:
                value += 11
            else:
                value += 1
        return value
    
    current_value = compute_hand_value(hand)
    
    # Safety net: if already very close to target, stay to avoid busting
    if current_value >= target - 2:
        return "STAY"
    
    # If no cards left to draw, must STAY
    if not remaining_cards:
        return "STAY"
    
    # Simulate drawing each possible next card and check for bust
    bust_count = 0
    total_count = len(remaining_cards)
    
    for card in remaining_cards:
        new_hand = hand + [card]
        new_value = compute_hand_value(new_hand)
        if new_value > target:
            bust_count += 1
    
    bust_probability = bust_count / total_count if total_count > 0 else 0
    
    # If bust risk is low, take the chance to improve hand
    if bust_probability < 0.5:
        return "HIT"
    else:
        # Even if risk is high, if we're far from target, we might take the chance
        # But if we're close, play it safe
        if current_value >= target - 4:
            return "STAY"
        else:
            # Risky but potentially necessary
            return "HIT" if bust_probability < 0.7 else "STAY"
