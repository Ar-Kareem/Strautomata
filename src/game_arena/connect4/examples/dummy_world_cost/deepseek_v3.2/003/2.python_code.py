
import time
import random

def policy(board: list[list[int]]) -> int:
    start_time = time.time()
    time_limit = 0.95  # seconds, keep a safety margin

    # ---------- Helper functions ----------
    def is_terminal(b):
        # Check for win for either player
        for row in range(6):
            for col in range(7):
                cell = b[row][col]
                if cell == 0:
                    continue
                # horizontal
                if col <= 3:
                    if cell == b[row][col+1] == b[row][col+2] == b[row][col+3]:
                        return True
                # vertical
                if row <= 2:
                    if cell == b[row+1][col] == b[row+2][col] == b[row+3][col]:
                        return True
                # diagonal down-right
                if row <= 2 and col <= 3:
                    if cell == b[row+1][col+1] == b[row+2][col+2] == b[row+3][col+3]:
                        return True
                # diagonal up-right
                if row >= 3 and col <= 3:
                    if cell == b[row-1][col+1] == b[row-2][col+2] == b[row-3][col+3]:
                        return True
        # Check if board full (draw)
        if all(b[0][c] != 0 for c in range(7)):
            return True
        return False

    def get_winner(b):
        # Return 1 if we win, -1 if opponent wins, 0 otherwise
        for row in range(6):
            for col in range(7):
                cell = b[row][col]
                if cell == 0:
                    continue
                # horizontal
                if col <= 3:
                    if cell == b[row][col+1] == b[row][col+2] == b[row][col+3]:
                        return cell
                # vertical
                if row <= 2:
                    if cell == b[row+1][col] == b[row+2][col] == b[row+3][col]:
                        return cell
                # diagonal down-right
                if row <= 2 and col <= 3:
                    if cell == b[row+1][col+1] == b[row+2][col+2] == b[row+3][col+3]:
                        return cell
                # diagonal up-right
                if row >= 3 and col <= 3:
                    if cell == b[row-1][col+1] == b[row-2][col+2] == b[row-3][col+3]:
                        return cell
        return 0

    def get_legal_moves(b):
        return [c for c in range(7) if b[0][c] == 0]

    def make_move(b, col, player):
        # Return new board with move made
        new_board = [row[:] for row in b]
        for row in reversed(range(6)):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                break
        return new_board

    # evaluation function (heuristic)
    def evaluate(b):
        score = 0
        # center preference
        center_col = 3
        for row in range(6):
            if b[row][center_col] == 1:
                score += 3
            elif b[row][center_col] == -1:
                score -= 3

        # evaluate all windows of 4
        for row in range(6):
            for col in range(7):
                # horizontal
                if col <= 3:
                    window = [b[row][col], b[row][col+1], b[row][col+2], b[row][col+3]]
                    score += evaluate_window(window)
                # vertical
                if row <= 2:
                    window = [b[row][col], b[row+1][col], b[row+2][col], b[row+3][col]]
                    score += evaluate_window(window)
                # diagonal down-right
                if row <= 2 and col <= 3:
                    window = [b[row][col], b[row+1][col+1], b[row+2][col+2], b[row+3][col+3]]
                    score += evaluate_window(window)
                # diagonal up-right
                if row >= 3 and col <= 3:
                    window = [b[row][col], b[row-1][col+1], b[row-2][col+2], b[row-3][col+3]]
                    score += evaluate_window(window)
        return score

    def evaluate_window(window):
        score = 0
        our = window.count(1)
        opp = window.count(-1)
        empty = window.count(0)
        if our == 4:
            score += 10000
        elif our == 3 and empty == 1:
            score += 50
        elif our == 2 and empty == 2:
            score += 10
        if opp == 3 and empty == 1:
            score -= 80  # block opponent's open three
        elif opp == 4:
            score -= 10000
        elif opp == 2 and empty == 2:
            score -= 8
        return score

    # minimax with alpha-beta
    def minimax(b, depth, alpha, beta, maximizing):
        if depth == 0 or is_terminal(b):
            winner = get_winner(b)
            if winner == 1:
                return 1000000
            elif winner == -1:
                return -1000000
            else:
                return evaluate(b)

        legal_moves = get_legal_moves(b)
        if maximizing:
            value = -float('inf')
            for col in legal_moves:
                new_b = make_move(b, col, 1)
                value = max(value, minimax(new_b, depth-1, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for col in legal_moves:
                new_b = make_move(b, col, -1)
                value = min(value, minimax(new_b, depth-1, alpha, beta, True))
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    # ---------- Main decision logic ----------
    legal_moves = get_legal_moves(board)
    if not legal_moves:
        return random.choice(range(7))  # fallback, shouldn't happen

    # 1. Check immediate win
    for col in legal_moves:
        new_board = make_move(board, col, 1)
        if get_winner(new_board) == 1:
            return col

    # 2. Block opponent's immediate win
    for col in legal_moves:
        new_board = make_move(board, col, -1)
        if get_winner(new_board) == -1:
            return col

    # 3. Minimax search with increasing depth as time permits
    best_move = legal_moves[0]
    best_value = -float('inf')

    # Adjust depth based on time left and board complexity
    # start with depth 4, go deeper if we have time
    depth = 4
    if sum(board[row][col] != 0 for row in range(6) for col in range(7)) <= 6:
        depth = 6  # deeper search for opening moves

    elapsed = time.time() - start_time
    while elapsed < time_limit and depth <= 7:
        current_best = None
        current_val = -float('inf')
        for col in legal_moves:
            new_board = make_move(board, col, 1)
            value = minimax(new_board, depth-1, -float('inf'), float('inf'), False)
            if value > current_val:
                current_val = value
                current_best = col
        if current_best is not None:
            best_move = current_best
            best_value = current_val
        depth += 1
        elapsed = time.time() - start_time
        if elapsed >= time_limit:
            break

    return best_move
