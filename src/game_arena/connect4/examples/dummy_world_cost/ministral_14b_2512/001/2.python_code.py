
import random

def policy(board: list[list[int]]) -> int:
    # Directions for checking lines (horizontal, vertical, diagonal, anti-diagonal)
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    def is_valid_move(col):
        return board[0][col] == 0

    def get_next_open_row(col):
        for row in range(5, -1, -1):
            if board[row][col] == 0:
                return row
        return -1

    def check_winning_move(player, col):
        row = get_next_open_row(col)
        if row == -1:
            return False
        # Simulate placing the disc
        board[row][col] = player
        # Check all directions for a win
        for dr, dc in directions:
            count = 1
            # Check right/down
            r, c = row + dr, col + dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                count += 1
                r += dr
                c += dc
            # Check left/up
            r, c = row - dr, col - dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if count >= 4:
                board[row][col] = 0
                return True
        board[row][col] = 0
        return False

    def evaluate_move(player, col):
        row = get_next_open_row(col)
        if row == -1:
            return -float('inf')
        # Simulate placing the disc
        board[row][col] = player
        score = 0
        # Check all directions for patterns
        for dr, dc in directions:
            count = 1
            # Check right/down
            r, c = row + dr, col + dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                count += 1
                r += dr
                c += dc
            # Check left/up
            r, c = row - dr, col - dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            # Score based on pattern length
            if count >= 4:
                score += 1000  # Winning move
            elif count == 3:
                score += 50  # Open three
            elif count == 2:
                score += 10  # Open two
        board[row][col] = 0
        return score

    # Check for opponent's winning move (block)
    for col in range(7):
        if is_valid_move(col) and check_winning_move(-1, col):
            return col

    # Check for our winning move
    for col in range(7):
        if is_valid_move(col) and check_winning_move(1, col):
            return col

    # Evaluate all possible moves
    best_score = -float('inf')
    best_col = -1
    for col in range(7):
        if is_valid_move(col):
            score = evaluate_move(1, col)
            if score > best_score:
                best_score = score
                best_col = col

    # If no strong move, pick a random legal move
    if best_col == -1:
        legal_moves = [col for col in range(7) if is_valid_move(col)]
        return random.choice(legal_moves)

    return best_col
