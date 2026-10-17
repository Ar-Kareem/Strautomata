
import numpy as np

# directions a queen can move: N, S, W, E, NW, NE, SW, SE
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)]

def queen_moves(pos, board):
    """Return a list of reachable empty squares from pos using queen moves."""
    moves = []
    r, c = pos
    n = board.shape[0]
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < n and 0 <= nc < n:
            if board[nr, nc] != 0:          # blocked by any piece or arrow
                break
            moves.append((nr, nc))
            nr += dr
            nc += dc
    return moves

def policy(board) -> str:
    """
    Return a legal move string for the current player.
    Format: "fr,fc:tr,tc:ar,ac"
    """
    n = board.shape[0]
    # locate all our amazons
    my_positions = [(r, c) for r in range(n) for c in range(n) if board[r, c] == 1]

    for fr, fc in my_positions:
        # possible landing squares for the amazon
        for tr, tc in queen_moves((fr, fc), board):
            # simulate the move
            temp = board.copy()
            temp[fr, fc] = 0          # vacate start
            temp[tr, tc] = 1          # place amazon at destination

            # possible arrow squares from the new location
            for ar, ac in queen_moves((tr, tc), temp):
                # first legal combination found
                return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

    # Should never reach here if the position has at least one legal move.
    # Return a dummy move to satisfy the signature (will be illegal but prevents crash).
    return "0,0:0,0:0,0"
