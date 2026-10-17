
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    you_board = np.array(you)
    opponent_board = np.array(opponent)

    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

    for row in range(5):
        for col in range(6):
            if you_board[row, col] == 1:
                for dr, dc, dir in directions:
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < 5 and 0 <= new_col < 6:
                        if opponent_board[new_row, new_col] == 1:
                            return f"{row},{col},{dir}"

    raise ValueError("No legal move found, but problem guarantees at least one exists.")
