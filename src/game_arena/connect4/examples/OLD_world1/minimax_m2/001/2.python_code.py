
import random

ROWS = 6
COLS = 7

def has_winning_move(board, player):
    """Check if the current board has a winning move for the player."""
    for i in range(ROWS):
        for j in range(COLS):
            if board[i][j] == player:
                # Check all four directions
                for dx, dy in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                    count = 0
                    x, y = i, j
                    while 0 <= x < ROWS and 0 <= y < COLS and board[x][y] == player and count < 4:
                        count += 1
                        x += dx
                        y += dy
                    if count == 4:
                        return True
    return False

def score_block(count, open1, open2):
    """Score a contiguous block based on its length and open ends."""
    if count >= 4:
        return 100000
    elif count == 3:
        open_count = open1 + open2
        if open_count == 2:
            return 1000
        elif open_count == 1:
            return 100
        else:
            return 10
    elif count == 2:
        open_count = open1 + open2
        if open_count == 2:
            return 100
        elif open_count == 1:
            return 10
        else:
            return 1
    else:
        return 0

def evaluate(board, player):
    """Evaluate the board state from the perspective of the player."""
    total_score = 0
    for i in range(ROWS):
        for j in range(COLS):
            if board[i][j] == player:
                # Horizontal (0,1)
                if j == 0 or board[i][j-1] != player:
                    count = 1
                    j1 = j + 1
                    while j1 < COLS and board[i][j1] == player:
                        count += 1
                        j1 += 1
                    left_open = (j-1 >= 0 and board[i][j-1] == 0)
                    right_open = (j+count < COLS and board[i][j+count] == 0)
                    total_score += score_block(count, left_open, right_open)

                # Vertical (1,0)
                if i == 0 or board[i-1][j] != player:
                    count = 1
                    i1 = i + 1
                    while i1 < ROWS and board[i1][j] == player:
                        count += 1
                        i1 += 1
                    top_open = (i-1 >= 0 and board[i-1][j] == 0)
                    bottom_open = (i+count < ROWS and board[i+count][j] == 0)
                    total_score += score_block(count, top_open, bottom_open)

                # Diagonal (1,1)
                if i == 0 or j == 0 or board[i-1][j-1] != player:
                    count = 1
                    i1, j1 = i+1, j+1
                    while i1 < ROWS and j1 < COLS and board[i1][j1] == player:
                        count += 1
                        i1 += 1
                        j1 += 1
                    top_left_open = (i-1 >= 0 and j-1 >= 0 and board[i-1][j-1] == 0)
                    bottom_right_open = (i+count < ROWS and j+count < COLS and board[i+count][j+count] == 0)
                    total_score += score_block(count, top_left_open, bottom_right_open)

                # Diagonal (1,-1)
                if i == 0 or j == COLS-1 or board[i-1][j+1] != player:
                    count = 1
                    i1, j1 = i+1, j-1
                    while i1 < ROWS and j1 >= 0 and board[i1][j1] == player:
                        count += 1
                        i1 += 1
                        j1 -= 1
                    top_right_open = (i-1 >= 0 and j+1 < COLS and board[i-1][j+1] == 0)
                    bottom_left_open = (i+count < ROWS and j-count >= 0 and board[i+count][j-count] == 0)
                    total_score += score_block(count, top_right_open, bottom_left_open)
    return total_score

def simulate_move(board, col, player):
    """Simulate dropping a disc in the column. Returns the row index where the disc was placed, or None if column is full."""
    for row in range(ROWS-1, -1, -1):
        if board[row][col] == 0:
            board[row][col] = player
            return row
    return None

def policy(board):
    """Determine the best column to drop a disc."""
    # Step 1: Check for immediate winning move
    for col in range(COLS):
        row = simulate_move(board, col, 1)
        if row is not None:
            if has_winning_move(board, 1):
                board[row][col] = 0  # Revert move
                return col
            else:
                board[row][col] = 0  # Revert move

    # Step 2: Check for immediate blocking move (opponent's win)
    for col in range(COLS):
        row = simulate_move(board, col, -1)
        if row is not None:
            if has_winning_move(board, -1):
                board[row][col] = 0  # Revert move
                return col
            else:
                board[row][col] = 0  # Revert move

    # Step 3: Evaluate all possible moves using heuristic
    best_score = -10**9
    best_columns = []
    for col in range(COLS):
        row = simulate_move(board, col, 1)
        if row is not None:
            # Evaluate the board from current player's perspective
            score = evaluate(board, 1) - evaluate(board, -1)
            board[row][col] = 0  # Revert move
            if score > best_score:
                best_score = score
                best_columns = [col]
            elif score == best_score:
                best_columns.append(col)

    # Select randomly among the best columns to add some randomness
    if best_columns:
        return random.choice(best_columns)
    else:
        # Fallback: choose randomly from any valid column
        for col in range(COLS):
            if board[0][col] == 0:  # Check if column has space
                return col
        # Should never happen if there are valid moves
        return random.randint(0, COLS-1)
