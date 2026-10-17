
import numpy as np

def policy(board):
    rows, cols = board.shape
    my_amazons = list(np.argwhere(board == 1))
    
    # Directions include all queen's moves (8 possible directions)
    directions = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
    
    for (from_row, from_col) in my_amazons:
        # Check all queen directions for possible moves
        for direction in directions:
            dx, dy = direction
            s = 1
            while True:
                new_row = from_row + dx * s
                new_col = from_col + dy * s
                # Check if the new position is within the board
                if not (0 <= new_row < rows and 0 <= new_col < cols):
                    break
                # Check if all cells along the path to new_pos are empty
                path_clear = True
                for step in range(1, s):
                    inter_row = from_row + dx * step
                    inter_col = from_col + dy * step
                    if inter_row < 0 or inter_row >= rows or inter_col < 0 or inter_col >= cols:
                        path_clear = False
                        break
                    if board[inter_row][inter_col] != 0:
                        path_clear = False
                        break
                if not path_clear:
                    break  # Path is blocked, no further steps in this direction
                
                # Check if the destination cell is empty
                if board[new_row][new_col] == 0:
                    # Check for valid arrow shots from new position
                    # Simulate new_board after moving the amazon
                    def get_cell_val(rx, ry):
                        return 0 if (rx, ry) == (from_row, from_col) else board[rx][ry]
                    
                    # Check all eight possible directions for an arrow shot
                    arrow_dirs = [(dx_arrow, dy_arrow) for dx_arrow in (-1, 0, 1) for dy_arrow in (-1, 0, 1) if (dx_arrow, dy_arrow) != (0, 0)]
                    for arrow_dx, arrow_dy in arrow_dirs:
                        s_arrow = 1
                        arrow_targets = []
                        while True:
                            arrow_x = new_row + arrow_dx * s_arrow
                            arrow_y = new_col + arrow_dy * s_arrow
                            if not (0 <= arrow_x < rows and 0 <= arrow_y < cols):
                                break
                            # Determine cell value in new board context
                            cell_val = get_cell_val(arrow_x, arrow_y)
                            if cell_val != 0:
                                break
                            arrow_targets.append((arrow_x, arrow_y))
                            s_arrow += 1
                        if arrow_targets:
                            # Found a valid arrow shot; return the move
                            arrow_x, arrow_y = arrow_targets[0]
                            return f"{from_row},{from_col}:{new_row},{new_col}:{arrow_x},{arrow_y}"
                # Move to next step in this direction to find further possible moves
                s += 1
