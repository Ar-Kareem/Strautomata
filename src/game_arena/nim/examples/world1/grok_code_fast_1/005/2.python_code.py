
import random

MAX_PILE = 40  # Assumed upper limit for pile sizes to keep state space manageable

memo = {}

def is_win(position):
    pos_tuple = tuple(position)
    if pos_tuple in memo:
        return memo[pos_tuple]
    
    total = sum(position)
    if total == 0:
        return 0  # Terminal state: player who moved here already lost
    
    can_win = False
    for pile in range(4):
        if position[pile] > 0:
            max_take = min(position[pile], MAX_PILE)  # Cap at MAX_PILE for safety
            for take in range(1, max_take + 1):
                new_pos = list(position)
                new_pos[pile] -= take
                new_tuple = tuple(new_pos)
                if sum(new_pos) == 0:
                    continue  # Skip moves that immediately lose
                if not is_win(new_tuple):  # Opponent loses from this position
                    can_win = True
                    break
            if can_win:
                break
    memo[pos_tuple] = 1 if can_win else 0
    return memo[pos_tuple]

def policy(piles):
    # Filter out possibly large piles, but proceed with assumption it's small
    for p in piles:
        if p > MAX_PILE:
            # Fallback: use a simple strategy, e.g., reduce a pile to match XOR if possible
            xor = piles[0] ^ piles[1] ^ piles[2] ^ piles[3]
            if xor != 0:
                for i in range(4):
                    if piles[i] ^ xor < piles[i]:
                        take = piles[i] - (piles[i] ^ xor)
                        if take >= 1:
                            return f"{i},{take}"
            # Otherwise, just take from largest pile
            max_i = piles.index(max(piles))
            take = 1
            return f"{max_i},{take}"
    
    # Compute possible moves
    good_moves = []
    bad_but_legal_moves = []
    for pile in range(4):
        for take in range(1, piles[pile] + 1):
            new_pos = piles[:]
            new_pos[pile] -= take
            if sum(new_pos) == 0:
                bad_but_legal_moves.append((pile, take))
            elif not is_win(tuple(new_pos)):  # Opponent loses
                good_moves.append((pile, take))
    
    # Choose a good move if available, else a bad one
    if good_moves:
        chosen = random.choice(good_moves)  # Random among good moves for simplicity
    elif bad_but_legal_moves:
        chosen = random.choice(bad_but_legal_moves)
    else:
        # Fallback: should not happen, but take 1 from smallest non-zero pile
        for i in range(4):
            if piles[i] > 0:
                return f"{i},1"
        raise ValueError("No moves possible, but piles are not empty")
    
    return f"{chosen[0]},{chosen[1]}"
