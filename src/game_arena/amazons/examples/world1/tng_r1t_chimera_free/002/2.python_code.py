
import numpy as np
import random

def policy(board) -> str:
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0),
                  (1, 1), (1, -1), (-1, 1), (-1, -1)]
    legal_moves = []

    # Iterate through each cell to find my amazons
    for from_r in range(6):
        for from_c in range(6):
            if board[from_r, from_c] == 1:
                # Generate all valid to positions
                to_positions = []
                for dr, dc in directions:
                    nr, nc = from_r + dr, from_c + dc
                    while 0 <= nr < 6 and 0 <= nc < 6:
                        if board[nr, nc] != 0:
                            break
                        to_positions.append((nr, nc))
                        nr += dr
                        nc += dc

                # Process each to position for arrow shots
                for (to_r, to_c) in to_positions:
                    temp_board = board.copy()
                    temp_board[from_r, from_c] = 0
                    temp_board[to_r, to_c] = 1

                    # Generate all valid arrow positions
                    arrow_positions = []
                    for dr, dc in directions:
                        ar, ac = to_r + dr, to_c + dc
                        while 0 <= ar < 6 and 0 <= ac < 6:
                            if temp_board[ar, ac] != 0:
                                break
                            arrow_positions.append((ar, ac))
                            ar += dr
                            ac += dc

                    # Create move strings
                    for arrow_r, arrow_c in arrow_positions:
                        move = f"{from_r},{from_c}:{to_r},{to_c}:{arrow_r},{arrow_c}"
                        legal_moves.append(move)

    # Return a random legal move
    return random.choice(legal_moves)
