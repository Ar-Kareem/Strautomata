
def compute_hand_value(hand, T):
    non_ace_value = 0
    num_aces = 0
    for card in hand:
        if card == "A":
            num_aces += 1
        elif card in ['J', 'Q', 'K']:
            non_ace_value += 10
        else:
            non_ace_value += int(card)
    total = non_ace_value + 11 * num_aces
    if total <= T:
        return total
    else:
        return non_ace_value + num_aces

def policy(hand: list[str], target: int) -> str:
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    card_to_index = {card: i for i, card in enumerate(all_cards)}
    n = 13
    global global_dp_cache
    if 'global_dp_cache' not in globals():
        global_dp_cache = {}
    
    if target not in global_dp_cache:
        dp = [0] * (1 << n)
        full_mask = (1 << n) - 1
        for bitmask in range(full_mask, -1, -1):
            hand_set = set()
            for i in range(n):
                if bitmask & (1 << i):
                    hand_set.add(all_cards[i])
            hand_list = list(hand_set)
            hand_value = compute_hand_value(hand_list, target)
            if hand_value > target:
                dp[bitmask] = -10**9
            else:
                best = hand_value
                if bitmask != full_mask:
                    for i in range(n):
                        if not (bitmask & (1 << i)):
                            new_bitmask = bitmask | (1 << i)
                            best = max(best, dp[new_bitmask])
                dp[bitmask] = best
        global_dp_cache[target] = dp
    
    dp = global_dp_cache[target]
    hand_set = set(hand)
    bitmask = 0
    for card in hand_set:
        if card in card_to_index:
            bitmask |= 1 << card_to_index[card]
    
    best_hand_value = dp[bitmask]
    current_hand_value = compute_hand_value(hand, target)
    
    if current_hand_value > target:
        return "STAY"
    else:
        if best_hand_value > current_hand_value:
            return "HIT"
        else:
            return "STAY"
