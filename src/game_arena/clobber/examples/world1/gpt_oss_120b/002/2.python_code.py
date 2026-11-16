
import copy
from typing import List, Tuple

# Directions: (delta row, delta col, letter)
DIRS: List[Tuple[int, int, str]] = [
    (-1, 0, 'U'),
    (0, 1, 'R'),
    (1, 0, 'D'),
    (0, -1, 'L')
]

def _legal_moves(you: List[List[int]], opponent: List[List[int]]) -> List[Tuple[int, int, str]]:
    """Return a list of all legal moves for the player whose pieces are in `you`."""
    moves = []
    rows, cols = len(you), len(you[0])
    for r in range(rows):
        for c in range(cols):
            if you[r][c] != 1:
                continue
            for dr, dc, dletter in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and opponent[nr][nc] == 1:
                    moves.append((r, c, dletter))
    return moves

def _apply_move(you: List[List[int]], opponent: List[List[int]],
                move: Tuple[int, int, str]) -> Tuple[List[List[int]], List[List[int]]]:
    """Return new board copies after applying `move` for player `you`."""
    r, c, d = move
    # Find delta for direction
    dr, dc = next((dr, dc) for dr, dc, dl in DIRS if dl == d)
    nr, nc = r + dr, c + dc

    # Deep copy the board (small board, cheap)
    new_you = [row[:] for row in you]
    new_opponent = [row[:] for row in opponent]

    # Move piece
    new_you[r][c] = 0          # start square becomes empty
    new_opponent[nr][nc] = 0   # captured opponent piece removed
    new_you[nr][nc] = 1        # our piece lands here
    return new_you, new_opponent

def policy(you: List[List[int]], opponent: List[List[int]]) -> int:
    """
    Choose a legal Clobber move for the player represented by `you`.

    Returns
    -------
    str
        Move encoded as "row,col,dir".
    """
    # 1. Gather all our legal moves
    my_moves = _legal_moves(you, opponent)

    # The problem guarantees at least one move exists.
    best_move = my_moves[0]
    min_opp_moves = None

    for move in my_moves:
        # 2. Simulate the move
        new_you, new_opp = _apply_move(you, opponent, move)

        # 3. Count opponent's possible captures on the resulting board
        #   (swap roles because opponent will move next)
        opp_moves = _legal_moves(new_opp, new_you)
        opp_count = len(opp_moves)

        # 4. Keep move that minimizes opponent's options
        if (min_opp_moves is None) or (opp_count < min_opp_moves):
            min_opp_moves = opp_count
            best_move = move

            # Early exit: if we can leave the opponent with zero moves, we win immediately.
            if min_opp_moves == 0:
                break

    # 5. Format the selected move
    r, c, d = best_move
    return f"{r},{c},{d}"
