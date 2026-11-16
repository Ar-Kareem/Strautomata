
import sys
from functools import lru_cache

# Lines that constitute a win (indices 0‑8, row‑major order)
LINES = [(0, 1, 2),
         (3, 4, 5),
         (6, 7, 8),
         (0, 3, 6),
         (1, 4, 7),
         (2, 5, 8),
         (0, 4, 8),
         (2, 4, 6)]

def opponent(player: str) -> str:
    """Return the other player ('x' <-> 'o')."""
    return 'o' if player == 'x' else 'x'

def is_line(board, idx, player):
    """Check whether placing `player` at `idx` completes a line."""
    for a, b, c in LINES:
        if idx in (a, b, c):
            if board[a] == board[b] == board[c] == player:
                return True
    return False

def empty_indices(board):
    """Return list of empty cell indices."""
    return [i for i, cell in enumerate(board) if cell == 'b']

@lru_cache(maxsize=None)
def solve(board_tuple, player):
    """
    Minimax solver for the current board and player to move.
    Returns:
        1  – player to move can force a win (opponent will be the first to make a line)
       -1  – player to move will be forced to make a line (opponent can force a win)
        0  – draw
    """
    # Terminal: board full -> draw
    if all(cell != 'b' for cell in board_tuple):
        return 0

    best = -2  # worse than any legal value
    for idx in empty_indices(board_tuple):
        # simulate move
        new_board = list(board_tuple)
        new_board[idx] = player

        # immediate loss if the move creates a line
        if is_line(new_board, idx, player):
            val = -1
        else:
            child = solve(tuple(new_board), opponent(player))
            # invert child's result because we view from opposite perspective
            if child == 1:
                val = -1
            elif child == -1:
                val = 1
            else:
                val = 0

        if val > best:
            best = val
            if best == 1:          # can't improve beyond a sure win
                break
    return best

def policy(state, role):
    """
    Stanford GameMaster policy for the 'suicide' game.
    state – list of facts (e.g. ["cell","1","1","b"])
    role  – "x" or "o"
    Returns a legal action string such as "mark(1,1)".
    """
    # Build a 9‑cell board (row‑major).  Empty cells are 'b'.
    board = ['b'] * 9
    for fact in state:
        if fact[0] == 'cell':
            r = int(fact[1]) - 1   # convert to 0‑based
            c = int(fact[2]) - 1
            mark = fact[3]
            board[r * 3 + c] = mark

    empties = empty_indices(board)
    if not empties:
        # No legal moves (should not happen in a real game state)
        return "mark(1,1)"  # fallback – will likely be ignored

    best_move = None
    best_val = -2

    for idx in empties:
        # simulate placing `role` at idx
        new_board = board.copy()
        new_board[idx] = role

        if is_line(new_board, idx, role):
            val = -1                     # immediate loss
        else:
            child = solve(tuple(new_board), opponent(role))
            if child == 1:
                val = -1
            elif child == -1:
                val = 1
            else:
                val = 0

        if val > best_val:
            best_val = val
            best_move = idx
            if best_val == 1:            # winning move found
                break

    # Convert index back to 1‑based row/col for the output format
    row = best_move // 3 + 1
    col = best_move % 3 + 1
    return f"mark({row},{col})"
