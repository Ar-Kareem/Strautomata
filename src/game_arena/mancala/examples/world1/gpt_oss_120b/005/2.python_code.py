
import sys
from functools import lru_cache

# ---------- Kalah mechanics ----------
# positions in sowing order (skip opponent's store)
# (side, idx) where side 0 = you, 1 = opponent, idx 0‑5 houses, 6 = your store
_POSITIONS = [(0, i) for i in range(6)] + [(0, 6)] + [(1, i) for i in range(6)]  # length 12


def _simulate_move(you, opp, house):
    """Return (new_you, new_opp, extra_turn) after sowing from `house`."""
    you = list(you)
    opp = list(opp)

    seeds = you[house]
    you[house] = 0
    # start from the selected house index in the circular order
    pos = house  # index inside _POSITIONS (0‑5 for your houses)

    while seeds:
        pos = (pos + 1) % 12
        side, idx = _POSITIONS[pos]
        if side == 0:
            you[idx] += 1
        else:
            opp[idx] += 1
        seeds -= 1

    side, idx = _POSITIONS[pos]
    extra_turn = (side == 0 and idx == 6)

    # capture rule
    if side == 0 and idx != 6 and you[idx] == 1:          # landed on an empty house
        opp_idx = 5 - idx
        if opp[opp_idx] > 0:
            captured = opp[opp_idx] + you[idx]
            you[6] += captured
            you[idx] = 0
            opp[opp_idx] = 0

    return tuple(you), tuple(opp), extra_turn


def _terminal_score(you, opp):
    """Score (you_store - opp_store) when the game is over."""
    # opponent takes all remaining seeds
    opp_store = opp[6] + sum(opp[:6])
    return you[6] - opp_store


# ---------- Minimax with memoisation ----------
@lru_cache(maxsize=None)
def _solve(you, opp):
    """
    Return (best_value, best_move) for the player whose turn it is,
    where `you` is the current player and `opp` the opponent.
    """
    # No legal move -> game ends, opponent gathers remaining seeds
    if sum(you[:6]) == 0:
        return _terminal_score(you, opp), None

    best_val = -float('inf')
    best_move = None

    for house in range(6):
        if you[house] == 0:
            continue
        n_you, n_opp, extra = _simulate_move(you, opp, house)

        if extra:
            # same player moves again
            val, _ = _solve(n_you, n_opp)
        else:
            # opponent's turn: swap perspective, invert sign
            opp_val, _ = _solve(n_opp, n_you)
            val = -opp_val

        if val > best_val:
            best_val = val
            best_move = house

    return best_val, best_move


# ---------- Public API ----------
def policy(you, opponent):
    """
    Return the index (0‑5) of the chosen house.
    `you` and `opponent` are lists of length 7 as described in the task.
    """
    # Convert to tuples for caching
    you_t = tuple(you)
    opp_t = tuple(opponent)

    _, move = _solve(you_t, opp_t)

    # The search is exhaustive, so `move` is always valid.
    # Defensive fallback (should never trigger):
    if move is None:
        for i in range(6):
            if you[i] > 0:
                return i
    return move
