
import sys
from typing import List, Tuple

# ----------------------------------------------------------------------
# Constants
HOUSE_COUNT = 6                 # number of pits on each side
TOTAL_SLOTS = 14                # 6 pits + your store + 6 opponent pits + opponent store

# ----------------------------------------------------------------------
def _apply_move(board: List[int], start_idx: int, is_you_turn: bool) -> List[int]:
    """
    Perform one sowing move (including possible captures) and any subsequent
    extra moves when `is_you_turn` is True.
    The board is mutated and returned as a new list.
    """
    b = board[:]                       # work on a copy
    if b[start_idx] == 0:              # illegal call – never happens in the policy
        return b

    # Store / opposite house indices
    if start_idx < 7:                   # our side
        opp_idx = 7 + (5 - start_idx)    # opponent’s opposite pit
        store_idx = 6
    else:                              # opponent’s side
        opp_idx = 12 - start_idx        # opposite pit on our side
        store_idx = 13

    orig = b[start_idx]                # seeds taken from the start pit
    b[start_idx] = 0                   # empty the start pit

    pos = (start_idx + 1) % TOTAL_SLOTS
    remaining = orig
    last_drop = None

    while remaining > 0:
        # skip opponent’s store
        if pos == 13:
            pos = (pos + 1) % TOTAL_SLOTS
            continue

        # drop a seed
        b[pos] += 1
        last_drop = pos
        remaining -= 1
        pos = (pos + 1) % TOTAL_SLOTS

        # capture if the seed landed back on the start pit and the opposite pit is not empty
        if last_drop == start_idx and b[opp_idx] > 0:
            captured = b[opp_idx]        # seeds from opposite pit
            b[store_idx] += captured + 1  # include the seed just placed
            b[last_drop] = 0             # the start pit becomes empty again
            b[opp_idx] = 0               # opposite pit emptied
            remaining -= captured         # we no longer have to sow those seeds
            pos = (start_idx + 1) % TOTAL_SLOTS  # continue sowing from the next pit
            continue

    # ---- extra‑move handling (only for us) ------------------------------
    if is_you_turn:
        if last_drop == store_idx:        # last seed landed in our store → another turn
            while True:
                # find any non‑empty pit on our side (0‑5)
                extra_i = None
                for i in range(HOUSE_COUNT):
                    if b[i] > 0:
                        extra_i = i
                        break
                if extra_i is None:
                    break
                # recursively apply the next move (still our turn)
                b = _apply_move(b, extra_i, is_you_turn=True)

    return b


def _is_your_turn_over(board: List[int]) -> bool:
    """True if all of your pits are empty."""
    return sum(board[:HOUSE_COUNT]) == 0


def _is_opponent_turn_over(board: List[int]) -> bool:
    """True if all of opponent’s pits are empty."""
    return sum(board[HOUSE_COUNT:]) == 0


def _evaluate(board_tuple: Tuple[int, ...]) -> int:
    """
    Terminal heuristic:
    - If we have no pits left, the opponent collects all his remaining seeds.
    - If the opponent has no pits left, we collect all our seeds.
    The returned value is our store minus opponent’s store (higher = win).
    """
    board = list(board_tuple)
    if _is_your_turn_over(board):
        # opponent’s last turn – he automatically moves all his seeds into his store
        board[13] += sum(board[HOUSE_COUNT:])   # houses 7‑12
        board[HOUSE_COUNT:] = [0] * HOUSE_COUNT
    elif _is_opponent_turn_over(board):
        # our last turn – move all our seeds into our store
        board[6] += sum(board[:HOUSE_COUNT])     # pits 0‑5
        board[:HOUSE_COUNT] = [0] * HOUSE_COUNT
    return board[6] - board[13]


def _alphabeta(board_tuple: Tuple[int, ...],
               turn: int,
               depth: int,
               alpha: float,
               beta: float) -> Tuple[int, int]:
    """
    Depth‑limited α‑β search.
    `turn == 0` → it is our move, `turn == 1` → opponent’s move.
    Returns (best_score, best_move_index) where best_move_index is always legal.
    """
    board = list(board_tuple)

    if depth == 0 or _is_your_turn_over(board) or _is_opponent_turn_over(board):
        return _evaluate(board_tuple), None

    if turn == 0:                      # we move
        best_score = -float('inf')
        best_move = None
        for i in range(HOUSE_COUNT):
            if board[i] > 0:
                new_board = _apply_move(board, i, is_you_turn=True)
                new_board_tuple = tuple(new_board)
                score = _alphabeta(new_board_tuple,
                                  turn=1,
                                  depth=depth - 1,
                                  alpha=alpha,
                                  beta=beta)[0]
                if score > best_score:
                    best_score = score
                    best_move = i
                alpha = max(alpha, best_score)
                if alpha >= beta:      # pruning
                    break
        return best_score, best_move
    else:                              # opponent moves
        best_score = float('inf')
        best_move = None
        for i in range(HOUSE_COUNT, TOTAL_SLOTS):
            if board[i] > 0:
                new_board = _apply_move(board, i, is_you_turn=False)
                new_board_tuple = tuple(new_board)
                score = _alphabeta(new_board_tuple,
                                  turn=0,
                                  depth=depth - 1,
                                  alpha=alpha,
                                  beta=beta)[0]
                if score < best_score:
                    best_score = score
                    best_move = i
                beta = min(beta, best_score)
                if beta <= alpha:      # pruning
                    break
        return best_score, best_move


def policy(you: List[int], opponent: List[int]) -> int:
    """
    Required API – returns a legal house index (0 ≤ i ≤ 5) for us to sow.
    """
    # combine both sides into a single 14‑slot board
    full_board = you + opponent
    # search depth 5 is enough to beat most baseline opponents while staying well under 1 s
    MAX_DEPTH = 5

    best_score, best_move = _alphabeta(tuple(full_board),
                                      turn=0,
                                      depth=MAX_DEPTH,
                                      alpha=-float('inf'),
                                      beta=float('inf'))

    # `best_move` is guaranteed to be a legal index because the arena only
    # calls `policy` when at least one move exists.
    return best_move
