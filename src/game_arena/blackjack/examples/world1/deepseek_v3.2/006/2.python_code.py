
import random
from functools import lru_cache

# Precompute all cards
ALL_CARDS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
CARD_TO_INDEX = {card: i for i, card in enumerate(ALL_CARDS)}

def hand_value(hand, target):
    """
    Compute total value of hand given target T.
    hand is a list of card strings.
    """
    total = 0
    ace_count = 0
    for card in hand:
        if card == 'A':
            ace_count += 1
        elif card in ('J', 'Q', 'K'):
            total += 10
        else:
            total += int(card)
    # Process aces: at most one, but handle multiple just in case
    for _ in range(ace_count):
        if total + 11 <= target:
            total += 11
        else:
            total += 1
    return total

def subset_to_cards(mask):
    """Convert bitmask to list of card strings."""
    cards = []
    for i in range(13):
        if mask & (1 << i):
            cards.append(ALL_CARDS[i])
    return cards

def cards_to_subset(cards):
    """Convert list of cards to bitmask."""
    mask = 0
    for card in cards:
        mask |= 1 << CARD_TO_INDEX[card]
    return mask

class OptimalPolicy:
    """Precompute optimal actions for a given target T."""
    def __init__(self, target):
        self.target = target
        self.all_mask = (1 << 13) - 1
        # Precompute hand value for all subsets
        self.hand_value_cache = {}
        for mask in range(self.all_mask + 1):
            cards = subset_to_cards(mask)
            self.hand_value_cache[mask] = hand_value(cards, target)
        
        # Solve via value iteration
        self.V = {}  # win probability for each state
        self.action = {}  # optimal action: 'STAY' or 'HIT'
        
        # Opponent distribution (prob_sum) maps sum to probability (sum <= target) and 'bust' key
        # Initialize opponent distribution as uniform over 0..target (including bust? no bust prob 0)
        self.opp_dist = {s: 1.0 / (target + 1) for s in range(target + 1)}
        self.opp_dist['bust'] = 0.0
        
        self.converge()
    
    def stop_win_prob(self, mask):
        """Probability of winning if we stop at state mask."""
        s = self.hand_value_cache[mask]
        win = self.opp_dist['bust']
        for o, prob in self.opp_dist.items():
            if o == 'bust':
                continue
            if abs(o - self.target) > abs(s - self.target):
                win += prob
        return win
    
    def draw_win_prob(self, mask):
        """Expected win probability if we draw one card from remaining."""
        remaining_mask = self.all_mask ^ mask
        if remaining_mask == 0:
            return 0.0  # no cards left, cannot draw (should not happen if optimal)
        # count remaining cards and compute average
        remaining_indices = [i for i in range(13) if remaining_mask & (1 << i)]
        total = 0.0
        for i in remaining_indices:
            new_mask = mask | (1 << i)
            if self.hand_value_cache[new_mask] > self.target:
                # bust, lose immediately
                continue
            else:
                total += self.V[new_mask]
        return total / len(remaining_indices)
    
    def compute_opp_dist(self):
        """Compute opponent's final sum distribution given current optimal policy."""
        # prob_state[mask] = probability of reaching mask and not having stopped before
        prob_state = [0.0] * (self.all_mask + 1)
        prob_state[0] = 1.0  # start with empty hand
        new_opp_dist = {s: 0.0 for s in range(self.target + 1)}
        new_opp_dist['bust'] = 0.0
        
        # Process masks in increasing order of size (number of bits)
        masks_by_size = [[] for _ in range(14)]
        for mask in range(self.all_mask + 1):
            cnt = bin(mask).count('1')
            masks_by_size[cnt].append(mask)
        
        for size in range(14):
            for mask in masks_by_size[size]:
                p = prob_state[mask]
                if p == 0:
                    continue
                if self.action.get(mask, 'HIT') == 'STAY':
                    # stop at this state
                    s = self.hand_value_cache[mask]
                    if s > self.target:
                        new_opp_dist['bust'] += p
                    else:
                        new_opp_dist[s] += p
                else:
                    # draw a card
                    remaining_mask = self.all_mask ^ mask
                    if remaining_mask == 0:
                        # no cards left, must stay (should not happen if policy correct)
                        s = self.hand_value_cache[mask]
                        if s > self.target:
                            new_opp_dist['bust'] += p
                        else:
                            new_opp_dist[s] += p
                        continue
                    remaining_indices = [i for i in range(13) if remaining_mask & (1 << i)]
                    for i in remaining_indices:
                        new_mask = mask | (1 << i)
                        prob_state[new_mask] += p / len(remaining_indices)
        
        # Normalize (should sum to 1)
        total = sum(new_opp_dist.values())
        if total > 0:
            for k in new_opp_dist:
                new_opp_dist[k] /= total
        return new_opp_dist
    
    def converge(self, max_iter=100, tol=1e-6):
        """Iterate until opponent distribution stabilizes."""
        for it in range(max_iter):
            # Compute V and actions for all states given current opp_dist
            # Process masks in decreasing order of size so that V for supersets is computed first
            masks_by_size = [[] for _ in range(14)]
            for mask in range(self.all_mask + 1):
                cnt = bin(mask).count('1')
                masks_by_size[cnt].append(mask)
            
            for size in range(13, -1, -1):
                for mask in masks_by_size[size]:
                    stop_val = self.stop_win_prob(mask)
                    draw_val = self.draw_win_prob(mask)
                    if stop_val >= draw_val:
                        self.V[mask] = stop_val
                        self.action[mask] = 'STAY'
                    else:
                        self.V[mask] = draw_val
                        self.action[mask] = 'HIT'
            
            # Update opponent distribution
            new_opp_dist = self.compute_opp_dist()
            # Check change
            diff = 0.0
            for k in self.opp_dist:
                diff += abs(self.opp_dist[k] - new_opp_dist.get(k, 0.0))
            self.opp_dist = new_opp_dist
            if diff < tol:
                break

# Cache optimal policy objects per target
policy_cache = {}

def policy(hand, target):
    # Convert hand to bitmask
    mask = cards_to_subset(hand)
    
    # Get or create optimal policy for this target
    if target not in policy_cache:
        policy_cache[target] = OptimalPolicy(target)
    opt = policy_cache[target]
    
    # Return optimal action for current state
    return opt.action.get(mask, 'STAY')
