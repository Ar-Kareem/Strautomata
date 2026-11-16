
def policy(board: list[list[int]]) -> int:
    # Check for an immediate winning move
    for col in range(7):
        if board[0][col] != 0:
            continue
        row = get_next_available_row(board, col)
        new_board = [row.copy() for row in board]
        new_board[row][col] = 1
        if has_four_in_row(new_board, 1):
            return col
    
    # Check for moves that block the opponent's potential win
    safe_cols = []
    for col in range(7):
        if board[0][col] != 0:
            continue
        row = get_next_available_row(board, col)
        new_board = [r.copy() for r in board]
        new_board[row][col] = 1
        if not any_opponent_can_win(new_board):
            safe_cols.append(col)
    
    if safe_cols:
        return select_best_move(board, safe_cols)
    
    # If all moves are losing, pick any legal move
    for col in range(7):
        if board[0][col] == 0:
            return col
    return -1

def get_next_available_row(board, col):
    for row in range(5, -1, -1):
        if board[row][col] == 0:
            return row
    return -1

def has_four_in_row(board, player):
    # Check rows
    for row in range(6):
        for col in range(4):
            if (board[row][col] == player and board[row][col+1] == player and
                board[row][col+2] == player and board[row][col+3] == player):
                return True
    # Check columns
    for col in range(7):
        for row in range(3):
            if (board[row][col] == player and board[row+1][col] == player and
                board[row+2][col] == player and board[row+3][col] == player):
                return True
    # Check diagonals (top-left to bottom-right)
    for row in range(3):
        for col in range(4):
            if (board[row][col] == player and board[row+1][col+1] == player and
                board[row+2][col+2] == player and board[row+3][col+3] == player):
                return True
    # Check diagonals (top-right to bottom-left)
    for row in range(3):
        for col in range(3, 7):
            if (board[row][col] == player and board[row+1][col-1] == player and
                board[row+2][col-2] == player and board[row+3][col-3] == player):
                return True
    return False

def any_opponent_can_win(board):
    for col in range(7):
        if board[0][col] != 0:
            continue
        new_board = [row.copy() for row in board]
        row = get_next_available_row(new_board, col)
        new_board[row][col] = -1
        if has_four_in_row(new_board, -1):
            return True
    return False

def select_best_move(board, possible_cols):
    # Prioritize columns in this order: 3, 2, 4, 5, 1, 6, 0
    priority_order = {3: 0, 2: 1, 4: 2, 5: 3, 1: 4, 6: 5, 0: 6}
    best_col = None
    best_priority = 7  # Initialize with highest priority value (worst)
    for col in possible_cols:
        current_priority = priority_order.get(col, priority_order.get(None))
        if current_priority < best_priority:
            best_priority = current_priority
            best_col = col
    return best_col
