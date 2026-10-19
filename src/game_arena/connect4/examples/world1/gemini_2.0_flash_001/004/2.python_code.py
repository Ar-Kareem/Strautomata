
import numpy as np

def policy(board: list[list[int]]) -> int:
    """
    A Connect 4 policy based on minimax search with alpha-beta pruning and heuristics.
    """
    board = np.array(board)
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

        # Check positive diagonals
        for c in range(4):
            for r in range(3):
                if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                    return True

        # Check negative diagonals
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
        score += center_array.count(piece) * 3

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

        # Score positive sloped diagonal
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)

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
                    return (None, 1000000000000)
                elif winning_move(board, -1):
                    return (None, -1000000000000)
                else: # Game is over, no more valid moves
                    return (None, 0)
            else: # Depth is zero
                return (None, score_position(board, 1))

        if maximizingPlayer:
            value = -np.Inf
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
            value = np.Inf
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
        
    # Check for winning move for self
    for col in range(7):
        if is_valid_move(board, col):
            row = get_next_open_row(board, col)
            temp_board = board.copy()
            drop_piece(temp_board, row, col, 1)
            if winning_move(temp_board, 1):
                return col

    # Check for winning move for opponent and block it
    for col in range(7):
        if is_valid_move(board, col):
            row = get_next_open_row(board, col)
            temp_board = board.copy()
            drop_piece(temp_board, row, col, -1)
            if winning_move(temp_board, -1):
                return col
            
    #Check for traps
    for col in range(7):
        if is_valid_move(board, col):
            row = get_next_open_row(board, col)
            temp_board = board.copy()
            drop_piece(temp_board, row, col, 1)
            
            can_opponent_win_next_turn = True
            opponent_valid_moves = get_valid_locations(temp_board)
            for opponent_col in opponent_valid_moves:
              opponent_row = get_next_open_row(temp_board, opponent_col)
              opponent_temp_board = temp_board.copy()
              drop_piece(opponent_temp_board, opponent_row, opponent_col, -1)
              if not winning_move(opponent_temp_board, -1):
                  can_opponent_win_next_turn = False

            if can_opponent_win_next_turn and len(opponent_valid_moves) != 0:
               continue
            
    # Choose the best move using minimax search
    valid_locations = get_valid_locations(board)
    if len(valid_locations) == 0:
        return 0  # No valid moves, return a default value

    #Adjusted depth for initial moves and avoid time exceeds
    if sum(sum(abs(board))) < 5:
        depth = 5
    else:
        depth = 4
    
    col, minimax_score = minimax(board, depth, -np.Inf, np.Inf, True)

    return col
