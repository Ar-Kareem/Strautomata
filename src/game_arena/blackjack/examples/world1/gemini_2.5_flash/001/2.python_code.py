
import collections

# Define card values as a global constant for efficiency
CARD_VALUES_MAP = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10
}

# Define all possible card types as a global constant
ALL_CARD_TYPES = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def calculate_score(hand: list[str], target: int) -> int:
    """
    Calculates the current score of a given hand, adjusting Ace values
    to 1 if necessary to avoid busting relative to the target.
    """
    score = 0
    num_aces = 0

    # First, calculate score assuming Aces are 11
    for card in hand:
        if card == "A":
            num_aces += 1
            score += 11
        else:
            score += CARD_VALUES_MAP[card]

    # If the score exceeds the target, and we have Aces,
    # convert 11-point Aces to 1-point Aces one by one until score is <= target or no more Aces to convert.
    while score > target and num_aces > 0:
        score -= 10  # Convert an 11-point Ace to a 1-point Ace
        num_aces -= 1

    return score

def policy(hand: list[str], target: int) -> str:
    """
    Determines whether to "HIT" or "STAY" in the Blackjack-like game.

    Args:
        hand: A list of strings representing the cards currently held.
        target: The integer target score to approach.

    Returns:
        "HIT" to draw another card, or "STAY" to stop drawing.
    """
    current_score = calculate_score(hand, target)

    # 1. If the current score is already at or above the target, it's safest to STAY.
    #    Hitting further would risk busting or not improving a perfect score.
    if current_score >= target:
        return "STAY"

    # 2. Determine which cards are still theoretically available in our deck.
    #    Each card type appears once in a 13-card deck.
    available_cards_count = collections.Counter(ALL_CARD_TYPES)
    for card_in_hand in hand:
        if card_in_hand in available_cards_count:
            available_cards_count[card_in_hand] -= 1

    available_cards_list = [card_type for card_type, count in available_cards_count.items() if count > 0]

    # If there are no cards left to draw (e.g., we hold all 13 unique cards), we must STAY.
    if not available_cards_list:
        return "STAY"

    # 3. Calculate the risk of busting if we were to HIT.
    bust_count = 0
    # Iterate through potential next cards from our remaining deck
    for next_card_type in available_cards_list:
        # Create a temporary hand by adding the potential next card
        temp_hand = hand + [next_card_type]
        score_if_hit = calculate_score(temp_hand, target)

        # If adding this card would make us bust (score > target), increment bust_count
        if score_if_hit > target:
            bust_count += 1

    num_available_cards = len(available_cards_list)
    bust_probability = bust_count / num_available_cards

    # 4. Make a decision based on bust risk.
    # If the probability of busting with the next card is high (e.g., greater than 50%),
    # it's generally safer to STAY with the current score rather than risk busting.
    if bust_probability > 0.5:
        return "STAY"
    else:
        # Otherwise, if the risk of busting is low or moderate,
        # it's worth taking another card to try and improve the score and get closer to the target.
        return "HIT"

