
import numpy as np

def policy(board):
    for from_row in range(6):
        for from_col in range(6):
            if board[from_row][from_col] == 1:
                # Generate all possible queen moves for this Amazon
                possible_to = []
                directions = [
                    (0, 1),  # right
                    (1, 0),  # down
                    (0, -1), # left
                    (-1, 0), # up
                    (1, 1),  # down-right
                    (1, -1), # down-left
                    (-1, 1), # up-right
                    (-1, -1) # up-left
                ]
                for dx, dy in directions:
                    step = 1
                    while True:
                        new_r = from_row + dx * step
                        new_c = from_col + dy * step
                        if new_r < 0 or new_r >= 6 or new_c < 0 or new_c >= 6:
                            break
                        if board[new_r, new_c] != 0:
                            break
                        possible_to.append((new_r, new_c))
                        step += 1
                # Check each possible move for an arrow shot
                for to_row, to_col in possible_to:
                    temp_board = np.copy(board)
                    temp_board[from_row, from_col] = 0
                    temp_board[to_row, to_col] = 1
                    # Generate arrow moves from temp position
                    arrow_moves = []
                    for dx, dy in directions:
                        step = 1
                        while True:
                            a_r = to_row + dx * step
                            a_c = to_col + dy * step
                            if a_r < 0 or a_r >= 6 or a_c < 0 or a_c >= 6:
                                break
                            val = temp_board[a_r, a_c]
                            if val != 0:
                                break
                            arrow_moves.append((a_r, a_c))
                            step += 1
                    if arrow_moves:
                        arrow = arrow_moves[0]
                        return f"{from_row},{from_col}:{to_row},{to_col}:{arrow[0]},{arrow[1]}"
    # This return is theoretically unreachable due to problem constraints
    return ""
