
import random
from copy import deepcopy
from typing import List, Tuple

# Board dimensions
ROWS, COLS = 5, 6

# Directions: (delta row, delta col, label)
DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]


def generate_moves(you: List[List[int]], opp: List[List[int]]) -> List[Tuple[int, int, str]]:
    """Return a list of all legal moves for the player `you`."""
    moves = []
    for r in range(ROWS):
        for c in range(COLS):
            if you[r][c] != 1:
                continue
            for dr, dc, dlab in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS and opp[nr][nc] == 1:
                    moves.append((r, c, dlab))
    return moves


def apply_move(you: List[List[int]], opp: List[List[int]],
               move: Tuple[int, int, str]) -> Tuple[List[List[int]], List[List[int]]]:
    """Return new board after `you` performs `move`."""
    r, c, dlab = move
    # locate destination using direction label
    dr, dc = next((dr, dc) for dr, dc, lab in DIRS if lab == dlab)
    nr, nc = r + dr, c + dc

    # deepcopy to avoid mutating original boards
    new_you = deepcopy(you)
    new_opp = deepcopy(opp)

    # source becomes empty
    new_you[r][c] = 0
    # capture opponent piece
    new_opp[nr][nc] = 0
    # our piece occupies destination
    new_you[nr][nc] = 1

    return new_you, new_opp


def count_legal_moves(you: List[List[int]], opp: List[List[int]]) -> int:
    """Count how many captures `you` could make on the given board."""
    return len(generate_moves(you, opp))


def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    """
    Choose a capture that minimises the opponent's number of legal moves
    after the capture.
    """
    legal_moves = generate_moves(you, opponent)

    if not legal_moves:
        # No legal move – this should not happen in a valid position,
        # but we must return a string. Return a dummy illegal move.
        return "0,0,U"

    # Evaluate each move
    best_moves = []
    best_score = None  # minimal opponent move count

    for mv in legal_moves:
        new_you, new_opp = apply_move(you, opponent, mv)
        # After our move, opponent becomes the player to move
        opp_move_count = count_legal_moves(new_opp, new_you)

        if best_score is None or opp_move_count < best_score:
            best_score = opp_move_count
            best_moves = [mv]
        elif opp_move_count == best_score:
            best_moves.append(mv)

    # Pick randomly among equally good moves
    chosen = random.choice(best_moves)
    r, c, d = chosen
    return f"{r},{c},{d}"
