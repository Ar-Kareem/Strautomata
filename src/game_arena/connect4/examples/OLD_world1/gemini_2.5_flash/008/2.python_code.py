
import random

def policy(board: list[list[int]]) -> int:
    ROWS = len(board)
    COLS = len(board[0])

    def is_valid_location(board, col):
        return board[0][col] == 0

    def get_next_open_row(board, col):
        for r in range(ROWS - 1, -1, -1):
            if board[r][col] == 0:
                return r
        return -1 # Should not happen if column is valid

    def check_win(board, player):
        # Check horizontal locations for win
        for c in range(COLS - 3):
            for r in range(ROWS):
                if board[r][c] == player and board[r][c + 1] == player and board[r][c + 2] == player and board[r][c + 3] == player:
                    return True

        # Check vertical locations for win
        for c in range(COLS):
            for r in range(ROWS - 3):
                if board[r][c] == player and board[r + 1][c] == player and board[r + 2][c] == player and board[r + 3][c] == player:
                    return True

        # Check positively sloped diagonals
        for c in range(COLS - 3):
            for r in range(ROWS - 3):
                if board[r][c] == player and board[r + 1][c + 1] == player and board[r + 2][c + 2] == player and board[r + 3][c + 3] == player:
                    return True

        # Check negatively sloped diagonals
        for c in range(COLS - 3):
            for r in range(3, ROWS):
                if board[r][c] == player and board[r - 1][c + 1] == player and board[r - 2][c + 2] == player and board[r - 3][c + 3] == player:
                    return True
        return False

    def get_score(board, player):
        score = 0
        # Center column preference
        center_col = COLS // 2
        center_count = sum(1 for r in range(ROWS) if board[r][center_col] == player)
        score += center_count * 3

        # Evaluate windows of 4
        def evaluate_window(window, player):
            score_window = 0
            opponent = -player
            if window.count(player) == 4:
                score_window += 100000 # Winning move
            elif window.count(player) == 3 and window.count(0) == 1:
                score_window += 100 # Potential win
            elif window.count(player) == 2 and window.count(0) == 2:
                score_window += 10
            if window.count(opponent) == 3 and window.count(0) == 1:
                score_window -= 50000 # Block opponent's win
            return score_window

        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = board[r][c:c + 4]
                score += evaluate_window(window, player)

        # Vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                window = [board[r + i][c] for i in range(4)]
                score += evaluate_window(window, player)

        # Positive diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [board[r + i][c + i] for i in range(4)]
                score += evaluate_window(window, player)

        # Negative diagonal
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [board[r - i][c + i] for i in range(4)]
                score += evaluate_window(window, player)
        return score

    # Minimax (simplified - 2 ply for performance)
    # This is a very simplified minimax; a full minimax with alpha-beta pruning and a deeper search would be better
    # but might exceed the time limit.

    best_score = -float('inf')
    best_col = random.choice([col for col in range(COLS) if is_valid_location(board, col)])

    valid_cols = [col for col in range(COLS) if is_valid_location(board, col)]
    random.shuffle(valid_cols) # randomize order to avoid always picking the leftmost equal-score column

    for col in valid_cols:
        r = get_next_open_row(board, col)
        
        # Simulate our move
        temp_board_our_move = [row[:] for row in board]
        temp_board_our_move[r][col] = 1

        if check_win(temp_board_our_move, 1):
            return col # Immediate win

        # Simulate opponent's best response (1-ply lookahead for opponent)
        opponent_best_score_response = float('inf')
        
        opponent_valid_moves = [c for c in range(COLS) if is_valid_location(temp_board_our_move, c)]
        if not opponent_valid_moves: # Game might be over or no moves left for opponent
             current_score = get_score(temp_board_our_move, 1)
             if current_score > best_score:
                best_score = current_score
                best_col = col
             continue

        for opp_col in opponent_valid_moves:
            opp_r = get_next_open_row(temp_board_our_move, opp_col)
            
            temp_board_opp_move = [row[:] for row in temp_board_our_move]
            temp_board_opp_move[opp_r][opp_col] = -1

            if check_win(temp_board_opp_move, -1): # Opponent can win next turn
                opponent_best_score_response = -float('inf') # Mark as very bad move for us
                break # Opponent found a winning move, no need to check other moves for them

            score_after_opp_move = get_score(temp_board_opp_move, 1)
            opponent_best_score_response = min(opponent_best_score_response, score_after_opp_move)
        
        # Consider the worst case after our move + opponent's response
        current_score = opponent_best_score_response
        
        if current_score > best_score:
            best_score = current_score
            best_col = col

    return best_col
