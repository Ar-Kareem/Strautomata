
import random

def policy(board: list[list[int]]) -> int:
    def is_valid_location(board, col):
        return board[0][col] == 0

    def get_next_open_row(board, col):
        for r in reversed(range(6)):
            if board[r][col] == 0:
                return r
        return None

    def board_copy(board):
        return [row[:] for row in board]

    def check_winning_move(board, piece):
        # Check horizontal
        for r in range(6):
            for c in range(4):
                if all(board[r][c + i] == piece for i in range(4)):
                    return True
        # Check vertical
        for c in range(7):
            for r in range(3):
                if all(board[r + i][c] == piece for i in range(4)):
                    return True
        # Check positive diagonal
        for r in range(3):
            for c in range(4):
                if all(board[r + i][c + i] == piece for i in range(4)):
                    return True
        # Check negative diagonal
        for r in range(3):
            for c in range(3, 7):
                if all(board[r + i][c - i] == piece for i in range(4)):
                    return True
        return False

    def is_terminal_node(board):
        return check_winning_move(board, 1) or check_winning_move(board, -1) or len(get_valid_locations(board)) == 0

    def get_valid_locations(board):
        valid = []
        for col in range(7):
            if board[0][col] == 0:
                valid.append(col)
        return valid

    def evaluate_window(window, me, opponent):
        score = 0
        my_count = window.count(me)
        their_count = window.count(opponent)
        if my_count == 4:
            score += 100
        elif their_count == 4:
            score -= 100
        else:
            if my_count == 3 and their_count == 0:
                score += 50
            elif my_count == 2 and their_count == 0:
                score += 20
            elif their_count == 3 and my_count == 0:
                score -= 40
        return score

    def score_position(board, me):
        opponent = -1 if me == 1 else 1
        score = 0
        # Score horizontal
        for r in range(6):
            for c in range(4):
                window = [board[r][c + i] for i in range(4)]
                score += evaluate_window(window, me, opponent)
        # Score vertical
        for c in range(7):
            for r in range(3):
                window = [board[r + i][c] for i in range(4)]
                score += evaluate_window(window, me, opponent)
        # Score positive slope diagonal
        for r in range(3):
            for c in range(4):
                window = [board[r + i][c + i] for i in range(4)]
                score += evaluate_window(window, me, opponent)
        # Score negative slope diagonal
        for r in range(3):
            for c in range(3, 7):
                window = [board[r + i][c - i] for i in range(4)]
                score += evaluate_window(window, me, opponent)
        return score

    def minimax(board, depth, alpha, beta, maximizing_player):
        valid_columns = get_valid_locations(board)
        is_terminal = is_terminal_node(board)
        if depth == 0 or is_terminal:
            if is_terminal:
                if check_winning_move(board, 1):
                    return (None, float('inf'))
                elif check_winning_move(board, -1):
                    return (None, -float('inf'))
                else:
                    return (None, 0)
            else:
                return (None, score_position(board, 1))
        if maximizing_player:
            value = -float('inf')
            best_col = valid_columns[0]
            for col in valid_columns:
                row = get_next_open_row(board, col)
                temp_board = board_copy(board)
                temp_board[row][col] = 1
                _, new_score = minimax(temp_board, depth - 1, alpha, beta, False)
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return best_col, value
        else:
            value = float('inf')
            best_col = valid_columns[0]
            for col in valid_columns:
                row = get_next_open_row(board, col)
                temp_board = board_copy(board)
                temp_board[row][col] = -1
                _, new_score = minimax(temp_board, depth - 1, alpha, beta, True)
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col, value

    valid_moves = get_valid_locations(board)
    if not valid_moves:
        return 0
    best_col, _ = minimax(board, 4, -float('inf'), float('inf'), True)
    return best_col
