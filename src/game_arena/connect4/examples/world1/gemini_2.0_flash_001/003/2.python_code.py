
import numpy as np
import time

def policy(board):
    """
    A Connect 4 policy based on minimax with alpha-beta pruning and a heuristic evaluation function.
    """

    def get_legal_moves(board):
        """Returns a list of legal moves (column indices) for the given board."""
        return [col for col in range(7) if board[0][col] == 0]

    def drop_piece(board, col, player):
        """Drops a piece for the given player in the specified column and returns the new board state."""
        new_board = [row[:] for row in board]
        for row in range(5, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                return new_board
        return None  # Column is full, should not happen if called with legal move

    def winning_move(board, player):
        """Checks for a winning condition for the given player."""
        # Check horizontal locations for win
        for c in range(4):
            for r in range(6):
                if board[r][c] == player and board[r][c+1] == player and board[r][c+2] == player and board[r][c+3] == player:
                    return True

        # Check vertical locations for win
        for c in range(7):
            for r in range(3):
                if board[r][c] == player and board[r+1][c] == player and board[r+2][c] == player and board[r+3][c] == player:
                    return True

        # Check positively sloped diagonals
        for c in range(4):
            for r in range(3):
                if board[r][c] == player and board[r+1][c+1] == player and board[r+2][c+2] == player and board[r+3][c+3] == player:
                    return True

        # Check negatively sloped diagonals
        for c in range(4):
            for r in range(3, 6):
                if board[r][c] == player and board[r-1][c+1] == player and board[r-2][c+2] == player and board[r-3][c+3] == player:
                    return True
        return False

    def evaluate_window(window, player):
        """Evaluates a window of 4 locations for the given player."""
        score = 0
        opp_player = 1 if player == -1 else -1
        count = window.count(player)
        empty = window.count(0)
        opp_count = window.count(opp_player)
        if count == 4:
            score += 100
        elif count == 3 and empty == 1:
            score += 5
        elif count == 2 and empty == 2:
            score += 2
        if opp_count == 3 and empty == 1:
            score -= 4  # Block potential opponent win
        return score

    def evaluate_board(board, player):
        """Evaluates the board state for the given player."""
        score = 0
        # Score center column
        center_array = [int(i) for i in list(board[:, 3])]
        center_count = center_array.count(player)
        score += center_count * 3

        # Score Horizontal
        for r in range(6):
            row_array = [int(i) for i in list(board[r,:])]
            for c in range(4):
                window = row_array[c:c+4]
                score += evaluate_window(window, player)

        # Score Vertical
        for c in range(7):
            col_array = [int(i) for i in list(board[:,c])]
            for r in range(3):
                window = col_array[r:r+4]
                score += evaluate_window(window, player)

        # Score positive sloped diagonal
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, player)

        for r in range(3):
            for c in range(4):
                window = [board[r+3-i][c+i] for i in range(4)]

                score += evaluate_window(window, player)
        return score

    def minimax(board, depth, alpha, beta, maximizing_player):
        """Minimax algorithm with alpha-beta pruning."""
        legal_moves = get_legal_moves(board)
        is_terminal = winning_move(board, 1) or winning_move(board, -1) or len(legal_moves) == 0
        if depth == 0 or is_terminal:
            if is_terminal:
                if winning_move(board, 1):
                    return (None, 1000000)
                elif winning_move(board, -1):
                    return (None, -1000000)
                else:
                    return (None, 0)
            else:
                return (None, evaluate_board(board, 1))
        if maximizing_player:
            value = -np.inf
            column = np.random.choice(legal_moves)
            for col in legal_moves:
                new_board = drop_piece(board, col, 1)
                if new_board is None:
                    continue #Column is full
                new_score = minimax(new_board, depth-1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:
            value = np.inf
            column = np.random.choice(legal_moves)
            for col in legal_moves:
                new_board = drop_piece(board, col, -1)
                if new_board is None:
                   continue
                new_score = minimax(new_board, depth-1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    # Convert board to numpy array for easier processing
    board = np.array(board)

    legal_moves = get_legal_moves(board)

    # Check for immediate winning move
    for col in legal_moves:
        temp_board = drop_piece(board.tolist(), col, 1)  # Use tolist() to convert NumPy array to list
        if temp_board is not None and winning_move(temp_board, 1):
            return col

    # Check for opponent's winning move and block it
    for col in legal_moves:
        temp_board = drop_piece(board.tolist(), col, -1)  # Use tolist() to convert NumPy array to list
        if temp_board is not None and winning_move(temp_board, -1):
            return col

    # Use minimax to find the best move
    start_time = time.time()
    depth = 1
    best_move = np.random.choice(legal_moves) # Default random move
    while time.time() - start_time < 0.9:
      try:
        move, score = minimax(board.tolist(), depth, -np.inf, np.inf, True)  # Use tolist()
        if move is not None:
          best_move = move
        depth += 1 #Increase the search depth for iterative deepening
      except Exception as e:
        break
    return best_move
