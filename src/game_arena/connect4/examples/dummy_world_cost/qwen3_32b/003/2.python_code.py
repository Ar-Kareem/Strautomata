
import random

def policy(board: list[list[int]]) -> int:
    def get_next_row(current_board, col):
        for r in range(5, -1, -1):
            if current_board[r][col] == 0:
                return r
        return None
    
    def is_winning(current_board, player):
        # Check horizontal
        for r in range(6):
            for c in range(4):
                if all(current_board[r][c + i] == player for i in range(4)):
                    return True
        # Check vertical
        for c in range(7):
            for r in range(3):
                if all(current_board[r + i][c] == player for i in range(4)):
                    return True
        # Check positive diagonals (top-left to bottom-right)
        for r in range(3):
            for c in range(4):
                if all(current_board[r + i][c + i] == player for i in range(4)):
                    return True
        # Check negative diagonals (top-right to bottom-left)
        for r in range(3):
            for c in range(3, 7):
                if all(current_board[r + i][c - i] == player for i in range(4)):
                    return True
        return False

    def evaluate_window(window, player):
        score = 0
        opponent = -player
        if window.count(player) == 4:
            score += 100
        elif window.count(player) == 3 and window.count(0) == 1:
            score += 9
        elif window.count(player) == 2 and window.count(0) == 2:
            score += 3
        if window.count(opponent) == 4:
            score -= 100
        elif window.count(opponent) == 3 and window.count(0) == 1:
            score -= 40  # Penalize opponent's 3-seq significantly more to prioritize blocking
        elif window.count(opponent) == 2 and window.count(0) == 2:
            score -= 2
        return score

    def score_position(current_board, player):
        score = 0

        # Center column bonus
        center_array = [current_board[i][3] for i in range(6)]
        center_count = center_array.count(player)
        score += center_count * 3

        # Horizontal
        for r in range(6):
            row_array = current_board[r]
            for c in range(4):
                window = row_array[c:c+4]
                score += evaluate_window(window, player)

        # Vertical
        for c in range(7):
            col_array = [current_board[i][c] for i in range(6)]
            for r in range(3):
                window = col_array[r:r+4]
                score += evaluate_window(window, player)

        # Positive diagonal
        for r in range(3):
            for c in range(4):
                diag = [current_board[r + i][c + i] for i in range(4)]
                score += evaluate_window(diag, player)

        # Negative diagonal
        for r in range(3):
            for c in range(6, 2, -1):
                diag = [current_board[r + i][c - i] for i in range(4)]
                score += evaluate_window(diag, player)
        return score

    def minmax(current_board, depth, alpha, beta, maximizing):
        valid_cols = [col for col in range(7) if current_board[0][col] == 0]
        valid_cols_ordered = sorted(valid_cols, key=lambda c: abs(c - 3))
        is_terminal = is_winning(current_board, 1) or is_winning(current_board, -1) or not valid_cols
        if depth == 0 or is_terminal:
            if is_terminal:
                if is_winning(current_board, 1):  # current player wins
                    return (100000000, None)
                elif is_winning(current_board, -1):  # opponent wins
                    return (-100000000, None)
                else:
                    return (0, None)  # full board, draw
            else:
                return (score_position(current_board, 1), None)

        if maximizing:
            best_score = -float('inf')
            best_col = random.choice(valid_cols_ordered)
            for col in valid_cols_ordered:
                new_board = [row[:] for row in current_board]
                row = get_next_row(new_board, col)
                if row is None:
                    continue
                new_board[row][col] = 1
                score = minmax(new_board, depth - 1, alpha, beta, False)[0]
                if score > best_score:
                    best_score = score
                    best_col = col
                alpha = max(alpha, best_score)
                if alpha >= beta:
                    break
            return (best_score, best_col)
        else:
            best_score = float('inf')
            best_col = random.choice(valid_cols_ordered)
            for col in valid_cols_ordered:
                new_board = [row[:] for row in current_board]
                row = get_next_row(new_board, col)
                if row is None:
                    continue
                new_board[row][col] = -1
                score = minmax(new_board, depth - 1, alpha, beta, True)[0]
                if score < best_score:
                    best_score = score
                    best_col = col
                beta = min(beta, best_score)
                if alpha >= beta:
                    break
            return (best_score, best_col)

    # Step 1: Check for immediate winning moves
    valid = [col for col in range(7) if board[0][col] == 0]
    for col in sorted(valid, key=lambda c: abs(c - 3)):
        row = get_next_row(board, col)
        if row is not None:
            new_board = [r[:] for r in board]
            new_board[row][col] = 1
            if is_winning(new_board, 1):
                return col

    # Step 2: Block opponent's immediate win
    for col in sorted(valid, key=lambda c: abs(c - 3)):
        row = get_next_row(board, col)
        if row is not None:
            new_board = [r[:] for r in board]
            new_board[row][col] = -1
            if is_winning(new_board, -1):
                return col

    # Step 3: Run minimax with alpha-beta pruning
    best_score, best_col = minmax(board, 4, -float('inf'), float('inf'), True)
    return best_col
