
#!/usr/bin/env python3
"""
Simple Kalah move selection policy.

The board is represented by two lists of length 7:
    you = [h0, h1, h2, h3, h4, h5, store]
    opponent = [h0, h1, h2, h3, h4, h5, store]

The function `policy(you, opponent)` returns an integer 0‑5 indicating the
house to play. The policy prefers:
    1. moves that give an extra turn,
    2. moves that capture opponent seeds,
    3. moves that increase the player's store the most.
"""

from __future__ import annotations
from typing import List, Tuple


def _simulate_move(you: List[int], opponent: List[int], house: int) -> Tuple[
    List[int], List[int], bool, bool
]:
    """
    Simulate sowing from `house` (0‑5) and return the new board,
    a flag indicating an extra move, and a flag indicating a capture.

    Returns:
        new_you, new_opponent, extra_move, capture_move
    """
    # copy board
    new_you = you.copy()
    new_opp = opponent.copy()

    seeds = new_you[house]
    if seeds == 0:
        raise ValueError("Attempted to simulate an illegal move")

    # remove seeds from selected house
    new_you[house] = 0

    # Index mapping in the 13‑pit circular board:
    # 0‑5 -> your houses, 6 -> your store, 7‑12 -> opponent houses 0‑5
    idx = house  # current position before first seed

    for _ in range(seeds):
        idx = (idx + 1) % 13
        if idx <= 5:            # your house
            new_you[idx] += 1
        elif idx == 6:          # your store
            new_you[6] += 1
        else:                   # opponent house (idx 7‑12 -> opp 0‑5)
            new_opp[idx - 7] += 1

    final_idx = idx
    extra_move = final_idx == 6
    capture_move = False

    # Capture rule
    if 0 <= final_idx <= 5:
        # after placing, if the house now has exactly 1 seed,
        # it was empty before the last seed.
        if new_you[final_idx] == 1:
            opp_house = 5 - final_idx
            if new_opp[opp_house] > 0:
                capture_move = True
                captured = new_you[final_idx] + new_opp[opp_house]
                new_you[6] += captured
                new_you[final_idx] = 0
                new_opp[opp_house] = 0

    return new_you, new_opp, extra_move, capture_move


def policy(you: List[int], opponent: List[int]) -> int:
    """
    Choose a legal move for the current player.

    The move is selected based on the following priority:
        1. any move that grants an extra turn,
        2. any move that captures opponent seeds,
        3. the move that maximises the player's store after the move.
    """
    best_move = None
    best_score = (-1, -1, -1)  # (extra, capture, store)

    for house in range(6):
        if you[house] == 0:
            continue  # illegal move

        new_you, _, extra, capture = _simulate_move(you, opponent, house)
        score = (int(extra), int(capture), new_you[6])

        if score > best_score:
            best_score = score
            best_move = house

    # best_move is guaranteed to be set because there is at least one legal move
    return best_move  # type: ignore

# If the module is run directly, perform a tiny self‑test.
if __name__ == "__main__":
    # Example board where an extra turn is possible from house 2
    you_example = [0, 0, 4, 0, 0, 0, 10]
    opp_example = [4, 4, 4, 4, 4, 4, 0]
    print("Chosen move:", policy(you_example, opp_example))
