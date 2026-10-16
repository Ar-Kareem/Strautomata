
import math

def policy(board: list[list[int]]) -> int:
    rows = 6
    cols = 7

    def can_win(b: list[list[int]], player: int) -> int:
        for c in range(cols):
            if b[0][c] != 0:
                continue
            row = next(r for r in range(rows-1, -1, -1) if b[r][c] == 0)
            b[row][c] = player
            if check_win(b, row, c, player):
                b[row][c] = 0
                return c
            b[row][c] = 0
        return -1

    def check_win(b: list[list[int]], row: int, col: int, player: int) -> bool:
        # horizontal
        count = 0
        for c in range(col-3, col+4):
            if 0 <= c < cols and b[row][c] == player:
                count += 1
            else:
                count = 0
            if count >= 4:
                return True
        # vertical
        count = 0
        for r in range(row-3, row+4):
            if 0 <= r < rows and b[r][col] == player:
                count += 1
            else:
                count = 0
            if count >= 4:
                return True
        # diagonal \
        count = 0
        for i in range(-3, 4):
            if 0 <= row+i < rows and 0 <= col+i < cols and b[row+i][col+i] == player:
                count += 1
            else:
                count = 0
            if count >= 4:
                return True
        # diagonal /
        count = 0
        for i in range(-3, 4):
            if 0 <= row+i < rows and 0 <= col-i < cols and b[row+i][col-i] == player:
                count += 1
            else:
                count = 0
            if count >= 4:
                return True
        return False

    # Check if I can win immediately
    c = can_win(board, 1)
    if c != -1:
        return c

    # Check if I need to block opponent's win
    c = can_win(board, -1)
    if c != -1:
        return c

    # Otherwise, use minimax with evaluation
    inf = math.inf
    depth = 4

    def eval_window(w: list) -> int:
        ones = w.count(1)
        mins = w.count(-1)
        if ones > 0 and mins > 0:
            return 0
        if ones == 4:
            return 10000
        if mins == 4:
            return -10000
        if ones == 3:
            return 100
        if mins == 3:
            return -100
        if ones == 2:
            return 10
        if mins == 2:
            return -10
        return 0

    def evaluate(b: list[list[int]]) -> int:
        score = 0
        # horizontal
        for r in range(rows):
            for c in range(cols-3):
                window = b[r][c:c+4]
                score += eval_window(window)
        # vertical
        for c in range(cols):
            for r in range(rows-3):
                window = [b[r+i][c] for i in range(4)]
                score += eval_window(window)
        # diagonal \
        for r in range(rows-3):
            for c in range(cols-3):
                window = [b[r+i][c+i] for i in range(4)]
                score += eval_window(window)
        # diagonal /
        for r in range(rows-3):
            for c in range(3, cols):
                window = [b[r+i][c-i] for i in range(4)]
                score += eval_window(window)
        return score

    def minimax(b: list[list[int]], d: int, alpha: float, beta: float, maxp: bool) -> float:
        valid = [col for col in range(cols) if b[0][col] == 0]
        if not valid or d == 0:
            return evaluate(b) if maxp else -evaluate(b)  # Adjust for maximizing player
        if maxp:
            maxe = -inf
            for c in valid:
                row = next(r for r in range(rows-1, -1, -1) if b[r][c] == 0)
                b[row][c] = 1
                e = minimax(b, d-1, alpha, beta, False)
                b[row][c] = 0
                maxe = max(maxe, e)
                alpha = max(alpha, e)
                if beta <= alpha:
                    break
            return maxe
        else:
            mine = inf
            for c in valid:
                row = next(r for r in range(rows-1, -1, -1) if b[r][c] == 0)
                b[row][c] = -1
                e = minimax(b, d-1, alpha, beta, True)
                b[row][c] = 0
                mine = min(mine, e)
                beta = min(beta, e)
                if beta <= alpha:
                    break
            return mine

    # Find the best move using minimax
    best_score = -inf
    best_c = 0
    for c in range(cols):
        if board[0][c] != 0:
            continue
        row = next(r for r in range(rows-1, -1, -1) if board[r][c] == 0)
        board[row][c] = 1
        score = minimax(board, depth-1, -inf, inf, False)
        board[row][c] = 0
        if score > best_score:
            best_score = score
            best_c = c
    return best_c
