
import random

def policy(board: list[list[int]]) -> int:
    rows = len(board)
    cols = len(board[0])
    
    # Helper function to check if a column is valid for a move
    def is_valid_column(col):
        return 0 <= col < cols and board[0][col] == 0

    # Helper function to get the next available row in a column
    def get_next_open_row(col):
        for r in range(rows - 1, -1, -1):
            if board[r][col] == 0:
                return r
        return -1 # Should not happen if is_valid_column is true

    # Helper function to check if a player wins with a potential move
    def check_win(temp_board, player, r, c):
        # Check horizontal
        for col_offset in range(-3, 4):
            count = 0
            for i in range(4):
                if 0 <= c + col_offset + i < cols and temp_board[r][c + col_offset + i] == player:
                    count += 1
                else:
                    count = 0
                if count == 4:
                    return True

        # Check vertical
        for row_offset in range(-3, 4):
            count = 0
            for i in range(4):
                if 0 <= r + row_offset + i < rows and temp_board[r + row_offset + i][c] == player:
                    count += 1
                else:
                    count = 0
                if count == 4:
                    return True

        # Check positive diagonal
        for offset in range(-3, 4):
            count = 0
            for i in range(4):
                if 0 <= r + offset + i < rows and 0 <= c + offset + i < cols and \
                   temp_board[r + offset + i][c + offset + i] == player:
                    count += 1
                else:
                    count = 0
                if count == 4:
                    return True

        # Check negative diagonal
        for offset in range(-3, 4):
            count = 0
            for i in range(4):
                if 0 <= r + offset + i < rows and 0 <= c - offset - i < cols and \
                   temp_board[r + offset + i][c - offset - i] == player:
                    count += 1
                else:
                    count = 0
                if count == 4:
                    return True
        return False

    # 1. Check for a winning move for self
    for col in range(cols):
        if is_valid_column(col):
            r = get_next_open_row(col)
            temp_board = [row[:] for row in board]
            temp_board[r][col] = 1
            if check_win(temp_board, 1, r, col):
                return col

    # 2. Check for opponent's winning move and block it
    for col in range(cols):
        if is_valid_column(col):
            r = get_next_open_row(col)
            temp_board = [row[:] for row in board]
            temp_board[r][col] = -1
            if check_win(temp_board, -1, r, col):
                return col

    # 3. Prioritize middle columns if possible
    center_cols = [cols // 2]
    if cols % 2 == 0:
        center_cols.append(cols // 2 - 1)
    
    for col in center_cols:
        if is_valid_column(col):
            return col

    # 4. Otherwise, choose a random valid move
    valid_columns = [c for c in range(cols) if is_valid_column(c)]
    if valid_columns:
        return random.choice(valid_columns)
    
    # Fallback (should not be reached in a normal game if valid_columns is handled)
    return 0 
