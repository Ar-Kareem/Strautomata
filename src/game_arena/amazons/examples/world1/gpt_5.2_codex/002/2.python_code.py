
import numpy as np
import random

# Directions for queen-like movement
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1),
              (-1, -1), (-1, 1), (1, -1), (1, 1)]

def in_bounds(r, c):
    return 0 <= r < 6 and 0 <= c < 6

def reachable_squares(board, start):
    """Return list of empty squares reachable by queen move from start."""
    r0, c0 = start
    squares = []
    for dr, dc in DIRECTIONS:
        r, c = r0 + dr, c0 + dc
        while in_bounds(r, c) and board[r, c] == 0:
            squares.append((r, c))
            r += dr
            c += dc
    return squares

def mobility(board, player):
    """Count total reachable squares for all amazons of player."""
    positions = list(zip(*np.where(board == player)))
    total = 0
    for pos in positions:
        total += len(reachable_squares(board, pos))
    return total

def generate_moves(board, player):
    """Generate all legal moves (from, to, arrow) for player."""
    moves = []
    positions = list(zip(*np.where(board == player)))
    for fr, fc in positions:
        for tr, tc in reachable_squares(board, (fr, fc)):
            # simulate move
            board[fr, fc] = 0
            board[tr, tc] = player
            for ar, ac in reachable_squares(board, (tr, tc)):
                moves.append((fr, fc, tr, tc, ar, ac))
            # undo move
            board[tr, tc] = 0
            board[fr, fc] = player
    return moves

def policy(board) -> str:
    board = board.copy()
    player = 1
    opponent = 2

    moves = generate_moves(board, player)
    if not moves:
        # Fallback: should not happen, but return any syntactically valid move
        return "0,0:0,0:0,0"

    best_score = -1e9
    best_moves = []

    for fr, fc, tr, tc, ar, ac in moves:
        # apply move
        board[fr, fc] = 0
        board[tr, tc] = player
        board[ar, ac] = -1

        score = mobility(board, player) - mobility(board, opponent)

        # undo move
        board[ar, ac] = 0
        board[tr, tc] = 0
        board[fr, fc] = player

        if score > best_score:
            best_score = score
            best_moves = [(fr, fc, tr, tc, ar, ac)]
        elif score == best_score:
            best_moves.append((fr, fc, tr, tc, ar, ac))

    fr, fc, tr, tc, ar, ac = random.choice(best_moves)
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
