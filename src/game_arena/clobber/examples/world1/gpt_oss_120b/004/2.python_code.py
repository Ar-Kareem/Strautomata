
import random
from copy import deepcopy
from typing import List, Tuple

# Board dimensions
ROWS, COLS = 5, 6

# Directions: (delta_row, delta_col, label)
DIRS = [
    (-1, 0, "U"),
    (0, 1, "R"),
    (1, 0, "D"),
    (0, -1, "L"),
]

def _legal_moves(your: List[List[int]], opp: List[List[int]]) -> List[Tuple[int, int, str]]:
    """Return all legal capture moves for the player whose pieces are in `your`."""
    moves = []
    for r in range(ROWS):
        for c in range(COLS):
            if your[r][c] != 1:
                continue
            for dr, dc, dlabel in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS and opp[nr][nc] == 1:
                    moves.append((r, c, dlabel))
    return moves

def _apply_move(your: List[List[int]], opp: List[List[int]],
                move: Tuple[int, int, str]) -> Tuple[List[List[int]], List[List[int]]]:
    """Return new (your, opp) boards after performing `move`."""
    r, c, d = move
    # Determine destination cell
    dr, dc = next((dr, dc) for dr, dc, lbl in DIRS if lbl == d)
    nr, nc = r + dr, c + dc

    # Deep copy boards
    new_your = [row[:] for row in your]
    new_opp = [row[:] for row in opp]

    # Move piece
    new_your[r][c] = 0           # origin becomes empty
    new_opp[nr][nc] = 0          # captured opponent piece disappears
    new_your[nr][nc] = 1         # your piece occupies destination

    return new_your, new_opp

def _opponent_move_count(your: List[List[int]], opp: List[List[int]]) -> int:
    """Count how many captures the opponent could make on their turn."""
    # Opponent's perspective: their pieces are in `opp`, our pieces in `your`
    return len(_legal_moves(opp, your))

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    """
    Choose a capture that leaves the opponent with the fewest possible moves.
    Return the move as a string: "row,col,dir".
    """
    # Gather all legal moves for us
    moves = _legal_moves(you, opponent)

    # Defensive programming: if no move exists (should not happen in a valid call)
    if not moves:
        # Return a dummy but legal-looking move; the caller will treat it as loss.
        return "0,0,U"

    # Evaluate each move
    best_score = None
    best_moves = []

    for mv in moves:
        new_you, new_opp = _apply_move(you, opponent, mv)
        opp_cnt = _opponent_move_count(new_you, new_opp)

        # Lower opponent count is better
        if best_score is None or opp_cnt < best_score:
            best_score = opp_cnt
            best_moves = [mv]
        elif opp_cnt == best_score:
            best_moves.append(mv)

    # Pick randomly among equally good moves
    chosen = random.choice(best_moves)
    r, c, d = chosen
    return f"{r},{c},{d}"
