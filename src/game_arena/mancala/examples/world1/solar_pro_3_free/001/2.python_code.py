
from typing import List, Tuple

# -------------------------------------------------
# Helper functions for Kalah
# -------------------------------------------------
RING_SIZE = 13  # 6 your pits + 1 your store + 6 opponent pits

def apply_one_move(
    moving: List[int],
    opponent: List[int],
    start: int,
) -> Tuple[List[int], List[int]]:
    """
    Apply a single move for the player whose board is `moving`.
    Does NOT handle extra moves; only the immediate sowing and possible capture.
    """
    seeds = moving[start]
    if seeds == 0:
        raise ValueError("Attempted to move from an empty pit (illegal).")
    new_moving = moving[:]
    new_moving[start] = 0
    idx = start

    for _ in range(seeds):
        idx = (idx + 1) % RING_SIZE
        if idx < 6:
            new_moving[idx] += 1          # your own pits
        elif idx == 6:
            new_moving[6] += 1            # your own store (you get seeds here)
        else:  # idx 7..12  → opponent pits
            new_opponent = opponent[:]
            new_opponent[idx - 7] += 1

    # capture detection
    last_idx = idx - 1
    if last_idx == start and opponent[5 - start] > 0:
        # last seed landed in your pit `start` (which is now empty) and the opposite pit
        # of the opponent has seeds → capture everything into your store
        capture = new_moving[start] + opponent[5 - start]
        new_moving[6] += capture
        new_moving[start] = 0
        opponent[5 - start] = 0

    return new_moving, opponent


def simulate_one_turn(
    moving: List[int],
    opponent: List[int],
) -> Tuple[List[int], List[int]]:
    """
    Simulate a full turn for `moving` (including extra moves).
    Returns the board state after the turn finishes.
    """
    # Choose the first legal pit (you are always allowed to move)
    start_move = None
    for m in range(6):
        if moving[m] > 0:
            start_move = m
            break
    if start_move is None:
        raise RuntimeError("No legal move found – should never happen in policy.")

    new_moving, new_opponent = apply_one_move(moving, opponent, start_move)

    # Handle extra moves if we landed a seed in our own store
    while new_moving[6] > 0:
        # pick next legal house (smallest index)
        next_move = None
        for m in range(6):
            if new_moving[m] > 0:
                next_move = m
                break
        if next_move is None:
            break
        new_moving, new_opponent = apply_one_move(new_moving, new_opponent, next_move)

    return new_moving, new_opponent


def evaluate(you: List[int], opponent: List[int]) -> int:
    """
    Simple evaluation: difference in store totals.
    Positive → you ahead, negative → opponent ahead.
    """
    return you[6] - opponent[6]


def simulate_final(
    you: List[int],
    opponent: List[int],
    start_move: int,
) -> Tuple[List[int], List[int]]:
    """
    Simulate your turn (with start_move) followed by the opponent's optimal response.
    Returns the final board after opponent's best reply.
    """
    # Your turn
    after_you, after_opp = simulate_one_turn(you, opponent)

    # Opponent's legal moves (on his own houses)
    opp_moves = [i for i in range(6) if after_opp[i] > 0]

    if not opp_moves:  # opponent exhausted → game ends
        return after_you, after_opp

    # Opponent's best response (minimises your store‑difference)
    best_score = float('inf')
    best_board = None
    for om in opp_moves:
        # opponent moves using his board as `moving` and your board as `opponent`
        after_opp_you, after_opp_opp = simulate_one_turn(after_opp, after_you)
        score = evaluate(after_opp_you, after_opp_opp)
        if score < best_score:
            best_score = score
            best_board = (after_opp_you, after_opp_opp)

    return best_board if best_board else (after_you, after_opp)


def policy(you: List[int], opponent: List[int]) -> int:
    """
    Main API: returns a legal move index for the player to move.
    Implements a one‑move look‑ahead that prefers captures.
    """
    legal_moves = [i for i in range(6) if you[i] > 0]

    # Prefer moves that capture everything immediately
    capture_moves = []
    for i in legal_moves:
        seeds = you[i]
        if seeds % RING_SIZE == 0 and opponent[5 - i] > 0:
            capture_amount = seeds + opponent[5 - i]
            capture_moves.append((i, capture_amount))

    if capture_moves:
        # Choose the capture that yields the most seeds in your store
        capture_moves.sort(key=lambda x: -x[1])
        return capture_moves[0][0]

    # No immediate captures – evaluate each legal move with opponent lookahead
    final_scores = []
    final_boards = []
    for i in legal_moves:
        final_board = simulate_final(you, opponent, start_move=i)
        final_score = evaluate(*final_board)
        final_scores.append(final_score)
        final_boards.append(final_board)

    # Pick the move with highest score (opponent's best reply)
    best_score = max(final_scores)
    # Resolve ties by smallest index
    for i, score in enumerate(final_scores):
        if score == best_score:
            return i
