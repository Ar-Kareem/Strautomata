
import functools

CARD_LIST = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
CARD_TO_INDEX = {card: i for i, card in enumerate(CARD_LIST)}

def card_value(card: str, current_sum: int, target: int) -> int:
    """Return the value of a single card given current sum and target."""
    if card == "A":
        return 11 if current_sum + 11 <= target else 1
    if card in ("J", "Q", "K"):
        return 10
    return int(card)

def hand_value(hand: list[str], target: int) -> int:
    """Compute total value of a hand, respecting the Ace rule."""
    total = 0
    for card in hand:
        if card == "A":
            # decide value for this ace based on current total and target
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        elif card in ("J", "Q", "K"):
            total += 10
        else:
            total += int(card)
    return total

def hand_to_mask(hand: list[str]) -> int:
    """Convert list of cards to a bitmask (13 bits)."""
    mask = 0
    for card in hand:
        mask |= 1 << CARD_TO_INDEX[card]
    return mask

def mask_to_cards(mask: int) -> list[str]:
    """Convert bitmask back to list of card strings (not needed but useful for debugging)."""
    cards = []
    for i in range(13):
        if mask & (1 << i):
            cards.append(CARD_LIST[i])
    return cards

@functools.lru_cache(maxsize=None)
def opponent_win_probability(
    our_sum: int,
    target: int,
    opp_sum: int,
    opp_mask: int
) -> float:
    """
    Probability that opponent wins given:
      - our_sum: our total after we stay
      - target: T
      - opp_sum: opponent's current sum
      - opp_mask: bitmask of cards already drawn by opponent
    Assumes opponent plays optimally to maximize their win probability.
    Returns a value between 0 and 1.
    """
    if opp_sum > target:
        return 0.0  # opponent busted -> they lose

    # If opponent stays now, what is their win probability?
    our_dist = abs(our_sum - target)
    opp_dist = abs(opp_sum - target)
    if opp_dist < our_dist:
        stay_value = 1.0
    elif opp_dist == our_dist:
        stay_value = 0.5
    else:
        stay_value = 0.0

    # If opponent has drawn all cards, they must stay
    if opp_mask == 0b1111111111111:
        return stay_value

    # Consider hitting: average over all remaining cards
    hit_value = 0.0
    remaining_count = 0
    for i in range(13):
        if not (opp_mask & (1 << i)):
            card = CARD_LIST[i]
            # compute opponent's new sum after drawing this card
            if card == "A":
                if opp_sum + 11 <= target:
                    new_sum = opp_sum + 11
                else:
                    new_sum = opp_sum + 1
            elif card in ("J", "Q", "K"):
                new_sum = opp_sum + 10
            else:
                new_sum = opp_sum + int(card)
            new_mask = opp_mask | (1 << i)
            # recursive call
            hit_value += opponent_win_probability(our_sum, target, new_sum, new_mask)
            remaining_count += 1

    if remaining_count == 0:
        hit_value = stay_value
    else:
        hit_value /= remaining_count

    # opponent chooses the better action
    return max(stay_value, hit_value)

@functools.lru_cache(maxsize=None)
def our_win_probability(
    our_sum: int,
    our_mask: int,
    target: int
) -> float:
    """
    Probability that we win from this state, assuming opponent plays optimally
    from the beginning (empty hand).
    """
    if our_sum > target:
        return 0.0  # we busted

    # Option 1: STAY
    # opponent starts from scratch
    opp_win = opponent_win_probability(our_sum, target, 0, 0)
    stay_value = 1.0 - opp_win

    # Option 2: HIT
    # if we have drawn all cards, we cannot hit
    if our_mask == 0b1111111111111:
        hit_value = stay_value
    else:
        hit_value = 0.0
        remaining_count = 0
        for i in range(13):
            if not (our_mask & (1 << i)):
                card = CARD_LIST[i]
                # compute our new sum after drawing this card
                if card == "A":
                    if our_sum + 11 <= target:
                        new_sum = our_sum + 11
                    else:
                        new_sum = our_sum + 1
                elif card in ("J", "Q", "K"):
                    new_sum = our_sum + 10
                else:
                    new_sum = our_sum + int(card)
                new_mask = our_mask | (1 << i)
                hit_value += our_win_probability(new_sum, new_mask, target)
                remaining_count += 1
        if remaining_count > 0:
            hit_value /= remaining_count
        else:
            hit_value = stay_value

    # choose the action that gives higher win probability
    return max(stay_value, hit_value)

def policy(hand: list[str], target: int) -> str:
    # compute current sum and mask
    current_sum = hand_value(hand, target)
    mask = hand_to_mask(hand)

    # if already bust (should not happen since policy wouldn't be called)
    if current_sum > target:
        return "STAY"

    # compute win probability if we stay now
    opp_win_stay = opponent_win_probability(current_sum, target, 0, 0)
    stay_win_prob = 1.0 - opp_win_stay

    # compute average win probability if we hit
    hit_win_prob = 0.0
    remaining_count = 0
    for i in range(13):
        if not (mask & (1 << i)):
            card = CARD_LIST[i]
            if card == "A":
                if current_sum + 11 <= target:
                    new_sum = current_sum + 11
                else:
                    new_sum = current_sum + 1
            elif card in ("J", "Q", "K"):
                new_sum = current_sum + 10
            else:
                new_sum = current_sum + int(card)
            if new_sum > target:
                # drawing this card makes us bust -> win probability 0
                contribution = 0.0
            else:
                new_mask = mask | (1 << i)
                contribution = our_win_probability(new_sum, new_mask, target)
            hit_win_prob += contribution
            remaining_count += 1

    if remaining_count > 0:
        hit_win_prob /= remaining_count
    else:
        hit_win_prob = stay_win_prob

    # choose the action with higher win probability
    if hit_win_prob > stay_win_prob:
        return "HIT"
    else:
        return "STAY"

# Optional: pre‑compute for all targets to speed up first call (not required but helpful)
def precompute_all():
    """Pre‑compute win probabilities for all targets between 10 and 30."""
    for t in range(10, 31):
        # warm‑up the caches
        our_win_probability(0, 0, t)

# Call precomputation when module loads (takes a fraction of a second)
if __name__ == "__main__":
    precompute_all()
