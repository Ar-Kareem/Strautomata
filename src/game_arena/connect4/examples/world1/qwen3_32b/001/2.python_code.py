
import numpy as np

def policy(board: list[list[int]]) -> int:
    def is_valid_location(b, col):
        return any(b[row][col] == 0 for row in range(6))

    def get_next_open_row(b, col):
        for r in reversed(range(6)):
            if b[r][col] == 0:
                return r
        return None

    def is_winning_position(b, player):
        # Check horizontal
        for r in range(6):
            for c in range(4):
                if b[r][c] == player and b[r][c+1] == player and b[r][c+2] == player and b[r][c+3] == player:
                    return True
        # Check vertical
        for c in range(7):
            for r in range(3):
                if b[r][c] == player and b[r+1][c] == player and b[r+2][c] == player and b[r+3][c] == player:
                    return True
        # Check positive diagonal
        for r in range(3, 6):
            for c in range(4):
                if b[r][c] == player and b[r-1][c+1] == player and b[r-2][c+2] == player and b[r-3][c+3] == player:
                    return True
        # Check negative diagonal
        for r in range(3):
            for c in range(4):
                if b[r][c] == player and b[r+1][c+1] == player and b[r+2][c+2] == player and b[r+3][c+3] == player:
                    return True
        return False

    def create_board_copy(b):
        return [row.copy() for row in b]

    def evaluate_window(window, me, them):
        score = 0
        me_count = window.count(me)
        them_count = window.count(them)
        if them_count == 0:
            if me_count == 4:
                score += 100
            elif me_count == 3:
                score += 5
            elif me_count == 2:
                score += 2
        if me_count == 0 and them_count == 3:
            score -= 5
        elif me_count == 0 and them_count == 4:
            score -= 100
        return score

    def evaluate_board(b):
        score = 0
        # Center column bonus
        center_array = [b[row][3] for row in range(6)]
        center_me = center_array.count(1)
        center_them = center_array.count(-1)
        score += center_me * 3
        score -= center_them * 3
        # Horizontal
        for r in range(6):
            for c in range(4):
                window = [b[r][c], b[r][c+1], b[r][c+2], b[r][c+3]]
                score += evaluate_window(window, 1, -1)
        # Vertical
        for c in range(7):
            for r in range(3):
                window = [b[r][c], b[r+1][c], b[r+2][c], b[r+3][c]]
                score += evaluate_window(window, 1, -1)
        # Positive diagonal
        for r in range(3, 6):
            for c in range(4):
                window = [b[r][c], b[r-1][c+1], b[r-2][c+2], b[r-3][c+3]]
                score += evaluate_window(window, 1, -1)
        # Negative diagonal
        for r in range(3):
            for c in range(4):
                window = [b[r][c], b[r+1][c+1], b[r+2][c+2], b[r+3][c+3]]
                score += evaluate_window(window, 1, -1)
        return score

    def minimax(b, depth, alpha, beta, maximizing_player):
        valid_locations = [col for col in range(7) if is_valid_location(b, col)]
        is_terminal = is_winning_position(b, 1) or is_winning_position(b, -1) or len(valid_locations) == 0
        if depth == 0 or is_terminal:
            if is_terminal:
                if is_winning_position(b, 1):
                    return (1000000, None)
                elif is_winning_position(b, -1):
                    return (-1000000, None)
                else:  # draw
                    return (0, None)
            else:  # depth=0
                return (evaluate_board(b), None)
        if maximizing_player:
            value = -np.inf
            best_col = None
            for col in valid_locations:
                row = get_next_open_row(b, col)
                new_b = create_board_copy(b)
                new_b[row][col] = 1
                new_score = minimax(new_b, depth - 1, alpha, beta, False)[0]
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return (value, best_col)
        else:  # minimizing
            value = np.inf
            best_col = None
            for col in valid_locations:
                row = get_next_open_row(b, col)
                new_b = create_board_copy(b)
                new_b[row][col] = -1
                new_score = minimax(new_b, depth - 1, alpha, beta, True)[0]
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return (value, best_col)

    best_score, best_col = minimax(board, 4, -np.inf, np.inf, True)
    valid_locations = [col for col in range(7) if is_valid_location(board, col)]
    if best_col is None:
        return valid_locations[0]
    return best_col
