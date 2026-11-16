
import numpy as np
from typing import List
import random

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    # Convert to numpy arrays for easier manipulation
    you_board = np.array(you, dtype=int)
    opponent_board = np.array(opponent, dtype=int)

    # Directions: U, R, D, L (up, right, down, left)
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    dir_chars = ['U', 'R', 'D', 'L']

    legal_moves = []

    # Iterate over all your pieces
    for row in range(5):
        for col in range(6):
            if you_board[row, col] == 1:
                # Check all four directions
                for i, (dr, dc) in enumerate(directions):
                    new_row, new_col = row + dr, col + dc
                    # Check if destination is within bounds and contains opponent piece
                    if 0 <= new_row < 5 and 0 <= new_col < 6 and opponent_board[new_row, new_col] == 1:
                        legal_moves.append((row, col, dir_chars[i]))

    # If no legal moves (shouldn't happen per problem statement)
    if not legal_moves:
        return "0,0,U"  # fallback, though problem says this won't occur

    # Score each legal move: higher if more of your pieces are adjacent to the destination
    scored_moves = []
    for move in legal_moves:
        row, col, dir_char = move
        dr, dc = next((d for d, c in zip(directions, dir_chars) if c == dir_char))
        new_row, new_col = row + dr, col + dc

        # Count adjacent your pieces to the destination (new_row, new_col)
        adjacent_you = 0
        for r in [new_row - 1, new_row, new_row + 1]:
            for c in [new_col - 1, new_col, new_col + 1]:
                if 0 <= r < 5 and 0 <= c < 6 and you_board[r, c] == 1:
                    adjacent_you += 1
        # Subtract the count of adjacent opponent pieces to the destination
        adjacent_opponent = 0
        for r in [new_row - 1, new_row, new_row + 1]:
            for c in [new_col - 1, new_col, new_col + 1]:
                if 0 <= r < 5 and 0 <= c < 6 and opponent_board[r, c] == 1:
                    adjacent_opponent += 1
        # Score is adjacent_you - adjacent_opponent
        score = adjacent_you - adjacent_opponent
        scored_moves.append((score, move))

    # Sort moves by score descending, then by randomness to break ties
    scored_moves.sort(key=lambda x: (-x[0], random.random()))
    best_move = scored_moves[0][1]

    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
