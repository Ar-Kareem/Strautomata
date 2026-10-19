
import numpy as np
import random

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Othello policy that prioritizes corners and maximizing flips."""

    def get_legal_moves(board, player, opponent):
        """Finds all legal moves for a given player."""
        moves = []
        for r in range(8):
            for c in range(8):
                if board[r][c] == 0 and opponent[r][c] == 0:
                    if is_legal_move(board, player, opponent, r, c):
                        moves.append((r, c))
        return moves

    def is_legal_move(board, player, opponent, row, col):
        """Checks if a move is legal."""
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                if dr == 0 and dc == 0:
                    continue
                if is_valid_direction(board, player, opponent, row, col, dr, dc):
                    return True
        return False

    def is_valid_direction(board, player, opponent, row, col, dr, dc):
        """Checks if a direction results in a flip."""
        r, c = row + dr, col + dc
        if 0 <= r < 8 and 0 <= c < 8 and opponent[r][c] == 1:
            r += dr
            c += dc
            while 0 <= r < 8 and 0 <= c < 8:
                if player[r][c] == 1:
                    return True
                if board[r][c] == 0 and opponent[r][c] == 0:
                    return False
                r += dr
                c += dc
        return False

    def flip_discs(board, player, opponent, row, col):
        """Flips discs resulting from a move."""
        flipped = []
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                if dr == 0 and dc == 0:
                    continue
                if is_valid_direction(board, player, opponent, row, col, dr, dc):
                    r, c = row + dr, col + dc
                    to_flip = []
                    while 0 <= r < 8 and 0 <= c < 8 and opponent[r][c] == 1:
                        to_flip.append((r, c))
                        r += dr
                        c += dc
                    if 0 <= r < 8 and 0 <= c < 8 and player[r][c] == 1:
                        flipped.extend(to_flip)
        return flipped

    def count_flips(board, player, opponent, row, col):
        """Counts the number of flips a move would result in."""
        return len(flip_discs(board, player, opponent, row, col))

    board = np.zeros((8, 8), dtype=int)
    board[you == 1] = 1
    board[opponent == 1] = 2

    legal_moves = get_legal_moves(board, you, opponent)

    if not legal_moves:
        return "pass"

    # 1. Corner Preference
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    for corner in corners:
        if corner in legal_moves:
            row, col = corner
            return chr(col + ord('a')) + str(row + 1)

    # 2. Maximize Flips
    best_move = None
    max_flips = -1
    for row, col in legal_moves:
        flips = count_flips(board, you, opponent, row, col)
        if flips > max_flips:
            max_flips = flips
            best_move = (row, col)

    if best_move:
        row, col = best_move
        return chr(col + ord('a')) + str(row + 1)
    else:
        # Should not happen, but just in case
        row, col = legal_moves[0]
        return chr(col + ord('a')) + str(row + 1)
