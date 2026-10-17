
from typing import List

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def evaluate(you: List[int], opponent: List[int]) -> int:
    """
    Simple heuristic:
    * total seeds owned by the player whose turn it is (sum(you) – sum(opponent))
    * +1 for each empty house of the player (capture potential)
    * -1 for each empty house of the opponent (removes capture potential)
    """
    # total seeds owned by the current player
    advantage = sum(you) - sum(opponent)
    # empty house bonuses
    advantage += sum(1 for v in you[:6] if v == 0)  # your empty houses
    advantage -= sum(1 for v in opponent[:6] if v == 0)  # opponent empty houses
    return advantage


def simulate_one_move(you: List[int], opponent: List[int], move: int) -> (List[int], List[int]):
    """
    Perform a single sowing from `move` (0‑5, `you[move] > 0`).
    Returns the new you‑board and opponent‑board after:
      – moving all seeds,
      – possible capture,
      – no extra handling of subsequent extra moves (they will be handled by recursion).
    """
    # deep copy of both sides
    new_you = you[:]
    new_opp = opponent[:]
    seeds = new_you[move]
    new_you[move] = 0          # remove the seeds from the chosen house

    # board positions (0‑5 = your houses, 6 = your store,
    # 7‑12 = opponent houses). Index 13 (opp store) is never used.
    # We walk clockwise using modulo 13.
    pos = move
    capture_this_move = False
    last_pos = None

    while seeds > 0:
        pos_mod = pos % 13
        if pos_mod <= 5:                     # your houses
            bucket_val = new_you[pos_mod]
            bucket_val += 1
            # capture detection: empty house *and* this is the last seed
            if bucket_val == 1 and seeds == 1:
                capture_this_move = True
                last_pos = pos_mod
            new_you[pos_mod] = bucket_val
        elif pos_mod == 6:                   # your store
            bucket_val = new_you[6] + 1
            new_you[6] = bucket_val
        else:                               # opponent houses 7‑12
            bucket_idx = pos_mod - 6
            bucket_val = new_opp[bucket_idx] + 1
            new_opp[bucket_idx] = bucket_val

        seeds -= 1
        pos += 1

    # ----- capture ----------------------------------------------------
    if capture_this_move and last_pos <= 5 and new_opp[5 - last_pos] > 0:
        # all seeds from both houses go to your store
        capture_amount = new_you[last_pos] + new_opp[5 - last_pos]
        new_you[6] += capture_amount
        new_you[last_pos] = 0
        new_opp[5 - last_pos] = 0

    return new_you, new_opp


# ----------------------------------------------------------------------
# Depth‑limited minimax
# ----------------------------------------------------------------------
def minimax(you: List[int], opponent: List[int], depth: int, is_you_turn: bool) -> int:
    """
    Return the evaluation from the perspective of the player who is to move.
    depth = remaining number of moves (including extra moves) to consider.
    is_you_turn == True  → you are moving (maximise your advantage)
    is_you_turn == False → opponent is moving (minimise your advantage)
    """
    # termination condition: opponent has no seeds in any house → game ends.
    opponent_houses = opponent[:6]
    if all(v == 0 for v in opponent_houses):
        return evaluate(you, opponent)

    if depth == 0:
        # Evaluate with static heuristic
        if is_you_turn:
            return evaluate(you, opponent)
        else:
            # flip sign because opponent’s advantage is our loss
            return -evaluate(you, opponent)

    # Choose the player's legal moves
    if is_you_turn:
        moves = [(i, you[i]) for i in range(7) if you[i] > 0 and i <= 5]
    else:
        moves = [(i, opponent[i]) for i in range(7) if opponent[i] > 0 and i <= 5]

    # Prefer moves with more seeds (heuristic pruning)
    moves.sort(key=lambda x: x[1], reverse=True)

    if is_you_turn:
        best_score = -float('inf')
        for idx, _ in moves:
            new_you, new_opp = simulate_one_move(you, opponent, idx)
            # opponent gets a response
            score = minimax(new_you, new_opp, depth - 1, False)
            if score > best_score:
                best_score = score
        return best_score
    else:
        best_score = float('inf')
        for idx, _ in moves:
            new_you, new_opp = simulate_one_move(you, opponent, idx)
            # you respond
            score = minimax(new_you, new_opp, depth - 1, True)
            if score < best_score:
                best_score = score
        return best_score


# ----------------------------------------------------------------------
# Main policy function required by the arena
# ----------------------------------------------------------------------
def policy(you: List[int], opponent: List[int]) -> int:
    """
    Return the index (0‑5) of the best legal move for the current player.
    The move is chosen using a 3‑move lookahead minimax search.
    """
    # Ensure a legal move exists (as promised by the problem statement)
    legal_moves = [i for i in range(7) if you[i] > 0 and i <= 5]

    # Depth = 3 moves (≈ a few extra moves per side) is enough for quick decisions.
    best_move = None
    best_eval = -float('inf')

    # Explore moves in order of decreasing house size (a quick pruning heuristic)
    for idx, _ in sorted([(i, you[i]) for i in legal_moves if you[i] > 0], key=lambda x: -x[1]):
        new_you, new_opp = simulate_one_move(you, opponent, idx)
        # opponent will reply, we ask minimax to estimate the outcome from our perspective
        score = minimax(new_you, new_opp, depth=3, is_you_turn=False)
        if score > best_eval:
            best_eval = score
            best_move = idx

    return best_move
