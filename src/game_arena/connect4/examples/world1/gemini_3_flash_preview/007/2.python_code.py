
import random

def policy(board: list[list[int]]) -> int:
    # Constants
    ROWS = 6
    COLS = 7
    PLAYER = 1
    OPPONENT = -1
    EMPTY = 0
    
    def get_valid_locations(grid):
        return [c for c in range(COLS) if grid[0][c] == EMPTY]

    def get_next_open_row(grid, col):
        for r in range(ROWS-1, -1, -1):
            if grid[r][col] == EMPTY:
                return r
        return -1

    def drop_piece(grid, row, col, piece):
        new_grid = [row[:] for row in grid]
        new_grid[row][col] = piece
        return new_grid

    def score_window(window, piece):
        score = 0
        opp_piece = -piece
        if window.count(piece) == 4:
            score += 1000
        elif window.count(piece) == 3 and window.count(EMPTY) == 1:
            score += 10
        elif window.count(piece) == 2 and window.count(EMPTY) == 2:
            score += 2
        
        if window.count(opp_piece) == 3 and window.count(EMPTY) == 1:
            score -= 80
            
        return score

    def score_position(grid, piece):
        score = 0
        
        # Score center column
        center_array = [grid[r][COLS//2] for r in range(ROWS)]
        center_count = center_array.count(piece)
        score += center_count * 3

        # Score Horizontal
        for r in range(ROWS):
            row_array = grid[r]
            for c in range(COLS-3):
                window = row_array[c:c+4]
                score += score_window(window, piece)

        # Score Vertical
        for c in range(COLS):
            col_array = [grid[r][c] for r in range(ROWS)]
            for r in range(ROWS-3):
                window = col_array[r:r+4]
                score += score_window(window, piece)

        # Score positive sloped diagonal
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = [grid[r+3-i][c+i] for i in range(4)]
                score += score_window(window, piece)

        # Score negative sloped diagonal
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = [grid[r+i][c+i] for i in range(4)]
                score += score_window(window, piece)

        return score

    def is_terminal_node(grid):
        # Returns True if someone won or board is full
        def check_win(p):
            for c in range(COLS-3):
                for r in range(ROWS):
                    if grid[r][c] == p and grid[r][c+1] == p and grid[r][c+2] == p and grid[r][c+3] == p: return True
            for c in range(COLS):
                for r in range(ROWS-3):
                    if grid[r][c] == p and grid[r+1][c] == p and grid[r+2][c] == p and grid[r+3][c] == p: return True
            for c in range(COLS-3):
                for r in range(ROWS-3):
                    if grid[r][c] == p and grid[r+1][c+1] == p and grid[r+2][c+2] == p and grid[r+3][c+3] == p: return True
            for c in range(COLS-3):
                for r in range(3, ROWS):
                    if grid[r][c] == p and grid[r-1][c+1] == p and grid[r-2][c+2] == p and grid[r-3][c+3] == p: return True
            return False

        if check_win(PLAYER) or check_win(OPPONENT) or len(get_valid_locations(grid)) == 0:
            return True, check_win(PLAYER), check_win(OPPONENT)
        return False, False, False

    def minimax(grid, depth, alpha, beta, maximizingPlayer):
        valid_locations = get_valid_locations(grid)
        terminal, win_p, win_o = is_terminal_node(grid)
        if depth == 0 or terminal:
            if terminal:
                if win_p: return (None, 10000000)
                elif win_o: return (None, -10000000)
                else: return (None, 0)
            else:
                return (None, score_position(grid, PLAYER))

        # Reorder valid locations to check center first
        valid_locations.sort(key=lambda x: abs(x - 3))

        if maximizingPlayer:
            value = -float('inf')
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = get_next_open_row(grid, col)
                b_copy = drop_piece(grid, row, col, PLAYER)
                new_score = minimax(b_copy, depth-1, alpha, beta, False)[1]
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
            for col in valid_locations:
                row = get_next_open_row(grid, col)
                b_copy = drop_piece(grid, row, col, OPPONENT)
                new_score = minimax(b_copy, depth-1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    col, _ = minimax(board, 5, -float('inf'), float('inf'), True)
    return col
