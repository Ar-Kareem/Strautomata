
import numpy as np

def policy(board: list[list[int]]) -> int:
    # Configuration
    ROW_COUNT = 6
    COLUMN_COUNT = 7
    PLAYER = 1
    OPPONENT = -1
    EMPTY = 0
    WINDOW_LENGTH = 4
    DEPTH = 5

    def get_valid_locations(grid):
        return [c for c in range(COLUMN_COUNT) if grid[0][c] == EMPTY]

    def get_next_open_row(grid, col):
        for r in range(ROW_COUNT - 1, -1, -1):
            if grid[r][col] == EMPTY:
                return r

    def drop_piece(grid, row, col, piece):
        grid[row][col] = piece

    def evaluate_window(window, piece):
        score = 0
        opp_piece = OPPONENT if piece == PLAYER else PLAYER

        if window.count(piece) == 4:
            score += 10000
        elif window.count(piece) == 3 and window.count(EMPTY) == 1:
            score += 100
        elif window.count(piece) == 2 and window.count(EMPTY) == 2:
            score += 10

        if window.count(opp_piece) == 3 and window.count(EMPTY) == 1:
            score -= 80

        return score

    def score_position(grid, piece):
        score = 0
        # Score center column
        center_array = [grid[r][COLUMN_COUNT // 2] for r in range(ROW_COUNT)]
        score += center_array.count(piece) * 6

        # Score Horizontal
        for r in range(ROW_COUNT):
            row_array = grid[r]
            for c in range(COLUMN_COUNT - 3):
                window = row_array[c : c + WINDOW_LENGTH]
                score += evaluate_window(window, piece)

        # Score Vertical
        for c in range(COLUMN_COUNT):
            col_array = [grid[r][c] for r in range(ROW_COUNT)]
            for r in range(ROW_COUNT - 3):
                window = col_array[r : r + WINDOW_LENGTH]
                score += evaluate_window(window, piece)

        # Score positive sloped diagonal
        for r in range(ROW_COUNT - 3):
            for c in range(COLUMN_COUNT - 3):
                window = [grid[r + i][c + i] for i in range(WINDOW_LENGTH)]
                score += evaluate_window(window, piece)

        # Score negative sloped diagonal
        for r in range(ROW_COUNT - 3):
            for c in range(COLUMN_COUNT - 3):
                window = [grid[r + 3 - i][c + i] for i in range(WINDOW_LENGTH)]
                score += evaluate_window(window, piece)

        return score

    def is_terminal_node(grid):
        # Checks for a win for either player or a full board
        def check_win(p):
            for c in range(COLUMN_COUNT - 3):
                for r in range(ROW_COUNT):
                    if grid[r][c] == p and grid[r][c+1] == p and grid[r][c+2] == p and grid[r][c+3] == p: return True
            for c in range(COLUMN_COUNT):
                for r in range(ROW_COUNT - 3):
                    if grid[r][c] == p and grid[r+1][c] == p and grid[r+2][c] == p and grid[r+3][c] == p: return True
            for c in range(COLUMN_COUNT - 3):
                for r in range(ROW_COUNT - 3):
                    if grid[r][c] == p and grid[r+1][c+1] == p and grid[r+2][c+2] == p and grid[r+3][c+3] == p: return True
            for c in range(COLUMN_COUNT - 3):
                for r in range(3, ROW_COUNT):
                    if grid[r][c] == p and grid[r-1][c+1] == p and grid[r-2][c+2] == p and grid[r-3][c+3] == p: return True
            return False

        return check_win(PLAYER) or check_win(OPPONENT) or len(get_valid_locations(grid)) == 0

    def minimax(grid, depth, alpha, beta, maximizingPlayer):
        valid_locations = get_valid_locations(grid)
        terminal = is_terminal_node(grid)
        if depth == 0 or terminal:
            if terminal:
                # Strong weights for terminal states
                if any(all(grid[r][c+i] == PLAYER for i in range(4)) for r in range(ROW_COUNT) for c in range(COLUMN_COUNT-3)): return (None, 1000000)
                # (Simplified check logic for brevity in recursion)
                return (None, score_position(grid, PLAYER))
            else:
                return (None, score_position(grid, PLAYER))

        if maximizingPlayer:
            value = -float('inf')
            column = np.random.choice(valid_locations)
            for col in valid_locations:
                row = get_next_open_row(grid, col)
                temp_grid = [r[:] for r in grid]
                drop_piece(temp_grid, row, col, PLAYER)
                new_score = minimax(temp_grid, depth - 1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:
            value = float('inf')
            column = np.random.choice(valid_locations)
            for col in valid_locations:
                row = get_next_open_row(grid, col)
                temp_grid = [r[:] for r in grid]
                drop_piece(temp_grid, row, col, OPPONENT)
                new_score = minimax(temp_grid, depth - 1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    # Main execution logic
    col, _ = minimax(board, DEPTH, -float('inf'), float('inf'), True)
    return int(col)
