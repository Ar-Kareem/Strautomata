
import collections

# Card face values for non-Ace cards.
card_face_values = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10
}

# The full deck of available cards (one of each rank).
FULL_DECK_RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def calculate_score(hand: list[str], target: int) -> int:
    """
    Calculates the score of a given hand based on the game's specific Ace rule.
    An Ace is 11 when the hand value (after all cards are drawn and Aces evaluated)
    is <= target, or 1 when the hand value is > target.
    This implementation prioritizes making Aces 11 if it doesn't exceed the target,
    otherwise, they are counted as 1.
    """
    score_no_aces = 0
    num_aces = 0
    for card in hand:
        if card == "A":
            num_aces += 1
        else:
            score_no_aces += card_face_values[card]

    # Start by counting all Aces as 1.
    current_score = score_no_aces + num_aces

    # Then, for each Ace, try to convert its value from 1 to 11 (by adding 10)
    # if it helps to reach the target without exceeding it.
    for _ in range(num_aces):
        # If adding 10 to the current score (converting an Ace from 1 to 11)
        # would not make the total score exceed the target, perform the conversion.
        if current_score + 10 <= target:
            current_score += 10
        else:
            # If converting would exceed the target, stop converting further Aces
            # as they would definitely make the score exceed or stay as 1.
            break

    return current_score

def policy(hand: list[str], target: int) -> str:
    """
    Implements the policy to decide whether to "HIT" or "STAY".

    Args:
        hand: A list of strings representing the cards currently held.
        target: The integer 'T' the player is trying to approach.

    Returns:
        "HIT" to draw another card, or "STAY" to stop drawing.
    """
    current_score = calculate_score(hand, target)

    # If the current score exactly matches the target, it's a perfect score. STAY.
    if current_score == target:
        return "STAY"

    # Determine which cards are still available in the player's deck.
    # The opponent has a separate deck, so only our own hand matters for available cards.
    drawn_cards_count = collections.Counter(hand)
    available_cards_to_draw = []
    for card_rank in FULL_DECK_RANKS:
        # Each rank appears once in the FULL_DECK_RANKS.
        # If the card of this rank has not been drawn, it's available.
        if drawn_cards_count[card_rank] == 0:
            available_cards_to_draw.append(card_rank)

    total_possible_draws = len(available_cards_to_draw)

    # If there are no more cards to draw, we must STAY.
    if total_possible_draws == 0:
        return "STAY"

    # Calculate the number of cards that would cause a bust if drawn.
    bust_count = 0
    for next_card in available_cards_to_draw:
        hypothetical_hand = hand + [next_card]
        hypothetical_score = calculate_score(hypothetical_hand, target)
        if hypothetical_score > target:
            bust_count += 1

    # Calculate the probability of busting if we HIT.
    bust_probability = bust_count / total_possible_draws

    # Decision Logic:
    # 1. If current score is very low, always HIT to get closer to the target.
    #    This prevents staying with a score that is unlikely to win.
    #    The threshold `target * 0.65` (e.g., if target=20, score < 13) is a tunable parameter.
    if current_score < target * 0.65:
        return "HIT"

    # 2. If the current score is decent, but not necessarily very close to the target,
    #    we decide based on the bust probability.
    #    `risk_tolerance_threshold` is another tunable parameter (e.g., 0.35 means 35% chance of bust is tolerated).
    #    If the probability of busting is below this threshold, it's relatively safe to HIT.
    risk_tolerance_threshold = 0.35
    if bust_probability < risk_tolerance_threshold:
        return "HIT"

    # 3. In all other cases (e.g., score is high, or bust probability is high), STAY.
    #    This protects against busting when close to the target or when risk is substantial.
    return "STAY"

