
def policy(state: dict) -> str:
    private_card = state['private_cards'][0]
    public_cards = state['public_cards']
    allowed_actions = state['allowed_actions']
    to_call = state['to_call']
    pot_total = state['pot']
    opponent_spent = state['opponent_spent']
    my_spent = state['my_spent']

    def evaluate_hand(private_card, public_cards):
        if not public_cards:
            return private_card['rank'] / 14.0
        score = 0.0
        if any(c['rank'] == private_card['rank'] for c in public_cards):
            score += 0.4
        suit_count = sum(1 for c in public_cards if c['suit'] == private_card['suit']) + 1
        if suit_count >= 3:
            score += 0.3
        all_ranks = {private_card['rank']} | {c['rank'] for c in public_cards}
        sorted_ranks = sorted(all_ranks)
        for i in range(len(sorted_ranks) - 2):
            if sorted_ranks[i+2] - sorted_ranks[i] <= 4:
                score += 0.2
                break
        score += private_card['rank'] / 140.0
        return min(score, 1.0)

    hand_score = evaluate_hand(private_card, public_cards)
    current_bet_ratio = (opponent_spent - my_spent) / (pot_total + 1e-6) if pot_total else 0

    if 'raise' in allowed_actions and hand_score > 0.7 + current_bet_ratio * 0.2:
        return 'raise'
    if 'all-in' in allowed_actions and hand_score > 0.8 + current_bet_ratio * 0.2:
        return 'all-in'
    if to_call == 0:
        if 'raise' in allowed_actions and hand_score > 0.6:
            return 'raise'
        else:
            return 'call'
    else:
        pot_odds = to_call / (pot_total + to_call + 1e-6)
        equity_required = pot_odds
        if hand_score > equity_required * 1.2:
            return 'call' if 'call' in allowed_actions else 'fold'
        else:
            return 'fold' if 'fold' in allowed_actions else 'call'
