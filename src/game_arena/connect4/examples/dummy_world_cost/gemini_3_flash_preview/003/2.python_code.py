
import numpy as np

def policy(board: list[list[int]]) -> int:
    board_np = np.array(board)
    rows = 6
    cols = 7
    depth = 4

    def get_valid_moves(b):
        return [c for c in [3, 2, 4, 1, 5, 0, 6] if b[0][c] == 0]

    def drop_piece(b, col, piece):
        new_b = b.copy()
        for r in range(rows - 1, -1, -1):
            if new_b[r][col] == 0:
                new_b[r][col] = piece
                break
        return new_b

    def evaluate_window(window, piece):
        score = 0
        opp_piece = -piece
        if window.count(piece) == 4:
            score += 10000
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 100
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 10

        if window.count(opp_piece) == 3 and window.count(0) == 1:
            score -= 80
        return score

    def score_position(b, piece):
        score = 0
        # Score center column
        center_array = [int(i) for i in list(b[:, cols//2])]
        center_count = center_array.count(piece)
        score += center_count * 6

        # Score Horizontal
        for r in range(rows):
            row_array = [int(i) for i in list(b[r, :])]
            for c in range(cols - 3):
                window = row_array[c:c+4]
                score += evaluate_window(window, piece)

        # Score Vertical
        for c in range(cols):
            col_array = [int(i) for i in list(b[:, c])]
            for r in range(rows - 3):
                window = col_array[r:r+4]
                score += evaluate_window(window, piece)

        # Score positive sloped diagonal
        for r in range(rows - 3):
            for c in range(cols - 3):
                window = [b[r+3-i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)

        # Score negative sloped diagonal
        for r in range(rows - 3):
            for c in range(cols - 3):
                window = [b[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)

        return score

    def is_terminal(b):
        # Checks if someone won or board is full
        def check_win(piece):
            for c in range(cols - 3):
                for r in range(rows):
                    if all(b[r][c+i] == piece for i in range(4)): return True
            for c in range(cols):
                for r in range(rows - 3):
                    if all(b[r+i][c] == piece for i in range(4)): return True
            for c in range(cols - 3):
                for r in range(rows - 3):
                    if all(b[r+i][c+i] == piece for i in range(4)): return True
                    if all(b[r+3-i][c+i] == piece for i in range(4)): return True
            return False
            
        return check_win(1) or check_win(-1) or len(get_valid_moves(b)) == 0

    def minimax(b, depth, alpha, beta, maximizingPlayer):
        valid_moves = get_valid_moves(b)
        terminal = is_terminal(b)
        if depth == 0 or terminal:
            if terminal:
                # Big score for winning/losing
                if any(all(b[r][c+i] == 1 for i in range(4)) for r in range(rows) for c in range(cols-3)): return (None, 1000000)
                if any(all(b[r][c+i] == -1 for i in range(4)) for r in range(rows) for c in range(cols-3)): return (None, -1000000)
                return (None, 0)
            else:
                return (None, score_position(b, 1))

        if maximizingPlayer:
            value = -float('inf')
            column = valid_moves[0]
            for col in valid_moves:
                b_copy = drop_piece(b, col, 1)
                new_score = minimax(b_copy, depth - 1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:
            value = float('inf')
            column = valid_moves[0]
            for col in valid_moves:
                b_copy = drop_piece(b, col, -1)
                new_score = minimax(b_copy, depth - 1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    col, score = minimax(board_np, depth, -float('inf'), float('inf'), True)
    return int(col)
