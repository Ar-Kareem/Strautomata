
from copy import deepcopy
from typing import List, Tuple

def next_pos(player: str, idx: int) -> Tuple[str, int]:
    """
    Return the next board position when sowing seeds.
    player: 'you' or 'opp'
    idx:   0‑5 for houses, 6 only for your store.
    """
    if player == "you":
        if idx < 5:        # next house on your side
            return "you", idx + 1
        elif idx == 5:     # after house5 comes your store
            return "you", 6
        else:              # idx == 6, after your store comes opponent house0
            return "opp", 0
    else:  # player == "opp"
        if idx < 5:        # next opponent house
            return "opp", idx + 1
        else:              # idx == 5, after opponent house5 comes your house0
            return "you", 0

def simulate_move(you: List[int], opp: List[int], house: int) -> Tuple[List[int], List[int], bool, bool]:
    """
    Simulate picking house `house` (0‑5) on your side.
    Returns:
        new_you, new_opp, extra_move_flag, capture_flag
    """
    new_you = you[:]
    new_opp = opp[:]

    seeds = new_you[house]
    new_you[house] = 0                     # empty the chosen house
    player, idx = "you", house             # start from the chosen house

    # sow the seeds
    while seeds > 0:
        player, idx = next_pos(player, idx)
        if player == "you":
            new_you[idx] += 1
        else:
            new_opp[idx] += 1
        seeds -= 1

    # Determine special effects
    extra = (player == "you" and idx == 6)   # landed in my store

    capture = False
    # capture occurs only if last seed lands in an empty own house (now has exactly 1 seed)
    if player == "you" and 0 <= idx <= 5 and new_you[idx] == 1:
        opposite_idx = 5 - idx
        if new_opp[opposite_idx] > 0:
            # perform capture
            captured = new_you[idx] + new_opp[opposite_idx]
            new_you[6] += captured
            new_you[idx] = 0
            new_opp[opposite_idx] = 0
            capture = True

    return new_you, new_opp, extra, capture

def policy(you: List[int], opponent: List[int]) -> int:
    """
    Choose a legal move (house index 0‑5) according to a simple heuristic:
    1. Prefer moves that give an extra turn.
    2. Then prefer moves that capture opponent seeds.
    3. Otherwise pick the move that maximises my store after the move.
    """
    legal_moves = [i for i in range(6) if you[i] > 0]

    best_extra = []
    best_capture = []
    best_store = -1
    best_move_store = None

    for move in legal_moves:
        new_you, new_opp, extra, capture = simulate_move(you, opponent, move)

        if extra:
            best_extra.append(move)
        elif capture:
            best_capture.append(move)

        # track move giving the biggest store (used if no extra/capture)
        if new_you[6] > best_store:
            best_store = new_you[6]
            best_move_store = move

    if best_extra:
        # if multiple, choose the one that also gives the biggest store
        # (optional tie‑breaker)
        if len(best_extra) > 1:
            best_extra.sort(key=lambda m: simulate_move(you, opponent, m)[0][6], reverse=True)
        return best_extra[0]

    if best_capture:
        if len(best_capture) > 1:
            best_capture.sort(key=lambda m: simulate_move(you, opponent, m)[0][6], reverse=True)
        return best_capture[0]

    # fallback: move that leaves the most seeds in my store
    return best_move_store
