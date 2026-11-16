
import random
from copy import deepcopy

ROWS, COLS = 5, 6
DIRS = {'U': (-1, 0), 'R': (0, 1), 'D': (1, 0), 'L': (0, -1)}

def _in_bounds(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS

def _legal_moves(you, opp):
    """Return list of (r, c, d) legal moves for player 'you' against 'opp'."""
    moves = []
    for r in range(ROWS):
        for c in range(COLS):
            if you[r][c] != 1:
                continue
            for d, (dr, dc) in DIRS.items():
                nr, nc = r + dr, c + dc
                if _in_bounds(nr, nc) and opp[nr][nc] == 1:
                    moves.append((r, c, d))
    return moves

def _apply_move(you, opp, move):
    """Return new (you, opp) boards after performing *move*."""
    r, c, d = move
    dr, dc = DIRS[d]
    nr, nc = r + dr, c + dc
    # copy boards
    you2 = [row[:] for row in you]
    opp2 = [row[:] for row in opp]
    # move our piece
    you2[r][c] = 0
    you2[nr][nc] = 1
    # remove captured opponent piece
    opp2[nr][nc] = 0
    return you2, opp2

def policy(you, opponent):
    """
    Return a legal move string 'row,col,dir' for the current player.
    The move is chosen by a one‑ply look‑ahead that minimises the opponent's
    number of possible captures.
    """
    # 1️⃣ enumerate our legal captures
    my_moves = _legal_moves(you, opponent)
    if not my_moves:
        # No legal move – return a dummy (cannot happen in a legal game state)
        return "0,0,U"

    best_move = None
    best_score = None          # lower is better (opponent's move count)
    best_my_moves = -1

    for mv in my_moves:
        # simulate our move
        you2, opp2 = _apply_move(you, opponent, mv)
        # opponent's legal moves after our move
        opp_moves = _legal_moves(opp2, you2)   # note swapped roles
        score = len(opp_moves)

        # tie‑breaker: keep the move that leaves us with most moves
        my_moves_after = len(_legal_moves(you2, opp2))

        if (best_score is None or
            score < best_score or
            (score == best_score and my_moves_after > best_my_moves)):
            best_move = mv
            best_score = score
            best_my_moves = my_moves_after

    r, c, d = best_move
    return f"{r},{c},{d}"
