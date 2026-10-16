
import numpy as np

def policy(board):
    directions = [ (-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1) ]
    
    for row in range(6):
        for col in range(6):
            if board[row, col] == 1:
                for move_dir in directions:
                    step = 1
                    while True:
                        new_row = row + dir_move[0] * step
                        new_col = col + dir_move[1] * step
                        if new_row < 0 or new_row >= 6 or new_col < 0 or new_col >= 6:
                            break
                        if board[new_row, new_col] != 0:
                            break
                        new_board = board.copy()
                        new_board[new_row, new_col] = 1
                        new_board[row, col] = 0
                        found = False
                        arrow_dirs = directions  # Check all arrow directions
                        for ad in arrow_dirs:
                            arrow_x, arrow_y = new_row, new_col
                            arrow_list = []
                            while True:
                                arrow_x += ad[0]
                                arrow_y += ad[1]
                                if arrow_x < 0 or arrow_x >= 6 or arrow_y < 0 or arrow_y >= 6:
                                    break
                                if new_board[arrow_x, arrow_y] != 0:
                                    break
                                arrow_list.append((arrow_x, arrow_y))
                            if arrow_list:
                                ax, ay = arrow_list[0]
                                return f"{row},{col}:{new_row},{new_col}:{ax},{ay}"
                        step += 1
    return "0,0:0,0:0,0"  # Fallback (should not reach here)
