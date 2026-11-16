
import numpy as np
from typing import Tuple, List
import random

# Directions for searching possible flips
DIRS: List[Tuple[int, int]] = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if not (dr == 0 and dc == 0)]
CORNERS: List[Tuple[int, int]] = [(0, 0), (0, 7), (7, 0), (7, 7)]

def legal_moves(you: np.ndarray, opponent: np.ndarray) -> List[Tuple[int, int]]:
    """Return all legal moves for the player whose discs are stored in `you`."""
    moves: List[Tuple[int, int]] = []
    for r in range(8):
        for c in range(8):
            if you[r, c] == 0 and opponent[r, c] == 0:
                for dr, dc in DIRS:
                    flips = []
                    step = 1
                    while True:
                        nr = r + dr * step
                        nc = c + dc * step
                        if not (0 <= nr < 8 and 0 <= nc < 8):
                            break
                        piece = opponent[nr, nc]
                        if piece == 0:
                            break
                        if piece == 1:
                            flips.append((nr, nc))
                        else:
                            break
                    if flips:
                        moves.append((r, c))
                        break
    return moves

def apply_move(you: np.ndarray, opponent: np.ndarray, move: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
    """Place a disc for `you` at `move` and flip opponent discs where appropriate."""
    r, c = move
    new_you = you.copy()
    new_opp = opponent.copy()
    new_you[r, c] = 1  # place own disc

    for dr, dc in DIRS:
        flips = []
        step = 1
        while True:
            nr = r + dr * step
            nc = c + dc * step
            if not (0 <= nr < 8 and 0 <= nc < 8):
                break
            piece = opponent[nr, nc]
            if piece == 0:
                break
            if piece == 1:
                flips.append((nr, nc))
            else:
                break
        if flips:
            for nr, nc in flips:
                new_you[nr, nc] = 1
                new_opp[nr, nc] = 0
    return new_you, new_opp

def evaluate(you: np.ndarray, opponent: np.ndarray) -> int:
    """Simple static evaluation: disc difference + mobility + corner weighting."""
    disc_diff = np.sum(you) - np.sum(opponent)

    my_moves = len(legal_moves(you, opponent))
    opp_moves = len(legal_moves(opponent, you))
    mobility = my_moves - opp_moves

    corner_score = 0
    for r, c in CORNERS:
        if you[r, c]:
            corner_score += 10
        elif opponent[r, c]:
            corner_score -= 10

    # A very light stability bonus (only flips that happen in the simulation)
    # can be ignored; corners and mobility are enough for depth‑2 play.
    return disc_diff + mobility + corner_score

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Return the next move as an algebraic notation string or \"pass\"."""
    my_moves = legal_moves(you, opponent)
    if not my_moves:
        return "pass"

    best_score = -float('inf')
    tied_moves: List[Tuple[int, int]] = []

    # For each candidate move we evaluate the opponent’s best reply (two‑ply depth)
    for mv in my_moves:
        board_me, board_op = apply_move(you, opponent, mv)

        opp_moves = legal_moves(board_op, board_me)  # opponent’s turn
        if not opp_moves:
            # opponent will pass
            score = evaluate(board_me, board_op)
        else:
            # Assume opponent chooses the move that maximises his own gain
            opp_scores = []
            for opp_mv in opp_moves:
                # opponent makes a move
                board_me_after, board_op_after = apply_move(board_op, board_me, opp_mv)
                # now it is our turn again – evaluate from our perspective
                leaf_score = evaluate(board_me_after, board_op_after)
                opp_scores.append(leaf_score)
            # opponent’s best (worst for us) reply
            best_opp_index = np.argmax(opp_scores)
            score = opp_scores[best_opp_index]

        # Update best move list
        if score > best_score:
            best_score = score
            tied_moves = [mv]
        elif score == best_score:
            tied_moves.append(mv)

    # Random tie‑break among equally scoring moves
    chosen_move = random.choice(tied_moves)
    file = chr(ord('a') + chosen_move[1])
    rank = chosen_move[0] + 1
    return f"{file}{rank}"
