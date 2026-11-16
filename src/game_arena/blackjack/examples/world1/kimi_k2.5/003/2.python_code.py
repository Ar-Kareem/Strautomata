
import functools

# Card indices: 0=A, 1=2, 2=3, ..., 8=9, 9=10, 10=J, 11=Q, 12=K
# Values: A=11 (flexible), 2-9 face value, 10/J/Q/K=10

def _get_score(mask: int, target: int) -> int:
    """Calculate hand score. Returns value > target if bust."""
    total = 0
    aces = 0
    for i in range(13):
        if mask & (1 << i):
            if i == 0:  # Ace
                aces += 1
                total += 11
            elif i <= 8:  # 2-9
                total += i + 1
            else:  # 10, J, Q, K
                total += 10
    # Convert aces from 11 to 1 as needed
    while total > target and aces > 0:
        total -= 10
        aces -= 1
    return total

def _hand_to_mask(hand: list[str]) -> int:
    """Convert list of card strings to bitmask."""
    card_to_idx = {
        "A": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "7": 6, "8": 7, "9": 8,
        "10": 9, "J": 10, "Q": 11, "K": 12
    }
    mask = 0
    for card in hand:
        mask |= 1 << card_to_idx[card]
    return mask

@functools.lru_cache(maxsize=32)
def _precompute_strategy(target: int):
    """Precompute the optimal action table for a given target."""
    n = 1 << 13
    
    # Step 1: Compute opponent's expected score if they play to maximize expected score
    # E_score[mask] = expected final score starting from mask
    E_score = [0.0] * n
    for mask in range(n - 1, -1, -1):
        s = _get_score(mask, target)
        if s > target:
            E_score[mask] = 0.0  # Bust yields 0
        else:
            best = float(s)  # Staying
            remaining = []
            for c in range(13):
                if not (mask & (1 << c)):
                    remaining.append(c)
            if remaining:
                avg = 0.0
                for c in remaining:
                    avg += E_score[mask | (1 << c)]
                avg /= len(remaining)
                if avg > best:
                    best = avg
            E_score[mask] = best
    
    # Step 2: Compute opponent's score distribution when playing the above strategy
    # D[s] = prob opponent ends with score s (0 <= s <= target)
    # D_bust = prob opponent busts
    prob = [0.0] * n
    prob[0] = 1.0
    D = [0.0] * (target + 1)
    D_bust = 0.0
    
    for mask in range(n):
        if prob[mask] == 0:
            continue
        s = _get_score(mask, target)
        if s > target:
            D_bust += prob[mask]
            continue
        
        remaining = [c for c in range(13) if not (mask & (1 << c))]
        if not remaining:
            D[min(s, target)] += prob[mask]
            continue
        
        # Decide if opponent stays or hits based on E_score
        avg_future = sum(E_score[mask | (1 << c)] for c in remaining) / len(remaining)
        if E_score[mask] <= s + 1e-9:  # Stay
            D[min(s, target)] += prob[mask]
        else:  # Hit
            p_next = prob[mask] / len(remaining)
            for c in remaining:
                prob[mask | (1 << c)] += p_next
    
    # Step 3: Compute our optimal strategy to maximize win probability against this opponent
    # V[mask] = max win prob from this state
    # Action: "STAY" or "HIT"
    action_table = ["STAY"] * n
    
    for mask in range(n - 1, -1, -1):
        s = _get_score(mask, target)
        
        # Win probability if we stay
        if s > target:
            w_stay = 0.5 * D_bust
        else:
            w_stay = D_bust  # Win if opponent busts
            for s_opp in range(s):
                w_stay += D[s_opp]  # Win if opponent score lower
            w_stay += 0.5 * D[s]  # Draw if equal
        
        remaining = [c for c in range(13) if not (mask & (1 << c))]
        if not remaining:
            continue  # Must stay, already set to STAY
            
        # Win probability if we hit (expectation over next states)
        w_hit = 0.0
        for c in remaining:
            w_hit += action_table[mask | (1 << c)]  # Actually we need V, not action
        # Wait, we need V values, not action strings. Let me use a separate array.
    
    # Recompute with proper value array
    V = [0.0] * n
    for mask in range(n - 1, -1, -1):
        s = _get_score(mask, target)
        
        if s > target:
            w_stay = 0.5 * D_bust
        else:
            w_stay = D_bust
            for s_opp in range(s):
                w_stay += D[s_opp]
            w_stay += 0.5 * D[s]
        
        remaining = [c for c in range(13) if not (mask & (1 << c))]
        if not remaining or s > target:
            V[mask] = w_stay
            action_table[mask] = "STAY"
        else:
            w_hit = sum(V[mask | (1 << c)] for c in remaining) / len(remaining)
            if w_hit > w_stay + 1e-9:
                V[mask] = w_hit
                action_table[mask] = "HIT"
            else:
                V[mask] = w_stay
                action_table[mask] = "STAY"
    
    return action_table

def policy(hand: list[str], target: int) -> str:
    mask = _hand_to_mask(hand)
    action_table = _precompute_strategy(target)
    return action_table[mask]
