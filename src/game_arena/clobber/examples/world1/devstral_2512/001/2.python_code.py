
import random
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    # Convert lists to numpy arrays for easier manipulation
    you_board = np.array(you).reshape(5, 6)
    opponent_board = np.array(opponent).reshape(5, 6)

    legal_moves = []

    # Directions: up, right, down, left
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

    # Iterate over all cells to find your pieces
    for row in range(5):
        for col in range(6):
            if you_board[row, col] == 1:
                # Check all four directions for opponent pieces
                for dr, dc, dir in directions:
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < 5 and 0 <= new_col < 6:
                        if opponent_board[new_row, new_col] == 1:
                            legal_moves.append((row, col, dir))

    # If no legal moves, return a dummy move (should not happen per problem statement)
    if not legal_moves:
        return "0,0,U"

    # Randomly select a legal move
    selected_move = random.choice(legal_moves)
    return f"{selected_move[0]},{selected_move[1]},{selected_move[2]}"
