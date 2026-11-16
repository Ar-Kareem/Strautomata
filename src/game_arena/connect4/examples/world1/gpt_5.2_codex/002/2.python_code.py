
def policy(board):
    ROWS, COLS = 6, 7

    def valid_cols(b):
        return [c for c in range(COLS) if b[0][c] == 0]

    def get_next_open_row(b, col):
        for r in range(ROWS-1, -1, -1):
            if b[r][col] == 0:
                return r
        return None

    def drop_piece(b, col, piece):
        r = get_next_open_row(b, col)
        if r is None:
            return None
        newb = [row[:] for row in b]
        newb[r][col] = piece
        return newb

    def winning_move(b, piece):
        # horizontal
        for r in range(ROWS):
            for c in range(COLS-3):
                if all(b[r][c+i] == piece for i in range(4)):
                    return True
        # vertical
        for c in range(COLS):
            for r in range(ROWS-3):
                if all(b[r+i][c] == piece for i in range(4)):
                    return True
        # diagonals
        for r in range(ROWS-3):
            for c in range(COLS-3):
                if all(b[r+i][c+i] == piece for i in range(4)):
                    return True
        for r in range(3, ROWS):
            for c in range(COLS-3):
                if all(b[r-i][c+i] == piece for i in range(4)):
                    return True
        return False

    def evaluate_window(window, piece):
        opp = -piece
        score = 0
        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 2
        if window.count(opp) == 3 and window.count(0) == 1:
            score -= 4
        if window.count(opp) == 4:
            score -= 100
        return score

    def score_position(b, piece):
        score = 0
        # center control
        center_array = [b[r][COLS//2] for r in range(ROWS)]
        score += center_array.count(piece) * 3

        # horizontal
        for r in range(ROWS):
            row_array = b[r]
            for c in range(COLS-3):
                window = row_array[c:c+4]
                score += evaluate_window(window, piece)
        # vertical
        for c in range(COLS):
            col_array = [b[r][c] for r in range(ROWS)]
            for r in range(ROWS-3):
                window = col_array[r:r+4]
                score += evaluate_window(window, piece)
        # positive diag
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = [b[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
        # negative diag
        for r in range(3, ROWS):
            for c in range(COLS-3):
                window = [b[r-i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)

        return score

    def is_terminal(b):
        return winning_move(b, 1) or winning_move(b, -1) or len(valid_cols(b)) == 0

    def minimax(b, depth, alpha, beta, maximizing):
        valid = valid_cols(b)
        if depth == 0 or is_terminal(b):
            if winning_move(b, 1):
                return (float('inf'), None)
            elif winning_move(b, -1):
                return (float('-inf'), None)
            else:
                return (score_position(b, 1), None)

        order = [3,2,4,1,5,0,6]
        if maximizing:
            value = float('-inf')
            best_col = valid[0]
            for col in order:
                if col in valid:
                    newb = drop_piece(b, col, 1)
                    score, _ = minimax(newb, depth-1, alpha, beta, False)
                    if score > value:
                        value = score
                        best_col = col
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        break
            return value, best_col
        else:
            value = float('inf')
            best_col = valid[0]
            for col in order:
                if col in valid:
                    newb = drop_piece(b, col, -1)
                    score, _ = minimax(newb, depth-1, alpha, beta, True)
                    if score < value:
                        value = score
                        best_col = col
                    beta = min(beta, value)
                    if alpha >= beta:
                        break
            return value, best_col

    valid = valid_cols(board)
    if not valid:
        return 0

    # Immediate win
    for col in valid:
        if winning_move(drop_piece(board, col, 1), 1):
            return col
    # Immediate block
    for col in valid:
        if winning_move(drop_piece(board, col, -1), -1):
            return col

    depth = 4
    _, best_col = minimax(board, depth, float('-inf'), float('inf'), True)
    if best_col is None:
        return valid[0]
    return best_col
