
import random

def policy(board: list[list[int]]) -> int:
    ROWS = 6
    COLS = 7
    EMPTY = 0
    PLAYER = 1
    OPPONENT = -1

    def get_valid_locations(grid):
        return [c for c in range(COLS) if grid[0][c] == EMPTY]

    def get_next_open_row(grid, col):
        for r in range(ROWS - 1, -1, -1):
            if grid[r][col] == EMPTY:
                return r
        return None

    def drop_piece(grid, row, col, piece):
        new_grid = [row[:] for row in grid]
        new_grid[row][col] = piece
        return new_grid

    def is_winning_move(grid, piece):
        # Horizontal
        for c in range(COLS - 3):
            for r in range(ROWS):
                if grid[r][c] == piece and grid[r][c+1] == piece and grid[r][c+2] == piece and grid[r][c+3] == piece:
                    return True
        # Vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                if grid[r][c] == piece and grid[r+1][c] == piece and grid[r+2][c] == piece and grid[r+3][c] == piece:
                    return True
        # Positive diagonal
        for c in range(COLS - 3):
            for r in range(ROWS - 3):
                if grid[r][c] == piece and grid[r+1][c+1] == piece and grid[r+2][c+2] == piece and grid[r+3][c+3] == piece:
                    return True
        # Negative diagonal
        for c in range(COLS - 3):
            for r in range(3, ROWS):
                if grid[r][c] == piece and grid[r-1][c+1] == piece and grid[r-2][c+2] == piece and grid[r-3][c+3] == piece:
                    return True
        return False

    def evaluate_window(window, piece):
        score = 0
        opp_piece = -piece
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
        # Center column preference
        center_array = [grid[r][COLS // 2] for r in range(ROWS)]
        center_count = center_array.count(piece)
        score += center_count * 6

        # Horizontal
        for r in range(ROWS):
            row_array = grid[r]
            for c in range(COLS - 3):
                window = row_array[c:c+4]
                score += evaluate_window(window, piece)

        # Vertical
        for c in range(COLS):
            col_array = [grid[r][c] for r in range(ROWS)]
            for r in range(ROWS - 3):
                window = col_array[r:r+4]
                score += evaluate_window(window, piece)

        # Diagonals
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [grid[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [grid[r+3-i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)

        return score

    def minimax(grid, depth, alpha, beta, maximizingPlayer):
        valid_locations = get_valid_locations(grid)
        is_terminal = is_winning_move(grid, PLAYER) or is_winning_move(grid, OPPONENT) or len(valid_locations) == 0
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if is_winning_move(grid, PLAYER):
                    return (None, 10000000)
                elif is_winning_move(grid, OPPONENT):
                    return (None, -10000000)
                else:
                    return (None, 0)
            else:
                return (None, score_position(grid, PLAYER))

        if maximizingPlayer:
            value = -float('inf')
            column = random.choice(valid_locations)
            # Reorder valid_locations to check center first for better pruning
            valid_locations.sort(key=lambda x: abs(x - 3))
            for col in valid_locations:
                row = get_next_open_row(grid, col)
                b_copy = drop_piece(grid, row, col, PLAYER)
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
            column = random.choice(valid_locations)
            valid_locations.sort(key=lambda x: abs(x - 3))
            for col in valid_locations:
                row = get_next_open_row(grid, col)
                b_copy = drop_piece(grid, row, col, OPPONENT)
                new_score = minimax(b_copy, depth - 1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    # Depth 4 is generally safe for Python under 1s
    col, _ = minimax(board, 4, -float('inf'), float('inf'), True)
    return col if col is not None else random.choice(get_valid_locations(board))
