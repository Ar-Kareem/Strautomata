
def policy(board: list[list[int]]) -> int:
    BOARD_ROWS = 6
    BOARD_COLS = 7

    def find_lowest_empty_row(b: list, col: int) -> int:
        for r in reversed(range(BOARD_ROWS)):
            if b[r][col] == 0:
                return r
        return -1

    def check_win(b: list, p: int) -> bool:
        # Horizontal
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS - 3):
                if all(b[row][col + k] == p for k in range(4)):
                    return True
        # Vertical
        for col in range(BOARD_COLS):
            for row in range(BOARD_ROWS - 3):
                if all(b[row + k][col] == p for k in range(4)):
                    return True
        # Diagonal down-right
        for row in range(3):
            for col in range(BOARD_COLS - 3):
                if all(b[row + k][col + k] == p for k in range(4)):
                    return True
        # Diagonal down-left
        for row in range(3):
            for col in range(3, BOARD_COLS):
                if all(b[row + k][col - k] == p for k in range(4)):
                    return True
        return False

    def evaluate(b: list, player: int) -> int:
        score = 0

        directions = [(0, -1), (1, 0), (1, 1), (-1, 1)]

        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                if b[row][col] != player:
                    continue
                for (dr, dc) in directions:
                    count = 1
                    # Check in the positive direction
                    r, c = row + dr, col + dc
                    while 0 <= r < BOARD_ROWS and 0 <= c < BOARD_COLS and b[r][c] == player:
                        count += 1
                        r += dr
                        c += dc
                    # Check in the negative direction
                    r, c = row - dr, col - dc
                    while 0 <= r < BOARD_ROWS and 0 <= c < BOARD_COLS and b[r][c] == player:
                        count += 1
                        r -= dr
                        c -= dc
                    if count >= 3:
                        if count == 3:
                            score += 10 if player == 1 else -10
                        elif count == 4:
                            return 1000 if player == 1 else -1000
        return score

    def valid_columns(b: list) -> list:
        return [col for col in range(BOARD_COLS) if b[0][col] == 0]

    def minimax(b: list, depth: int, alpha: int, beta: int, is_me: bool) -> int:
        if not valid_columns(b):
            return 0  # Stalemate
        if is_win(b, 1):
            return 10000 if is_me else -10000
        if is_win(b, -1):
            return -10000 if is_me else 10000

        if depth == 0:
            return evaluate(b, 1 if is_me else -1)

        valid = valid_columns(b)
        best = -float('inf') if is_me else float('inf')

        for col in valid:
            row = find_lowest_empty_row(b, col)
            new_b = [r.copy() for r in b]
            new_b[row][col] = 1 if is_me else -1

            if is_win(new_b, 1 if is_me else -1):
                score = 10000 if is_me else -10000
            else:
                score = minimax(new_b, depth - 1, alpha, beta, not is_me)

            if is_me:
                if score > best:
                    best = score
                alpha = max(alpha, score)
                if alpha >= beta:
                    break
            else:
                if score < best:
                    best = score
                beta = min(beta, score)
                if beta <= alpha:
                    break

        return best

    valid = valid_columns(board)
    best_col = valid[0]
    best_score = float('-inf')
    alpha, beta = float('-inf'), float('inf')

    for col in valid:
        row = find_lowest_empty_row(board, col)
        new_b = [r.copy() for r in board]
        new_b[row][col] = 1
        if check_win(new_b, 1):
            return col
        val = minimax(new_b, beta, alpha, False, depth=4)
        if val > best_score:
            best_score = val
            best_col = col
        alpha = max(alpha, best_score)

    return best_col
