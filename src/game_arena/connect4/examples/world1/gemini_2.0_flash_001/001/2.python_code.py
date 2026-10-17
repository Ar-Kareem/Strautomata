
import numpy as np

def policy(board: list[list[int]]) -> int:
    """
    A Connect 4 policy that uses minimax with alpha-beta pruning and a heuristic evaluation function.
    """
    board = np.array(board)  # Convert to NumPy array for easier manipulation
    def is_valid_move(board, col):
        return board[0][col] == 0

    def get_next_open_row(board, col):
        for r in range(5, -1, -1):
            if board[r][col] == 0:
                return r

    def drop_piece(board, row, col, piece):
        board[row][col] = piece

    def winning_move(board, piece):
        # Check horizontal
        for c in range(4):
            for r in range(6):
                if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                    return True

        # Check vertical
        for c in range(7):
            for r in range(3):
                if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                    return True

        # Check positively sloped diagonals
        for c in range(4):
            for r in range(3):
                if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                    return True

        # Check negatively sloped diagonals
        for c in range(4):
            for r in range(3, 6):
                if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                    return True
        return False

    def evaluate_window(window, piece):
        score = 0
        opp_piece = 1 if piece == -1 else -1

        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 2

        if window.count(opp_piece) == 3 and window.count(0) == 1:
            score -= 4

        return score

    def score_position(board, piece):
        score = 0

        # Score center column
        center_array = [int(i) for i in list(board[:, 3])]
        center_count = center_array.count(piece)
        score += center_count * 3

        # Score Horizontal
        for r in range(6):
            row_array = [int(i) for i in list(board[r,:])]
            for c in range(4):
                window = row_array[c:c+4]
                score += evaluate_window(window, piece)

        # Score Vertical
        for c in range(7):
            col_array = [int(i) for i in list(board[:,c])]
            for r in range(3):
                window = col_array[r:r+4]
                score += evaluate_window(window, piece)

        # Score positively sloped diagonal
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)

        # Score negatively sloped diagonal
        for r in range(3):
            for c in range(4):
                window = [board[r+3-i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)

        return score

    def is_terminal_node(board):
        return winning_move(board, 1) or winning_move(board, -1) or len(get_valid_locations(board)) == 0

    def get_valid_locations(board):
        valid_locations = []
        for col in range(7):
            if is_valid_move(board, col):
                valid_locations.append(col)
        return valid_locations

    def minimax(board, depth, alpha, beta, maximizingPlayer):
        valid_locations = get_valid_locations(board)
        is_terminal = is_terminal_node(board)
        if depth == 0 or is_terminal:
            if is_terminal:
                if winning_move(board, 1):
                    return (None, 10000000000)
                elif winning_move(board, -1):
                    return (None, -10000000000)
                else: # Game is over, no more valid moves
                    return (None, 0)
            else: # Depth is zero
                return (None, score_position(board, 1))

        if maximizingPlayer:
            value = -np.inf
            column = np.random.choice(valid_locations)
            for col in valid_locations:
                row = get_next_open_row(board, col)
                b_copy = board.copy()
                drop_piece(b_copy, row, col, 1)
                new_score = minimax(b_copy, depth-1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value

        else: # Minimizing player
            value = np.inf
            column = np.random.choice(valid_locations)
            for col in valid_locations:
                row = get_next_open_row(board, col)
                b_copy = board.copy()
                drop_piece(b_copy, row, col, -1)
                new_score = minimax(b_copy, depth-1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    valid_locations = get_valid_locations(board)
    # Check for winning move
    for col in valid_locations:
        row = get_next_open_row(board.copy(), col)
        temp_board = board.copy()
        drop_piece(temp_board, row, col, 1)
        if winning_move(temp_board, 1):
            return col

    # Check for opponent's winning move and block it
    for col in valid_locations:
        row = get_next_open_row(board.copy(), col)
        temp_board = board.copy()
        drop_piece(temp_board, row, col, -1)
        if winning_move(temp_board, -1):
            return col

    # Otherwise, use minimax
    depth = 4 # Search depth. Increase with faster hardware.
    col, minimax_score = minimax(board, depth, -np.inf, np.inf, True)
    if col is None:
        return np.random.choice(valid_locations)

    return col
