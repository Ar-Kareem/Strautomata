
from typing import List

def simulate_move(you: List[int], opponent: List[int], move: int) -> (List[int], List[int], bool):
    """Apply a sowing move from house `move` (0..5) on the given board.

    Returns:
        new_you      – the board after the move for the player who just moved,
        new_opp      – the opponent’s board after the move,
        extra        – True if the last seed landed in the moving player's store.
    """
    # Copy the mutable inputs
    new_you = you[:]       # length 7 list
    new_opp = opponent[:]  # length 7 list

    seeds = new_you[move]          # number of seeds to distribute
    new_you[move] = 0              # clear the source house
    pos = move                     # current position on a 14‑slot circle (0..13)

    # The 14‑slot circle consists of:
    #   0‑5 : your houses
    #   6   : your store
    #   7‑12: opponent houses
    #   13  : opponent store (always skipped when sowing)
    while seeds > 0:
        pos = (pos + 1) % 14
        if pos == 13:                     # skip opponent's store
            seeds -= 1
            continue
        if pos <= 5:                       # your house
            new_you[pos] += 1
        elif pos == 6:                     # your store
            new_you[6] += 1
        else:                              # opponent house (7‑12)
            new_opp[pos - 7] += 1
        seeds -= 1

    extra_move = (pos == 6)                # last seed fell in your store

    # Capture rule – only the last seed can capture
    if 0 <= pos <= 5:
        # Was the house empty before the final seed?
        if new_you[pos] == 1:
            opp_house = 5 - pos
            if new_opp[opp_house] > 0:
                captured = 1 + new_opp[opp_house]
                new_you[6] += captured
                new_you[pos] = 0
                new_opp[opp_house] = 0

    return new_you, new_opp, extra_move


def _terminal_value(you: List[int], opponent: List[int]) -> int:
    """Return the evaluation when the game has finished.
    All remaining seeds in houses are moved to their owner's store.
    """
    you_total = you[6] + sum(you[:6])
    opp_total = opponent[6] + sum(opponent[:6])
    return you_total - opp_total


def _minimax(you: List[int], opponent: List[int], depth: int,
             maximizing: bool,
             alpha: float = -float('inf'),
             beta: float = float('inf')) -> int:
    """Depth‑limited minimax with alpha‑beta pruning.

    `maximizing` is True when the player to move is the original 'you' side,
    False when it is the opponent side. The returned value is the
    evaluation from the original player's perspective.
    """
    # Terminal position – one side has no seeds in its houses
    if all(v == 0 for v in you[:6]) or all(v == 0 for v in opponent[:6]):
        return _terminal_value(you, opponent)

    if depth == 0:
        return you[6] - opponent[6]

    if maximizing:
        best = -float('inf')
        for i in range(6):
            if you[i] == 0:
                continue
            new_you, new_opp, extra = simulate_move(you, opponent, i)
            # After your move you retain the turn only if an extra move was earned
            next_max = extra
            val = _minimax(new_you, new_opp, depth - 1, next_max, alpha, beta)
            if val > best:
                best = val
            if val > alpha:
                alpha = val
            if beta <= alpha:          # alpha‑beta cut‑off
                break
        return best
    else:
        best = float('inf')
        for i in range(6):
            if opponent[i] == 0:
                continue
            # Simulate opponent's move (they are treated as the "you" side)
            new_opp_you, new_opp_opp, extra = simulate_move(opponent, you, i)
            # Opponent keeps the turn only on an extra move
            next_max = not extra
            val = _minimax(new_opp_opp, new_opp_you, depth - 1, next_max, alpha, beta)
            if val < best:
                best = val
            if val < beta:
                beta = val
            if beta <= alpha:
                break
        return best


def policy(you: List[int], opponent: List[int]) -> int:
    """Select a legal move for the current player.

    The policy uses a 3‑ply minimax search with alpha‑beta pruning.
    Returns an index 0..5 where `you[i] > 0`.
    """
    max_depth = 3          # can be increased to 4 if the time budget permits
    best_move = 0
    best_score = -float('inf')

    for i in range(6):
        if you[i] == 0:
            continue
        new_you, new_opp, extra = simulate_move(you, opponent, i)
        # After the move the next player is 'you' only on an extra move
        score = _minimax(new_you, new_opp, max_depth - 1, extra)
        if score > best_score:
            best_score = score
            best_move = i
    return best_move
